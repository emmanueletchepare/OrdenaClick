"""Editar/anular un movimiento manual exige contraasiento; nunca DELETE.

Una Cobranza, Pago, traslado o corrección ajena no puede cambiarse por aquí.
"""
import hashlib
import json
import logging
import uuid
from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from usuarios.models import Caja, CorreccionMovimientoCaja, MovimientoCaja
from usuarios.services.caja_disponibilidad import saldo_efectivo_caja
from usuarios.services.caja_movimientos import _validar_movimiento
from usuarios.services.identidades import obtener_identidad_usuario_empresa
from usuarios.services.seguridad import obtener_caja_autorizada

AUDIT = logging.getLogger('ordenaclick.audit')


def corregir_movimiento(*, usuario, empresa_id, caja_id, movimiento_id, datos):
    empresa, caja = obtener_caja_autorizada(usuario, empresa_id, caja_id)
    if not isinstance(datos, dict):
        raise ValueError('Datos de corrección inválidos.')
    accion = datos.get('accion')
    motivo = datos.get('motivo')
    if accion not in ('Editar', 'Anular'):
        raise ValueError('Acción no válida.')
    if not isinstance(motivo, str) or not 6 <= len(motivo.strip()) <= 300:
        raise ValueError('Indicá un motivo de al menos 6 caracteres.')
    motivo = motivo.strip()
    try:
        clave = uuid.UUID(datos.get('clave', ''))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError('Identificador de operación inválido.') from exc
    nuevos = None
    if accion == 'Editar':
        fecha, tipo, moneda, importe, concepto, _, normalizados = _validar_movimiento({
            **datos.get('nuevo', {}), 'clave_idempotencia': str(clave),
        })
        nuevos = (fecha, tipo, moneda, importe, concepto, normalizados)
    contenido = {'accion': accion, 'motivo': motivo,
                 'nuevo': nuevos[5] if nuevos else None}
    huella = hashlib.sha256(json.dumps(contenido, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    with transaction.atomic():
        bloqueada = Caja.objects.select_for_update().filter(pk=caja.pk, empresa=empresa, activo=True,
                           centro_operativo__activo=True).first()
        if bloqueada is None:
            raise PermissionDenied('Caja no autorizada.')
        anterior = CorreccionMovimientoCaja.objects.filter(clave=clave).first()
        if anterior:
            if (anterior.original_id == int(movimiento_id) and anterior.huella == huella
                    and anterior.creado_por.usuario_id == usuario.pk):
                return anterior, False
            raise ValueError('Identificador utilizado para otra corrección.')
        original = MovimientoCaja.objects.select_for_update().filter(
            pk=movimiento_id, empresa=empresa, caja=bloqueada).first()
        if (original is None or original.cobranza_id is not None or
                CorreccionMovimientoCaja.objects.filter(original=original).exists() or
                CorreccionMovimientoCaja.objects.filter(contraasiento=original).exists() or
                CorreccionMovimientoCaja.objects.filter(reemplazo=original).exists()):
            raise PermissionDenied('Sólo puede corregir un movimiento manual sin corrección previa.')
        # Evaluar efecto NETO por moneda ANTES de emitir cualquier asiento.
        deltas = {original.moneda: (-original.importe if original.tipo == 'Ingreso' else original.importe)}
        if nuevos:
            nueva_moneda, nuevo_tipo, nuevo_importe = nuevos[2], nuevos[1], nuevos[3]
            deltas[nueva_moneda] = deltas.get(nueva_moneda, Decimal('0')) + (
                nuevo_importe if nuevo_tipo == 'Ingreso' else -nuevo_importe)
        for moneda, delta in deltas.items():
            if saldo_efectivo_caja(empresa, bloqueada, moneda) + delta < 0:
                raise ValueError('La corrección dejaría el saldo de Caja negativo.')
        identidad = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        # Contraasiento fechado HOY: nunca reemplazar ni ocultar historia anterior.
        contra = MovimientoCaja.objects.create(
            empresa=empresa, caja=bloqueada, cobranza=None, fecha=timezone.localdate(),
            tipo='Egreso' if original.tipo == 'Ingreso' else 'Ingreso',
            moneda=original.moneda, importe=original.importe,
            concepto=f'Contraasiento movimiento #{original.pk}', creado_por=identidad)
        reemplazo = None
        if nuevos:
            reemplazo = MovimientoCaja.objects.create(
                empresa=empresa, caja=bloqueada, cobranza=None, fecha=nuevos[0],
                tipo=nuevos[1], moneda=nuevos[2], importe=nuevos[3],
                concepto=nuevos[4], creado_por=identidad)
        correccion = CorreccionMovimientoCaja.objects.create(
            original=original, contraasiento=contra, reemplazo=reemplazo,
            clave=clave, accion=accion, motivo=motivo, creado_por=identidad, huella=huella)
    AUDIT.info('caja.movimiento_corregido empresa_id=%s caja_id=%s original_id=%s correccion_id=%s accion=%s',
               empresa.pk, caja.pk, original.pk, correccion.pk, accion)
    return correccion, True
