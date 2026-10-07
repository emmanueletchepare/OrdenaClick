from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from usuarios.services.financiero import (
    estado_vencimiento_movimiento,
    movimientos_con_saldo_pendiente,
    movimientos_en_alerta,
)
from usuarios.services.seguridad import obtener_empresa_autorizada


@login_required
def estado_llamador_alertas(request):
    """
    Indica si corresponde mostrar el llamador de Alertas
    para la empresa activa.

    La vista no expone movimientos, importes ni cantidades.
    La política de Alertas se obtiene exclusivamente desde
    el servicio financiero central.
    """
    empresa_id = (
        request.GET.get("empresa")
        or ""
    ).strip()

    if not empresa_id:
        return JsonResponse(
            {
                "ok": False,
                "mostrar_llamador": False,
                "mensaje": "No hay una empresa seleccionada.",
            },
            status=400,
        )

    empresa = obtener_empresa_autorizada(
        request.user,
        empresa_id,
    )

    mostrar_llamador = (
        movimientos_en_alerta(
            empresa=empresa,
            fecha_referencia=date.today(),
        )
        .exists()
    )

    return JsonResponse(
        {
            "ok": True,
            "mostrar_llamador": mostrar_llamador,
        }
    )

@login_required
def listar_proximos_vencimientos(request):
    """
    Devuelve los Movimientos con saldo pendiente de una empresa
    para alimentar la interfaz de Próximos Vencimientos.

    Los períodos "hoy" y "semana" incluyen también obligaciones
    vencidas que continúan con saldo pendiente.

    El período "alertas" utiliza la política central de Alertas
    definida en el servicio financiero.

    La vista no calcula saldos ni estados financieros.
    Toda regla financiera se obtiene desde el servicio central.
    """

    empresa_id = (
        request.GET.get("empresa")
        or ""
    ).strip()

    periodo = (
        request.GET.get("periodo")
        or "hoy"
    ).strip()

    if not empresa_id:
        return JsonResponse(
            {
                "ok": False,
                "mensaje": "No hay una empresa seleccionada.",
            },
            status=400,
        )

    empresa = obtener_empresa_autorizada(
        request.user,
        empresa_id,
    )

    hoy = date.today()

    fecha_desde = None
    fecha_hasta = None

    if periodo == "alertas":
        movimientos = (
            movimientos_en_alerta(
                empresa=empresa,
                fecha_referencia=hoy,
            )
            .select_related(
                "proveedor",
                "tipo_gasto",
                "centro_operativo",
                "recurso_operativo",
                "cuenta_debito",
            )
        )

    elif periodo == "hoy":
        fecha_hasta = hoy

        movimientos = (
            movimientos_con_saldo_pendiente(
                empresa=empresa,
                fecha_hasta=fecha_hasta,
            )
            .select_related(
                "proveedor",
                "tipo_gasto",
                "centro_operativo",
                "recurso_operativo",
                "cuenta_debito",
            )
        )

    elif periodo == "semana":
        fecha_hasta = hoy + timedelta(
            days=6,
        )

        movimientos = (
            movimientos_con_saldo_pendiente(
                empresa=empresa,
                fecha_hasta=fecha_hasta,
            )
            .select_related(
                "proveedor",
                "tipo_gasto",
                "centro_operativo",
                "recurso_operativo",
                "cuenta_debito",
            )
        )

    elif periodo == "rango":
        fecha_desde_texto = (
            request.GET.get("fecha_desde")
            or ""
        ).strip()

        fecha_hasta_texto = (
            request.GET.get("fecha_hasta")
            or ""
        ).strip()

        if (
            not fecha_desde_texto
            or not fecha_hasta_texto
        ):
            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Ingrese las fechas desde y hasta."
                    ),
                },
                status=400,
            )

        try:
            fecha_desde = date.fromisoformat(
                fecha_desde_texto
            )

            fecha_hasta = date.fromisoformat(
                fecha_hasta_texto
            )

        except ValueError:
            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El rango de fechas no es válido."
                    ),
                },
                status=400,
            )

        if fecha_hasta < fecha_desde:
            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "La fecha hasta no puede ser "
                        "anterior a la fecha desde."
                    ),
                },
                status=400,
            )

        movimientos = (
            movimientos_con_saldo_pendiente(
                empresa=empresa,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
            )
            .select_related(
                "proveedor",
                "tipo_gasto",
                "centro_operativo",
                "recurso_operativo",
                "cuenta_debito",
            )
        )

    else:
        return JsonResponse(
            {
                "ok": False,
                "mensaje": "El período solicitado no es válido.",
            },
            status=400,
        )

    datos = []

    for movimiento in movimientos:
        proveedor = ""

        if movimiento.proveedor:
            proveedor = (
                movimiento.proveedor.razon_social
            )

        datos.append(
            {
                "id": movimiento.id,
                "fecha_vencimiento": (
                    movimiento.fecha_vencimiento.isoformat()
                    if movimiento.fecha_vencimiento
                    else None
                ),
                "estado_vencimiento": (
                    estado_vencimiento_movimiento(
                        movimiento
                    )
                ),
                "proveedor": proveedor,
                "tipo_comprobante": (
                    movimiento.tipo_comprobante
                    or ""
                ),
                "numero_comprobante": (
                    movimiento.numero_comprobante
                    or ""
                ),
                "total": str(
                    movimiento.total
                ),
                "total_aplicado": str(
                    movimiento.total_aplicado_calculado
                ),
                "saldo_pendiente": str(
                    movimiento.saldo_pendiente_calculado
                ),
                "modalidad_pago": (
                    movimiento.modalidad_pago
                ),
                "cuenta_debito": (
                    str(movimiento.cuenta_debito)
                    if movimiento.cuenta_debito
                    else ""
                ),
            }
        )

    return JsonResponse(
        {
            "ok": True,
            "periodo": periodo,
            "fecha_desde": (
                fecha_desde.isoformat()
                if fecha_desde
                else None
            ),
            "fecha_hasta": (
                fecha_hasta.isoformat()
                if fecha_hasta
                else None
            ),
            "movimientos": datos,
        }
    )
