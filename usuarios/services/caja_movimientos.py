"""Caja 1: movimientos manuales de efectivo, seguros e idempotentes.

No representa pagos de REGISTROS, transferencias bancarias ni envios entre
Cajas. Esos hechos requieren circuitos propios, con vinculos contables.
"""
import hashlib
import json
import re
import logging
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation

from django.db import transaction

from usuarios.models import Caja, IdempotenciaMovimientoCaja, MovimientoCaja
from usuarios.services.caja_disponibilidad import saldo_efectivo_caja
from usuarios.services.identidades import obtener_identidad_usuario_empresa
from usuarios.services.seguridad import obtener_caja_autorizada


AUDITORIA = logging.getLogger('ordenaclick.audit')
LIMITE_IMPORTE = Decimal('1000000000000.00')


def _validar_movimiento(datos):
    if not isinstance(datos, dict):
        raise ValueError('El movimiento tiene un formato invalido.')
    tipo = datos.get('tipo')
    moneda = datos.get('moneda')
    if tipo not in ('Ingreso', 'Egreso'):
        raise ValueError('Seleccione ingreso o egreso.')
    if moneda not in ('ARS', 'USD'):
        raise ValueError('La moneda no es valida.')
    fecha_texto = datos.get('fecha')
    if not isinstance(fecha_texto, str):
        raise ValueError('Indique una fecha valida.')
    try:
        fecha = date.fromisoformat(fecha_texto)
    except ValueError as error:
        raise ValueError('Indique una fecha valida.') from error
    if fecha.isoformat() != fecha_texto:
        raise ValueError('Indique una fecha valida.')
    concepto = datos.get('concepto')
    if not isinstance(concepto, str):
        raise ValueError('Indique un concepto.')
    concepto = concepto.strip()
    if not concepto or len(concepto) > 200:
        raise ValueError('El concepto debe tener entre 1 y 200 caracteres.')
    valor = datos.get('importe')
    if not isinstance(valor, str):
        raise ValueError('El importe no es valido.')
    valor_texto = str(valor).strip()
    if re.fullmatch(r'[0-9]{1,3}(?:\.[0-9]{3})+(?:,[0-9]{1,2})?', valor_texto):
        valor_texto = valor_texto.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'[0-9]+,[0-9]{1,2}', valor_texto):
        valor_texto = valor_texto.replace(',', '.')
    elif not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,2})?', valor_texto):
        raise ValueError('El importe no es valido.')
    try:
        importe = Decimal(valor_texto)
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError('El importe no es valido.') from error
    if (not importe.is_finite() or importe <= 0 or importe >= LIMITE_IMPORTE
            or importe.as_tuple().exponent < -2):
        raise ValueError('Ingrese un importe positivo con hasta dos decimales.')
    importe = importe.quantize(Decimal('0.01'))
    clave_texto = datos.get('clave_idempotencia')
    try:
        clave = uuid.UUID(clave_texto) if isinstance(clave_texto, str) else None
    except (ValueError, AttributeError):
        clave = None
    if clave is None:
        raise ValueError('Identificador de operacion invalido.')
    normalizados = {
        'fecha': fecha.isoformat(), 'tipo': tipo, 'moneda': moneda,
        'importe': f'{importe:.2f}', 'concepto': concepto,
    }
    return fecha, tipo, moneda, importe, concepto, clave, normalizados


def registrar_movimiento_caja(*, empresa, caja, usuario, datos):
    """Registra un ingreso/egreso manual mediante bloqueo e idempotencia.

    La vista primero autoriza al usuario y la Caja; la validacion de pertenencia
    se repite aqui por defensa en profundidad. Serializa operaciones sobre la
    Caja (PostgreSQL) antes de consultar saldo y clave. No permite Caja negativa.
    """
    if not usuario or not usuario.is_authenticated:
        raise ValueError('Se requiere un usuario autenticado.')
    empresa_autorizada, caja_autorizada = obtener_caja_autorizada(usuario, empresa.pk, caja.pk)
    empresa, caja = empresa_autorizada, caja_autorizada
    fecha, tipo, moneda, importe, concepto, clave, normalizados = _validar_movimiento(datos)
    huella = hashlib.sha256(json.dumps(normalizados, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()

    with transaction.atomic():
        caja_bloqueada = (Caja.objects.select_for_update()
                          .filter(pk=caja.pk, empresa=empresa, activo=True,
                                  centro_operativo__activo=True,
                                  centro_operativo__tipo__in=['Casa Central', 'Sucursal', 'Mostrador'])
                          .first())
        if caja_bloqueada is None:
            raise ValueError('La Caja no esta operativa en esta Empresa.')

        anterior, reservado = IdempotenciaMovimientoCaja.objects.get_or_create(
            clave=clave,
            defaults={
                'empresa': empresa, 'caja': caja_bloqueada, 'usuario': usuario,
                'huella': huella, 'respuesta': {},
            },
        )
        if not reservado:
            if (anterior.empresa_id != empresa.pk or anterior.caja_id != caja.pk
                    or anterior.usuario_id != usuario.pk or anterior.huella != huella
                    or not anterior.respuesta):
                raise ConflictoIdempotenciaCaja('El identificador ya pertenece a otra operacion.')
            return dict(anterior.respuesta), False

        if tipo == 'Egreso':
            saldo = saldo_efectivo_caja(empresa, caja_bloqueada, moneda)
            if saldo < importe:
                raise ValueError('La Caja no tiene efectivo suficiente en esta moneda.')

        identidad = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        movimiento = MovimientoCaja.objects.create(
            empresa=empresa, caja=caja_bloqueada, cobranza=None,
            fecha=fecha, tipo=tipo, moneda=moneda, importe=importe,
            concepto=concepto, creado_por=identidad,
        )
        respuesta = {'ok': True, 'mensaje': 'Movimiento de Caja registrado.', 'movimiento_id': movimiento.pk}
        anterior.respuesta = respuesta
        anterior.save(update_fields=['respuesta'])
    AUDITORIA.info('caja.movimiento_registrado empresa_id=%s caja_id=%s movimiento_id=%s tipo=%s',
                   empresa.pk, caja.pk, movimiento.pk, tipo)
    return respuesta, True


class ConflictoIdempotenciaCaja(ValueError):
    """La misma clave fue usada para otra operacion."""
