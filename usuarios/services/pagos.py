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

from usuarios.services.pagos_validacion import (
    normalizar_numero_cheque,
    validar_fechas_cheque,
    validar_pago_movimiento,
)
