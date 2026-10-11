"""Caja 2: tareas de aplicación externa, SIN crear pagos ni saldos.

Una autorización administrativa por Centro no concede acceso a Caja.
"""
import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from usuarios.models import (AsignacionUsuarioEmpresa, CentroOperativo, CuentaBancaria,
    Empresa, EventoPendienteBancario, EventoPermisoBancario, PendienteBancario, PermisoPendienteBancarioCentro)
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.identidades import obtener_identidad_usuario_empresa

LOG = logging.getLogger('ordenaclick.audit')


def alcance_pendientes(usuario, empresa_id):
    """(Empresa, None si alcance global; frozenset centros activos si limitado).

    Una asignación de Colaborador por sí sola no habilita nada.
    El acceso a una Empresa de otra persona nunca nace de IDs del cliente.
    """
    contexto = obtener_contexto_capacidades_empresa(usuario, empresa_id)
    empresa = contexto.empresa
    if contexto.es_superusuario or contexto.es_propietario or contexto.jerarquia == 'admin_general':
        return empresa, None
    if contexto.jerarquia == 'admin_centro':
        if not contexto.centro_operativo_id:
            raise PermissionDenied('No tiene Centro activo autorizado.')
        if not CentroOperativo.objects.filter(pk=contexto.centro_operativo_id, empresa=empresa, activo=True).exists():
            raise PermissionDenied('El Centro no está activo.')
        return empresa, frozenset([contexto.centro_operativo_id])
    if contexto.jerarquia == 'colaborador':
        centros = frozenset(PermisoPendienteBancarioCentro.objects.filter(
            empresa=empresa, usuario=usuario, activo=True,
            centro_operativo__empresa=empresa, centro_operativo__activo=True,
        ).values_list('centro_operativo_id', flat=True))
        if centros:
            return empresa, centros
    raise PermissionDenied('No tiene permisos para gestionar pendientes bancarios.')


def exigir_centro(centro_id, centros):
    if centro_id is None or str(centro_id).strip() == '':
        if centros is not None:
            raise PermissionDenied('Los pendientes sin Centro son exclusivos de administración general.')
        return None
    try:
        pk = int(centro_id)
    except (TypeError, ValueError) as exc:
        raise PermissionDenied('Centro no autorizado.') from exc
    if centros is not None and pk not in centros:
        raise PermissionDenied('Centro no autorizado.')
    return pk


def importe_positivo(valor):
    if not isinstance(valor, str) or len(valor) > 30:
        raise ValueError('El importe no es válido.')
    texto = valor.strip()
    if re.fullmatch(r'[0-9]{1,3}(?:\.[0-9]{3})+(?:,[0-9]{1,2})?', texto):
        texto = texto.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'[0-9]+,[0-9]{1,2}', texto):
        texto = texto.replace(',', '.')
    elif not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,2})?', texto):
        raise ValueError('El importe no es válido.')
    try:
        importe = Decimal(texto)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('El importe no es válido.') from exc
    if (not importe.is_finite() or importe <= 0 or importe >= Decimal('1000000000000')
            or importe.as_tuple().exponent < -2):
        raise ValueError('El importe debe ser positivo, con hasta dos decimales.')
    return importe.quantize(Decimal('0.01'))


def registrar_pendiente(*, usuario, empresa_id, datos):
    empresa, alcance = alcance_pendientes(usuario, empresa_id)
    if alcance is not None:
        raise PermissionDenied('El registro de movimientos detectados requiere administración general.')
    centro_pk = exigir_centro(datos.get('centro'), alcance)
    if centro_pk is not None and not CentroOperativo.objects.filter(pk=centro_pk, empresa=empresa, activo=True).exists():
        raise PermissionDenied('Centro no autorizado.')
    cuenta = CuentaBancaria.objects.filter(pk=datos.get('cuenta'), empresa=empresa, activo=True).first()
    if cuenta is None:
        raise ValueError('Seleccione una Cuenta Bancaria de esta Empresa.')
    tipo = datos.get('tipo')
    if tipo not in ('Transferencia', 'Deposito', 'ECheq'):
        raise ValueError('Seleccione un tipo de operación válido.')
    fecha_texto = datos.get('fecha', '')
    try:
        fecha = date.fromisoformat(fecha_texto)
        if fecha.isoformat() != fecha_texto:
            raise ValueError()
    except (ValueError, TypeError) as exc:
        raise ValueError('Ingrese una fecha válida.') from exc
    referencia = datos.get('referencia', '')
    observaciones = datos.get('observaciones', '')
    if not isinstance(referencia, str) or not 1 <= len(referencia.strip()) <= 200:
        raise ValueError('La referencia es obligatoria (máximo 200 caracteres).')
    if not isinstance(observaciones, str) or len(observaciones) > 300:
        raise ValueError('Las observaciones superan el máximo permitido.')
    importe = importe_positivo(datos.get('importe'))
    try:
        clave = UUID(datos.get('clave', ''))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError('Identificador de operación inválido.') from exc
    with transaction.atomic():
        # Serializar por Empresa para evitar dos altas simultáneas con la misma clave.
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        anterior = PendienteBancario.objects.filter(clave=clave).first()
        if anterior:
            if (anterior.empresa_id != empresa.pk or anterior.cuenta_bancaria_id != cuenta.pk
                or anterior.centro_operativo_id != centro_pk or anterior.fecha != fecha
                or anterior.tipo != tipo or anterior.importe != importe
                or anterior.referencia != referencia.strip() or anterior.observaciones != observaciones.strip()
                or anterior.creado_por.usuario_id != usuario.pk):
                raise ValueError('La clave ya pertenece a otra operación.')
            return anterior, False
        identidad = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        pendiente = PendienteBancario.objects.create(
            empresa=empresa, cuenta_bancaria=cuenta, centro_operativo_id=centro_pk,
            clave=clave, fecha=fecha, tipo=tipo, importe=importe,
            referencia=referencia.strip(), observaciones=observaciones.strip(), creado_por=identidad)
        EventoPendienteBancario.objects.create(pendiente=pendiente, actor=identidad, accion='Creado')
    LOG.info('banco.pendiente_creado empresa_id=%s pendiente_id=%s', empresa.pk, pendiente.pk)
    return pendiente, True


def resolver_pendiente(*, usuario, empresa_id, pendiente_id, tipo_resolucion, referencia):
    empresa, alcance = alcance_pendientes(usuario, empresa_id)
    if tipo_resolucion not in ('YaImputado', 'ReciboGenerado'):
        raise ValueError('Seleccione el resultado de la comprobación.')
    if not isinstance(referencia, str) or not 3 <= len(referencia.strip()) <= 200:
        raise ValueError('Indique la referencia del recibo o la comprobación (3 a 200 caracteres).')
    with transaction.atomic():
        # Bloqueo global de la Empresa para impedir resoluciones concurrentes.
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        pendiente = PendienteBancario.objects.select_for_update().filter(pk=pendiente_id, empresa=empresa).first()
        if pendiente is None:
            raise PermissionDenied('Pendiente no autorizado.')
        exigir_centro(pendiente.centro_operativo_id, alcance)
        if pendiente.estado != 'Pendiente':
            raise ValueError('Este movimiento ya fue resuelto.')
        actor = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        pendiente.estado = 'Resuelto'
        pendiente.tipo_resolucion = tipo_resolucion
        pendiente.referencia_resolucion = referencia.strip()
        pendiente.resuelto_por = actor
        pendiente.resuelto_en = timezone.now()
        pendiente.save(update_fields=['estado', 'tipo_resolucion', 'referencia_resolucion',
                                      'resuelto_por', 'resuelto_en', 'modificado'])
        EventoPendienteBancario.objects.create(pendiente=pendiente, actor=actor, accion='Resuelto', detalle=tipo_resolucion)
    LOG.info('banco.pendiente_resuelto empresa_id=%s pendiente_id=%s', empresa.pk, pendiente.pk)
    return pendiente


def cambiar_permiso(*, admin, empresa_id, usuario_id, centro_id, activo):
    contexto = obtener_contexto_capacidades_empresa(admin, empresa_id)
    if not (contexto.es_superusuario or contexto.es_propietario or contexto.jerarquia == 'admin_general'):
        raise PermissionDenied('Sólo la administración general asigna Centros de gestión.')
    empresa = contexto.empresa
    from django.contrib.auth import get_user_model
    usuario = get_user_model().objects.filter(pk=usuario_id, is_active=True).first()
    centro = CentroOperativo.objects.filter(pk=centro_id, empresa=empresa, activo=True).first()
    if not centro or not usuario or not AsignacionUsuarioEmpresa.objects.filter(
        empresa=empresa, usuario=usuario, jerarquia='colaborador', activo=True).exists():
        raise ValueError('Seleccione un Colaborador activo y un Centro de la Empresa.')
    if activo not in ('1', '0'):
        raise ValueError('Seleccione conceder o revocar permiso.')
    with transaction.atomic():
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        identidad = obtener_identidad_usuario_empresa(empresa=empresa, usuario=admin)
        permiso, _ = PermisoPendienteBancarioCentro.objects.update_or_create(
            empresa=empresa, usuario=usuario, centro_operativo=centro,
            defaults={'activo': activo == '1', 'otorgado_por': identidad})
        EventoPermisoBancario.objects.create(empresa=empresa, usuario=usuario, centro_operativo=centro,
            actor=identidad, concedido=permiso.activo)
    LOG.info('banco.permiso_centro_%s empresa_id=%s centro_id=%s usuario_id=%s actor_id=%s',
             'concedido' if permiso.activo else 'revocado', empresa.pk, centro.pk, usuario.pk, admin.pk)
    return permiso


def clasificar_pendiente(*, admin, empresa_id, pendiente_id, centro_id):
    """Asignación del Centro por administración general, con evento inmutable."""
    empresa, alcance = alcance_pendientes(admin, empresa_id)
    if alcance is not None:
        raise PermissionDenied('Sólo administración general puede clasificar un pendiente.')
    centro = CentroOperativo.objects.filter(pk=centro_id, empresa=empresa, activo=True).first()
    if centro is None:
        raise ValueError('Centro no válido para la Empresa.')
    with transaction.atomic():
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        pendiente = PendienteBancario.objects.select_for_update().filter(pk=pendiente_id, empresa=empresa).first()
        if pendiente is None:
            raise PermissionDenied('Pendiente no autorizado.')
        if pendiente.estado != 'Pendiente' or pendiente.centro_operativo_id is not None:
            raise ValueError('Este pendiente no admite clasificación.')
        identidad = obtener_identidad_usuario_empresa(empresa=empresa, usuario=admin)
        pendiente.centro_operativo = centro
        pendiente.save(update_fields=['centro_operativo', 'modificado'])
        EventoPendienteBancario.objects.create(pendiente=pendiente, actor=identidad,
            accion='CentroAsignado', detalle=f'centro_id={centro.pk}')
    LOG.info('banco.pendiente_clasificado empresa_id=%s pendiente_id=%s centro_id=%s',
        empresa.pk, pendiente.pk, centro.pk)
    return pendiente
