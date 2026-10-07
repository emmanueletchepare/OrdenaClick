from django.db import transaction
from django.http import JsonResponse
from django.template.loader import render_to_string

from usuarios.models import Empresa, Proveedor, TipoGasto, TipoGastoProveedor


def obtener_proveedores_tipo_gasto(request, empresa_id):
    """
    Obtiene y valida los proveedores enviados para un tipo de gasto.

    Sólo admite proveedores activos pertenecientes a la empresa indicada.
    """

    proveedores_ids = request.POST.getlist(
        "proveedores"
    )

    proveedores_ids = [
        proveedor_id
        for proveedor_id in proveedores_ids
        if proveedor_id
    ]

    proveedores = Proveedor.objects.filter(
        id__in=proveedores_ids,
        empresa_id=empresa_id,
        activo=True
    )

    if proveedores.count() != len(set(proveedores_ids)):

        return None

    return proveedores


def listar_tipos_gasto(request):
    """
    Devuelve el ABM de tipos de gasto correspondiente a la empresa activa.
    """

    empresa_id = request.GET.get(
        "empresa"
    )

    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La empresa no existe."
        }, status=404)

    tipos_gasto = (
        TipoGasto.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .prefetch_related(
            "relaciones_proveedores__proveedor"
        )
        .order_by(
            "nombre"
        )
    )

    proveedores = Proveedor.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by(
        "razon_social"
    )

    html = render_to_string(
        "usuarios/maestros/tipos_gasto.html",
        {
            "empresa": empresa,
            "tipos_gasto": tipos_gasto,
            "proveedores": proveedores
        },
        request=request
    )

    return JsonResponse({
        "ok": True,
        "html": html,
        "tipos_gasto": [
            {
                "id": tipo_gasto.id,
                "nombre": tipo_gasto.nombre,
                "descripcion": tipo_gasto.descripcion,
                "proveedores": [
                    relacion.proveedor_id
                    for relacion
                    in tipo_gasto.relaciones_proveedores.all()
                ]
            }
            for tipo_gasto in tipos_gasto
        ]
    })


@transaction.atomic
def guardar_tipo_gasto(request):
    """
    Crea un tipo de gasto y registra sus proveedores relacionados.
    """

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    descripcion = (
        request.POST.get("descripcion") or ""
    ).strip()

    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La empresa no existe."
        }, status=404)

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese el nombre del tipo de gasto."
        })

    tipo_gasto_existente = (
        TipoGasto.objects
        .filter(
            empresa=empresa,
            nombre=nombre
        )
        .first()
    )

    if tipo_gasto_existente:

        if tipo_gasto_existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe un tipo de gasto activo "
                    "con ese nombre."
                )
            })

        return JsonResponse({
            "ok": False,
            "requiere_reactivacion": True,
            "mensaje": (
                "Ese tipo de gasto se encuentra inactivo. "
                "Puede reactivarlo."
            ),
            "tipo_gasto": {
                "id": tipo_gasto_existente.id,
                "nombre": tipo_gasto_existente.nombre,
                "descripcion": tipo_gasto_existente.descripcion,
                "proveedores": [
                    relacion.proveedor_id
                    for relacion
                    in tipo_gasto_existente
                    .relaciones_proveedores
                    .all()
                ]
            }
        })

    proveedores = obtener_proveedores_tipo_gasto(
        request,
        empresa.id
    )

    if proveedores is None:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Uno o más proveedores seleccionados "
                "no son válidos."
            )
        })

    tipo_gasto = TipoGasto.objects.create(
        empresa=empresa,
        nombre=nombre,
        descripcion=descripcion
    )

    TipoGastoProveedor.objects.bulk_create([
        TipoGastoProveedor(
            tipo_gasto=tipo_gasto,
            proveedor=proveedor
        )
        for proveedor in proveedores
    ])

    return JsonResponse({
        "ok": True,
        "tipo_gasto": {
            "id": tipo_gasto.id,
            "nombre": tipo_gasto.nombre
        }
    })


@transaction.atomic
def modificar_tipo_gasto(request):
    """
    Modifica un tipo de gasto y reemplaza sus proveedores relacionados.
    """

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    tipo_gasto_id = request.POST.get(
        "tipo_gasto"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    descripcion = (
        request.POST.get("descripcion") or ""
    ).strip()

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese el nombre del tipo de gasto."
        })

    try:

        tipo_gasto = TipoGasto.objects.get(
            id=tipo_gasto_id,
            empresa_id=empresa_id,
            activo=True
        )

    except TipoGasto.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "El tipo de gasto no existe."
        }, status=404)

    nombre_duplicado = (
        TipoGasto.objects
        .filter(
            empresa_id=empresa_id,
            nombre=nombre
        )
        .exclude(
            id=tipo_gasto.id
        )
        .exists()
    )

    if nombre_duplicado:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otro tipo de gasto, activo "
                "o inactivo, con ese nombre."
            )
        })

    proveedores = obtener_proveedores_tipo_gasto(
        request,
        empresa_id
    )

    if proveedores is None:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Uno o más proveedores seleccionados "
                "no son válidos."
            )
        })

    tipo_gasto.nombre = nombre
    tipo_gasto.descripcion = descripcion

    tipo_gasto.save(
        update_fields=[
            "nombre",
            "descripcion"
        ]
    )

    tipo_gasto.relaciones_proveedores.all().delete()

    TipoGastoProveedor.objects.bulk_create([
        TipoGastoProveedor(
            tipo_gasto=tipo_gasto,
            proveedor=proveedor
        )
        for proveedor in proveedores
    ])

    return JsonResponse({
        "ok": True
    })


def eliminar_tipo_gasto(request):
    """
    Da de baja lógica un tipo de gasto activo.
    """

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    tipo_gasto_id = request.POST.get(
        "tipo_gasto"
    )

    try:

        tipo_gasto = TipoGasto.objects.get(
            id=tipo_gasto_id,
            empresa_id=empresa_id,
            activo=True
        )

    except TipoGasto.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "El tipo de gasto no existe."
        }, status=404)

    tipo_gasto.activo = False

    tipo_gasto.save(
        update_fields=[
            "activo"
        ]
    )

    return JsonResponse({
        "ok": True
    })


def reactivar_tipo_gasto(request):
    """
    Reactiva un tipo de gasto previamente dado de baja.
    """

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    tipo_gasto_id = request.POST.get(
        "tipo_gasto"
    )

    try:

        tipo_gasto = TipoGasto.objects.get(
            id=tipo_gasto_id,
            empresa_id=empresa_id,
            activo=False
        )

    except TipoGasto.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "El tipo de gasto inactivo no existe "
                "o ya fue reactivado."
            )
        }, status=404)

    tipo_gasto.activo = True

    tipo_gasto.save(
        update_fields=[
            "activo"
        ]
    )

    return JsonResponse({
        "ok": True,
        "tipo_gasto": {
            "id": tipo_gasto.id,
            "nombre": tipo_gasto.nombre
        }
    })
