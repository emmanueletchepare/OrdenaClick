import re

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from usuarios.models import Empresa, Movimiento, Proveedor


@login_required
def verificar_comprobante_duplicado(request):
    """
    Verifica si ya existe un Movimiento con el mismo
    comprobante para una empresa y proveedor.

    La identidad documental se determina por:

    - Empresa.
    - Proveedor.
    - Tipo de comprobante.
    - Número de comprobante normalizado.

    El tipo de gasto no forma parte de la identidad
    del comprobante.

    Cuando la consulta proviene de la edición de un
    Movimiento existente, ese mismo Movimiento se
    excluye de la búsqueda de duplicados.
    """

    if request.method != "GET":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido.",
            },
            status=405,
        )


    empresa_id = (
        request.GET.get(
            "empresa"
        )
        or ""
    ).strip()

    proveedor_id = (
        request.GET.get(
            "proveedor"
        )
        or ""
    ).strip()

    tipo_comprobante = (
        request.GET.get(
            "tipo_comprobante"
        )
        or ""
    ).strip()

    numero_comprobante = (
        request.GET.get(
            "numero_comprobante"
        )
        or ""
    ).strip()

    movimiento_id = (
        request.GET.get(
            "movimiento"
        )
        or ""
    ).strip()


    if(
        not empresa_id or
        not proveedor_id or
        not tipo_comprobante or
        not numero_comprobante
    ):

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Faltan datos para verificar "
                    "el comprobante."
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
                    "El número de comprobante "
                    "no tiene un formato válido."
                ),
            },
            status=400,
        )


    empresa = Empresa.objects.filter(
        id=empresa_id
    ).first()


    if not empresa:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "La empresa seleccionada "
                    "no existe."
                ),
            },
            status=404,
        )


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
                    "El proveedor seleccionado "
                    "no es válido."
                ),
            },
            status=400,
        )


    movimientos_coincidentes = (
        Movimiento.objects.filter(
            empresa=empresa,
            proveedor=proveedor,
            tipo_comprobante=tipo_comprobante,
            numero_comprobante=numero_comprobante,
        )
    )


    if movimiento_id:

        movimientos_coincidentes = (
            movimientos_coincidentes.exclude(
                id=movimiento_id
            )
        )


    duplicado = (
        movimientos_coincidentes.exists()
    )


    return JsonResponse(
        {
            "ok": True,
            "duplicado": duplicado,
        }
    )

@login_required
def obtener_movimiento_edicion(request):
    """
    Devuelve los datos necesarios para editar un Movimiento
    existente desde Carga Simple.

    La Empresa se valida mediante el servicio central de
    autorización.

    Los importes aplicado y pendiente se obtienen desde el
    servicio financiero central para no duplicar reglas de
    cálculo dentro de la vista.

    Si el Movimiento posee un comprobante histórico con formato
    legado, se informa explícitamente para permitir conservarlo
    sin habilitar ese formato para nuevos comprobantes.
    """

    from usuarios.services.financiero import (
        movimientos_con_saldo_pendiente,
    )

    from usuarios.services.seguridad import (
        obtener_empresa_autorizada,
    )


    empresa_id = (
        request.GET.get("empresa")
        or ""
    ).strip()


    movimiento_id = (
        request.GET.get("movimiento")
        or ""
    ).strip()


    if not empresa_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "No hay una empresa seleccionada.",
            },
            status=400,
        )


    if not movimiento_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "No se indicó el Movimiento.",
            },
            status=400,
        )


    empresa = obtener_empresa_autorizada(
        request.user,
        empresa_id,
    )


    movimiento = (
        movimientos_con_saldo_pendiente(
            empresa=empresa,
        )
        .filter(
            id=movimiento_id,
        )
        .select_related(
            "tipo_gasto",
            "proveedor",
            "centro_operativo",
            "recurso_operativo",
            "cuenta_debito",
        )
        .first()
    )


    if not movimiento:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "El Movimiento no existe "
                    "o ya no posee saldo pendiente."
                ),
            },
            status=404,
        )


    comprobante_original = (
        movimiento.numero_comprobante
        or ""
    ).strip()


    comprobante_normalizado = bool(
        re.fullmatch(
            r"\d{4}-\d{8}",
            comprobante_original,
        )
    )


    punto_venta = ""
    numero = ""


    if comprobante_normalizado:

        punto_venta, numero = (
            comprobante_original.split(
                "-",
                1,
            )
        )

    else:

        numero = comprobante_original


    return JsonResponse(
        {
            "ok": True,

            "movimiento": {

                "id":
                    movimiento.id,

                # Mientras Carga Planificada todavía no
                # exista, los Movimientos persistidos por
                # este flujo provienen de Carga Simple.
                "origen":
                    "carga_simple",

                "tipo_gasto_id":
                    movimiento.tipo_gasto_id,

                "proveedor_id":
                    movimiento.proveedor_id,

                "centro_operativo_id":
                    movimiento.centro_operativo_id,

                "recurso_operativo_id":
                    movimiento.recurso_operativo_id,

                "fecha_registro": (
                    movimiento.fecha_registro.isoformat()
                    if movimiento.fecha_registro
                    else ""
                ),

                "fecha_vencimiento": (
                    movimiento.fecha_vencimiento.isoformat()
                    if movimiento.fecha_vencimiento
                    else ""
                ),

                "modalidad_pago":
                    movimiento.modalidad_pago,

                "cuenta_debito_id":
                    movimiento.cuenta_debito_id,

                "tipo_comprobante":
                    movimiento.tipo_comprobante or "",

                "punto_venta":
                    punto_venta,

                "numero_comprobante":
                    numero,

                # Identificación documental persistida.
                # Se utiliza exclusivamente para distinguir
                # un comprobante legado conservado de uno
                # nuevo o modificado por el usuario.
                "comprobante_original":
                    comprobante_original,

                "comprobante_legado":
                    not comprobante_normalizado,

                "neto_gravado":
                    str(movimiento.neto_gravado),

                "no_gravado_exento":
                    str(movimiento.no_gravado_exento),

                "iva_21":
                    str(movimiento.iva_21),

                "iva_27":
                    str(movimiento.iva_27),

                "iva_105":
                    str(movimiento.iva_105),

                "recargos_intereses":
                    str(movimiento.recargos_intereses),

                "ajuste_redondeo":
                    str(movimiento.ajuste_redondeo),

                "percepcion_iibb":
                    str(movimiento.percepcion_iibb),

                "percepcion_iva":
                    str(movimiento.percepcion_iva),

                "percepcion_ganancias":
                    str(movimiento.percepcion_ganancias),

                "percepcion_tasas_municipales":
                    str(
                        movimiento.percepcion_tasas_municipales
                    ),

                "total":
                    str(movimiento.total),

                "total_aplicado":
                    str(
                        movimiento.total_aplicado_calculado
                    ),

                "saldo_pendiente":
                    str(
                        movimiento.saldo_pendiente_calculado
                    ),

                "estado":
                    movimiento.estado,

                "tiene_archivo":
                    bool(movimiento.archivo),
            },
        }
    )
