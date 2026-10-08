from django.http import JsonResponse
from django.template.loader import render_to_string

from usuarios.models import CentroOperativo
from usuarios.services.seguridad import obtener_empresa_administrable
from django.contrib.auth.decorators import login_required


@login_required
def listar_centros_operativos(request):

    empresa_id = request.GET.get("empresa")

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    centros = CentroOperativo.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by("nombre")

    html = render_to_string(
        "usuarios/maestros/centros_operativos.html",
        {
            "empresa": empresa,
            "centros": centros
        },
        request=request
    )

    return JsonResponse({
        "html": html,
        "centros": [
            {
                "id": centro.id,
                "nombre": centro.nombre,
                "tipo": centro.tipo,
                "direccion": centro.direccion
            }
            for centro in centros
        ]
    })

@login_required
def guardar_centro_operativo(request):

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

    tipo = (
        request.POST.get("tipo") or ""
    ).strip()

    direccion = (
        request.POST.get("direccion") or ""
    ).strip().upper()

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre."
        })

    if not tipo:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo."
        })

    if CentroOperativo.objects.filter(
        empresa=empresa,
        nombre=nombre,
        activo=True
    ).exists():

        return JsonResponse({
            "ok": False,
            "mensaje": "Ese centro operativo ya existe."
        })

    centro = CentroOperativo.objects.create(
        empresa=empresa,
        nombre=nombre,
        tipo=tipo,
        direccion=direccion
    )

    return JsonResponse({
        "ok": True,
        "centro": {
            "id": centro.id,
            "nombre": centro.nombre,
        }
    })

@login_required
def modificar_centro_operativo(request):

    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    centro_id = request.POST.get("centro")
    empresa_id = request.POST.get("empresa")

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo = (
        request.POST.get("tipo") or ""
    ).strip()

    direccion = (
        request.POST.get("direccion") or ""
    ).strip().upper()

    if not nombre:
        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese el nombre del centro operativo."
        })

    if not tipo:
        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione el tipo."
        })

    tipos_validos = {
        "Casa Central",
        "Sucursal",
        "Deposito",
        "Mostrador"
    }

    if tipo not in tipos_validos:
        return JsonResponse({
            "ok": False,
            "mensaje": "El tipo seleccionado no es válido."
        })

    try:
        centro = CentroOperativo.objects.get(
            id=centro_id,
            empresa=empresa,
            activo=True
        )

    except CentroOperativo.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "mensaje": "El centro operativo no existe."
        }, status=404)

    if CentroOperativo.objects.filter(
        empresa=empresa,
        nombre=nombre,
        activo=True
    ).exclude(id=centro.id).exists():

        return JsonResponse({
            "ok": False,
            "mensaje": "Ya existe otro centro operativo con ese nombre."
        })

    centro.nombre = nombre
    centro.tipo = tipo
    centro.direccion = direccion

    centro.save(
        update_fields=[
            "nombre",
            "tipo",
            "direccion"
        ]
    )

    return JsonResponse({
        "ok": True
    })


@login_required
def eliminar_centro_operativo(request):

    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    centro_id = request.POST.get("centro")
    empresa_id = request.POST.get("empresa")

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    try:
        centro = CentroOperativo.objects.get(
            id=centro_id,
            empresa=empresa,
            activo=True
        )

    except CentroOperativo.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "mensaje": "El centro operativo no existe."
        }, status=404)

    cantidad_centros_activos = (
        CentroOperativo.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .count()
    )

    if cantidad_centros_activos <= 1:
        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No se puede eliminar el único centro operativo "
                "de la empresa. Cree otro centro operativo antes "
                "de eliminar este."
            )
        })

    centro.activo = False
    centro.save(update_fields=["activo"])

    return JsonResponse({
        "ok": True
    })

# =========================================
# RECURSOS OPERATIVOS
# =========================================
