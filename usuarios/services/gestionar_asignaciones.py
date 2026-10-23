"""Edición y revocación de relaciones de Empresa con controles y auditoría."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from usuarios.models import (
    AsignacionUsuarioEmpresa, CentroAdicionalAdministrador, CentroOperativo,
    EventoGestionAsignacion, PermisoAccesoColaborador, PermisoPendienteBancarioCentro,
    RolFuncionalUsuarioEmpresa,
)
from usuarios.services.alcances_centros import centros_activos_de_asignacion
from usuarios.services.seguridad import obtener_empresa_administrable


def _id_estricto(valor):
    try:
        numero = int(valor)
    except (ValueError, TypeError) as error:
        raise ValidationError('Identificador inválido.') from error
    if numero <= 0:
        raise ValidationError('Identificador inválido.')
    return numero


@transaction.atomic
def guardar_centros_asignacion(*, actor, empresa_id, asignacion_id, centros):
    """Reemplaza el conjunto de centros de un Administrador existente; nunca concede otros."""
    empresa = obtener_empresa_administrable(actor, empresa_id)
    try:
        asignacion = AsignacionUsuarioEmpresa.objects.select_for_update().get(
            pk=_id_estricto(asignacion_id), empresa=empresa, activo=True,
            jerarquia='admin_centro',
        )
    except AsignacionUsuarioEmpresa.DoesNotExist as error:
        raise PermissionDenied('No existe una asignación activa autorizada.') from error
    if not isinstance(centros, (list, tuple)) or not centros or len(centros) > 100:
        raise ValidationError('Seleccioná al menos un Centro Operativo.')
    nuevos = [_id_estricto(x) for x in centros]
    if len(set(nuevos)) != len(nuevos):
        raise ValidationError('No se permiten centros duplicados.')
    validos = set(CentroOperativo.objects.filter(
        pk__in=nuevos, empresa=empresa, activo=True,
    ).values_list('pk', flat=True))
    if validos != set(nuevos):
        raise PermissionDenied('Todos los centros deben estar activos y pertenecer a la Empresa.')
    anteriores = sorted(centros_activos_de_asignacion(asignacion))
    # Conservamos el centro principal si sigue seleccionado: compatibilidad de consumidores legacy.
    principal = asignacion.centro_operativo_id if asignacion.centro_operativo_id in validos else nuevos[0]
    asignacion.centro_operativo_id = principal
    asignacion.full_clean()
    asignacion.save(update_fields=['centro_operativo', 'actualizado'])
    adicionales = set(nuevos) - {principal}
    CentroAdicionalAdministrador.objects.filter(asignacion=asignacion).exclude(
        centro_operativo_id__in=adicionales,
    ).delete()
    existentes = set(CentroAdicionalAdministrador.objects.filter(asignacion=asignacion)
                     .values_list('centro_operativo_id', flat=True))
    for centro_id in adicionales - existentes:
        CentroAdicionalAdministrador.objects.create(asignacion=asignacion, centro_operativo_id=centro_id)
    if set(anteriores) != validos:
        EventoGestionAsignacion.objects.create(
            empresa=empresa, usuario=asignacion.usuario, actor=actor,
            accion='actualizar_centros', detalle={'antes':anteriores,'despues':sorted(validos)},
        )
    return asignacion


@transaction.atomic
def revocar_relacion(*, actor, empresa_id, relacion_id, tipo):
    """Revoca relación sin destruir registros históricos ni permisos anteriores auditados."""
    empresa = obtener_empresa_administrable(actor, empresa_id)
    pk = _id_estricto(relacion_id)
    if tipo == 'jerarquia':
        try:
            objeto = AsignacionUsuarioEmpresa.objects.select_for_update().get(
                pk=pk, empresa=empresa, activo=True,
            )
        except AsignacionUsuarioEmpresa.DoesNotExist as error:
            raise PermissionDenied('La relación no está activa.') from error
        antes = sorted(centros_activos_de_asignacion(objeto))
        objeto.activo = False
        objeto.save(update_fields=['activo', 'actualizado'])
        # La revocación también anula los privilegios funcionales que podrían
        # quedar latentes y resucitar ante un cambio de jerarquía.
        PermisoAccesoColaborador.objects.filter(empresa=empresa, usuario=objeto.usuario, activo=True).update(activo=False)
        PermisoPendienteBancarioCentro.objects.filter(empresa=empresa, usuario=objeto.usuario, activo=True).update(activo=False)
        CentroAdicionalAdministrador.objects.filter(asignacion=objeto).delete()
        from usuarios.models import PermisoNominaCentro
        PermisoNominaCentro.objects.filter(empresa=empresa,usuario=objeto.usuario,activo=True).update(activo=False)
        detalle = {'jerarquia':objeto.jerarquia, 'centros_anteriores':antes}
    elif tipo == 'funcional':
        try:
            objeto = RolFuncionalUsuarioEmpresa.objects.select_for_update().get(
                pk=pk, empresa=empresa, activo=True,
            )
        except RolFuncionalUsuarioEmpresa.DoesNotExist as error:
            raise PermissionDenied('El rol funcional no está activo.') from error
        objeto.activo = False
        objeto.save(update_fields=['activo', 'actualizado'])
        # Si ya no conserva vínculo alguno, no dejar permisos de Nómina latentes.
        if (not AsignacionUsuarioEmpresa.objects.filter(empresa=empresa,usuario=objeto.usuario,activo=True).exists()
                and not RolFuncionalUsuarioEmpresa.objects.filter(empresa=empresa,usuario=objeto.usuario,activo=True).exists()):
            from usuarios.models import PermisoNominaCentro
            PermisoNominaCentro.objects.filter(empresa=empresa,usuario=objeto.usuario,activo=True).update(activo=False)
            PermisoAccesoColaborador.objects.filter(empresa=empresa,usuario=objeto.usuario,codigo='nomina.total',activo=True).update(activo=False)
        detalle = {'rol':objeto.rol}
    else:
        raise ValidationError('Tipo de relación inválido.')
    EventoGestionAsignacion.objects.create(
        empresa=empresa, usuario=objeto.usuario, actor=actor,
        accion='revocar_'+tipo, detalle=detalle,
    )
    return objeto
