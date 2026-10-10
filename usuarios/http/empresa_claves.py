from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.template.loader import render_to_string

from usuarios.models import GestionClave
from usuarios.services.seguridad import obtener_empresa_administrable
from usuarios.seguridad_claves import cifrar_clave, descifrar_clave
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


# =========================================


def datos_gestion_clave_request(request):

    return {

        "nombre": (
            request.POST.get(
                "nombre"
            ) or ""
        ).strip(),

        "sitio": (
            request.POST.get(
                "sitio"
            ) or ""
        ).strip(),

        "usuario": (
            request.POST.get(
                "usuario"
            ) or ""
        ).strip(),

        "correo": (
            request.POST.get(
                "correo"
            ) or ""
        ).strip().lower(),

        "contrasena": (
            request.POST.get(
                "contrasena"
            ) or ""
        ),

        "referencia_recuperacion_1": (
            request.POST.get(
                "referencia_recuperacion_1"
            ) or ""
        ).strip(),

        "referencia_recuperacion_2": (
            request.POST.get(
                "referencia_recuperacion_2"
            ) or ""
        ).strip(),

        "observaciones": (
            request.POST.get(
                "observaciones"
            ) or ""
        ).strip(),

    }


def validar_datos_gestion_clave(
    datos,
    requiere_contrasena=True
):

    if not datos["nombre"]:

        return (
            "Ingrese el nombre "
            "de la credencial."
        )

    if (
        requiere_contrasena and
        not datos["contrasena"]
    ):

        return (
            "Ingrese una contraseña."
        )

    if datos["correo"]:

        try:

            validate_email(
                datos["correo"]
            )

        except ValidationError:

            return (
                "El correo ingresado "
                "no es válido."
            )

    return None


@login_required
def listar_gestion_claves(request):

    empresa_id = request.GET.get(
        "empresa"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    claves = GestionClave.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by(
        "nombre"
    )

    html = render_to_string(
        "usuarios/empresa/gestion_claves.html",
        {
            "empresa": empresa,
            "claves": claves
        },
        request=request
    )

    return JsonResponse({
        "ok": True,
        "html": html
    })

@login_required
def guardar_gestion_clave(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    datos = datos_gestion_clave_request(
        request
    )

    error = validar_datos_gestion_clave(
        datos,
        requiere_contrasena=True
    )

    if error:

        return JsonResponse({
            "ok": False,
            "mensaje": error
        })

    existente = (
        GestionClave.objects
        .filter(
            empresa=empresa,
            nombre__iexact=datos["nombre"]
        )
        .first()
    )

    if existente:

        if existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe una credencial "
                    "activa con ese nombre."
                )
            })

        return JsonResponse({

            "ok": False,

            "requiere_reactivacion": True,

            "mensaje": (
                "Ya existe una credencial "
                "inactiva con ese nombre."
            ),

            "clave": {
                "id": existente.id,
                "nombre": existente.nombre
            }

        })

    try:

        contrasena_cifrada = cifrar_clave(
            datos["contrasena"]
        )

    except Exception as error:

        print(
            "Error cifrando contraseña:",
            error
        )

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No fue posible cifrar "
                "la contraseña."
            )
        }, status=500)

    clave = GestionClave.objects.create(

        empresa=empresa,

        nombre=datos["nombre"],

        sitio=datos["sitio"],

        usuario=datos["usuario"],

        correo=datos["correo"],

        contrasena_cifrada=
            contrasena_cifrada,

        referencia_recuperacion_1=
            datos[
                "referencia_recuperacion_1"
            ],

        referencia_recuperacion_2=
            datos[
                "referencia_recuperacion_2"
            ],

        observaciones=
            datos["observaciones"]

    )

    return JsonResponse({

        "ok": True,

        "clave": {
            "id": clave.id,
            "nombre": clave.nombre
        }

    })

@login_required
@never_cache
def ver_gestion_clave(request):

    empresa_id = request.GET.get(
        "empresa"
    )

    clave_id = request.GET.get(
        "clave"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    try:

        clave = GestionClave.objects.get(
            id=clave_id,
            empresa=empresa,
            activo=True
        )

    except GestionClave.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La credencial no existe."
        }, status=404)

    try:

        contrasena = descifrar_clave(
            clave.contrasena_cifrada
        )

    except ValueError:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No fue posible recuperar "
                "la contraseña."
            )
        }, status=500)

    return JsonResponse({

        "ok": True,

        "clave": {

            "id":
                clave.id,

            "nombre":
                clave.nombre,

            "sitio":
                clave.sitio,

            "usuario":
                clave.usuario,

            "correo":
                clave.correo,

            "contrasena":
                contrasena,

            "referencia_recuperacion_1":
                clave.referencia_recuperacion_1,

            "referencia_recuperacion_2":
                clave.referencia_recuperacion_2,

            "observaciones":
                clave.observaciones,

        }

    })

@login_required
def modificar_gestion_clave(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    clave_id = request.POST.get(
        "clave"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    try:

        clave = GestionClave.objects.get(
            id=clave_id,
            empresa=empresa,
            activo=True
        )

    except GestionClave.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La credencial no existe."
        }, status=404)

    datos = datos_gestion_clave_request(
        request
    )

    error = validar_datos_gestion_clave(
        datos,
        requiere_contrasena=False
    )

    if error:

        return JsonResponse({
            "ok": False,
            "mensaje": error
        })

    duplicado = (
        GestionClave.objects
        .filter(
            empresa=empresa,
            nombre__iexact=datos["nombre"],
            activo=True
        )
        .exclude(
            id=clave.id
        )
        .exists()
    )

    if duplicado:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra credencial "
                "activa con ese nombre."
            )
        })

    clave.nombre = (
        datos["nombre"]
    )

    clave.sitio = (
        datos["sitio"]
    )

    clave.usuario = (
        datos["usuario"]
    )

    clave.correo = (
        datos["correo"]
    )

    clave.referencia_recuperacion_1 = (
        datos[
            "referencia_recuperacion_1"
        ]
    )

    clave.referencia_recuperacion_2 = (
        datos[
            "referencia_recuperacion_2"
        ]
    )

    clave.observaciones = (
        datos["observaciones"]
    )

    campos_actualizados = [
        "nombre",
        "sitio",
        "usuario",
        "correo",
        "referencia_recuperacion_1",
        "referencia_recuperacion_2",
        "observaciones",
        "modificado"
    ]

    if datos["contrasena"]:

        try:

            clave.contrasena_cifrada = (
                cifrar_clave(
                    datos["contrasena"]
                )
            )

        except Exception as error:

            print(
                "Error cifrando contraseña:",
                error
            )

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "No fue posible cifrar "
                    "la contraseña."
                )
            }, status=500)

        campos_actualizados.append(
            "contrasena_cifrada"
        )

    clave.save(
        update_fields=campos_actualizados
    )

    return JsonResponse({
        "ok": True
    })

@login_required
def eliminar_gestion_clave(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    clave_id = request.POST.get(
        "clave"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    try:

        clave = GestionClave.objects.get(
            id=clave_id,
            empresa=empresa,
            activo=True
        )

    except GestionClave.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La credencial no existe."
        }, status=404)

    clave.activo = False

    clave.save(
        update_fields=[
            "activo",
            "modificado"
        ]
    )

    return JsonResponse({
        "ok": True
    })


@login_required
def reactivar_gestion_clave(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    clave_id = request.POST.get(
        "clave"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    try:

        clave = GestionClave.objects.get(
            id=clave_id,
            empresa=empresa,
            activo=False
        )

    except GestionClave.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "La credencial inactiva "
                "no existe o ya fue activada."
            )
        }, status=404)

    duplicado_activo = (
        GestionClave.objects
        .filter(
            empresa=empresa,
            nombre__iexact=clave.nombre,
            activo=True
        )
        .exclude(
            id=clave.id
        )
        .exists()
    )

    if duplicado_activo:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe una credencial "
                "activa con ese nombre."
            )
        })

    clave.activo = True

    clave.save(
        update_fields=[
            "activo",
            "modificado"
        ]
    )

    return JsonResponse({

        "ok": True,

        "clave": {
            "id": clave.id,
            "nombre": clave.nombre
        }

    })

# =========================================
# TIPOS DE GASTO
# =========================================
