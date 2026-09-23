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

def eliminar_pago_movimiento(
    empresa,
    movimiento,
    pago,
):
    """
    Elimina un Pago cargado por error y deshace su aplicación
    sobre un Movimiento.

    La operación sólo admite Pagos pertenecientes a la misma
    Empresa y aplicados exclusivamente al Movimiento indicado.

    No permite eliminar cheques/e-Cheqs cuyo estado ya evidencia
    que avanzaron en un circuito financiero posterior.

    El llamador debe ejecutar esta función dentro de una
    transaction.atomic() y bloquear previamente los registros
    financieros involucrados cuando exista riesgo de concurrencia.

    Devuelve el nuevo resumen financiero del Movimiento.
    """

    from usuarios.models import (
        AplicacionPago,
        Cheque,
        DebitoAutomaticoPago,
        OperacionBancariaPago,
        RetencionPago,
        TarjetaPago,
    )


    if pago.empresa_id != empresa.id:

        raise ValueError(
            "El Pago no pertenece a la Empresa seleccionada."
        )


    if movimiento.empresa_id != empresa.id:

        raise ValueError(
            "El Movimiento no pertenece a la Empresa seleccionada."
        )


    aplicaciones = list(
        AplicacionPago.objects.filter(
            pago=pago,
        )
    )


    if not aplicaciones:

        raise ValueError(
            "El Pago no posee una aplicación financiera."
        )


    if len(aplicaciones) != 1:

        raise ValueError(
            "El Pago posee múltiples aplicaciones y no puede "
            "eliminarse desde este circuito."
        )


    aplicacion = aplicaciones[0]


    if aplicacion.movimiento_id != movimiento.id:

        raise ValueError(
            "El Pago no está aplicado al Movimiento indicado."
        )


    if aplicacion.cuota_id is not None:

        raise ValueError(
            "El Pago está aplicado a una cuota y no puede "
            "eliminarse desde este circuito."
        )


    cheques = list(
        Cheque.objects.filter(
            pago=pago,
        )
    )


    estados_cheque_eliminables = {
        "Pendiente",
    }


    for cheque in cheques:

        if (
            cheque.estado not in
            estados_cheque_eliminables
        ):

            raise ValueError(
                "El Pago contiene un cheque/e-Cheq que ya "
                "avanzó en su circuito financiero y no puede "
                "eliminarse."
            )


    # =========================================
    # DESHACER APLICACIÓN
    # =========================================

    aplicacion.delete()


    # =========================================
    # ELIMINAR COMPONENTES DEL PAGO
    # =========================================
    #
    # Las relaciones utilizan PROTECT de forma
    # intencional. Por eso los componentes se
    # eliminan explícitamente antes del Pago.
    #

    OperacionBancariaPago.objects.filter(
        pago=pago,
    ).delete()

    DebitoAutomaticoPago.objects.filter(
        pago=pago,
    ).delete()

    TarjetaPago.objects.filter(
        pago=pago,
    ).delete()

    RetencionPago.objects.filter(
        pago=pago,
    ).delete()

    Cheque.objects.filter(
        pago=pago,
    ).delete()


    pago.delete()


    # =========================================
    # RECALCULAR MOVIMIENTO
    # =========================================

    nuevo_estado = estado_financiero_movimiento(
        movimiento
    )

    movimiento.estado = nuevo_estado

    movimiento.save(
        update_fields=[
            "estado",
            "modificado",
        ]
    )


    return resumen_financiero_movimiento(
        movimiento
    )

def validar_pago_movimiento(
    empresa,
    pago_datos,
    archivos=None,
):
    """
    Valida y normaliza un Pago manual antes de persistirlo.

    La función no depende de request ni devuelve respuestas HTTP.

    Recibe:

    - la Empresa autorizada;
    - un diccionario con los datos del Pago;
    - opcionalmente un objeto tipo diccionario con archivos
      asociados a operaciones bancarias, tarjetas o retenciones.

    Devuelve una estructura normalizada compatible con
    crear_pago_validado_movimiento().

    Lanza ValueError cuando algún dato financiero no es válido.

    Esta validación se utiliza como regla común para evitar
    duplicar lógica entre:

    - alta de un Movimiento con Pago;
    - incorporación posterior de un Pago;
    - futuros circuitos financieros.
    """

    from datetime import datetime
    from decimal import (
        Decimal,
        InvalidOperation,
    )

    from usuarios.models import (
        Banco,
        CuentaBancaria,
        Retencion,
        Tarjeta,
    )


    if not isinstance(
        pago_datos,
        dict,
    ):

        raise ValueError(
            "El Pago tiene un formato inválido."
        )


    if archivos is None:

        archivos = {}


    # =========================================
    # FECHA DEL PAGO
    # =========================================

    fecha_pago = str(
        pago_datos.get(
            "fecha",
            "",
        )
        or ""
    ).strip()


    if not fecha_pago:

        raise ValueError(
            "El Pago debe tener una fecha."
        )


    try:

        fecha_pago_validada = (
            datetime.strptime(
                fecha_pago,
                "%Y-%m-%d",
            ).date()
        )

    except ValueError as error:

        raise ValueError(
            "La fecha del Pago no es válida."
        ) from error


    # =========================================
    # EFECTIVO
    # =========================================

    try:

        importe_efectivo = Decimal(
            str(
                pago_datos.get(
                    "importe_efectivo",
                    0,
                )
            )
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as error:

        raise ValueError(
            "El importe en efectivo no es válido."
        ) from error


    if importe_efectivo < Decimal("0.00"):

        raise ValueError(
            "El efectivo no puede ser negativo."
        )


    # =========================================
    # OPERACIONES BANCARIAS
    # =========================================

    operaciones_raw = (
        pago_datos.get(
            "operaciones_bancarias",
        )
        or []
    )


    if not isinstance(
        operaciones_raw,
        list,
    ):

        raise ValueError(
            "Las operaciones bancarias del Pago "
            "no son válidas."
        )


    operaciones_validadas = []

    total_operaciones = Decimal(
        "0.00"
    )


    for operacion_datos in operaciones_raw:

        if not isinstance(
            operacion_datos,
            dict,
        ):

            raise ValueError(
                "Existe una operación bancaria "
                "con formato inválido."
            )


        tipo_operacion = str(
            operacion_datos.get(
                "tipo_operacion",
                "",
            )
            or ""
        ).strip()


        if tipo_operacion not in {
            "Transferencia",
            "Deposito",
        }:

            raise ValueError(
                "El tipo de operación bancaria "
                "no es válido."
            )


        moneda = str(
            operacion_datos.get(
                "moneda",
                "",
            )
            or ""
        ).strip()


        if moneda != "ARS":

            raise ValueError(
                "La versión Beta de OrdenaClick "
                "admite pagos únicamente en Pesos."
            )


        fecha_operacion = str(
            operacion_datos.get(
                "fecha",
                "",
            )
            or ""
        ).strip()


        if not fecha_operacion:

            raise ValueError(
                "La operación bancaria debe tener "
                "una fecha."
            )


        try:

            fecha_operacion_validada = (
                datetime.strptime(
                    fecha_operacion,
                    "%Y-%m-%d",
                ).date()
            )

        except ValueError as error:

            raise ValueError(
                "Existe una operación bancaria "
                "con una fecha inválida."
            ) from error


        try:

            importe_operacion = Decimal(
                str(
                    operacion_datos.get(
                        "importe",
                        0,
                    )
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as error:

            raise ValueError(
                "Existe una operación bancaria "
                "con un importe inválido."
            ) from error


        if importe_operacion <= Decimal(
            "0.00"
        ):

            raise ValueError(
                "El importe de una operación bancaria "
                "debe ser mayor a cero."
            )


        banco_destino_id = (
            operacion_datos.get(
                "banco_destino_id",
            )
        )


        banco_destino = (
            Banco.objects.filter(
                id=banco_destino_id,
                empresa=empresa,
                activo=True,
            ).first()
        )


        if not banco_destino:

            raise ValueError(
                "El banco de destino no es válido."
            )


        cuenta_origen = None

        cuenta_origen_id = (
            operacion_datos.get(
                "cuenta_origen_id",
            )
        )


        if (
            tipo_operacion ==
            "Transferencia"
        ):

            if not cuenta_origen_id:

                raise ValueError(
                    "Una transferencia debe tener "
                    "una cuenta bancaria de origen."
                )


            cuenta_origen = (
                CuentaBancaria.objects.filter(
                    id=cuenta_origen_id,
                    empresa=empresa,
                    activo=True,
                    moneda="ARS",
                ).first()
            )


            if not cuenta_origen:

                raise ValueError(
                    "La cuenta bancaria de origen "
                    "no es válida para este Pago."
                )


        elif cuenta_origen_id:

            raise ValueError(
                "Un depósito no debe tener "
                "cuenta bancaria de origen."
            )


        referencia_destino = str(
            operacion_datos.get(
                "referencia_destino",
                "",
            )
            or ""
        ).strip()


        comprobante_clave = str(
            operacion_datos.get(
                "comprobante_clave",
                "",
            )
            or ""
        ).strip()


        comprobante = None


        if comprobante_clave:

            comprobante = archivos.get(
                comprobante_clave
            )


        operaciones_validadas.append(
            {
                "tipo_operacion":
                    tipo_operacion,

                "cuenta_origen":
                    cuenta_origen,

                "banco_destino":
                    banco_destino,

                "referencia_destino":
                    referencia_destino,

                "moneda":
                    "ARS",

                "importe":
                    importe_operacion,

                "fecha":
                    fecha_operacion_validada,

                "comprobante":
                    comprobante,
            }
        )


        total_operaciones += (
            importe_operacion
        )


    # =========================================
    # TARJETAS
    # =========================================

    tarjetas_raw = (
        pago_datos.get(
            "tarjetas",
        )
        or []
    )


    if not isinstance(
        tarjetas_raw,
        list,
    ):

        raise ValueError(
            "Las operaciones con tarjeta "
            "del Pago no son válidas."
        )


    tarjetas_validadas = []

    total_tarjetas = Decimal(
        "0.00"
    )


    for tarjeta_datos in tarjetas_raw:

        if not isinstance(
            tarjeta_datos,
            dict,
        ):

            raise ValueError(
                "Existe una operación con tarjeta "
                "con formato inválido."
            )


        tarjeta_id = (
            tarjeta_datos.get(
                "tarjeta_id",
            )
        )


        tarjeta = (
            Tarjeta.objects.filter(
                id=tarjeta_id,
                empresa=empresa,
                activo=True,
            ).first()
        )


        if not tarjeta:

            raise ValueError(
                "La tarjeta seleccionada "
                "no es válida para este Pago."
            )


        tipo_tarjeta = str(
            tarjeta_datos.get(
                "tipo_tarjeta",
                "",
            )
            or ""
        ).strip()


        if tipo_tarjeta not in {
            "Credito",
            "Debito",
        }:

            raise ValueError(
                "El tipo de tarjeta no es válido."
            )


        if (
            tipo_tarjeta !=
            tarjeta.tipo_tarjeta
        ):

            raise ValueError(
                "El tipo de tarjeta recibido "
                "no coincide con la tarjeta seleccionada."
            )


        fecha_tarjeta = str(
            tarjeta_datos.get(
                "fecha",
                "",
            )
            or ""
        ).strip()


        if not fecha_tarjeta:

            raise ValueError(
                "La operación con tarjeta "
                "debe tener una fecha."
            )


        try:

            fecha_tarjeta_validada = (
                datetime.strptime(
                    fecha_tarjeta,
                    "%Y-%m-%d",
                ).date()
            )

        except ValueError as error:

            raise ValueError(
                "Existe una operación con tarjeta "
                "con una fecha inválida."
            ) from error


        try:

            importe_tarjeta = Decimal(
                str(
                    tarjeta_datos.get(
                        "importe",
                        0,
                    )
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as error:

            raise ValueError(
                "Existe una operación con tarjeta "
                "con un importe inválido."
            ) from error


        if importe_tarjeta <= Decimal(
            "0.00"
        ):

            raise ValueError(
                "El importe aplicado de una operación "
                "con tarjeta debe ser mayor a cero."
            )


        try:

            cuotas = int(
                tarjeta_datos.get(
                    "cuotas",
                    1,
                )
            )

        except (
            TypeError,
            ValueError,
        ) as error:

            raise ValueError(
                "La cantidad de cuotas "
                "no es válida."
            ) from error


        if cuotas < 1:

            raise ValueError(
                "La cantidad de cuotas "
                "debe ser mayor a cero."
            )


        try:

            intereses_financiacion = Decimal(
                str(
                    tarjeta_datos.get(
                        "intereses_financiacion",
                        0,
                    )
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as error:

            raise ValueError(
                "Los intereses de financiación "
                "de la tarjeta no son válidos."
            ) from error


        if (
            intereses_financiacion <
            Decimal("0.00")
        ):

            raise ValueError(
                "Los intereses de financiación "
                "no pueden ser negativos."
            )


        if (
            tarjeta.tipo_tarjeta ==
            "Debito"
        ):

            if cuotas != 1:

                raise ValueError(
                    "Una operación con tarjeta de débito "
                    "debe registrarse en una sola cuota."
                )


            if (
                intereses_financiacion !=
                Decimal("0.00")
            ):

                raise ValueError(
                    "Una operación con tarjeta de débito "
                    "no puede registrar intereses "
                    "de financiación."
                )


        referencia = str(
            tarjeta_datos.get(
                "referencia",
                "",
            )
            or ""
        ).strip()


        comprobante_clave = str(
            tarjeta_datos.get(
                "comprobante_clave",
                "",
            )
            or ""
        ).strip()


        comprobante = None


        if comprobante_clave:

            comprobante = archivos.get(
                comprobante_clave
            )


        tarjetas_validadas.append(
            {
                "tarjeta":
                    tarjeta,

                "fecha":
                    fecha_tarjeta_validada,

                "importe":
                    importe_tarjeta,

                "cuotas":
                    cuotas,

                "intereses_financiacion":
                    intereses_financiacion,

                "referencia":
                    referencia,

                "comprobante":
                    comprobante,
            }
        )


        total_tarjetas += (
            importe_tarjeta
        )


    # =========================================
    # CHEQUES / E-CHEQS
    # =========================================

    cheques_raw = (
        pago_datos.get(
            "cheques",
        )
        or []
    )


    if not isinstance(
        cheques_raw,
        list,
    ):

        raise ValueError(
            "Los cheques del Pago no son válidos."
        )


    cheques_validados = []

    total_cheques = Decimal(
        "0.00"
    )


    for cheque_datos in cheques_raw:

        if not isinstance(
            cheque_datos,
            dict,
        ):

            raise ValueError(
                "Existe un cheque "
                "con formato inválido."
            )


        tipo_instrumento = str(
            cheque_datos.get(
                "tipo_instrumento",
                "",
            )
            or ""
        ).strip()


        origen = str(
            cheque_datos.get(
                "origen",
                "",
            )
            or ""
        ).strip()


        tipo_cheque = str(
            cheque_datos.get(
                "tipo_cheque",
                "",
            )
            or ""
        ).strip()


        if tipo_instrumento not in {
            "Cheque",
            "ECheq",
        }:

            raise ValueError(
                "El tipo de instrumento "
                "del cheque no es válido."
            )


        if origen not in {
            "Propio",
            "Tercero",
        }:

            raise ValueError(
                "El origen del cheque no es válido."
            )


        if tipo_cheque not in {
            "Comun",
            "Diferido",
        }:

            raise ValueError(
                "El tipo de cheque no es válido."
            )


        entidad_id = (
            cheque_datos.get(
                "entidad_id",
            )
        )


        banco = None
        cuenta_bancaria = None


        if origen == "Propio":

            cuenta_bancaria = (
                CuentaBancaria.objects.filter(
                    id=entidad_id,
                    empresa=empresa,
                    activo=True,
                    moneda="ARS",
                ).first()
            )


            if not cuenta_bancaria:

                raise ValueError(
                    "El cheque propio debe usar "
                    "una cuenta bancaria ARS activa "
                    "de la empresa."
                )


        else:

            banco = (
                Banco.objects.filter(
                    id=entidad_id,
                    empresa=empresa,
                    activo=True,
                ).first()
            )


            if not banco:

                raise ValueError(
                    "El cheque de tercero debe tener "
                    "un banco válido de la empresa."
                )


        numero = str(
            cheque_datos.get(
                "numero",
                "",
            )
            or ""
        ).strip()


        if not numero:

            raise ValueError(
                "Ingrese el número del cheque."
            )


        try:

            importe_cheque = Decimal(
                str(
                    cheque_datos.get(
                        "importe",
                        0,
                    )
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as error:

            raise ValueError(
                "Existe un cheque "
                "con un importe inválido."
            ) from error


        if importe_cheque <= Decimal(
            "0.00"
        ):

            raise ValueError(
                "El importe del cheque "
                "debe ser mayor a cero."
            )


        fecha_emision = str(
            cheque_datos.get(
                "fecha_emision",
                "",
            )
            or ""
        ).strip()


        if not fecha_emision:

            raise ValueError(
                "Ingrese la fecha de emisión "
                "del cheque."
            )


        try:

            fecha_emision_validada = (
                datetime.strptime(
                    fecha_emision,
                    "%Y-%m-%d",
                ).date()
            )

        except ValueError as error:

            raise ValueError(
                "La fecha de emisión "
                "del cheque no es válida."
            ) from error


        fecha_acreditacion = str(
            cheque_datos.get(
                "fecha_acreditacion",
                "",
            )
            or ""
        ).strip()


        fecha_acreditacion_validada = None


        if fecha_acreditacion:

            try:

                fecha_acreditacion_validada = (
                    datetime.strptime(
                        fecha_acreditacion,
                        "%Y-%m-%d",
                    ).date()
                )

            except ValueError as error:

                raise ValueError(
                    "La fecha de acreditación "
                    "del cheque no es válida."
                ) from error


        quien_entrega = str(
            cheque_datos.get(
                "quien_entrega",
                "",
            )
            or ""
        ).strip()


        cheques_validados.append(
            {
                "tipo_instrumento":
                    tipo_instrumento,

                "origen":
                    origen,

                "tipo_cheque":
                    tipo_cheque,

                "banco":
                    banco,

                "cuenta_bancaria":
                    cuenta_bancaria,

                "numero":
                    numero,

                "importe":
                    importe_cheque,

                "fecha_emision":
                    fecha_emision_validada,

                "fecha_acreditacion":
                    fecha_acreditacion_validada,

                "quien_entrega":
                    quien_entrega,
            }
        )


        total_cheques += (
            importe_cheque
        )


    # =========================================
    # RETENCIONES
    # =========================================

    retenciones_raw = (
        pago_datos.get(
            "retenciones",
        )
        or []
    )


    if not isinstance(
        retenciones_raw,
        list,
    ):

        raise ValueError(
            "Las retenciones del Pago "
            "no son válidas."
        )


    retenciones_validadas = []

    total_retenciones = Decimal(
        "0.00"
    )


    for retencion_datos in retenciones_raw:

        if not isinstance(
            retencion_datos,
            dict,
        ):

            raise ValueError(
                "Existe una retención "
                "con formato inválido."
            )


        retencion_id = (
            retencion_datos.get(
                "retencion_id",
            )
        )


        retencion = (
            Retencion.objects.filter(
                id=retencion_id,
                empresa=empresa,
                activo=True,
            ).first()
        )


        if not retencion:

            raise ValueError(
                "La retención seleccionada "
                "no es válida para este Pago."
            )


        retencion_tipo = str(
            retencion_datos.get(
                "retencion_tipo",
                "",
            )
            or ""
        ).strip()


        if not retencion_tipo:

            retencion_tipo = (
                retencion.tipo
            )


        if (
            retencion_tipo.upper() !=
            retencion.tipo.upper()
        ):

            raise ValueError(
                "El tipo de retención recibido "
                "no coincide con la retención seleccionada."
            )


        try:

            importe_retencion = Decimal(
                str(
                    retencion_datos.get(
                        "importe",
                        0,
                    )
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as error:

            raise ValueError(
                "Existe una retención "
                "con un importe inválido."
            ) from error


        if (
            importe_retencion <=
            Decimal("0.00")
        ):

            raise ValueError(
                "El importe de una retención "
                "debe ser mayor a cero."
            )


        comprobante_clave = str(
            retencion_datos.get(
                "comprobante_clave",
                "",
            )
            or ""
        ).strip()


        comprobante = None


        if comprobante_clave:

            comprobante = archivos.get(
                comprobante_clave
            )


        retenciones_validadas.append(
            {
                "tipo":
                    retencion.tipo,

                "importe":
                    importe_retencion,

                "comprobante":
                    comprobante,
            }
        )


        total_retenciones += (
            importe_retencion
        )


    # =========================================
    # TOTAL APLICADO POR EL PAGO
    # =========================================

    importe_pago = (
        importe_efectivo +
        total_operaciones +
        total_tarjetas +
        total_cheques +
        total_retenciones
    )


    if importe_pago <= Decimal(
        "0.00"
    ):

        raise ValueError(
            "El importe total del Pago "
            "debe ser mayor a cero."
        )


    return {
        "fecha":
            fecha_pago_validada,

        "importe_efectivo":
            importe_efectivo,

        "importe_pago":
            importe_pago,

        "operaciones_bancarias":
            operaciones_validadas,

        "tarjetas":
            tarjetas_validadas,

        "cheques":
            cheques_validados,

        "retenciones":
            retenciones_validadas,
    }

# =========================================
# COBRANZAS / INGRESOS DE CAJA
# =========================================

def validar_cobranza(
    empresa,
    cobranza_datos,
):
    """
    Valida y normaliza una Cobranza antes de persistirla.

    La Cobranza puede contener efectivo en ARS y/o USD y cheques físicos
    de terceros. El total declarado debe coincidir con la suma de todos
    los componentes recibidos.

    Esta función no persiste información ni depende de request o de
    formularios HTTP. Devuelve una estructura normalizada apta para el
    servicio de creación de la Cobranza.

    Lanza ValueError cuando algún dato no cumple las reglas del dominio.
    """
    from datetime import datetime
    from decimal import (
        Decimal,
        InvalidOperation,
    )

    from usuarios.models import (
        Banco,
        Caja,
        Cliente,
    )

    if not isinstance(cobranza_datos, dict):
        raise ValueError(
            "La Cobranza tiene un formato inválido."
        )

    # =========================================
    # CAJA
    # =========================================

    caja_id = cobranza_datos.get("caja_id")

    try:
        caja = Caja.objects.get(
            id=caja_id,
            empresa=empresa,
            activo=True,
        )
    except (
        Caja.DoesNotExist,
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "La Caja seleccionada no es válida para esta Empresa."
        ) from error

    if caja.centro_operativo.tipo not in {
        "Casa Central",
        "Sucursal",
    }:
        raise ValueError(
            "La Caja seleccionada no pertenece a una "
            "Casa Central o Sucursal."
        )

    # =========================================
    # FECHA
    # =========================================

    fecha_raw = str(
        cobranza_datos.get("fecha", "") or ""
    ).strip()

    if not fecha_raw:
        raise ValueError(
            "La Cobranza debe tener una fecha."
        )

    try:
        fecha = datetime.strptime(
            fecha_raw,
            "%Y-%m-%d",
        ).date()
    except ValueError as error:
        raise ValueError(
            "La fecha de la Cobranza no es válida."
        ) from error

    # =========================================
    # DATOS GENERALES
    # =========================================

    referencia = str(
        cobranza_datos.get("referencia", "") or ""
    ).strip()

    if not referencia:
        raise ValueError(
            "La referencia de la Cobranza es obligatoria."
        )

    if len(referencia) > 200:
        raise ValueError(
            "La referencia de la Cobranza es demasiado extensa."
        )

    vendedor_referencia = str(
        cobranza_datos.get(
            "vendedor_referencia",
            "",
        )
        or ""
    ).strip()

    if len(vendedor_referencia) > 150:
        raise ValueError(
            "La referencia del vendedor es demasiado extensa."
        )

    observaciones = str(
        cobranza_datos.get("observaciones", "") or ""
    ).strip()

    # =========================================
    # TOTAL DECLARADO
    # =========================================

    try:
        total_declarado = Decimal(
            str(
                cobranza_datos.get(
                    "total_declarado",
                    "0.00",
                )
            )
        )
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "El total declarado de la Cobranza no es válido."
        ) from error

    if total_declarado <= Decimal("0.00"):
        raise ValueError(
            "El total declarado debe ser mayor que cero."
        )

    # =========================================
    # EFECTIVO
    # =========================================

    efectivo_raw = (
        cobranza_datos.get("efectivo")
        or {}
    )

    if not isinstance(efectivo_raw, dict):
        raise ValueError(
            "El efectivo de la Cobranza tiene un formato inválido."
        )

    efectivo = {}

    for moneda in ("ARS", "USD"):
        valor_raw = efectivo_raw.get(
            moneda,
            "0.00",
        )

        try:
            importe = Decimal(
                str(valor_raw or "0.00")
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"El importe en efectivo {moneda} no es válido."
            ) from error

        if importe < Decimal("0.00"):
            raise ValueError(
                f"El efectivo {moneda} no puede ser negativo."
            )

        if importe > Decimal("0.00"):
            efectivo[moneda] = importe

    # =========================================
    # CHEQUES FÍSICOS RECIBIDOS
    # =========================================

    cheques_raw = (
        cobranza_datos.get("cheques")
        or []
    )

    if not isinstance(cheques_raw, list):
        raise ValueError(
            "Los cheques de la Cobranza tienen un formato inválido."
        )

    cheques = []
    total_cheques = Decimal("0.00")

    for indice, cheque_raw in enumerate(
        cheques_raw,
        start=1,
    ):
        if not isinstance(cheque_raw, dict):
            raise ValueError(
                f"El cheque {indice} tiene un formato inválido."
            )

        numero = str(
            cheque_raw.get("numero", "") or ""
        ).strip()

        if not numero:
            raise ValueError(
                f"El cheque {indice} debe tener número."
            )

        if len(numero) > 30:
            raise ValueError(
                f"El número del cheque {indice} es demasiado extenso."
            )

        try:
            importe = Decimal(
                str(
                    cheque_raw.get(
                        "importe",
                        "0.00",
                    )
                )
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"El importe del cheque {indice} no es válido."
            ) from error

        if importe <= Decimal("0.00"):
            raise ValueError(
                f"El importe del cheque {indice} debe ser mayor que cero."
            )

        banco_id = cheque_raw.get("banco_id")

        try:
            banco = Banco.objects.get(
                id=banco_id,
                empresa=empresa,
            )
        except (
            Banco.DoesNotExist,
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"El banco del cheque {indice} no es válido."
            ) from error

        cliente = None
        cliente_id = cheque_raw.get("cliente_id")

        if cliente_id not in (
            None,
            "",
        ):
            try:
                cliente = Cliente.objects.get(
                    id=cliente_id,
                    empresa=empresa,
                    activo=True,
                )
            except (
                Cliente.DoesNotExist,
                TypeError,
                ValueError,
            ) as error:
                raise ValueError(
                    f"El Cliente del cheque {indice} no es válido."
                ) from error

        fecha_acreditacion = _validar_fecha_opcional_cobranza(
            cheque_raw.get("fecha_acreditacion"),
            f"fecha de acreditación del cheque {indice}",
        )

        fecha_vencimiento = _validar_fecha_opcional_cobranza(
            cheque_raw.get("fecha_vencimiento"),
            f"fecha de vencimiento del cheque {indice}",
        )

        tipo_cheque = str(
            cheque_raw.get(
                "tipo_cheque",
                "Diferido",
            )
            or ""
        ).strip()

        if tipo_cheque not in {
            "Comun",
            "Diferido",
        }:
            raise ValueError(
                f"El tipo del cheque {indice} no es válido."
            )

        quien_entrega = str(
            cheque_raw.get(
                "quien_entrega",
                "",
            )
            or ""
        ).strip()

        if len(quien_entrega) > 200:
            raise ValueError(
                f"El dato de entrega del cheque {indice} es demasiado extenso."
            )

        cheques.append({
            "numero": numero,
            "importe": importe,
            "banco": banco,
            "cliente": cliente,
            "tipo_cheque": tipo_cheque,
            "fecha_acreditacion": fecha_acreditacion,
            "fecha_vencimiento": fecha_vencimiento,
            "quien_entrega": quien_entrega,
        })

        total_cheques += importe

    # =========================================
    # CONCILIACIÓN
    # =========================================
    #
    # En esta primera versión, USD no se convierte a ARS.
    # Por lo tanto no puede formar parte de una conciliación
    # monetaria única con el total declarado en ARS.
    #

    total_efectivo_ars = efectivo.get(
        "ARS",
        Decimal("0.00"),
    )

    total_componentes_ars = (
        total_efectivo_ars
        + total_cheques
    )

    if total_componentes_ars != total_declarado:
        diferencia = (
            total_declarado
            - total_componentes_ars
        )

        raise ValueError(
            "La Cobranza no concilia. "
            f"Diferencia: {diferencia:.2f}."
        )

    if (
        not efectivo
        and not cheques
    ):
        raise ValueError(
            "La Cobranza debe contener al menos un medio recibido."
        )

    return {
        "caja": caja,
        "fecha": fecha,
        "referencia": referencia,
        "vendedor_referencia": vendedor_referencia,
        "total_declarado": total_declarado,
        "observaciones": observaciones,
        "efectivo": efectivo,
        "cheques": cheques,
        "total_cheques": total_cheques,
        "total_componentes_ars": total_componentes_ars,
    }


def _validar_fecha_opcional_cobranza(
    valor,
    descripcion,
):
    """
    Normaliza una fecha opcional utilizada por los componentes de una
    Cobranza.

    Devuelve None cuando no se informó una fecha y lanza ValueError
    cuando el valor recibido no utiliza el formato ISO YYYY-MM-DD.
    """
    from datetime import datetime

    valor = str(
        valor or ""
    ).strip()

    if not valor:
        return None

    try:
        return datetime.strptime(
            valor,
            "%Y-%m-%d",
        ).date()
    except ValueError as error:
        raise ValueError(
            f"La {descripcion} no es válida."
        ) from error

def crear_cobranza_validada(
    empresa,
    usuario,
    cobranza_datos,
):
    """
    Crea una Cobranza y todos sus componentes financieros dentro de una
    única transacción atómica.

    Primero valida y normaliza la información recibida. Luego crea la
    cabecera de Cobranza, los movimientos de efectivo y los cheques
    físicos de terceros incorporados a cartera.

    Si falla cualquier componente, la transacción completa se revierte
    para evitar cobranzas parciales o disponibilidades inconsistentes.
    """
    from django.db import transaction

    from usuarios.models import (
        Cheque,
        Cobranza,
        MovimientoCaja,
    )

    datos = validar_cobranza(
        empresa=empresa,
        cobranza_datos=cobranza_datos,
    )

    if not usuario or not usuario.is_authenticated:
        raise ValueError(
            "Se requiere un usuario autenticado para registrar la Cobranza."
        )

    with transaction.atomic():

        cobranza = Cobranza.objects.create(
            empresa=empresa,
            caja=datos["caja"],
            fecha=datos["fecha"],
            referencia=datos["referencia"],
            vendedor_referencia=datos[
                "vendedor_referencia"
            ],
            total_declarado=datos[
                "total_declarado"
            ],
            observaciones=datos[
                "observaciones"
            ],
            creado_por=usuario,
        )

        movimientos_efectivo = []

        for moneda, importe in datos[
            "efectivo"
        ].items():

            movimiento = MovimientoCaja.objects.create(
                empresa=empresa,
                caja=datos["caja"],
                cobranza=cobranza,
                fecha=datos["fecha"],
                tipo="Ingreso",
                moneda=moneda,
                importe=importe,
                concepto=(
                    f"Cobranza: {datos['referencia']}"
                ),
                creado_por=usuario,
            )

            movimientos_efectivo.append(
                movimiento
            )

        cheques_creados = []

        for cheque_datos in datos[
            "cheques"
        ]:

            cheque = Cheque.objects.create(
                empresa=empresa,
                cobranza=cobranza,
                caja=datos["caja"],
                cliente=cheque_datos[
                    "cliente"
                ],
                pago=None,
                tipo_instrumento="Cheque",
                origen="Tercero",
                tipo_cheque=cheque_datos[
                    "tipo_cheque"
                ],
                banco=cheque_datos[
                    "banco"
                ],
                cuenta_bancaria=None,
                numero=cheque_datos[
                    "numero"
                ],
                importe=cheque_datos[
                    "importe"
                ],
                fecha_emision=None,
                fecha_acreditacion=cheque_datos[
                    "fecha_acreditacion"
                ],
                fecha_vencimiento=cheque_datos[
                    "fecha_vencimiento"
                ],
                quien_entrega=cheque_datos[
                    "quien_entrega"
                ],
                estado="Disponible",
            )

            cheques_creados.append(
                cheque
            )

    return {
        "cobranza": cobranza,
        "movimientos_efectivo":
            movimientos_efectivo,
        "cheques":
            cheques_creados,
    }

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