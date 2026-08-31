from decimal import Decimal

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce


# =========================================
# ESTADOS FINANCIEROS
# =========================================

ESTADO_PENDIENTE = "Pendiente"
ESTADO_PARCIAL = "Parcial"
ESTADO_PAGADO = "Pagado"


# =========================================
# SALDO DE MOVIMIENTOS
# =========================================

def total_aplicado_movimiento(movimiento):
    """
    Devuelve el importe total aplicado a un Movimiento.

    La fuente de verdad son las AplicacionPago relacionadas
    con el Movimiento. Los componentes internos de cada Pago
    no se suman directamente aquí.

    De esta manera, costos financieros, intereses de mora u
    otros importes que no cancelan la obligación documental
    no alteran el saldo pendiente del Movimiento.
    """

    resultado = movimiento.aplicaciones_pago.aggregate(
        total=Coalesce(
            Sum("importe"),
            Value(Decimal("0.00")),
            output_field=DecimalField(
                max_digits=14,
                decimal_places=2,
            ),
        )
    )

    return resultado["total"]


def saldo_pendiente_movimiento(movimiento):
    """
    Devuelve el saldo pendiente de un Movimiento.

    El saldo surge exclusivamente de restar al total
    documental del Movimiento las AplicacionPago que
    efectivamente fueron imputadas a él.

    Nunca devuelve un saldo negativo.
    """

    total = movimiento.total or Decimal("0.00")
    total_aplicado = total_aplicado_movimiento(movimiento)

    saldo = total - total_aplicado

    if saldo <= Decimal("0.00"):
        return Decimal("0.00")

    return saldo


def estado_financiero_movimiento(movimiento):
    """
    Determina el estado financiero de un Movimiento.

    Estados posibles en esta primera implementación:

    - Pendiente:
      no posee importe aplicado.

    - Parcial:
      posee aplicaciones, pero todavía mantiene saldo.

    - Pagado:
      el importe aplicado alcanza o supera el total
      documental del Movimiento.

    Este estado representa exclusivamente la situación
    financiera del Movimiento. No determina todavía si
    el Movimiento está vencido, cancelado documentalmente
    ni otras condiciones operativas.
    """

    total = movimiento.total or Decimal("0.00")
    total_aplicado = total_aplicado_movimiento(movimiento)

    if total_aplicado <= Decimal("0.00"):
        return ESTADO_PENDIENTE

    if total_aplicado >= total:
        return ESTADO_PAGADO

    return ESTADO_PARCIAL