from decimal import Decimal

# =========================================
# DISPONIBILIDAD DE CAJA Y CARTERA
# =========================================

def saldo_efectivo_caja(
    empresa,
    caja,
    moneda,
):
    """
    Calcula el saldo actual de efectivo de una Caja para una moneda.

    El saldo no se almacena como un valor mutable. Surge de sumar los
    ingresos y restar los egresos registrados en MovimientoCaja.

    La consulta exige que la Caja pertenezca a la Empresa indicada.
    """
    from django.db.models import (
        DecimalField,
        Sum,
        Value,
    )
    from django.db.models.functions import Coalesce

    from usuarios.models import MovimientoCaja

    if caja.empresa_id != empresa.id:
        raise ValueError(
            "La Caja no pertenece a la Empresa seleccionada."
        )

    if moneda not in {
        "ARS",
        "USD",
    }:
        raise ValueError(
            "La moneda de la Caja no es válida."
        )

    campo_decimal = DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    ingresos = (
        MovimientoCaja.objects
        .filter(
            empresa=empresa,
            caja=caja,
            moneda=moneda,
            tipo="Ingreso",
        )
        .aggregate(
            total=Coalesce(
                Sum("importe"),
                Value(Decimal("0.00")),
                output_field=campo_decimal,
            )
        )["total"]
    )

    egresos = (
        MovimientoCaja.objects
        .filter(
            empresa=empresa,
            caja=caja,
            moneda=moneda,
            tipo="Egreso",
        )
        .aggregate(
            total=Coalesce(
                Sum("importe"),
                Value(Decimal("0.00")),
                output_field=campo_decimal,
            )
        )["total"]
    )

    return ingresos - egresos


def cheques_fisicos_disponibles_caja(
    empresa,
    caja,
    fecha_referencia=None,
):
    """
    Devuelve los cheques físicos de terceros realmente disponibles
    en una Caja.

    Un cheque sólo puede ofrecerse como disponibilidad cuando:

    - pertenece a la Empresa y Caja indicadas;
    - es un cheque físico de tercero;
    - su estado persistido es Disponible;
    - no posee una fecha de vencimiento anterior a la fecha de referencia.

    La comprobación temporal es deliberadamente defensiva: aunque un
    registro conserve por error el estado Disponible, un cheque vencido
    no debe volver a ofrecerse para un Pago u Orden de Pago.
    """
    from datetime import date

    from django.db.models import Q

    from usuarios.models import Cheque

    if caja.empresa_id != empresa.id:
        raise ValueError(
            "La Caja no pertenece a la Empresa seleccionada."
        )

    if fecha_referencia is None:
        fecha_referencia = date.today()

    cheques = (
        Cheque.objects
        .filter(
            empresa=empresa,
            caja=caja,
            tipo_instrumento="Cheque",
            origen="Tercero",
            estado="Disponible",
        )
        .filter(
            Q(fecha_vencimiento__isnull=True)
            | Q(fecha_vencimiento__gte=fecha_referencia)
        )
        .select_related(
            "banco",
            "cliente",
            "cobranza",
        )
        .order_by(
            "fecha_acreditacion",
            "fecha_vencimiento",
            "numero",
            "id",
        )
    )

    return cheques


def resumen_disponibilidad_caja(
    empresa,
    caja,
    fecha_referencia=None,
):
    """
    Construye el resumen central de disponibilidad de una Caja.

    Expone saldos de efectivo ARS/USD y la cartera física actualmente
    utilizable. Las vistas y futuras Órdenes de Pago deben consumir estas
    reglas en lugar de recalcular disponibilidad en HTML o JavaScript.
    """
    cheques = cheques_fisicos_disponibles_caja(
        empresa=empresa,
        caja=caja,
        fecha_referencia=fecha_referencia,
    )

    return {
        "caja": caja,
        "efectivo": {
            "ARS": saldo_efectivo_caja(
                empresa=empresa,
                caja=caja,
                moneda="ARS",
            ),
            "USD": saldo_efectivo_caja(
                empresa=empresa,
                caja=caja,
                moneda="USD",
            ),
        },
        "cheques": cheques,
        "total_cheques": sum(
            (
                cheque.importe
                for cheque in cheques
            ),
            Decimal("0.00"),
        ),
    }
