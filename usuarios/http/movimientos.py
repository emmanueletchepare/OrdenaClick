import json
import re

from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse

from usuarios.models import (
    AplicacionPago,
    CentroOperativo,
    CuentaBancaria,
    DebitoAutomaticoPago,
    Empresa,
    Movimiento,
    Proveedor,
    RecursoOperativo,
    TipoGasto,
)


@login_required
def guardar_movimiento(request):
    """
    Guarda un Movimiento creado desde Carga Simple.

    Permite registrar:

    - Movimiento sin Pago.
    - Uno o varios Pagos.
    - Efectivo.
    - Transferencias.
    - DepÃ³sitos.
    - Tarjetas.
    - Cheques / e-Cheqs.
    - Retenciones.
    - Aplicaciones de Pago.

    Movimiento, Pagos, Aplicaciones, Operaciones Bancarias,
    Tarjetas, Cheques y Retenciones se guardan dentro
    de una Ãºnica transacciÃ³n atÃ³mica.
    """
    from usuarios.services.financiero import (
        crear_pago_validado_movimiento,
        validar_importe_aplicable,
        validar_pago_movimiento,
    )

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "MÃ©todo no permitido.",
            },
            status=405,
        )


    try:

        # =========================================
        # DATOS GENERALES
        # =========================================

        empresa_id = request.POST.get(
            "empresa"
        )

        tipo_gasto_id = request.POST.get(
            "tipo_gasto"
        )

        proveedor_id = request.POST.get(
            "proveedor"
        )

        centro_operativo_id = request.POST.get(
            "centro_operativo"
        )

        recurso_operativo_id = request.POST.get(
            "recurso_operativo"
        )

        fecha_registro = request.POST.get(
            "fecha_registro"
        )

        fecha_vencimiento = request.POST.get(
            "fecha_vencimiento"
        )

        modalidad_pago = (
            request.POST.get(
                "modalidad_pago"
            )
            or "Manual"
        ).strip()

        cuenta_debito_id = (
            request.POST.get(
                "cuenta_debito"
            )
            or ""
        ).strip()

        tipo_comprobante = (
            request.POST.get(
                "tipo_comprobante"
            )
            or ""
        ).strip()

        numero_comprobante = (
            request.POST.get(
                "numero_comprobante"
            )
            or ""
        ).strip()


        # =========================================
        # VALIDACIONES GENERALES
        # =========================================

        if not empresa_id:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": "Seleccione una empresa.",
                },
                status=400,
            )


        if not tipo_gasto_id:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": "Seleccione un tipo de gasto.",
                },
                status=400,
            )


        if not proveedor_id:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": "Seleccione un proveedor.",
                },
                status=400,
            )


        if not fecha_registro:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": "Ingrese la fecha del registro.",
                },
                status=400,
            )


        # =========================================
        # EMPRESA
        # =========================================

        empresa = Empresa.objects.filter(
            id=empresa_id
        ).first()


        if not empresa:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "La empresa seleccionada no existe."
                    ),
                },
                status=404,
            )

        # =========================================
        # PREVISIÃ“N DE PAGO
        # =========================================

        modalidades_validas = {
            valor
            for valor, etiqueta
            in Movimiento.MODALIDADES_PAGO
        }


        if modalidad_pago not in modalidades_validas:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "La forma prevista de pago "
                        "no es vÃ¡lida."
                    ),
                },
                status=400,
            )


        cuenta_debito = None


        if modalidad_pago == "DebitoAutomatico":

            if not cuenta_debito_id:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Seleccione la cuenta prevista "
                            "para el dÃ©bito automÃ¡tico."
                        ),
                    },
                    status=400,
                )


            cuenta_debito = (
                CuentaBancaria.objects.filter(
                    id=cuenta_debito_id,
                    empresa=empresa,
                    activo=True,
                    moneda="ARS",
                ).first()
            )


            if not cuenta_debito:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "La cuenta seleccionada para "
                            "el dÃ©bito automÃ¡tico no es vÃ¡lida."
                        ),
                    },
                    status=400,
                )


        elif cuenta_debito_id:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Un Pago manual no debe tener "
                        "una cuenta prevista para dÃ©bito."
                    ),
                },
                status=400,
            )

        # =========================================
        # EJERCICIO ABIERTO
        # =========================================

        ejercicio = empresa.ejercicios.filter(
            estado="Abierto"
        ).first()


        if not ejercicio:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "La empresa no tiene un ejercicio abierto."
                    ),
                },
                status=400,
            )


        # =========================================
        # TIPO DE GASTO
        # =========================================

        tipo_gasto = TipoGasto.objects.filter(
            id=tipo_gasto_id,
            empresa=empresa,
            activo=True,
        ).first()


        if not tipo_gasto:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El tipo de gasto no es vÃ¡lido."
                    ),
                },
                status=400,
            )


        # =========================================
        # PROVEEDOR
        # =========================================

        proveedor = Proveedor.objects.filter(
            id=proveedor_id,
            empresa=empresa,
            activo=True,
        ).first()


        if not proveedor:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El proveedor no es vÃ¡lido."
                    ),
                },
                status=400,
            )

        # =========================================
        # COMPROBANTE
        # =========================================

        tipos_comprobante_validos = {
            "A",
            "B",
            "C",
            "X",
        }


        if tipo_comprobante not in tipos_comprobante_validos:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Seleccione un tipo de comprobante vÃ¡lido."
                    ),
                },
                status=400,
            )


        if not re.fullmatch(
            r"\d{4}-\d{8}",
            numero_comprobante
        ):

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El nÃºmero de comprobante no tiene "
                        "un formato vÃ¡lido."
                    ),
                },
                status=400,
            )


        comprobante_duplicado = (
            Movimiento.objects.filter(
                empresa=empresa,
                proveedor=proveedor,
                tipo_comprobante=tipo_comprobante,
                numero_comprobante=numero_comprobante,
            )
            .exists()
        )


        if comprobante_duplicado:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Ese comprobante ya fue registrado "
                        "para este proveedor."
                    ),
                },
                status=400,
            )

        # =========================================
        # CENTRO OPERATIVO
        # =========================================

        centro_operativo = None


        if centro_operativo_id:

            centro_operativo = (
                CentroOperativo.objects.filter(
                    id=centro_operativo_id,
                    empresa=empresa,
                    activo=True,
                ).first()
            )


            if not centro_operativo:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Centro Operativo no es vÃ¡lido."
                        ),
                    },
                    status=400,
                )


        # =========================================
        # RECURSO OPERATIVO
        # =========================================

        recurso_operativo = None


        if recurso_operativo_id:

            recurso_operativo = (
                RecursoOperativo.objects.filter(
                    id=recurso_operativo_id,
                    empresa=empresa,
                    activo=True,
                ).first()
            )


            if not recurso_operativo:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Recurso Operativo no es vÃ¡lido."
                        ),
                    },
                    status=400,
                )


        # =========================================
        # DECIMALES
        # =========================================

        from decimal import (
            Decimal,
            InvalidOperation
        )


        def decimal_post(nombre):
            """
            Convierte un importe recibido mediante POST
            en un Decimal seguro para persistencia.
            """

            valor = (
                request.POST.get(nombre)
                or "0"
            )


            try:

                return Decimal(
                    str(valor)
                )


            except InvalidOperation:

                return Decimal("0")


        # =========================================
        # IMPORTES DEL MOVIMIENTO
        # =========================================

        neto_gravado = decimal_post(
            "neto_gravado"
        )

        no_gravado_exento = decimal_post(
            "no_gravado_exento"
        )

        iva_21 = decimal_post(
            "iva_21"
        )

        iva_27 = decimal_post(
            "iva_27"
        )

        iva_105 = decimal_post(
            "iva_105"
        )

        recargos_intereses = decimal_post(
            "recargos_intereses"
        )

        ajuste_redondeo = decimal_post(
            "ajuste_redondeo"
        )

        percepcion_iibb = decimal_post(
            "percepcion_iibb"
        )

        percepcion_iva = decimal_post(
            "percepcion_iva"
        )

        percepcion_ganancias = decimal_post(
            "percepcion_ganancias"
        )

        percepcion_tasas_municipales = (
            decimal_post(
                "percepcion_tasas_municipales"
            )
        )

        total = decimal_post(
            "total"
        )


        if total <= 0:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El total del registro debe ser mayor a cero."
                    ),
                },
                status=400,
            )


        # =========================================
        # PAGOS
        # =========================================

        pagos_raw = (
            request.POST.get(
                "pagos"
            )
            or "[]"
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
                        "Los datos de los Pagos no son vÃ¡lidos."
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
                        "El formato de los Pagos no es vÃ¡lido."
                    ),
                },
                status=400,
            )


        # =========================================
        # VALIDAR PAGOS
        # =========================================

        pagos_validados = []

        total_aplicado = Decimal(
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


            total_aplicado += (
                pago_validado[
                    "importe_pago"
                ]
            )


            pagos_validados.append(
                pago_validado
            )

        # =========================================
        # DÃ‰BITO AUTOMÃTICO REAL
        # =========================================
        #
        # La modalidad DebitoAutomatico del Movimiento
        # representa solamente la previsiÃ³n de pago.
        #
        # Este bloque registra el dÃ©bito Ãºnicamente
        # cuando el usuario confirmÃ³ que efectivamente
        # ocurriÃ³.
        #
        # El importe recibido desde el navegador es el
        # total efectivamente debitado por el banco.
        #
        # Si existe interÃ©s por mora:
        #
        # importe aplicado al Movimiento
        #     = saldo pendiente
        #
        # intereses_mora
        #     = importe debitado - saldo pendiente
        #
        # El interÃ©s nunca incrementa la AplicacionPago.
        #

        debito_automatico_validado = None

        debito_automatico_raw = (
            request.POST.get(
                "debito_automatico"
            )
            or "null"
        )

        try:

            debito_automatico = json.loads(
                debito_automatico_raw
            )

        except json.JSONDecodeError:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Los datos del dÃ©bito automÃ¡tico "
                        "no son vÃ¡lidos."
                    ),
                },
                status=400,
            )


        if debito_automatico is not None:

            if modalidad_pago != "DebitoAutomatico":

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "No puede registrarse un dÃ©bito automÃ¡tico "
                            "en un Movimiento configurado como Pago manual."
                        ),
                    },
                    status=400,
                )


            if pagos_validados:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Un Movimiento con dÃ©bito automÃ¡tico "
                            "no puede contener simultÃ¡neamente "
                            "Pagos manuales en esta carga."
                        ),
                    },
                    status=400,
                )


            if not isinstance(
                debito_automatico,
                dict
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El formato del dÃ©bito automÃ¡tico "
                            "no es vÃ¡lido."
                        ),
                    },
                    status=400,
                )


            # =====================================
            # FECHA REAL DEL DÃ‰BITO
            # =====================================

            fecha_debito = (
                debito_automatico.get(
                    "fecha"
                )
                or ""
            ).strip()


            if not fecha_debito:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Ingrese la fecha real del dÃ©bito."
                        ),
                    },
                    status=400,
                )


            try:

                fecha_debito_validada = (
                    datetime.strptime(
                        fecha_debito,
                        "%Y-%m-%d"
                    ).date()
                )

            except ValueError:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "La fecha del dÃ©bito automÃ¡tico "
                            "no es vÃ¡lida."
                        ),
                    },
                    status=400,
                )

            # =====================================
            # FECHA DEL GASTO
            # =====================================

            try:

                fecha_registro_validada = (
                    datetime.strptime(
                        fecha_registro,
                        "%Y-%m-%d"
                    ).date()
                )

            except ValueError:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "La fecha del registro "
                            "no es vÃ¡lida."
                        ),
                    },
                    status=400,
                )


            if (
                fecha_debito_validada <
                fecha_registro_validada
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "La fecha real del dÃ©bito "
                            "no puede ser anterior a "
                            "la fecha del gasto."
                        ),
                    },
                    status=400,
                )

            # =====================================
            # IMPORTE REAL DEBITADO
            # =====================================

            try:

                importe_debitado = Decimal(
                    str(
                        debito_automatico.get(
                            "importe_debitado",
                            0
                        )
                    )
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El importe del dÃ©bito automÃ¡tico "
                            "no es vÃ¡lido."
                        ),
                    },
                    status=400,
                )


            if importe_debitado <= 0:

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


            confirmar_intereses_mora = (
                debito_automatico.get(
                    "confirmar_intereses_mora"
                )
                is True
            )


            # =====================================
            # IMPORTE APLICADO / INTERÃ‰S
            # =====================================

            intereses_mora = Decimal(
                "0.00"
            )

            importe_aplicado_debito = (
                importe_debitado
            )


            if importe_debitado > total:

                if not fecha_vencimiento:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "El dÃ©bito supera el total del registro "
                                "y no existe una fecha de vencimiento "
                                "que permita clasificar la diferencia "
                                "como interÃ©s por mora."
                            ),
                        },
                        status=400,
                    )


                try:

                    fecha_vencimiento_validada = (
                        datetime.strptime(
                            fecha_vencimiento,
                            "%Y-%m-%d"
                        ).date()
                    )

                except ValueError:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "La fecha de vencimiento "
                                "no es vÃ¡lida."
                            ),
                        },
                        status=400,
                    )


                if (
                    fecha_debito_validada <=
                    fecha_vencimiento_validada
                ):

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "El dÃ©bito supera el total del registro, "
                                "pero no ocurriÃ³ despuÃ©s del vencimiento."
                            ),
                        },
                        status=400,
                    )


                if not confirmar_intereses_mora:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "La diferencia del dÃ©bito debe "
                                "confirmarse como interÃ©s por mora "
                                "antes de guardar."
                            ),
                        },
                        status=400,
                    )


                importe_aplicado_debito = (
                    total
                )

                intereses_mora = (
                    importe_debitado -
                    total
                )


            total_aplicado += (
                importe_aplicado_debito
            )


            debito_automatico_validado = {

                "fecha":
                    fecha_debito_validada,

                "importe_debitado":
                    importe_debitado,

                "importe_aplicado":
                    importe_aplicado_debito,

                "intereses_mora":
                    intereses_mora,

            }


        # =========================================
        # CONTROL DE SOBREAPLICACIÃ“N
        # =========================================
        #
        # En una Carga Simple nueva el saldo
        # disponible para aplicar coincide con el
        # total documental del Movimiento.
        #
        # La validaciÃ³n pertenece al servicio
        # financiero comÃºn para que la misma regla
        # pueda reutilizarse luego en ediciÃ³n,
        # Carga Planificada y otros circuitos.
        # =========================================

        try:

            validar_importe_aplicable(
                saldo_pendiente=total,
                importe_aplicar=total_aplicado,
            )

        except ValueError as error:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": str(error),
                },
                status=400,
            )


        # =========================================
        # ESTADO DEL MOVIMIENTO
        # =========================================

        if total_aplicado == Decimal(
            "0.00"
        ):

            estado_movimiento = (
                "Pendiente"
            )


        elif total_aplicado < total:

            estado_movimiento = (
                "Parcial"
            )


        else:

            estado_movimiento = (
                "Pagado"
            )


        # =========================================
        # ARCHIVO DEL MOVIMIENTO
        # =========================================

        archivo = request.FILES.get(
            "archivo"
        )


        # =========================================
        # TRANSACCIÃ“N ATÃ“MICA
        # =========================================

        with transaction.atomic():

            # =====================================
            # MOVIMIENTO
            # =====================================

            movimiento = Movimiento.objects.create(

                empresa=
                    empresa,

                ejercicio=
                    ejercicio,

                tipo_gasto=
                    tipo_gasto,

                proveedor=
                    proveedor,

                centro_operativo=
                    centro_operativo,

                recurso_operativo=
                    recurso_operativo,

                descripcion="",

                fecha_registro=
                    fecha_registro,

                fecha_vencimiento=(
                    fecha_vencimiento
                    or None
                ),

                modalidad_pago=
                    modalidad_pago,

                cuenta_debito=
                    cuenta_debito,

                tipo_comprobante=
                    tipo_comprobante,

                numero_comprobante=
                    numero_comprobante,

                moneda=
                    "ARS",

                neto_gravado=
                    neto_gravado,

                no_gravado_exento=
                    no_gravado_exento,

                iva_21=
                    iva_21,

                iva_27=
                    iva_27,

                iva_105=
                    iva_105,

                recargos_intereses=
                    recargos_intereses,

                ajuste_redondeo=
                    ajuste_redondeo,

                percepcion_iibb=
                    percepcion_iibb,

                percepcion_iva=
                    percepcion_iva,

                percepcion_ganancias=
                    percepcion_ganancias,

                percepcion_tasas_municipales=(
                    percepcion_tasas_municipales
                ),

                total=
                    total,

                # Compatibilidad temporal.
                importe=
                    total,

                estado=
                    estado_movimiento,

                archivo=
                    archivo,
            )


            # =====================================
            # PAGOS
            # =====================================

            pagos_creados = []

            operaciones_creadas = []

            tarjetas_creadas = []

            cheques_creados = []

            retenciones_creadas = []

            debitos_automaticos_creados = []


            for pago_datos in pagos_validados:

                resultado_pago = (
                    crear_pago_validado_movimiento(
                        empresa=empresa,
                        movimiento=movimiento,
                        pago_datos=pago_datos,
                    )
                )


                pagos_creados.append(
                    resultado_pago[
                        "pago_id"
                    ]
                )


                operaciones_creadas.extend(
                    resultado_pago[
                        "operaciones_bancarias_ids"
                    ]
                )


                tarjetas_creadas.extend(
                    resultado_pago[
                        "tarjetas_ids"
                    ]
                )


                cheques_creados.extend(
                    resultado_pago[
                        "cheques_ids"
                    ]
                )


                retenciones_creadas.extend(
                    resultado_pago[
                        "retenciones_ids"
                    ]
                )

            # =====================================
            # DÃ‰BITO AUTOMÃTICO REAL
            # =====================================

            debitos_automaticos_creados = []


            if debito_automatico_validado:

                pago_debito = Pago.objects.create(

                    empresa=
                        empresa,

                    fecha=
                        debito_automatico_validado[
                            "fecha"
                        ],

                    importe_efectivo=
                        Decimal("0.00"),

                )


                debito_creado = (
                    DebitoAutomaticoPago.objects.create(

                        pago=
                            pago_debito,

                        cuenta_bancaria=
                            cuenta_debito,

                        importe=
                            debito_automatico_validado[
                                "importe_debitado"
                            ],

                        intereses_mora=
                            debito_automatico_validado[
                                "intereses_mora"
                            ],

                        fecha_debito=
                            debito_automatico_validado[
                                "fecha"
                            ],

                    )
                )


                AplicacionPago.objects.create(

                    pago=
                        pago_debito,

                    movimiento=
                        movimiento,

                    importe=
                        debito_automatico_validado[
                            "importe_aplicado"
                        ],

                )


                pagos_creados.append(
                    pago_debito.id
                )


                debitos_automaticos_creados.append(
                    debito_creado.id
                )

        # =========================================
        # RESPUESTA
        # =========================================

        return JsonResponse(
            {
                "ok": True,

                "mensaje": (
                    "Registro guardado correctamente."
                ),

                "movimiento_id":
                    movimiento.id,

                "pagos_ids":
                    pagos_creados,

                "operaciones_bancarias_ids":
                    operaciones_creadas,

                "tarjetas_ids":
                    tarjetas_creadas,

                "cheques_ids":
                    cheques_creados,

                "retenciones_ids":
                    retenciones_creadas,

                "total_aplicado":
                    str(
                        total_aplicado
                    ),

                "estado":
                    estado_movimiento,
            }
        )


    except Exception as error:

        print(
            "Error guardando Movimiento:",
            error,
        )


        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "OcurriÃ³ un error al guardar el registro."
                ),
            },
            status=500,
        )

@login_required
def actualizar_movimiento(request):
    """
    Actualiza un Movimiento existente y puede registrar nuevos Pagos.

    Si el Movimiento todavÃ­a no tiene AplicacionPago histÃ³rica,
    sus datos pueden modificarse normalmente.

    Una vez aplicado al menos un Pago, los datos estructurales del
    Movimiento quedan bloqueados. SÃ³lo pueden modificarse la forma
    prevista de pago y su cuenta de dÃ©bito asociada, adjuntarse una
    factura y registrarse nuevos Pagos.

    Para modificar otros datos de un Movimiento con Pagos aplicados,
    primero deben eliminarse o revertirse esos Pagos.

    La actualizaciÃ³n y los nuevos Pagos se procesan dentro de una
    Ãºnica transacciÃ³n.
    """

    import json
    import logging

    from decimal import Decimal, InvalidOperation

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
                "mensaje": "MÃ©todo no permitido.",
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


    pagos = []


    if pagos_raw:

        try:

            pagos = json.loads(
                pagos_raw
            )

        except json.JSONDecodeError:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Los datos de los Pagos no son vÃ¡lidos."
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
                        "El formato de los Pagos no es vÃ¡lido."
                    ),
                },
                status=400,
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
                "mensaje": "No se indicÃ³ el Movimiento a modificar.",
            },
            status=400,
        )


    empresa = obtener_empresa_autorizada(
        request.user,
        empresa_id,
    )


    tipo_gasto_id = (
        request.POST.get("tipo_gasto")
        or ""
    ).strip()

    proveedor_id = (
        request.POST.get("proveedor")
        or ""
    ).strip()

    centro_operativo_id = (
        request.POST.get("centro_operativo")
        or ""
    ).strip()

    recurso_operativo_id = (
        request.POST.get("recurso_operativo")
        or ""
    ).strip()

    fecha_registro = (
        request.POST.get("fecha_registro")
        or ""
    ).strip()

    fecha_vencimiento = (
        request.POST.get("fecha_vencimiento")
        or ""
    ).strip()

    modalidad_pago = (
        request.POST.get("modalidad_pago")
        or "Manual"
    ).strip()

    cuenta_debito_id = (
        request.POST.get("cuenta_debito")
        or ""
    ).strip()

    tipo_comprobante = (
        request.POST.get("tipo_comprobante")
        or ""
    ).strip()

    numero_comprobante = (
        request.POST.get("numero_comprobante")
        or ""
    ).strip()


    if not tipo_gasto_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Seleccione un tipo de gasto.",
            },
            status=400,
        )


    if not proveedor_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Seleccione un proveedor.",
            },
            status=400,
        )


    if not fecha_registro:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Ingrese la fecha del registro.",
            },
            status=400,
        )


    tipo_gasto = (
        TipoGasto.objects.filter(
            id=tipo_gasto_id,
            empresa=empresa,
            activo=True,
        ).first()
    )


    if not tipo_gasto:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "El tipo de gasto no es vÃ¡lido.",
            },
            status=400,
        )


    proveedor = (
        Proveedor.objects.filter(
            id=proveedor_id,
            empresa=empresa,
            activo=True,
        ).first()
    )


    if not proveedor:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "El proveedor no es vÃ¡lido.",
            },
            status=400,
        )


    tipos_comprobante_validos = {
        "A",
        "B",
        "C",
        "X",
    }


    if tipo_comprobante not in tipos_comprobante_validos:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Seleccione un tipo de comprobante vÃ¡lido."
                ),
            },
            status=400,
        )


    centro_operativo = None


    if centro_operativo_id:

        centro_operativo = (
            CentroOperativo.objects.filter(
                id=centro_operativo_id,
                empresa=empresa,
                activo=True,
            ).first()
        )


        if not centro_operativo:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El Centro Operativo no es vÃ¡lido."
                    ),
                },
                status=400,
            )


    recurso_operativo = None


    if recurso_operativo_id:

        recurso_operativo = (
            RecursoOperativo.objects.filter(
                id=recurso_operativo_id,
                empresa=empresa,
                activo=True,
            ).first()
        )


        if not recurso_operativo:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El Recurso Operativo no es vÃ¡lido."
                    ),
                },
                status=400,
            )


        if (
            centro_operativo and
            hasattr(
                recurso_operativo,
                "centro_operativo"
            ) and
            recurso_operativo.centro_operativo_id !=
            centro_operativo.id
        ):

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El Recurso Operativo no pertenece "
                        "al Centro Operativo seleccionado."
                    ),
                },
                status=400,
            )


    modalidades_validas = {
        valor
        for valor, etiqueta
        in Movimiento.MODALIDADES_PAGO
    }


    if modalidad_pago not in modalidades_validas:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "La forma prevista de pago no es vÃ¡lida."
                ),
            },
            status=400,
        )


    cuenta_debito = None


    if modalidad_pago == "DebitoAutomatico":

        if not cuenta_debito_id:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Seleccione la cuenta prevista "
                        "para el dÃ©bito automÃ¡tico."
                    ),
                },
                status=400,
            )


        cuenta_debito = (
            CuentaBancaria.objects.filter(
                id=cuenta_debito_id,
                empresa=empresa,
                activo=True,
                moneda="ARS",
            ).first()
        )


        if not cuenta_debito:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "La cuenta seleccionada para "
                        "el dÃ©bito automÃ¡tico no es vÃ¡lida."
                    ),
                },
                status=400,
            )


    elif cuenta_debito_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Un Pago manual no debe tener "
                    "una cuenta prevista para dÃ©bito."
                ),
            },
            status=400,
        )


    def decimal_post(nombre):
        """
        Convierte un importe recibido mediante POST
        en Decimal para persistencia.
        """

        valor = (
            request.POST.get(nombre)
            or "0"
        )


        try:

            return Decimal(
                str(valor)
            )


        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):

            return Decimal("0")


    neto_gravado = decimal_post(
        "neto_gravado"
    )

    no_gravado_exento = decimal_post(
        "no_gravado_exento"
    )

    iva_21 = decimal_post(
        "iva_21"
    )

    iva_27 = decimal_post(
        "iva_27"
    )

    iva_105 = decimal_post(
        "iva_105"
    )

    recargos_intereses = decimal_post(
        "recargos_intereses"
    )

    ajuste_redondeo = decimal_post(
        "ajuste_redondeo"
    )

    percepcion_iibb = decimal_post(
        "percepcion_iibb"
    )

    percepcion_iva = decimal_post(
        "percepcion_iva"
    )

    percepcion_ganancias = decimal_post(
        "percepcion_ganancias"
    )

    percepcion_tasas_municipales = (
        decimal_post(
            "percepcion_tasas_municipales"
        )
    )

    total = decimal_post(
        "total"
    )


    if total <= Decimal("0.00"):

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "El total del registro debe ser mayor a cero."
                ),
            },
            status=400,
        )


    archivo = request.FILES.get(
        "archivo"
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
                            "no puede modificarse."
                        ),
                    },
                    status=400,
                )


            comprobante_original = (
                movimiento.numero_comprobante
                or ""
            ).strip()


            comprobante_original_normalizado = bool(
                re.fullmatch(
                    r"\d{4}-\d{8}",
                    comprobante_original,
                )
            )


            conserva_comprobante_legado = (
                not comprobante_original_normalizado
                and
                tipo_comprobante ==
                (movimiento.tipo_comprobante or "")
                and
                numero_comprobante ==
                comprobante_original
            )


            if (
                not conserva_comprobante_legado
                and
                not re.fullmatch(
                    r"\d{4}-\d{8}",
                    numero_comprobante,
                )
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El nÃºmero de comprobante no tiene "
                            "un formato vÃ¡lido."
                        ),
                    },
                    status=400,
                )


            comprobante_duplicado = (
                Movimiento.objects.filter(
                    empresa=empresa,
                    proveedor=proveedor,
                    tipo_comprobante=
                        tipo_comprobante,
                    numero_comprobante=
                        numero_comprobante,
                )
                .exclude(
                    id=movimiento.id,
                )
                .exists()
            )


            if comprobante_duplicado:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Ese comprobante ya fue registrado "
                            "para este proveedor."
                        ),
                    },
                    status=400,
                )


            total_aplicado_existente = (
                total_aplicado_movimiento(
                    movimiento
                )
            )

            # =========================================
            # PROTECCIÃ“N DEL MOVIMIENTO CON PAGOS
            # =========================================
            #
            # Una vez que existe al menos una
            # AplicacionPago histÃ³rica, el hecho
            # econÃ³mico/documental queda cerrado.
            #
            # SÃ³lo pueden modificarse:
            #
            # - la forma prevista de pago;
            # - la cuenta prevista de dÃ©bito asociada;
            # - el archivo de factura;
            # - y pueden incorporarse nuevos Pagos.
            #
            # Para modificar cualquier otro dato,
            # primero deben eliminarse/revertirse
            # todos los Pagos aplicados.
            #
            if (
                total_aplicado_existente >
                Decimal("0.00")
            ):

                fecha_registro_actual = (
                    str(
                        movimiento.fecha_registro
                    )
                    if movimiento.fecha_registro
                    else ""
                )

                fecha_vencimiento_actual = (
                    str(
                        movimiento.fecha_vencimiento
                    )
                    if movimiento.fecha_vencimiento
                    else ""
                )


                estructura_modificada = any(
                    [
                        str(
                            movimiento.tipo_gasto_id
                            or ""
                        ) != tipo_gasto_id,

                        str(
                            movimiento.proveedor_id
                            or ""
                        ) != proveedor_id,

                        str(
                            movimiento.centro_operativo_id
                            or ""
                        ) != centro_operativo_id,

                        str(
                            movimiento.recurso_operativo_id
                            or ""
                        ) != recurso_operativo_id,

                        fecha_registro_actual !=
                            fecha_registro,

                        fecha_vencimiento_actual !=
                            fecha_vencimiento,

                        (
                            movimiento.tipo_comprobante
                            or ""
                        ) != tipo_comprobante,

                        (
                            movimiento.numero_comprobante
                            or ""
                        ) != numero_comprobante,

                        movimiento.neto_gravado !=
                            neto_gravado,

                        movimiento.no_gravado_exento !=
                            no_gravado_exento,

                        movimiento.iva_21 !=
                            iva_21,

                        movimiento.iva_27 !=
                            iva_27,

                        movimiento.iva_105 !=
                            iva_105,

                        movimiento.recargos_intereses !=
                            recargos_intereses,

                        movimiento.ajuste_redondeo !=
                            ajuste_redondeo,

                        movimiento.percepcion_iibb !=
                            percepcion_iibb,

                        movimiento.percepcion_iva !=
                            percepcion_iva,

                        movimiento.percepcion_ganancias !=
                            percepcion_ganancias,

                        movimiento.percepcion_tasas_municipales !=
                            percepcion_tasas_municipales,

                        movimiento.total !=
                            total,
                    ]
                )


                if estructura_modificada:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "El Movimiento ya tiene Pagos "
                                "aplicados. Para modificar sus "
                                "datos primero debe eliminar "
                                "los Pagos realizados."
                            ),
                        },
                        status=400,
                    )

            try:

                validar_importe_aplicable(
                    saldo_pendiente=total,
                    importe_aplicar=
                        total_aplicado_existente,
                )


            except ValueError:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El total del registro no puede "
                            "ser menor al importe que ya fue "
                            "aplicado mediante Pagos."
                        ),
                    },
                    status=400,
                )


            saldo_disponible_pagos = (
                total -
                total_aplicado_existente
            )


            pagos_validados = []

            importe_total_nuevo = Decimal(
                "0.00"
            )


            if pagos:

                if modalidad_pago != "Manual":

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "Los Pagos manuales sÃ³lo pueden "
                                "registrarse cuando la forma prevista "
                                "de pago es Manual."
                            ),
                        },
                        status=400,
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
                            saldo_disponible_pagos,
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


            total_aplicado_nuevo = (
                total_aplicado_existente +
                importe_total_nuevo
            )


            saldo_nuevo = (
                total -
                total_aplicado_nuevo
            )

            if (
                total_aplicado_nuevo <=
                Decimal("0.00")
            ):

                estado_movimiento = (
                    "Pendiente"
                )


            elif saldo_nuevo > Decimal("0.00"):

                estado_movimiento = (
                    "Parcial"
                )


            else:

                estado_movimiento = (
                    "Pagado"
                )


            movimiento.tipo_gasto = (
                tipo_gasto
            )

            movimiento.proveedor = (
                proveedor
            )

            movimiento.centro_operativo = (
                centro_operativo
            )

            movimiento.recurso_operativo = (
                recurso_operativo
            )

            movimiento.fecha_registro = (
                fecha_registro
            )

            movimiento.fecha_vencimiento = (
                fecha_vencimiento
                or None
            )

            movimiento.modalidad_pago = (
                modalidad_pago
            )

            movimiento.cuenta_debito = (
                cuenta_debito
            )

            movimiento.tipo_comprobante = (
                tipo_comprobante
            )

            movimiento.numero_comprobante = (
                numero_comprobante
            )

            movimiento.neto_gravado = (
                neto_gravado
            )

            movimiento.no_gravado_exento = (
                no_gravado_exento
            )

            movimiento.iva_21 = (
                iva_21
            )

            movimiento.iva_27 = (
                iva_27
            )

            movimiento.iva_105 = (
                iva_105
            )

            movimiento.recargos_intereses = (
                recargos_intereses
            )

            movimiento.ajuste_redondeo = (
                ajuste_redondeo
            )

            movimiento.percepcion_iibb = (
                percepcion_iibb
            )

            movimiento.percepcion_iva = (
                percepcion_iva
            )

            movimiento.percepcion_ganancias = (
                percepcion_ganancias
            )

            movimiento.percepcion_tasas_municipales = (
                percepcion_tasas_municipales
            )

            movimiento.total = (
                total
            )

            # Compatibilidad temporal con el campo
            # histÃ³rico importe.
            movimiento.importe = (
                total
            )

            movimiento.estado = (
                estado_movimiento
            )


            if archivo:

                movimiento.archivo = (
                    archivo
                )


            campos_actualizados = [
                "tipo_gasto",
                "proveedor",
                "centro_operativo",
                "recurso_operativo",
                "fecha_registro",
                "fecha_vencimiento",
                "modalidad_pago",
                "cuenta_debito",
                "tipo_comprobante",
                "numero_comprobante",
                "neto_gravado",
                "no_gravado_exento",
                "iva_21",
                "iva_27",
                "iva_105",
                "recargos_intereses",
                "ajuste_redondeo",
                "percepcion_iibb",
                "percepcion_iva",
                "percepcion_ganancias",
                "percepcion_tasas_municipales",
                "total",
                "importe",
                "estado",
            ]


            if archivo:

                campos_actualizados.append(
                    "archivo"
                )


            movimiento.save(
                update_fields=
                    campos_actualizados
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

        return JsonResponse(
            {
                "ok": True,
                "mensaje": (
                    "Movimiento actualizado correctamente."
                ),
                "movimiento_id":
                    movimiento.id,
                "total":
                    str(total),
                "total_aplicado":
                    str(
                        total_aplicado_nuevo
                    ),
                "pagos_ids": [
                    resultado["pago_id"]
                    for resultado
                    in resultados_pagos
                ],
                "saldo_pendiente":
                    str(saldo_nuevo),
                "estado":
                    estado_movimiento,
            }
        )


    except Exception as error:

        print(
            "Error actualizando Movimiento:",
            error,
        )


        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "OcurriÃ³ un error al actualizar "
                    "el Movimiento."
                ),
            },
            status=500,
        )
