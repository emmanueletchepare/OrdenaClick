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
}
ETIQUETAS = {'EnCartera': 'En cartera', 'Rechazado': 'Rechazado',
             'Devuelto': 'Devuelto', 'Vencido': 'Vencido'}


def _autorizar(usuario, empresa_id, pendiente_id, *, escritura=False):
    empresa, alcance = alcance_pendientes(usuario, empresa_id)
    if escritura and alcance is not None:
        raise PermissionDenied('Sólo administración general puede cambiar estados de e-Cheqs.')
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
    eventos.sort(key=lambda x: (x[0], x[2], x[1]))
    return {
        'id': p.pk,
        'instrumento': p.echeq_numero,
        'titular': p.echeq_titular,
        'estado': p.estado_cartera,
        'estado_texto': ETIQUETAS[p.estado_cartera],
        'acciones': [a for a in TRANSICIONES[p.estado_cartera] if a != 'Vencido' or (p.echeq_fecha_acreditacion and timezone.localdate() >= p.echeq_fecha_acreditacion + timedelta(days=30))] if alcance is None else [],
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
        actualizados = PendienteBancario.objects.filter(
            pk=p.pk, empresa=empresa, estado_cartera=anterior).update(
                estado_cartera=nuevo_estado, modificado=timezone.now())
        if actualizados != 1:
            raise ValueError('El estado cambió mientras se registraba la operación.')
        actor = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        evento = EventoEstadoECheq.objects.create(
            pendiente=p, actor=actor, clave=clave, estado_anterior=anterior,
            estado_nuevo=nuevo_estado, fecha=fecha, observaciones=observaciones)
    LOG.info('echeq.cartera_estado empresa_id=%s pendiente_id=%s evento_id=%s estado=%s',
             empresa.pk, p.pk, evento.pk, nuevo_estado)
    return evento, True
