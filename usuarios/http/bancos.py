from django.http import JsonResponse
from django.template.loader import render_to_string

from usuarios.models import Banco
from usuarios.services.seguridad import obtener_empresa_administrable


def guardar_banco(request):

    if request.method != "POST":
        return JsonResponse(
            {"ok": False}
        )

    empresa = obtener_empresa_administrable(
        request.user,
        request.POST.get("empresa"),
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre."
        })

    if Banco.objects.filter(
        empresa=empresa,
        nombre=nombre,
        activo=True
    ).exists():

        return JsonResponse({
            "ok": False,
            "mensaje": "Ese banco ya existe."
        })

    banco = Banco.objects.create(

        empresa=empresa,

        nombre=nombre
    )

    return JsonResponse({

        "ok": True,

        "banco": {
            "id": banco.id,
            "nombre": banco.nombre
        }

    })


def listar_bancos(request):

    empresa_id = request.GET.get("empresa")

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    bancos = Banco.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by("nombre")

    html = render_to_string(

        "usuarios/maestros/bancos.html",

        {

            "empresa": empresa,
            "bancos": bancos

        },

        request=request

    )

    return JsonResponse({

    "html": html,

    "bancos": [

        {
            "id": banco.id,
            "nombre": banco.nombre
        }

        for banco in bancos

    ]

    })

def modificar_banco(request):

    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    banco_id = request.POST.get("banco")
    empresa_id = request.POST.get("empresa")

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    if not nombre:
        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese el nombre del banco."
        })

    try:
        banco = Banco.objects.get(
            id=banco_id,
            empresa=empresa,
            activo=True
        )

    except Banco.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "mensaje": "El banco no existe."
        }, status=404)

    if Banco.objects.filter(
        empresa=empresa,
        nombre=nombre,
        activo=True
    ).exclude(id=banco.id).exists():

        return JsonResponse({
            "ok": False,
            "mensaje": "Ya existe otro banco con ese nombre."
        })

    banco.nombre = nombre
    banco.save(update_fields=["nombre"])

    return JsonResponse({
        "ok": True
    })


def eliminar_banco(request):

    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    banco_id = request.POST.get("banco")
    empresa_id = request.POST.get("empresa")

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    try:
        banco = Banco.objects.get(
            id=banco_id,
            empresa=empresa,
            activo=True
        )

    except Banco.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "mensaje": "El banco no existe."
        }, status=404)

    banco.activo = False
    banco.save(update_fields=["activo"])

    return JsonResponse({
        "ok": True
    })
