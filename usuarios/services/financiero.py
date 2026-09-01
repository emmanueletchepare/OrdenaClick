from datetime import date
from decimal import Decimal

from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from usuarios.models import Movimiento


# =========================================
# ESTADOS FINANCIEROS
# =========================================

ESTADO_PENDIENTE = "Pendiente"
ESTADO_PARCIAL = "Parcial"
ESTADO_PAGADO = "Pagado"


# =========================================
# ESTADOS DE VENCIMIENTO
# =========================================

VENCIMIENTO_SIN_FECHA = "SinFecha"
VENCIMIENTO_FUTURO = "Futuro"
VENCIMIENTO_HOY = "Hoy"
VENCIMIENTO_VENCIDO = "Vencido"
VENCIMIENTO_PAGADO = "Pagado"


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

    Estados posibles:

    - Pendiente:
      no posee importe aplicado.

    - Parcial:
      posee aplicaciones, pero todavía mantiene saldo.

    - Pagado:
      el importe aplicado alcanza o supera el total
      documental del Movimiento.

    Este estado representa exclusivamente la situación
    financiera del Movimiento.
    """

    total = movimiento.total or Decimal("0.00")
    total_aplicado = total_aplicado_movimiento(movimiento)

    if total_aplicado <= Decimal("0.00"):
        return ESTADO_PENDIENTE

    if total_aplicado >= total:
        return ESTADO_PAGADO

    return ESTADO_PARCIAL


# =========================================
# VENCIMIENTOS
# =========================================

def estado_vencimiento_movimiento(
    movimiento,
    fecha_referencia=None,
):
    """
    Determina la situación temporal de vencimiento
    de un Movimiento.

    El estado financiero y el estado temporal se mantienen
    separados. Un Movimiento puede, por ejemplo, estar
    Parcial financieramente y Vencido temporalmente.

    La fecha de referencia permite probar y reutilizar la
    regla sin depender obligatoriamente del día actual.
    """

    if fecha_referencia is None:
        fecha_referencia = date.today()

    saldo_pendiente = saldo_pendiente_movimiento(
        movimiento
    )

    if saldo_pendiente <= Decimal("0.00"):
        return VENCIMIENTO_PAGADO

    if not movimiento.fecha_vencimiento:
        return VENCIMIENTO_SIN_FECHA

    if movimiento.fecha_vencimiento < fecha_referencia:
        return VENCIMIENTO_VENCIDO

    if movimiento.fecha_vencimiento == fecha_referencia:
        return VENCIMIENTO_HOY

    return VENCIMIENTO_FUTURO


def resumen_financiero_movimiento(
    movimiento,
    fecha_referencia=None,
):
    """
    Construye una representación financiera central
    de un Movimiento.

    Este resumen está pensado para ser reutilizado por:

    - Próximos Vencimientos.
    - Alertas.
    - Reportes.
    - APIs futuras.

    Las vistas no deben recalcular estas reglas por su cuenta.
    """

    total_aplicado = total_aplicado_movimiento(
        movimiento
    )

    total = movimiento.total or Decimal("0.00")

    saldo_pendiente = total - total_aplicado

    if saldo_pendiente < Decimal("0.00"):
        saldo_pendiente = Decimal("0.00")

    if total_aplicado <= Decimal("0.00"):
        estado_financiero = ESTADO_PENDIENTE
    elif total_aplicado >= total:
        estado_financiero = ESTADO_PAGADO
    else:
        estado_financiero = ESTADO_PARCIAL

    if fecha_referencia is None:
        fecha_referencia = date.today()

    if saldo_pendiente <= Decimal("0.00"):
        estado_vencimiento = VENCIMIENTO_PAGADO
    elif not movimiento.fecha_vencimiento:
        estado_vencimiento = VENCIMIENTO_SIN_FECHA
    elif movimiento.fecha_vencimiento < fecha_referencia:
        estado_vencimiento = VENCIMIENTO_VENCIDO
    elif movimiento.fecha_vencimiento == fecha_referencia:
        estado_vencimiento = VENCIMIENTO_HOY
    else:
        estado_vencimiento = VENCIMIENTO_FUTURO

    return {
        "movimiento": movimiento,
        "total": total,
        "total_aplicado": total_aplicado,
        "saldo_pendiente": saldo_pendiente,
        "estado_financiero": estado_financiero,
        "fecha_vencimiento": movimiento.fecha_vencimiento,
        "estado_vencimiento": estado_vencimiento,
        "modalidad_pago": getattr(
            movimiento,
            "modalidad_pago",
            "Manual",
        ),
        "cuenta_debito": getattr(
            movimiento,
            "cuenta_debito",
            None,
        ),
    }


# =========================================
# CONSULTAS FINANCIERAS
# =========================================

def movimientos_con_saldo_pendiente(
    empresa,
    fecha_desde=None,
    fecha_hasta=None,
):
    """
    Devuelve los Movimientos de una empresa que mantienen
    saldo pendiente.

    El saldo se calcula en la propia consulta a partir de:

        Movimiento.total
        - SUM(AplicacionPago.importe)

    Puede limitarse opcionalmente por fecha de vencimiento.

    Esta consulta constituye la base común para Próximos
    Vencimientos, Alertas y futuros reportes financieros.
    """

    campo_decimal = DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    movimientos = (
        Movimiento.objects
        .filter(
            empresa=empresa,
        )
        .exclude(
            estado="Cancelado",
        )
        .annotate(
            total_aplicado_calculado=Coalesce(
                Sum(
                    "aplicaciones_pago__importe"
                ),
                Value(
                    Decimal("0.00")
                ),
                output_field=campo_decimal,
            )
        )
        .annotate(
            saldo_pendiente_calculado=ExpressionWrapper(
                F("total") -
                F("total_aplicado_calculado"),
                output_field=campo_decimal,
            )
        )
        .filter(
            saldo_pendiente_calculado__gt=0,
        )
    )

    if fecha_desde is not None:
        movimientos = movimientos.filter(
            fecha_vencimiento__gte=fecha_desde,
        )

    if fecha_hasta is not None:
        movimientos = movimientos.filter(
            fecha_vencimiento__lte=fecha_hasta,
        )

    return movimientos.order_by(
        "fecha_vencimiento",
        "id",
    )