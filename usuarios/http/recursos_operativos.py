from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import (
    CentroOperativo,
    RecursoOperativo,
    RecursoOperativoCentro,
)

from usuarios.services.capacidades import (
    CAPACIDAD_EMPRESA_ADMINISTRAR,
    exigir_capacidad_empresa,
)


def obtener_centros_recurso_request(
    request,
    empresa
):

    centros_ids = request.POST.getlist(
        "centros_operativos"
    )


    # Evitamos IDs repetidos conservando el orden.
    centros_ids = list(
        dict.fromkeys(
            centro_id
            for centro_id in centros_ids
            if centro_id
        )
    )


    if not centros_ids:

        return (
            None,
            "Seleccione al menos un Centro Operativo."
        )


    centros = list(
        CentroOperativo.objects
        .filter(
            id__in=centros_ids,
            empresa=empresa,
            activo=True
        )
    )


    if len(centros) != len(centros_ids):

        return (
            None,
            (
                "Uno o más Centros Operativos "
                "no existen o están inactivos."
            )
        )


    centros_por_id = {
        str(centro.id): centro
        for centro in centros
    }


    centros_ordenados = [

        centros_por_id[
            str(centro_id)
        ]

        for centro_id in centros_ids

    ]


    return (
        centros_ordenados,
        None
    )

@login_required
@require_GET
def listar_recursos_operativos(request):

    empresa_id = request.GET.get(
        "empresa"
    )


    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa


    recursos = (
        RecursoOperativo.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .prefetch_related(
            "relaciones_centros__centro_operativo"
        )
        .order_by(
            "tipo_recurso",
            "nombre"
        )
    )


    centros = (
        CentroOperativo.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .order_by(
            "nombre"
        )
    )


    html = render_to_string(
        "usuarios/maestros/recursos_operativos.html",
        {
            "empresa": empresa,
            "recursos": recursos,
            "centros": centros
        },
        request=request
    )


    recursos_json = []


    for recurso in recursos:

        relaciones = list(
            recurso.relaciones_centros.all()
        )


        centros_recurso = [

            relacion.centro_operativo

            for relacion in relaciones

        ]


        recursos_json.append({

            "id":
                recurso.id,

            "nombre":
                recurso.nombre,

            "tipo_recurso":
                recurso.tipo_recurso,

            "tipo_recurso_label":
                recurso.get_tipo_recurso_display(),



            # =====================================
            # NUEVO SISTEMA MULTICENTRO
            # =====================================

            "centros_operativos_ids": [

                str(centro.id)

                for centro in centros_recurso

            ],

            "centros_operativos": [

                {
                    "id":
                        centro.id,

                    "nombre":
                        centro.nombre
                }

                for centro in centros_recurso

            ],

            "descripcion":
                recurso.descripcion

        })


    return JsonResponse({
        "ok": True,
        "html": html,
        "recursos": recursos_json
    })


@login_required
@require_POST
def guardar_recurso_operativo(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)


    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa


    nombre = (
        request.POST.get(
            "nombre"
        ) or ""
    ).strip().upper()


    tipo_recurso = (
        request.POST.get(
            "tipo_recurso"
        ) or ""
    ).strip()


    descripcion = (
        request.POST.get(
            "descripcion"
        ) or ""
    ).strip()


    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "Ingrese el nombre del recurso operativo."
        })


    tipos_validos = {
        "Persona",
        "Vehiculo",
        "Inmueble",
        "Equipo",
        "Otro"
    }


    if tipo_recurso not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "Seleccione un tipo de recurso válido."
        })


    centros, error_centros = (
        obtener_centros_recurso_request(
            request,
            empresa
        )
    )


    if error_centros:

        return JsonResponse({
            "ok": False,
            "mensaje": error_centros
        })


    existente = (
        RecursoOperativo.objects
        .filter(
            empresa=empresa,
            nombre__iexact=nombre
        )
        .first()
    )


    if existente:

        if existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe un recurso operativo "
                    "activo con ese nombre."
                )
            })


        return JsonResponse({
            "ok": False,
            "requiere_reactivacion": True,
            "mensaje": (
                "Ya existe un recurso operativo "
                "inactivo con ese nombre."
            ),
            "recurso": {
                "id":
                    existente.id,

                "nombre":
                    existente.nombre
            }
        })


    with transaction.atomic():

        recurso = RecursoOperativo.objects.create(

            empresa=
                empresa,

            nombre=
                nombre,

            tipo_recurso=
                tipo_recurso,

            descripcion=
                descripcion

        )


        RecursoOperativoCentro.objects.bulk_create([

            RecursoOperativoCentro(
                recurso_operativo=recurso,
                centro_operativo=centro
            )

            for centro in centros

        ])


    return JsonResponse({
        "ok": True,
        "recurso": {
            "id":
                recurso.id,

            "nombre":
                recurso.nombre,

            "centros_operativos_ids": [
                str(centro.id)
                for centro in centros
            ]
        }
    })


@login_required
@require_POST
def modificar_recurso_operativo(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)


    recurso_id = request.POST.get(
        "recurso"
    )


    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa


    nombre = (
        request.POST.get(
            "nombre"
        ) or ""
    ).strip().upper()


    tipo_recurso = (
        request.POST.get(
            "tipo_recurso"
        ) or ""
    ).strip()


    descripcion = (
        request.POST.get(
            "descripcion"
        ) or ""
    ).strip()


    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "Ingrese el nombre del recurso operativo."
        })


    tipos_validos = {
        "Persona",
        "Vehiculo",
        "Inmueble",
        "Equipo",
        "Otro"
    }


    if tipo_recurso not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "Seleccione un tipo de recurso válido."
        })


    try:

        recurso = RecursoOperativo.objects.get(
            id=recurso_id,
            empresa=empresa,
            activo=True
        )


    except RecursoOperativo.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "El recurso operativo no existe."
        }, status=404)


    centros, error_centros = (
        obtener_centros_recurso_request(
            request,
            empresa
        )
    )


    if error_centros:

        return JsonResponse({
            "ok": False,
            "mensaje": error_centros
        })


    duplicado = (
        RecursoOperativo.objects
        .filter(
            empresa=empresa,
            nombre__iexact=nombre,
            activo=True
        )
        .exclude(
            id=recurso.id
        )
        .exists()
    )


    if duplicado:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otro recurso operativo "
                "activo con ese nombre."
            )
        })


    with transaction.atomic():

        recurso.nombre = nombre

        recurso.tipo_recurso = tipo_recurso

        recurso.descripcion = descripcion

        recurso.save(
            update_fields=[
                "nombre",
                "tipo_recurso",
                "descripcion"
            ]
        )


        recurso.relaciones_centros.all().delete()


        RecursoOperativoCentro.objects.bulk_create([

            RecursoOperativoCentro(
                recurso_operativo=recurso,
                centro_operativo=centro
            )

            for centro in centros

        ])


    return JsonResponse({
        "ok": True,
        "centros_operativos_ids": [
            str(centro.id)
            for centro in centros
        ]
    })


@login_required
@require_POST
def eliminar_recurso_operativo(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    recurso_id = request.POST.get(
        "recurso"
    )

    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa

    try:

        recurso = RecursoOperativo.objects.get(
            id=recurso_id,
            empresa=empresa,
            activo=True
        )

    except RecursoOperativo.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "El recurso operativo no existe."
        }, status=404)


    cantidad_activos = (
        RecursoOperativo.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .count()
    )


    if cantidad_activos <= 1:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "La empresa debe conservar al menos "
                "un recurso operativo activo."
            )
        })


    recurso.activo = False

    recurso.save(
        update_fields=[
            "activo"
        ]
    )


    return JsonResponse({
        "ok": True
    })


@login_required
@require_POST
def reactivar_recurso_operativo(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)


    recurso_id = request.POST.get(
        "recurso"
    )


    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa


    try:

        recurso = (
            RecursoOperativo.objects
            .prefetch_related(
                "relaciones_centros__centro_operativo"
            )
            .get(
                id=recurso_id,
                empresa=empresa,
                activo=False
            )
        )


    except RecursoOperativo.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "El recurso operativo inactivo "
                "no existe o ya fue activado."
            )
        }, status=404)


    relaciones_activas = [

        relacion

        for relacion
        in recurso.relaciones_centros.all()

        if relacion.centro_operativo.activo

    ]


    if not relaciones_activas:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No se puede reactivar el recurso porque "
                "no tiene ningún Centro Operativo activo relacionado."
            )
        })


    duplicado = (
        RecursoOperativo.objects
        .filter(
            empresa=empresa,
            nombre__iexact=recurso.nombre,
            activo=True
        )
        .exclude(
            id=recurso.id
        )
        .exists()
    )


    if duplicado:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe un recurso operativo "
                "activo con ese nombre."
            )
        })


        recurso.activo = True


        recurso.save(
            update_fields=[
                "activo"
            ]
        )


    return JsonResponse({
        "ok": True,
        "recurso": {

            "id":
                recurso.id,

            "nombre":
                recurso.nombre,

            "centros_operativos_ids": [

                str(
                    relacion.centro_operativo_id
                )

                for relacion
                in recurso.relaciones_centros.all()

            ]

        }
    })
