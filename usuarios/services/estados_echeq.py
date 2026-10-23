"""Estado de cartera virtual de e-Cheqs detectados, separado de su imputación.

El registro no crea Cheque, Pago, Caja ni Alerta: sólo hechos auditables.
"""
import logging
from datetime import date, timedelta
from uuid import UUID

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from usuarios.models import (
    Empresa, EventoEstadoECheq, EventoPendienteBancario,
    PendienteBancario, RevisionPendienteBancario,
)
from usuarios.services.identidades import obtener_identidad_usuario_empresa
from usuarios.services.pendientes_bancarios import alcance_pendientes

LOG = logging.getLogger('ordenaclick.audit')
TRANSICIONES = {
    'EnCartera': ('Rechazado', 'Devuelto', 'Vencido'),
    'Rechazado': ('Devuelto',),
    'Vencido': ('Rechazado', 'Devuelto'),
    'Devuelto': (),
    'Depositado': (), 'Endosado': (), 'Cedido': (),
}
ETIQUETAS = {'EnCartera': 'En cartera', 'Rechazado': 'Rechazado',
             'Devuelto': 'Devuelto', 'Vencido': 'Vencido',
             'Depositado': 'Depositado', 'Endosado': 'Endosado', 'Cedido': 'Cedido'}


def _autorizar(usuario, empresa_id, pendiente_id, *, escritura=False):
    from usuarios.services.permisos_bancarios_accion import exigir, permitido
    if escritura:
        exigir(usuario,empresa_id,'pendientes.estado')
    elif not (permitido(usuario,empresa_id,'pendientes.estado')
              or permitido(usuario,empresa_id,'pendientes.ver')):
        raise PermissionDenied('Consulta de instrumento no autorizada.')
    empresa, alcance = alcance_pendientes(usuario, empresa_id)
    p = PendienteBancario.objects.filter(pk=pendiente_id, empresa=empresa, tipo='ECheq').first()
    if p is None:
        raise PermissionDenied('Instrumento no autorizado.')
    if p.estado == 'Resuelto' and alcance is not None and p.centro_operativo_id not in alcance:
        raise PermissionDenied('El Centro del instrumento no está autorizado.')
    return empresa, p


def _actor(actor):
    return actor.nombre_historico or actor.username_historico


def consultar_estado(*, usuario, empresa_id, pendiente_id):
    empresa, p = _autorizar(usuario, empresa_id, pendiente_id)
    _, alcance = alcance_pendientes(usuario, empresa.pk)
    from usuarios.services.permisos_bancarios_accion import permitido
    permiso_estado = permitido(usuario,empresa.pk,'pendientes.estado')
    eventos = []
    for e in EventoPendienteBancario.objects.filter(pendiente=p, accion__in=['Creado', 'Resuelto']).select_related('actor'):
        eventos.append((e.creado, e.pk, 'A', {
            'fecha': timezone.localtime(e.creado).strftime('%d/%m/%Y'),
            'accion': e.accion, 'usuario': _actor(e.actor), 'detalle': e.detalle,
        }))
    for e in RevisionPendienteBancario.objects.filter(pendiente=p).select_related('actor'):
        eventos.append((e.creado, e.pk, 'B', {
            'fecha': timezone.localtime(e.creado).strftime('%d/%m/%Y'),
            'accion': e.get_tipo_display(), 'usuario': _actor(e.actor), 'detalle': e.motivo,
        }))
    for e in EventoEstadoECheq.objects.filter(pendiente=p).select_related('actor'):
        eventos.append((e.creado, e.pk, 'C', {
            'fecha': e.fecha.strftime('%d/%m/%Y'), 'accion': ETIQUETAS[e.estado_nuevo],
            'usuario': _actor(e.actor), 'detalle': e.observaciones,
        }))
    from usuarios.models import ItemSalidaECheq
    for item in ItemSalidaECheq.objects.filter(pendiente=p).select_related('operacion__actor', 'operacion__cuenta', 'operacion__proveedor'):
        operacion = item.operacion
        destino = operacion.cuenta.nombre if operacion.cuenta_id else (operacion.proveedor.razon_social if operacion.proveedor_id else operacion.destino)
        eventos.append((item.creado, item.pk, 'D', {
            'fecha': timezone.localtime(item.creado).strftime('%d/%m/%Y'),
            'accion': ETIQUETAS[item.accion], 'usuario': _actor(operacion.actor), 'detalle': destino,
        }))
    eventos.sort(key=lambda x: (x[0], x[2], x[1]))
    return {
        'id': p.pk,
        'instrumento': p.echeq_numero,
        'titular': p.echeq_titular,
        'estado': p.estado_cartera,
        'gestion': p.estado,
        'regularizar_rechazo': (permiso_estado and p.estado == 'Pendiente'
                               and p.estado_cartera == 'Rechazado'),
        'estado_texto': ETIQUETAS[p.estado_cartera],
        'acciones': [a for a in TRANSICIONES[p.estado_cartera] if a != 'Vencido' or (p.echeq_fecha_acreditacion and timezone.localdate() >= p.echeq_fecha_acreditacion + timedelta(days=30))] if permiso_estado else [],
        'fecha_hoy': timezone.localdate().isoformat(),
        'historial': [e[3] for e in eventos],
    }


def registrar_estado(*, usuario, empresa_id, pendiente_id, clave, nuevo_estado,
                     fecha, observaciones=''):
    empresa, _ = _autorizar(usuario, empresa_id, pendiente_id, escritura=True)
    try:
        clave = UUID(str(clave))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError('Identificador de operación inválido.') from exc
    if nuevo_estado not in ('Rechazado', 'Devuelto', 'Vencido'):
        raise ValueError('Acción de cartera inválida.')
    try:
        fecha = date.fromisoformat(str(fecha))
    except (TypeError, ValueError) as exc:
        raise ValueError('Fecha inválida.') from exc
    if fecha > timezone.localdate():
        raise ValueError('La fecha no puede ser futura.')
    if not isinstance(observaciones, str) or len(observaciones.strip()) > 300:
        raise ValueError('Observaciones inválidas (máximo 300 caracteres).')
    observaciones = observaciones.strip()

    with transaction.atomic():
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        previa = EventoEstadoECheq.objects.select_related('actor').filter(clave=clave).first()
        if previa:
            if (previa.pendiente_id != pendiente_id or previa.actor.usuario_id != usuario.pk
                    or previa.estado_nuevo != nuevo_estado or previa.fecha != fecha
                    or previa.observaciones != observaciones):
                raise ValueError('Identificador ya utilizado para otra operación.')
            if previa.pendiente.empresa_id != empresa.pk:
                raise PermissionDenied('Operación no autorizada.')
            return previa, False
        p = PendienteBancario.objects.select_for_update().filter(
            pk=pendiente_id, empresa=empresa, tipo='ECheq').first()
        if p is None:
            raise PermissionDenied('Instrumento no autorizado.')
        anterior = p.estado_cartera
        if nuevo_estado == 'Vencido' and (not p.echeq_fecha_acreditacion or fecha < p.echeq_fecha_acreditacion + timedelta(days=30)):
            raise ValueError('Aún no se cumplieron los 30 días desde la acreditación.')
        if nuevo_estado not in TRANSICIONES[anterior]:
            raise ValueError('Transición de estado no permitida.')
        actor = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        # El rechazo termina la gestión del pendiente. Un Devuelto posterior se
        # agrega al historial; nunca vuelve a abrir la bandeja ni borra el rechazo.
        cerrar = p.estado == 'Pendiente' and (
            nuevo_estado == 'Rechazado' or anterior == 'Rechazado')
        ahora = timezone.now()
        cambios = {'estado_cartera': nuevo_estado, 'modificado': ahora}
        if cerrar:
            cambios.update(estado='Resuelto', resuelto_por=actor, resuelto_en=ahora,
                           tipo_resolucion='Rechazado',
                           referencia_resolucion='Gestión cerrada por rechazo de e-Cheq')
        actualizados = PendienteBancario.objects.filter(
            pk=p.pk, empresa=empresa, estado_cartera=anterior, estado=p.estado).update(**cambios)
        if actualizados != 1:
            raise ValueError('El estado cambió mientras se registraba la operación.')
        evento = EventoEstadoECheq.objects.create(
            pendiente=p, actor=actor, clave=clave, estado_anterior=anterior,
            estado_nuevo=nuevo_estado, fecha=fecha, observaciones=observaciones)
        if cerrar:
            EventoPendienteBancario.objects.create(
                pendiente=p, actor=actor, accion='Resuelto',
                detalle='Cierre administrativo por rechazo de e-Cheq; sin movimiento de Caja.')
    LOG.info('echeq.cartera_estado empresa_id=%s pendiente_id=%s evento_id=%s estado=%s',
             empresa.pk, p.pk, evento.pk, nuevo_estado)
    return evento, True


def regularizar_rechazo_historico(*, usuario, empresa_id, pendiente_id):
    """Cierre auditado explícito: solo e-Cheqs rechazados históricos pendientes."""
    empresa, _ = _autorizar(usuario, empresa_id, pendiente_id, escritura=True)
    with transaction.atomic():
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        cheque = PendienteBancario.objects.select_for_update().filter(
            pk=pendiente_id, empresa=empresa, tipo='ECheq').first()
        if cheque is None:
            raise PermissionDenied('Instrumento no autorizado.')
        if cheque.estado_cartera != 'Rechazado':
            raise ValueError('Solo se regularizan e-Cheqs ya rechazados.')
        if cheque.estado == 'Resuelto':
            return False
        if cheque.estado != 'Pendiente':
            raise ValueError('Estado de gestión no admitido.')
        if not EventoEstadoECheq.objects.filter(pendiente=cheque, estado_nuevo='Rechazado').exists():
            raise ValueError('No existe un rechazo auditado; revisar el instrumento.')
        actor = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        ahora = timezone.now()
        actualizados = PendienteBancario.objects.filter(
            pk=cheque.pk, empresa=empresa, estado='Pendiente', estado_cartera='Rechazado'
        ).update(estado='Resuelto', resuelto_por=actor, resuelto_en=ahora,
                 tipo_resolucion='Rechazado',
                 referencia_resolucion='Regularización auditada de rechazo anterior',
                 modificado=ahora)
        if actualizados != 1:
            raise ValueError('El pendiente cambió durante la regularización.')
        EventoPendienteBancario.objects.create(
            pendiente=cheque, actor=actor, accion='Resuelto',
            detalle='Regularización de rechazo previamente auditado; sin movimiento de Caja.')
    LOG.info('echeq.rechazo_regularizado empresa_id=%s pendiente_id=%s actor_id=%s',
             empresa.pk, pendiente_id, usuario.pk)
    return True
