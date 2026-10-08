from django.http import JsonResponse
from django.template.loader import render_to_string

from usuarios.models import Retencion
from usuarios.services.seguridad import obtener_empresa_administrable


def listar_retenciones(request):
    """
    Devuelve el ABM y el listado de retenciones activas
    pertenecientes a una empresa.
    """

    empresa_id = request.GET.get(
        "empresa"
    )


    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )


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


def guardar_retencion(request):
    """
    Crea una retención nueva para una empresa.

    Si existe una retención inactiva con el mismo tipo,
    no crea un duplicado y solicita su reactivación.
    """

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )


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


    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )


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


def modificar_retencion(request):
    """
    Modifica una retención activa perteneciente
    a una empresa.
    """

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )


    empresa_id = request.POST.get(
        "empresa"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

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


def eliminar_retencion(request):
    """
    Desactiva lógicamente una retención.

    La retención no se elimina físicamente para preservar
    referencias históricas de pagos.
    """

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )


    empresa_id = request.POST.get(
        "empresa"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

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


def reactivar_retencion(request):
    """
    Reactiva una retención previamente desactivada
    y permite actualizar sus datos.
    """

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )


    empresa_id = request.POST.get(
        "empresa"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

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
