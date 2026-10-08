import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.template.loader import render_to_string

from usuarios.models import Proveedor
from usuarios.services.seguridad import obtener_empresa_administrable
from django.contrib.auth.decorators import login_required


def validar_email_proveedor(valor, nombre_campo):

    if not valor:
        return None

    try:

        validate_email(valor)

    except ValidationError:

        return f"El e-mail de {nombre_campo} no es válido."

    return None


def datos_proveedor_request(request):

    return {

        "razon_social": (
            request.POST.get("razon_social") or ""
        ).strip().upper(),

        "cuit": (
            request.POST.get("cuit") or ""
        ).strip(),

        "direccion": (
            request.POST.get("direccion") or ""
        ).strip().upper(),

        "localidad": (
            request.POST.get("localidad") or ""
        ).strip().upper(),

        "contacto1_nombre": (
            request.POST.get("contacto1_nombre") or ""
        ).strip().upper(),

        "contacto1_telefono": (
            request.POST.get("contacto1_telefono") or ""
        ).strip(),

        "contacto1_email": (
            request.POST.get("contacto1_email") or ""
        ).strip().lower(),

        "contacto2_nombre": (
            request.POST.get("contacto2_nombre") or ""
        ).strip().upper(),

        "contacto2_telefono": (
            request.POST.get("contacto2_telefono") or ""
        ).strip(),

        "contacto2_email": (
            request.POST.get("contacto2_email") or ""
        ).strip().lower(),

        "email": (
            request.POST.get("email") or ""
        ).strip().lower(),

        "observaciones": (
            request.POST.get("observaciones") or ""
        ).strip(),

    }


def validar_datos_proveedor(datos):

    if not datos["razon_social"]:

        return "Ingrese la razón social del proveedor."

    if not re.match(
        r"^\d{2}-\d{8}-\d{1}$",
        datos["cuit"]
    ):

        return (
            "El CUIT debe tener el formato "
            "00-00000000-0."
        )

    validaciones_email = [

        (
            datos["contacto1_email"],
            "contacto 1"
        ),

        (
            datos["contacto2_email"],
            "contacto 2"
        ),

        (
            datos["email"],
            "proveedor"
        ),

    ]

    for email, nombre_campo in validaciones_email:

        error = validar_email_proveedor(
            email,
            nombre_campo
        )

        if error:

            return error

    return None


@login_required
def listar_proveedores(request):

    empresa_id = request.GET.get(
        "empresa"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    proveedores = Proveedor.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by(
        "razon_social"
    )

    html = render_to_string(
        "usuarios/maestros/proveedores.html",
        {
            "empresa": empresa,
            "proveedores": proveedores
        },
        request=request
    )

    return JsonResponse({

        "ok": True,

        "html": html,

        "proveedores": [

            {
                "id": proveedor.id,
                "razon_social": proveedor.razon_social,
                "cuit": proveedor.cuit
            }

            for proveedor in proveedores

        ]

    })


@login_required
def guardar_proveedor(request):

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

    datos = datos_proveedor_request(
        request
    )

    error = validar_datos_proveedor(
        datos
    )

    if error:

        return JsonResponse({
            "ok": False,
            "mensaje": error
        })

    proveedor_existente = (
        Proveedor.objects
        .filter(
            empresa=empresa,
            cuit=datos["cuit"]
        )
        .first()
    )

    if proveedor_existente:

        if proveedor_existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe un proveedor activo "
                    "con ese CUIT."
                )
            })

        return JsonResponse({
            "ok": False,
            "requiere_reactivacion": True,

            "mensaje": (
                "Este CUIT pertenece a un proveedor "
                "inactivo. Puede reactivarlo."
            ),

            "proveedor": {
                "id": proveedor_existente.id,
                "razon_social": proveedor_existente.razon_social,
                "cuit": proveedor_existente.cuit,
                "direccion": proveedor_existente.direccion,
                "localidad": proveedor_existente.localidad,

                "contacto1_nombre":
                    proveedor_existente.contacto1_nombre,

                "contacto1_telefono":
                    proveedor_existente.contacto1_telefono,

                "contacto1_email":
                    proveedor_existente.contacto1_email,

                "contacto2_nombre":
                    proveedor_existente.contacto2_nombre,

                "contacto2_telefono":
                    proveedor_existente.contacto2_telefono,

                "contacto2_email":
                    proveedor_existente.contacto2_email,

                "email": proveedor_existente.email,
                "observaciones": proveedor_existente.observaciones,
            }
        })

    proveedor = Proveedor.objects.create(
        empresa=empresa,
        **datos
    )

    return JsonResponse({

        "ok": True,

        "proveedor": {
            "id": proveedor.id,
            "razon_social": proveedor.razon_social,
            "cuit": proveedor.cuit
        }

    })


@login_required
def modificar_proveedor(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    proveedor_id = request.POST.get(
        "proveedor"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    try:

        proveedor = Proveedor.objects.get(
            id=proveedor_id,
            empresa=empresa,
            activo=True
        )

    except Proveedor.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "El proveedor no existe."
        }, status=404)

    datos = datos_proveedor_request(
        request
    )

    error = validar_datos_proveedor(
        datos
    )

    if error:

        return JsonResponse({
            "ok": False,
            "mensaje": error
        })

    cuit_duplicado = (
        Proveedor.objects
        .filter(
            empresa=empresa,
            cuit=datos["cuit"]
        )
        .exclude(
            id=proveedor.id
        )
        .exists()
    )

    if cuit_duplicado:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otro proveedor, activo "
                "o inactivo, con ese CUIT."
            )
        })

    for campo, valor in datos.items():

        setattr(
            proveedor,
            campo,
            valor
        )

    proveedor.save(
        update_fields=list(
            datos.keys()
        )
    )

    return JsonResponse({
        "ok": True
    })


@login_required
def eliminar_proveedor(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    proveedor_id = request.POST.get(
        "proveedor"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    try:

        proveedor = Proveedor.objects.get(
            id=proveedor_id,
            empresa=empresa,
            activo=True
        )

    except Proveedor.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "El proveedor no existe."
        }, status=404)

    proveedor.activo = False

    proveedor.save(
        update_fields=[
            "activo"
        ]
    )

    return JsonResponse({
        "ok": True
    })

@login_required
def reactivar_proveedor(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    proveedor_id = request.POST.get(
        "proveedor"
    )

    empresa = obtener_empresa_administrable(
        request.user,
        empresa_id,
    )

    try:

        proveedor = Proveedor.objects.get(
            id=proveedor_id,
            empresa=empresa,
            activo=False
        )

    except Proveedor.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "El proveedor inactivo no existe "
                "o ya fue reactivado."
            )
        }, status=404)

    proveedor.activo = True

    proveedor.save(
        update_fields=[
            "activo"
        ]
    )

    return JsonResponse({
        "ok": True,

        "proveedor": {
            "id": proveedor.id,
            "razon_social": proveedor.razon_social,
            "cuit": proveedor.cuit
        }
    })
