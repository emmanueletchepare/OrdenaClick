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
# POLÍTICAS DE ALERTA
# =========================================

DIAS_ANTICIPACION_ALERTA = 3


# =========================================
# SALDO DE MOVIMIENTOS
# =========================================

def validar_importe_aplicable(
    saldo_pendiente,
    importe_aplicar,
):
    """
    Valida que una nueva aplicación sobre un destino financiero
    no supere su saldo pendiente actual.

    Permite una aplicación nula, parcial o exacta.

    No permite importes negativos ni sobreaplicaciones.

    La función valida exclusivamente el importe que cancela
    obligación. Un Pago real puede contener otros importes
    financieros que no formen parte de la aplicación, como
    intereses por mora confirmados.
    """

    saldo_pendiente = Decimal(
        str(
            saldo_pendiente
            if saldo_pendiente is not None
            else "0.00"
        )
    )

    importe_aplicar = Decimal(
        str(
            importe_aplicar
            if importe_aplicar is not None
            else "0.00"
        )
    )


    if saldo_pendiente < Decimal("0.00"):

        raise ValueError(
            "El saldo pendiente no puede ser negativo."
        )


    if importe_aplicar < Decimal("0.00"):

        raise ValueError(
            "El importe a aplicar no puede ser negativo."
        )


    if importe_aplicar > saldo_pendiente:

        raise ValueError(
            "El importe a aplicar no puede superar "
            "el saldo pendiente."
        )


    return importe_aplicar

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

def movimientos_en_alerta(
    empresa,
    fecha_referencia=None,
):
    """
    Devuelve los Movimientos que requieren atención
    dentro de la política inicial de Alertas.

    Reglas actuales:
    - El Movimiento debe conservar saldo pendiente.
    - Debe poseer fecha de vencimiento.
    - Entra en Alerta desde tres días antes.
    - Si ya venció y continúa pendiente, permanece
      en Alerta sin límite hacia atrás.

    Las futuras fuentes de Alertas, como Cartera de
    Cheques/e-Cheqs, deberán aplicar su propia política
    temporal sin duplicar esta regla en la interfaz.
    """

    from datetime import date, timedelta

    if fecha_referencia is None:
        fecha_referencia = date.today()

    fecha_limite = (
        fecha_referencia
        + timedelta(
            days=DIAS_ANTICIPACION_ALERTA,
        )
    )

    return movimientos_con_saldo_pendiente(
        empresa=empresa,
        fecha_hasta=fecha_limite,
    )

def crear_pago_validado_movimiento(
    empresa,
    movimiento,
    pago_datos,
):
    """
    Persiste un Pago previamente validado y lo aplica
    a un Movimiento.

    La función no interpreta datos HTTP ni valida
    formularios. Recibe exclusivamente estructuras
    financieras ya validadas por el circuito llamador.

    Crea el Pago y sus componentes asociados:
    operaciones bancarias, tarjetas, cheques y
    retenciones.

    Finalmente crea la AplicacionPago correspondiente
    al Movimiento.

    La validación del saldo disponible debe realizarse
    antes de invocar esta función.
    """

    from usuarios.models import (
        AplicacionPago,
        Cheque,
        OperacionBancariaPago,
        Pago,
        RetencionPago,
        TarjetaPago,
    )

    pago = Pago.objects.create(
        empresa=empresa,
        fecha=pago_datos["fecha"],
        importe_efectivo=pago_datos[
            "importe_efectivo"
        ],
    )

    operaciones_creadas = []
    tarjetas_creadas = []
    cheques_creados = []
    retenciones_creadas = []

    for operacion_datos in pago_datos[
        "operaciones_bancarias"
    ]:
        operacion = (
            OperacionBancariaPago.objects.create(
                pago=pago,
                tipo_operacion=operacion_datos[
                    "tipo_operacion"
                ],
                cuenta_origen=operacion_datos[
                    "cuenta_origen"
                ],
                banco_destino=operacion_datos[
                    "banco_destino"
                ],
                referencia_destino=operacion_datos[
                    "referencia_destino"
                ],
                moneda="ARS",
                importe=operacion_datos[
                    "importe"
                ],
                fecha=operacion_datos[
                    "fecha"
                ],
                comprobante=operacion_datos[
                    "comprobante"
                ],
            )
        )

        operaciones_creadas.append(
            operacion.id
        )

    for tarjeta_datos in pago_datos[
        "tarjetas"
    ]:
        tarjeta_pago = TarjetaPago.objects.create(
            pago=pago,
            tarjeta=tarjeta_datos[
                "tarjeta"
            ],
            fecha=tarjeta_datos[
                "fecha"
            ],
            importe=tarjeta_datos[
                "importe"
            ],
            cuotas=tarjeta_datos[
                "cuotas"
            ],
            intereses_financiacion=tarjeta_datos[
                "intereses_financiacion"
            ],
            referencia=tarjeta_datos[
                "referencia"
            ],
            comprobante=tarjeta_datos[
                "comprobante"
            ],
        )

        tarjetas_creadas.append(
            tarjeta_pago.id
        )

    for cheque_datos in pago_datos[
        "cheques"
    ]:
        cheque = Cheque.objects.create(
            empresa=empresa,
            pago=pago,
            tipo_instrumento=cheque_datos[
                "tipo_instrumento"
            ],
            origen=cheque_datos[
                "origen"
            ],
            tipo_cheque=cheque_datos[
                "tipo_cheque"
            ],
            banco=cheque_datos[
                "banco"
            ],
            cuenta_bancaria=cheque_datos[
                "cuenta_bancaria"
            ],
            numero=cheque_datos[
                "numero"
            ],
            importe=cheque_datos[
                "importe"
            ],
            fecha_emision=cheque_datos[
                "fecha_emision"
            ],
            fecha_acreditacion=cheque_datos[
                "fecha_acreditacion"
            ],
            quien_entrega=cheque_datos[
                "quien_entrega"
            ],
            estado="Pendiente",
        )

        cheques_creados.append(
            cheque.id
        )

    for retencion_datos in pago_datos[
        "retenciones"
    ]:
        retencion_pago = (
            RetencionPago.objects.create(
                pago=pago,
                tipo=retencion_datos[
                    "tipo"
                ],
                importe=retencion_datos[
                    "importe"
                ],
                comprobante=retencion_datos[
                    "comprobante"
                ],
            )
        )

        retenciones_creadas.append(
            retencion_pago.id
        )

    aplicacion = AplicacionPago.objects.create(
        pago=pago,
        movimiento=movimiento,
        importe=pago_datos[
            "importe_pago"
        ],
    )

    return {
        "pago_id": pago.id,
        "aplicacion_id": aplicacion.id,
        "operaciones_bancarias_ids":
            operaciones_creadas,
        "tarjetas_ids":
            tarjetas_creadas,
        "cheques_ids":
            cheques_creados,
        "retenciones_ids":
            retenciones_creadas,
    }