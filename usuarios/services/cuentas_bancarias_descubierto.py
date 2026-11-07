"""Acuerdo bancario en el ABM: validación estricta y auditoría, sin contabilizar fondos.

Un vencimiento anterior a hoy se conserva históricamente pero jamás se expone
como descubierto disponible. Activar aviso sólo afecta Alertas, no Finanzas.
"""
from datetime import date
from decimal import Decimal

from django.db import transaction

from usuarios.models import EventoAcuerdoDescubierto
from usuarios.services.caja_bancos_informados import _importe_declarado
from usuarios.services.identidades import obtener_identidad_usuario_empresa

CAMPOS = ('descubierto_importe', 'descubierto_vencimiento',
          'descubierto_alerta_dias', 'descubierto_alerta_habilitada')


def valores_acuerdo(cuenta):
    """Snapshot apto para auditoría y exportación, sin números flotantes."""
    return {
        'importe': str(cuenta.descubierto_importe) if cuenta.descubierto_importe is not None else None,
        'vencimiento': cuenta.descubierto_vencimiento.isoformat() if cuenta.descubierto_vencimiento else None,
        'dias': cuenta.descubierto_alerta_dias,
        'alerta': cuenta.descubierto_alerta_habilitada,
    }


def leer_acuerdo(datos, anterior=None):
    """Acepta formato monetario es-AR y fecha ISO de input type=date.

    Formularios legados sin nuevos campos preservan lo que ya tenía la cuenta.
    Un acuerdo de descubierto exige importe positivo y vencimiento. La alerta
    requiere la configuración completa, no se autohabilita por omisión.
    """
    if 'descubierto_importe' not in datos and anterior is not None:
        return {campo: getattr(anterior, campo) for campo in CAMPOS}
    texto = (datos.get('descubierto_importe') or '').strip()
    venc = (datos.get('descubierto_vencimiento') or '').strip()
    flag = datos.get('descubierto_alerta_habilitada', '0')
    if flag not in ('0', '1'):
        raise ValueError('La opción de alerta de descubierto no es válida.')
    habilitada = flag == '1'
    dias_texto = str(datos.get('descubierto_alerta_dias', '3')).strip()
    if not dias_texto.isascii() or not dias_texto.isdecimal() or len(dias_texto) > 3:
        raise ValueError('Los días de aviso deben ser un número de 0 a 365.')
    dias = int(dias_texto)
    if dias > 365:
        raise ValueError('Los días de aviso deben estar entre 0 y 365.')
    importe = None
    fecha = None
    if texto:
        importe = _importe_declarado(texto)
        if importe <= Decimal('0.00'):
            raise ValueError('El descubierto acordado debe ser mayor que cero.')
    if venc:
        try:
            fecha = date.fromisoformat(venc)
        except ValueError as exc:
            raise ValueError('La fecha de vencimiento del descubierto no es válida.') from exc
        if fecha.isoformat() != venc:
            raise ValueError('La fecha de vencimiento debe ser válida.')
    if (importe is None) != (fecha is None):
        raise ValueError('Complete importe y vencimiento del descubierto, o deje ambos vacíos.')
    if habilitada and importe is None:
        raise ValueError('Para activar la alerta, complete el acuerdo de descubierto.')
    return dict(descubierto_importe=importe, descubierto_vencimiento=fecha,
                descubierto_alerta_dias=dias, descubierto_alerta_habilitada=habilitada)


def aplicar_acuerdo(cuenta, valores):
    """Asigna campos validados al objeto; devuelve la versión anterior."""
    antes = valores_acuerdo(cuenta)
    for campo in CAMPOS:
        setattr(cuenta, campo, valores[campo])
    return antes


def auditar_acuerdo(cuenta, antes, usuario):
    """Registra un evento persistente únicamente cuando cambia el acuerdo."""
    despues = valores_acuerdo(cuenta)
    if antes == despues:
        return
    identidad = obtener_identidad_usuario_empresa(empresa=cuenta.empresa, usuario=usuario)
    EventoAcuerdoDescubierto.objects.create(empresa=cuenta.empresa,
        cuenta_bancaria=cuenta, actor=identidad, antes=antes, despues=despues)
