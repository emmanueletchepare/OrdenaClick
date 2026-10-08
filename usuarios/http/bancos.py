from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import Banco
from usuarios.services.capacidades import (
    CAPACIDAD_EMPRESA_ADMINISTRAR,
    exigir_capacidad_empresa,
)


@login_required
@require_POST
def guardar_banco(request):

    contexto = exigir_capacidad_empresa(
        request.user,
        request.POST.get("empresa"),
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa

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


@login_required
@require_GET
def listar_bancos(request):

    empresa_id = request.GET.get("empresa")

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa

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

@login_required
@require_POST
def modificar_banco(request):

    banco_id = request.POST.get("banco")
    empresa_id = request.POST.get("empresa")

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa

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


@login_required
@require_POST
def eliminar_banco(request):

    banco_id = request.POST.get("banco")
    empresa_id = request.POST.get("empresa")

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa

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
