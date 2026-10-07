from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse

from usuarios.models import (
    AplicacionPago,
    DebitoAutomaticoPago,
    Movimiento,
    Pago,
)


@login_required
def eliminar_pago_movimiento(request):
    """
    Elimina un Pago cargado por error y recalcula el estado
    financiero del Movimiento al que estaba aplicado.

    La operación exige que Empresa, Movimiento y Pago pertenezcan
    al mismo contexto autorizado. Los registros principales se
    bloquean durante la transacción para evitar modificaciones
    financieras concurrentes.
    """

    import logging

    from django.db import transaction
    from django.http import JsonResponse

    from usuarios.models import (
        AplicacionPago,
        Movimiento,
        Pago,
    )
    from usuarios.services.financiero import (
        eliminar_pago_movimiento as eliminar_pago_servicio,
    )
    from usuarios.services.seguridad import (
        obtener_empresa_autorizada,
    )


    logger = logging.getLogger(__name__)


    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Método no permitido."
                ),
            },
            status=405,
        )


    empresa_id = request.POST.get(
        "empresa"
    )

    movimiento_id = request.POST.get(
        "movimiento"
    )

    pago_id = request.POST.get(
        "pago"
    )


    if (
        not empresa_id or
        not movimiento_id or
        not pago_id
    ):

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Faltan datos para eliminar el Pago."
                ),
            },
            status=400,
        )


    empresa = obtener_empresa_autorizada(
        request.user,
        empresa_id,
    )


    if not empresa:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "La Empresa seleccionada no es válida."
                ),
            },
            status=403,
        )


    try:

        with transaction.atomic():

            movimiento = (
                Movimiento.objects
                .select_for_update()
                .filter(
                    id=movimiento_id,
                    empresa=empresa,
                )
                .first()
            )


            if not movimiento:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Movimiento no es válido."
                        ),
                    },
                    status=404,
                )


            pago = (
                Pago.objects
                .select_for_update()
                .filter(
                    id=pago_id,
                    empresa=empresa,
                )
                .first()
            )


            if not pago:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Pago no es válido."
                        ),
                    },
                    status=404,
                )


            aplicaciones = list(
                AplicacionPago.objects
                .select_for_update()
                .filter(
                    pago=pago,
                )
            )


            if not aplicaciones:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Pago no posee una aplicación "
                            "financiera."
                        ),
                    },
                    status=400,
                )


            if (
                len(aplicaciones) != 1 or
                aplicaciones[0].movimiento_id !=
                    movimiento.id
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Pago no corresponde "
                            "exclusivamente a este Movimiento."
                        ),
                    },
                    status=400,
                )


            resumen = eliminar_pago_servicio(
                empresa=empresa,
                movimiento=movimiento,
                pago=pago,
            )


            return JsonResponse(
                {
                    "ok": True,
                    "mensaje": (
                        "El Pago fue eliminado correctamente."
                    ),
                    "movimiento": movimiento.id,
                    "total_aplicado": str(
                        resumen[
                            "total_aplicado"
                        ]
                    ),
                    "saldo_pendiente": str(
                        resumen[
                            "saldo_pendiente"
                        ]
                    ),
                    "estado": resumen[
                        "estado_financiero"
                    ],
                }
            )


    except ValueError as error:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": str(error),
            },
            status=400,
        )


    except Exception:

        logger.exception(
            "Error inesperado al eliminar Pago "
            "del Movimiento %s.",
            movimiento_id,
        )

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "No fue posible eliminar el Pago."
                ),
            },
            status=500,
        )

@login_required
def registrar_pago_manual_movimiento(request):
    """
    Registra uno o varios Pagos manuales sobre un Movimiento existente.

    La operación exige un usuario autenticado y una Empresa autorizada.
    El Movimiento se bloquea dentro de una transacción para recalcular
    su saldo real antes de crear cualquier Pago.

    Todas las formas de pago se validan nuevamente en backend aunque
    hayan sido validadas previamente por la interfaz.

    Si la suma de los nuevos Pagos supera el saldo pendiente real,
    no se crea ningún registro financiero.
    """

    import json
    import logging

    from decimal import Decimal

    from django.db import transaction

    from usuarios.services.financiero import (
        crear_pago_validado_movimiento,
        total_aplicado_movimiento,
        validar_importe_aplicable,
        validar_pago_movimiento,
    )

    from usuarios.services.seguridad import (
        obtener_empresa_autorizada,
    )


    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido.",
            },
            status=405,
        )


    empresa_id = (
        request.POST.get("empresa")
        or ""
    ).strip()

    movimiento_id = (
        request.POST.get("movimiento")
        or ""
    ).strip()

    pagos_raw = (
        request.POST.get("pagos")
        or ""
    ).strip()


    if not empresa_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Seleccione una empresa.",
            },
            status=400,
        )


    if not movimiento_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "No se indicó el Movimiento."
                ),
            },
            status=400,
        )


    if not pagos_raw:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "No se recibieron Pagos para registrar."
                ),
            },
            status=400,
        )


    try:

        pagos = json.loads(
            pagos_raw
        )

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Los datos de los Pagos no son válidos."
                ),
            },
            status=400,
        )


    if not isinstance(
        pagos,
        list
    ):

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "El formato de los Pagos no es válido."
                ),
            },
            status=400,
        )


    if not pagos:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Debe registrar al menos un Pago."
                ),
            },
            status=400,
        )


    empresa = obtener_empresa_autorizada(
        request.user,
        empresa_id,
    )


    try:

        with transaction.atomic():

            movimiento = (
                Movimiento.objects
                .select_for_update()
                .filter(
                    id=movimiento_id,
                    empresa=empresa,
                )
                .first()
            )


            if not movimiento:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Movimiento no existe "
                            "o no pertenece a la empresa."
                        ),
                    },
                    status=404,
                )


            if movimiento.estado == "Cancelado":

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Un Movimiento cancelado "
                            "no puede recibir Pagos."
                        ),
                    },
                    status=400,
                )


            if (
                movimiento.modalidad_pago ==
                "DebitoAutomatico"
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Este Movimiento está configurado "
                            "para débito automático. Utilice "
                            "el registro específico de débito."
                        ),
                    },
                    status=400,
                )


            total_aplicado_existente = (
                total_aplicado_movimiento(
                    movimiento
                )
            )


            saldo_pendiente = (
                movimiento.total -
                total_aplicado_existente
            )


            if saldo_pendiente <= Decimal("0.00"):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Movimiento ya no posee "
                            "saldo pendiente."
                        ),
                    },
                    status=400,
                )


            pagos_validados = []

            importe_total_nuevo = Decimal(
                "0.00"
            )


            for pago_datos in pagos:

                try:

                    pago_validado = (
                        validar_pago_movimiento(
                            empresa=empresa,
                            pago_datos=pago_datos,
                            archivos=request.FILES,
                        )
                    )

                except ValueError as error:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": str(error),
                        },
                        status=400,
                    )


                pagos_validados.append(
                    pago_validado
                )

                importe_total_nuevo += (
                    pago_validado[
                        "importe_pago"
                    ]
                )


            try:

                validar_importe_aplicable(
                    saldo_pendiente=
                        saldo_pendiente,
                    importe_aplicar=
                        importe_total_nuevo,
                )

            except ValueError as error:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": str(error),
                    },
                    status=400,
                )


            resultados_pagos = []


            for pago_validado in pagos_validados:

                resultado_pago = (
                    crear_pago_validado_movimiento(
                        empresa=empresa,
                        movimiento=movimiento,
                        pago_datos=pago_validado,
                    )
                )

                resultados_pagos.append(
                    resultado_pago
                )


            total_aplicado_nuevo = (
                total_aplicado_existente +
                importe_total_nuevo
            )


            saldo_nuevo = (
                movimiento.total -
                total_aplicado_nuevo
            )


            if saldo_nuevo <= Decimal("0.00"):

                estado_movimiento = (
                    "Pagado"
                )

                saldo_nuevo = Decimal(
                    "0.00"
                )

            else:

                estado_movimiento = (
                    "Parcial"
                )


            movimiento.estado = (
                estado_movimiento
            )

            movimiento.save(
                update_fields=[
                    "estado",
                ]
            )


        return JsonResponse(
            {
                "ok": True,
                "mensaje": (
                    "Pago registrado correctamente."
                    if len(resultados_pagos) == 1
                    else
                    "Pagos registrados correctamente."
                ),
                "movimiento_id":
                    movimiento.id,
                "pagos_ids": [
                    resultado[
                        "pago_id"
                    ]
                    for resultado
                    in resultados_pagos
                ],
                "aplicaciones_ids": [
                    resultado[
                        "aplicacion_id"
                    ]
                    for resultado
                    in resultados_pagos
                ],
                "importe_aplicado":
                    str(
                        importe_total_nuevo
                    ),
                "total_aplicado":
                    str(
                        total_aplicado_nuevo
                    ),
                "saldo_pendiente":
                    str(
                        saldo_nuevo
                    ),
                "estado":
                    estado_movimiento,
            }
        )


    except Exception:

        logger = logging.getLogger(
            __name__
        )

        logger.exception(
            "Error registrando Pago manual "
            "sobre Movimiento existente."
        )

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Ocurrió un error al registrar "
                    "el Pago."
                ),
            },
            status=500,
        )

@login_required
def registrar_debito_automatico_movimiento(request):
    """
    Registra el Pago real de un débito automático
    sobre un Movimiento existente.

    El Movimiento se bloquea durante la operación
    para recalcular su saldo pendiente real antes
    de aplicar el Pago.

    Si el importe debitado supera el saldo pendiente,
    la diferencia solamente puede registrarse como
    interés por mora cuando:

    - el Movimiento posee fecha de vencimiento;
    - el débito ocurrió después del vencimiento;
    - el usuario confirmó expresamente la mora.

    Los intereses por mora nunca incrementan el
    importe aplicado al Movimiento.
    """

    from decimal import (
        Decimal,
        InvalidOperation,
    )

    from usuarios.services.financiero import (
        total_aplicado_movimiento,
        validar_importe_aplicable,
    )

    from usuarios.services.seguridad import (
        obtener_empresa_autorizada,
    )


    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido.",
            },
            status=405,
        )


    empresa_id = (
        request.POST.get("empresa")
        or ""
    ).strip()

    movimiento_id = (
        request.POST.get("movimiento")
        or ""
    ).strip()

    fecha_debito_texto = (
        request.POST.get("fecha")
        or ""
    ).strip()

    importe_debitado_texto = (
        request.POST.get("importe_debitado")
        or ""
    ).strip()

    confirmar_intereses_mora = (
        (
            request.POST.get(
                "confirmar_intereses_mora"
            )
            or ""
        ).strip().lower()
        in {
            "1",
            "true",
            "si",
            "sí",
        }
    )


    if not empresa_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Seleccione una empresa.",
            },
            status=400,
        )


    if not movimiento_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "No se indicó el Movimiento."
                ),
            },
            status=400,
        )


    if not fecha_debito_texto:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Ingrese la fecha real del débito."
                ),
            },
            status=400,
        )


    try:

        fecha_debito = datetime.strptime(
            fecha_debito_texto,
            "%Y-%m-%d",
        ).date()

    except ValueError:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "La fecha del débito automático "
                    "no es válida."
                ),
            },
            status=400,
        )


    try:

        importe_debitado = Decimal(
            importe_debitado_texto
        )

    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ):

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "El importe del débito automático "
                    "no es válido."
                ),
            },
            status=400,
        )


    if importe_debitado <= Decimal("0.00"):

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "El importe debitado debe ser "
                    "mayor a cero."
                ),
            },
            status=400,
        )


    empresa = obtener_empresa_autorizada(
        request.user,
        empresa_id,
    )


    try:

        with transaction.atomic():

            movimiento = (
                Movimiento.objects
                .select_for_update()
                .filter(
                    id=movimiento_id,
                    empresa=empresa,
                )
                .first()
            )


            if not movimiento:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Movimiento no existe "
                            "o no pertenece a la empresa."
                        ),
                    },
                    status=404,
                )


            if movimiento.estado == "Cancelado":

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Un Movimiento cancelado "
                            "no puede recibir Pagos."
                        ),
                    },
                    status=400,
                )


            if (
                movimiento.modalidad_pago !=
                "DebitoAutomatico"
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Movimiento no está configurado "
                            "para débito automático."
                        ),
                    },
                    status=400,
                )


            cuenta_debito = (
                movimiento.cuenta_debito
            )


            if (
                not cuenta_debito
                or not cuenta_debito.activo
                or cuenta_debito.empresa_id !=
                    empresa.id
                or cuenta_debito.moneda !=
                    "ARS"
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "La cuenta prevista para el débito "
                            "automático no es válida."
                        ),
                    },
                    status=400,
                )


            if (
                movimiento.fecha_registro
                and
                fecha_debito <
                movimiento.fecha_registro
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "La fecha real del débito "
                            "no puede ser anterior a "
                            "la fecha del gasto."
                        ),
                    },
                    status=400,
                )


            total_aplicado_existente = (
                total_aplicado_movimiento(
                    movimiento
                )
            )


            saldo_pendiente = (
                movimiento.total -
                total_aplicado_existente
            )


            if saldo_pendiente <= Decimal("0.00"):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Movimiento ya no posee "
                            "saldo pendiente."
                        ),
                    },
                    status=400,
                )


            importe_aplicado = (
                importe_debitado
            )

            intereses_mora = Decimal(
                "0.00"
            )


            if importe_debitado > saldo_pendiente:

                if not movimiento.fecha_vencimiento:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "El débito supera el saldo "
                                "pendiente y el Movimiento "
                                "no posee fecha de vencimiento."
                            ),
                        },
                        status=400,
                    )


                if (
                    fecha_debito <=
                    movimiento.fecha_vencimiento
                ):

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "El débito supera el saldo "
                                "pendiente, pero no ocurrió "
                                "después del vencimiento."
                            ),
                        },
                        status=400,
                    )


                if not confirmar_intereses_mora:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "La diferencia del débito debe "
                                "confirmarse como interés por "
                                "mora antes de guardar."
                            ),
                        },
                        status=400,
                    )


                importe_aplicado = (
                    saldo_pendiente
                )

                intereses_mora = (
                    importe_debitado -
                    saldo_pendiente
                )


            try:

                validar_importe_aplicable(
                    saldo_pendiente=
                        saldo_pendiente,
                    importe_aplicar=
                        importe_aplicado,
                )

            except ValueError as error:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": str(error),
                    },
                    status=400,
                )


            pago = Pago.objects.create(
                empresa=empresa,
                fecha=fecha_debito,
                importe_efectivo=
                    Decimal("0.00"),
            )


            debito = (
                DebitoAutomaticoPago.objects.create(
                    pago=pago,
                    cuenta_bancaria=
                        cuenta_debito,
                    importe=
                        importe_debitado,
                    intereses_mora=
                        intereses_mora,
                    fecha_debito=
                        fecha_debito,
                )
            )


            aplicacion = (
                AplicacionPago.objects.create(
                    pago=pago,
                    movimiento=movimiento,
                    importe=
                        importe_aplicado,
                )
            )


            total_aplicado_nuevo = (
                total_aplicado_existente +
                importe_aplicado
            )

            saldo_nuevo = (
                movimiento.total -
                total_aplicado_nuevo
            )


            if saldo_nuevo <= Decimal("0.00"):

                estado_movimiento = (
                    "Pagado"
                )

            else:

                estado_movimiento = (
                    "Parcial"
                )


            movimiento.estado = (
                estado_movimiento
            )

            movimiento.save(
                update_fields=[
                    "estado",
                ]
            )


        return JsonResponse(
            {
                "ok": True,
                "mensaje": (
                    "Pago registrado correctamente."
                ),
                "movimiento_id":
                    movimiento.id,
                "pago_id":
                    pago.id,
                "debito_automatico_id":
                    debito.id,
                "aplicacion_id":
                    aplicacion.id,
                "importe_debitado":
                    str(importe_debitado),
                "importe_aplicado":
                    str(importe_aplicado),
                "intereses_mora":
                    str(intereses_mora),
                "total_aplicado":
                    str(total_aplicado_nuevo),
                "saldo_pendiente":
                    str(saldo_nuevo),
                "estado":
                    estado_movimiento,
            }
        )


    except Exception as error:

        print(
            "Error registrando débito "
            "automático en Movimiento:",
            error,
        )

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Ocurrió un error al registrar "
                    "el Pago."
                ),
            },
            status=500,
        )
