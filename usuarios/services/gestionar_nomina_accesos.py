"""Persistencia atómica, verificable y auditable de los permisos de Nómina."""
from django.core.exceptions import PermissionDenied
from django.db import transaction
from usuarios.models import (CentroOperativo, Empresa, EventoGestionAsignacion,
    PermisoNominaCentro, AsignacionUsuarioEmpresa)
from usuarios.services.accesos_colaborador import guardar_accesos, exigir_administrar_permisos


@transaction.atomic
def guardar_permisos_operativos(*,administrador,empresa_id,usuario_id,codigos,centros_nomina):
    empresa = exigir_administrar_permisos(administrador,empresa_id)
    Empresa.objects.select_for_update().get(pk=empresa.pk)
    try:
        usuario_id = int(usuario_id)
        centros_solicitados = [int(c) for c in centros_nomina]
    except (TypeError,ValueError) as e:
        raise PermissionDenied('Selección de Centros no válida.') from e
    if len(centros_solicitados)>500:
        raise PermissionDenied('Demasiados Centros.')
    ids = set(centros_solicitados)
    encontrados = set(CentroOperativo.objects.filter(empresa=empresa,activo=True,pk__in=ids)
                     .values_list('pk',flat=True))
    if ids != encontrados:
        raise PermissionDenied('Se incluyó un Centro ajeno o inactivo.')
    if 'nomina.total' in codigos:
        jerarquia = AsignacionUsuarioEmpresa.objects.filter(empresa=empresa,
            usuario_id=usuario_id,activo=True).values_list('jerarquia',flat=True).first()
        if jerarquia == 'admin_centro':
            if ids: raise PermissionDenied('Administrador de Centro utiliza su asignación, no Centros manuales.')
        elif not ids:
            raise PermissionDenied('Nómina requiere seleccionar al menos un Centro.')
    elif ids:
        raise PermissionDenied('No se pueden asignar Centros con Nómina deshabilitada.')
    # El guardado de permisos de módulos y centros es UNA transacción.
    guardar_accesos(administrador=administrador,empresa_id=empresa.pk,
                    colaborador_id=usuario_id,codigos=codigos)
    anteriores = set(PermisoNominaCentro.objects.select_for_update().filter(
        empresa=empresa,usuario_id=usuario_id,activo=True).values_list('centro_operativo_id',flat=True))
    nuevos = ids if 'nomina.total' in codigos else set()
    for p in PermisoNominaCentro.objects.select_for_update().filter(empresa=empresa,usuario_id=usuario_id):
        activo = p.centro_operativo_id in nuevos
        if p.activo != activo:
            p.activo = activo
            p.otorgado_por = administrador
            p.save(update_fields=['activo','otorgado_por','modificado'])
    existentes = set(PermisoNominaCentro.objects.filter(empresa=empresa,usuario_id=usuario_id)
                     .values_list('centro_operativo_id',flat=True))
    for centro in sorted(nuevos-existentes):
        PermisoNominaCentro.objects.create(empresa=empresa,usuario_id=usuario_id,
            centro_operativo_id=centro,otorgado_por=administrador)
    if anteriores != nuevos:
        EventoGestionAsignacion.objects.create(empresa=empresa,usuario_id=usuario_id,
            actor=administrador,accion='permisos_nomina_centros',
            detalle={'antes':sorted(anteriores),'despues':sorted(nuevos)})
