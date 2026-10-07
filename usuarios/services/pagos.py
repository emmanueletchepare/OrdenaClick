from usuarios.services.financiero import (
    estado_financiero_movimiento,
    resumen_financiero_movimiento,
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

def normalizar_numero_cheque(valor):
    """
    Normaliza un número de cheque al formato canónico de OrdenaClick.

    Acepta entre 1 y 8 dígitos numéricos y devuelve siempre una cadena
    de exactamente 8 posiciones, completando con ceros a la izquierda.

    Ejemplo:
        1698 -> "00001698"

    No elimina caracteres arbitrarios: si el valor recibido contiene
    letras, espacios internos, signos u otros caracteres, se rechaza.
    """
    numero = str(
        valor or ""
    ).strip()

    if not numero:
        raise ValueError(
            "Ingrese el número del cheque."
        )

    if not numero.isdigit():
        raise ValueError(
            "El número del cheque debe contener sólo dígitos."
        )

    if len(numero) > 8:
        raise ValueError(
            "El número del cheque no puede superar los 8 dígitos."
        )

    return numero.zfill(8)


def validar_fechas_cheque(
    tipo_cheque,
    fecha_emision,
    fecha_acreditacion=None,
):
    """
    Valida y normaliza las fechas comunes de un cheque.

    Para cheque Común, la fecha de acreditación coincide con la fecha
    de emisión.

    Para cheque Diferido, la fecha de acreditación es obligatoria,
    debe ser posterior a la emisión y no puede superar los 360 días
    desde esa fecha.
    """
    from datetime import datetime

    tipo_cheque = str(
        tipo_cheque or ""
    ).strip()

    if tipo_cheque not in {
        "Comun",
        "Diferido",
    }:
        raise ValueError(
            "El tipo de cheque no es válido."
        )

    fecha_emision_raw = str(
        fecha_emision or ""
    ).strip()

    if not fecha_emision_raw:
        raise ValueError(
            "Ingrese la fecha de emisión del cheque."
        )

    try:
        fecha_emision_validada = datetime.strptime(
            fecha_emision_raw,
            "%Y-%m-%d",
        ).date()
    except ValueError as error:
        raise ValueError(
            "La fecha de emisión del cheque no es válida."
        ) from error

    if tipo_cheque == "Comun":
        return (
            fecha_emision_validada,
            fecha_emision_validada,
        )

    fecha_acreditacion_raw = str(
        fecha_acreditacion or ""
    ).strip()

    if not fecha_acreditacion_raw:
        raise ValueError(
            "Ingrese la fecha de acreditación del cheque diferido."
        )

    try:
        fecha_acreditacion_validada = datetime.strptime(
            fecha_acreditacion_raw,
            "%Y-%m-%d",
        ).date()
    except ValueError as error:
        raise ValueError(
            "La fecha de acreditación del cheque no es válida."
        ) from error

    if fecha_acreditacion_validada <= fecha_emision_validada:
        raise ValueError(
            "La fecha de acreditación del cheque diferido "
            "debe ser posterior a la fecha de emisión."
        )

    dias_diferencia = (
        fecha_acreditacion_validada
        - fecha_emision_validada
    ).days

    if dias_diferencia > 360:
        raise ValueError(
            "La fecha de acreditación del cheque diferido "
            "no puede superar los 360 días desde la emisión."
        )

    return (
        fecha_emision_validada,
        fecha_acreditacion_validada,
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


        numero = normalizar_numero_cheque(
            cheque_datos.get(
                "numero",
                "",
            )
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


        (
            fecha_emision_validada,
            fecha_acreditacion_validada,
        ) = validar_fechas_cheque(
            tipo_cheque,
            cheque_datos.get(
                "fecha_emision",
                "",
            ),
            cheque_datos.get(
                "fecha_acreditacion",
                "",
            ),
        )


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
