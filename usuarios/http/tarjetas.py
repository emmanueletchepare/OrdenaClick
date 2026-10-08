from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import CuentaBancaria, Tarjeta
from usuarios.services.capacidades import (
    CAPACIDAD_EMPRESA_ADMINISTRAR,
    exigir_capacidad_empresa,
)


@login_required
@require_GET
def listar_tarjetas(request):

    empresa_id = request.GET.get(
        "empresa"
    )


    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa


    tarjetas = (
        Tarjeta.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .select_related(
            "cuenta_bancaria",
            "cuenta_bancaria__banco"
        )
        .order_by(
            "nombre"
        )
    )


    cuentas = (
        CuentaBancaria.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .select_related(
            "banco"
        )
        .order_by(
            "banco__nombre",
            "nombre"
        )
    )


    html = render_to_string(
        "usuarios/maestros/tarjetas.html",
        {
            "empresa":
                empresa,

            "tarjetas":
                tarjetas,

            "cuentas":
                cuentas,

            "tipos_tarjeta":
                Tarjeta.TIPOS_TARJETA,
        },
        request=request
    )


    return JsonResponse({
        "ok": True,

        "html":
            html,

        "tarjetas": [

            {
                "id":
                    tarjeta.id,

                "nombre":
                    tarjeta.nombre,

                "tipo_tarjeta":
                    tarjeta.tipo_tarjeta,

                "tipo_tarjeta_label":
                    tarjeta.get_tipo_tarjeta_display(),

                "cuenta_bancaria_id":
                    tarjeta.cuenta_bancaria_id,

                "cuenta_bancaria":
                    tarjeta.cuenta_bancaria.nombre,

                "banco":
                    tarjeta.cuenta_bancaria.banco.nombre,
            }

            for tarjeta in tarjetas
        ]
    })

# =========================================
# RETENCIONES
# =========================================

@login_required
@require_POST
def guardar_tarjeta(request):

    empresa_id = request.POST.get(
        "empresa"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_tarjeta = (
        request.POST.get("tipo_tarjeta") or ""
    ).strip()

    cuenta_id = request.POST.get(
        "cuenta_bancaria"
    )


    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre para la tarjeta."
        })


    tipos_validos = {
        valor
        for valor, etiqueta
        in Tarjeta.TIPOS_TARJETA
    }


    if tipo_tarjeta not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo de tarjeta válido."
        })


    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa


    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa=empresa,
            activo=True
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione una cuenta bancaria válida."
        })


    existente = (
        Tarjeta.objects
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
                    "Ya existe una tarjeta activa "
                    "con ese nombre."
                )
            })


        return JsonResponse({
            "ok": False,

            "requiere_reactivacion": True,

            "mensaje": (
                "La tarjeta ya existe pero está inactiva. "
                "Puede reactivarla."
            ),

            "tarjeta": {
                "id":
                    existente.id,

                "nombre":
                    existente.nombre,

                "tipo_tarjeta":
                    existente.tipo_tarjeta,

                "cuenta_bancaria_id":
                    existente.cuenta_bancaria_id,
            }
        })


    tarjeta = Tarjeta.objects.create(

        empresa=
            empresa,

        nombre=
            nombre,

        tipo_tarjeta=
            tipo_tarjeta,

        cuenta_bancaria=
            cuenta

    )


    return JsonResponse({
        "ok": True,

        "tarjeta": {
            "id":
                tarjeta.id,

            "nombre":
                tarjeta.nombre,
        }
    })


@login_required
@require_POST
def modificar_tarjeta(request):

    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa

    tarjeta_id = request.POST.get(
        "tarjeta"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_tarjeta = (
        request.POST.get("tipo_tarjeta") or ""
    ).strip()

    cuenta_id = request.POST.get(
        "cuenta_bancaria"
    )


    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre para la tarjeta."
        })


    tipos_validos = {
        valor
        for valor, etiqueta
        in Tarjeta.TIPOS_TARJETA
    }


    if tipo_tarjeta not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo de tarjeta válido."
        })


    try:

        tarjeta = Tarjeta.objects.get(
            id=tarjeta_id,
            empresa=empresa,
            activo=True
        )

    except Tarjeta.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La tarjeta no existe."
            },
            status=404
        )


    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa=empresa,
            activo=True
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione una cuenta bancaria válida."
        })


    duplicada = (
        Tarjeta.objects
        .filter(
            empresa=empresa,
            nombre__iexact=nombre,
            activo=True
        )
        .exclude(
            id=tarjeta.id
        )
        .exists()
    )


    if duplicada:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra tarjeta activa "
                "con ese nombre."
            )
        })


    tarjeta.nombre = nombre

    tarjeta.tipo_tarjeta = tipo_tarjeta

    tarjeta.cuenta_bancaria = cuenta


    tarjeta.save(
        update_fields=[
            "nombre",
            "tipo_tarjeta",
            "cuenta_bancaria",
        ]
    )


    return JsonResponse({
        "ok": True
    })


@login_required
@require_POST
def eliminar_tarjeta(request):

    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa

    tarjeta_id = request.POST.get(
        "tarjeta"
    )


    try:

        tarjeta = Tarjeta.objects.get(
            id=tarjeta_id,
            empresa=empresa,
            activo=True
        )

    except Tarjeta.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La tarjeta no existe."
            },
            status=404
        )


    tarjeta.activo = False


    tarjeta.save(
        update_fields=[
            "activo"
        ]
    )


    return JsonResponse({
        "ok": True
    })


@login_required
@require_POST
def reactivar_tarjeta(request):

    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_capacidad_empresa(
        request.user,
        empresa_id,
        CAPACIDAD_EMPRESA_ADMINISTRAR,
    )
    empresa = contexto.empresa

    tarjeta_id = request.POST.get(
        "tarjeta"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_tarjeta = (
        request.POST.get("tipo_tarjeta") or ""
    ).strip()

    cuenta_id = request.POST.get(
        "cuenta_bancaria"
    )


    try:

        tarjeta = Tarjeta.objects.get(
            id=tarjeta_id,
            empresa=empresa,
            activo=False
        )

    except Tarjeta.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La tarjeta inactiva no existe."
            },
            status=404
        )


    tipos_validos = {
        valor
        for valor, etiqueta
        in Tarjeta.TIPOS_TARJETA
    }


    if tipo_tarjeta not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo de tarjeta válido."
        })


    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa=empresa,
            activo=True
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione una cuenta bancaria válida."
        })


    duplicada = (
        Tarjeta.objects
        .filter(
            empresa=empresa,
            nombre__iexact=nombre,
            activo=True
        )
        .exclude(
            id=tarjeta.id
        )
        .exists()
    )


    if duplicada:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra tarjeta activa "
                "con ese nombre."
            )
        })


    tarjeta.nombre = nombre

    tarjeta.tipo_tarjeta = tipo_tarjeta

    tarjeta.cuenta_bancaria = cuenta

    tarjeta.activo = True


    tarjeta.save(
        update_fields=[
            "nombre",
            "tipo_tarjeta",
            "cuenta_bancaria",
            "activo",
        ]
    )


    return JsonResponse({
        "ok": True
    })
