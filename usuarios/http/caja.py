import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone

from usuarios.models import Banco, Cliente
from usuarios.services.caja import resumen_disponibilidad_caja


@login_required
def panel_caja(request):
    """
    Devuelve la portada operativa de Caja para la Empresa autorizada.

    La disponibilidad se calcula individualmente por cada Caja activa
    correspondiente a Casa Central, Sucursal o Mostrador. No mezcla la
    custodia física de distintos Centros Operativos.
    """
    from usuarios.services.seguridad import (
        cajas_autorizadas,
    )

    empresa_id = (
        request.GET.get("empresa")
        or request.POST.get("empresa")
    )

    try:
        empresa, cajas = cajas_autorizadas(
            request.user,
            empresa_id,
        )
    except PermissionDenied as error:
        return JsonResponse(
            {
                "ok": False,
                "mensaje": str(error),
            },
            status=403,
        )

    resumenes = [
        resumen_disponibilidad_caja(
            empresa,
            caja,
        )
        for caja in cajas
    ]

    html = render_to_string(
        "usuarios/caja/dashboard.html",
        {
            "empresa": empresa,
            "resumenes": resumenes,
        },
        request=request,
    )

    return JsonResponse(
        {
            "ok": True,
            "html": html,
        }
    )

@login_required
def nueva_cobranza(request):
    """
    Muestra o registra una nueva Cobranza para una Caja autorizada.

    Empresa, Caja y componentes recibidos desde el navegador se consideran
    datos no confiables. La autorización de alcance se resuelve siempre en
    backend antes de validar y persistir la operación financiera.
    """
    from django.core.exceptions import PermissionDenied

    from usuarios.services.caja import crear_cobranza_validada
    from usuarios.services.seguridad import obtener_caja_autorizada

    if request.method == "POST":
        try:
            datos = json.loads(
                request.body.decode("utf-8") or "{}"
            )
        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": "La Cobranza enviada tiene un formato inválido.",
                },
                status=400,
            )

        empresa_id = datos.get("empresa_id")
        caja_id = datos.get("caja_id")

        try:
            empresa, caja = obtener_caja_autorizada(
                request.user,
                empresa_id,
                caja_id,
            )
        except PermissionDenied as error:
            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": str(error),
                },
                status=403,
            )

        cobranza_datos = datos.get("cobranza")

        if not isinstance(cobranza_datos, dict):
            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": "La Cobranza enviada tiene un formato inválido.",
                },
                status=400,
            )

        cobranza_datos = dict(cobranza_datos)
        cobranza_datos["caja_id"] = caja.id

        try:
            resultado = crear_cobranza_validada(
                empresa=empresa,
                usuario=request.user,
                cobranza_datos=cobranza_datos,
            )
        except ValueError as error:
            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": str(error),
                },
                status=400,
            )

        cobranza = resultado["cobranza"]

        return JsonResponse(
            {
                "ok": True,
                "mensaje": "Cobranza registrada correctamente.",
                "cobranza_id": cobranza.id,
            },
            status=201,
        )

    empresa_id = request.GET.get("empresa")
    caja_id = request.GET.get("caja")

    try:
        empresa, caja = obtener_caja_autorizada(
            request.user,
            empresa_id,
            caja_id,
        )
    except PermissionDenied as error:
        return JsonResponse(
            {
                "ok": False,
                "mensaje": str(error),
            },
            status=403,
        )

    bancos = (
        Banco.objects
        .filter(
            empresa=empresa,
            activo=True,
        )
        .order_by("nombre")
    )

    clientes = (
        Cliente.objects
        .filter(
            empresa=empresa,
            activo=True,
        )
        .select_related("centro_operativo")
        .order_by(
            "razon_social",
            "numero_cliente",
        )
    )

    html = render_to_string(
        "usuarios/caja/nueva_cobranza.html",
        {
            "empresa": empresa,
            "caja": caja,
            "bancos": bancos,
            "clientes": clientes,
            "fecha_hoy": timezone.localdate(),
        },
        request=request,
    )

    return JsonResponse(
        {
            "ok": True,
            "html": html,
        }
    )
