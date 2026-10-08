from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import Retencion
from usuarios.services.capacidades import (
    CAPACIDAD_EMPRESA_ADMINISTRAR,
    exigir_capacidad_empresa,
)


@login_required
@require_GET
def listar_retenciones(request):
    """
    Devuelve el ABM y el listado de retenciones activas
    pertenecientes a una empresa.
    """

    empresa_id = request.GET.get(
        "empresa"
    )


    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa


    retenciones = (
        Retencion.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .order_by(
            "tipo"
        )
    )


    html = render_to_string(
        "usuarios/maestros/retenciones.html",
        {
            "empresa":
                empresa,

            "retenciones":
                retenciones,
        },
        request=request
    )


    return JsonResponse({

        "ok": True,

        "html":
            html,

        "retenciones": [

            {
                "id":
                    retencion.id,

                "tipo":
                    retencion.tipo,

                "descripcion":
                    retencion.descripcion,
            }

            for retencion in retenciones
        ]

    })


@login_required
@require_POST
def guardar_retencion(request):
    """
    Crea una retención nueva para una empresa.

    Si existe una retención inactiva con el mismo tipo,
    no crea un duplicado y solicita su reactivación.
    """

    empresa_id = request.POST.get(
        "empresa"
    )

    tipo = (
        request.POST.get("tipo") or ""
    ).strip().upper()

    descripcion = (
        request.POST.get("descripcion") or ""
    ).strip()


    if not tipo:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un tipo de retención."
        })


    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa


    existente = (
        Retencion.objects
        .filter(
            empresa=empresa,
            tipo__iexact=tipo
        )
        .first()
    )


    if existente:

        if existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe una retención activa "
                    "con ese tipo."
                )
            })


        return JsonResponse({

            "ok": False,

            "requiere_reactivacion": True,

            "mensaje": (
                "La retención ya existe pero está inactiva. "
                "Puede reactivarla."
            ),

            "retencion": {

                "id":
                    existente.id,

                "tipo":
                    existente.tipo,

                "descripcion":
                    existente.descripcion,

            }

        })


    retencion = Retencion.objects.create(

        empresa=
            empresa,

        tipo=
            tipo,

        descripcion=
            descripcion

    )


    return JsonResponse({

        "ok": True,

        "retencion": {

            "id":
                retencion.id,

            "tipo":
                retencion.tipo,

            "descripcion":
                retencion.descripcion,

        }

    })


@login_required
@require_POST
def modificar_retencion(request):
    """
    Modifica una retención activa perteneciente
    a una empresa.
    """

    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa

    retencion_id = request.POST.get(
        "retencion"
    )

    tipo = (
        request.POST.get("tipo") or ""
    ).strip().upper()

    descripcion = (
        request.POST.get("descripcion") or ""
    ).strip()


    if not tipo:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un tipo de retención."
        })


    try:

        retencion = Retencion.objects.get(
            id=retencion_id,
            empresa=empresa,
            activo=True
        )

    except Retencion.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La retención no existe."
            },
            status=404
        )


    duplicada = (
        Retencion.objects
        .filter(
            empresa=empresa,
            tipo__iexact=tipo
        )
        .exclude(
            id=retencion.id
        )
        .exists()
    )


    if duplicada:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra retención "
                "con ese tipo."
            )
        })


    retencion.tipo = tipo

    retencion.descripcion = descripcion


    retencion.save(
        update_fields=[
            "tipo",
            "descripcion",
        ]
    )


    return JsonResponse({

        "ok": True,

        "retencion": {

            "id":
                retencion.id,

            "tipo":
                retencion.tipo,

            "descripcion":
                retencion.descripcion,

        }

    })


@login_required
@require_POST
def eliminar_retencion(request):
    """
    Desactiva lógicamente una retención.

    La retención no se elimina físicamente para preservar
    referencias históricas de pagos.
    """

    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa

    retencion_id = request.POST.get(
        "retencion"
    )


    try:

        retencion = Retencion.objects.get(
            id=retencion_id,
            empresa=empresa,
            activo=True
        )

    except Retencion.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La retención no existe."
            },
            status=404
        )


    retencion.activo = False


    retencion.save(
        update_fields=[
            "activo"
        ]
    )


    return JsonResponse({
        "ok": True
    })


@login_required
@require_POST
def reactivar_retencion(request):
    """
    Reactiva una retención previamente desactivada
    y permite actualizar sus datos.
    """

    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa

    retencion_id = request.POST.get(
        "retencion"
    )

    tipo = (
        request.POST.get("tipo") or ""
    ).strip().upper()

    descripcion = (
        request.POST.get("descripcion") or ""
    ).strip()


    if not tipo:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un tipo de retención."
        })


    try:

        retencion = Retencion.objects.get(
            id=retencion_id,
            empresa=empresa,
            activo=False
        )

    except Retencion.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "La retención inactiva "
                    "no existe."
                )
            },
            status=404
        )


    duplicada = (
        Retencion.objects
        .filter(
            empresa=empresa,
            tipo__iexact=tipo,
            activo=True
        )
        .exclude(
            id=retencion.id
        )
        .exists()
    )


    if duplicada:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra retención activa "
                "con ese tipo."
            )
        })


    retencion.tipo = tipo

    retencion.descripcion = descripcion

    retencion.activo = True


    retencion.save(
        update_fields=[
            "tipo",
            "descripcion",
            "activo",
        ]
    )


    return JsonResponse({

        "ok": True,

        "retencion": {

            "id":
                retencion.id,

            "tipo":
                retencion.tipo,

            "descripcion":
                retencion.descripcion,

        }

    })
