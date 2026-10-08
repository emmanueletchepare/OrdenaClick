from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import Banco, CuentaBancaria
from usuarios.services.capacidades import (
    CAPACIDAD_EMPRESA_ADMINISTRAR,
    exigir_capacidad_empresa,
)


@login_required
@require_GET
def listar_cuentas_bancarias(request):
    """
    Devuelve el ABM de cuentas bancarias correspondiente
    a la empresa activa.
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

    cuentas = CuentaBancaria.objects.filter(
        empresa=empresa,
        activo=True
    ).select_related(
        "banco"
    ).order_by(
        "banco__nombre",
        "nombre"
    )

    bancos = Banco.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by(
        "nombre"
    )

    html = render_to_string(
        "usuarios/maestros/cuentas_bancarias.html",
        {
            "empresa": empresa,
            "cuentas": cuentas,
            "bancos": bancos,
            "tipos_cuenta": CuentaBancaria.TIPOS_CUENTA,
            "monedas": CuentaBancaria.MONEDAS,
        },
        request=request
    )

    return JsonResponse({
        "ok": True,
        "html": html,
        "cuentas": [
            {
                "id": cuenta.id,
                "nombre": cuenta.nombre,
                "banco_id": cuenta.banco_id,
                "banco": cuenta.banco.nombre,
                "tipo_cuenta": cuenta.tipo_cuenta,
                "moneda": cuenta.moneda,
                "numero_cuenta": cuenta.numero_cuenta,
                "cbu": cuenta.cbu,
                "alias": cuenta.alias,
            }
            for cuenta in cuentas
        ]
    })


@login_required
@require_POST
def guardar_cuenta_bancaria(request):
    """
    Crea una cuenta bancaria para la empresa activa.
    Si existe una cuenta equivalente inactiva,
    la reactiva en lugar de crear un duplicado.
    """

    empresa_id = request.POST.get(
        "empresa"
    )

    banco_id = request.POST.get(
        "banco"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_cuenta = (
        request.POST.get("tipo_cuenta") or ""
    ).strip()

    moneda = (
        request.POST.get("moneda") or ""
    ).strip()

    numero_cuenta = (
        request.POST.get("numero_cuenta") or ""
    ).strip()

    cbu = (
        request.POST.get("cbu") or ""
    ).strip()

    alias = (
        request.POST.get("alias") or ""
    ).strip().upper()

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre para la cuenta."
        })

    tipos_validos = {
        valor
        for valor, etiqueta
        in CuentaBancaria.TIPOS_CUENTA
    }

    if tipo_cuenta not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo de cuenta válido."
        })

    monedas_validas = {
        valor
        for valor, etiqueta
        in CuentaBancaria.MONEDAS
    }

    if moneda not in monedas_validas:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione una moneda válida."
        })

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
            "mensaje": "Seleccione un banco válido."
        })

    cuenta_existente = CuentaBancaria.objects.filter(
        empresa=empresa,
        banco=banco,
        nombre=nombre
    ).first()

    if cuenta_existente:

        if cuenta_existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe una cuenta bancaria "
                    "con ese nombre para ese banco."
                )
            })

        return JsonResponse({
            "ok": False,
            "inactiva": True,
            "cuenta": {
                "id": cuenta_existente.id,
                "nombre": cuenta_existente.nombre,
                "banco_id": cuenta_existente.banco_id,
                "tipo_cuenta": cuenta_existente.tipo_cuenta,
                "moneda": cuenta_existente.moneda,
                "numero_cuenta": cuenta_existente.numero_cuenta,
                "cbu": cuenta_existente.cbu,
                "alias": cuenta_existente.alias,
            },
            "mensaje": (
                "La cuenta bancaria ya existe pero está inactiva. "
                "Puede reactivarla."
            )
        })

    cuenta = CuentaBancaria.objects.create(
        empresa=empresa,
        banco=banco,
        nombre=nombre,
        tipo_cuenta=tipo_cuenta,
        moneda=moneda,
        numero_cuenta=numero_cuenta,
        cbu=cbu,
        alias=alias
    )

    return JsonResponse({
        "ok": True,
        "cuenta": {
            "id": cuenta.id,
            "nombre": cuenta.nombre
        }
    })


@login_required
@require_POST
def modificar_cuenta_bancaria(request):
    """
    Modifica una cuenta bancaria activa perteneciente
    a la empresa indicada.
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

    cuenta_id = request.POST.get(
        "cuenta"
    )

    banco_id = request.POST.get(
        "banco"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_cuenta = (
        request.POST.get("tipo_cuenta") or ""
    ).strip()

    moneda = (
        request.POST.get("moneda") or ""
    ).strip()

    numero_cuenta = (
        request.POST.get("numero_cuenta") or ""
    ).strip()

    cbu = (
        request.POST.get("cbu") or ""
    ).strip()

    alias = (
        request.POST.get("alias") or ""
    ).strip().upper()

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre para la cuenta."
        })

    tipos_validos = {
        valor
        for valor, etiqueta
        in CuentaBancaria.TIPOS_CUENTA
    }

    if tipo_cuenta not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo de cuenta válido."
        })

    monedas_validas = {
        valor
        for valor, etiqueta
        in CuentaBancaria.MONEDAS
    }

    if moneda not in monedas_validas:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione una moneda válida."
        })

    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa=empresa,
            activo=True
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La cuenta bancaria no existe."
            },
            status=404
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
            "mensaje": "Seleccione un banco válido."
        })

    duplicada = CuentaBancaria.objects.filter(
        empresa=empresa,
        banco=banco,
        nombre=nombre,
        activo=True
    ).exclude(
        id=cuenta.id
    ).exists()

    if duplicada:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra cuenta bancaria "
                "con ese nombre para ese banco."
            )
        })

    cuenta.banco = banco
    cuenta.nombre = nombre
    cuenta.tipo_cuenta = tipo_cuenta
    cuenta.moneda = moneda
    cuenta.numero_cuenta = numero_cuenta
    cuenta.cbu = cbu
    cuenta.alias = alias

    cuenta.save(
        update_fields=[
            "banco",
            "nombre",
            "tipo_cuenta",
            "moneda",
            "numero_cuenta",
            "cbu",
            "alias",
        ]
    )

    return JsonResponse({
        "ok": True
    })


@login_required
@require_POST
def eliminar_cuenta_bancaria(request):
    """
    Realiza la baja lógica de una cuenta bancaria.
    No elimina físicamente el registro.
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

    cuenta_id = request.POST.get(
        "cuenta"
    )

    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa=empresa,
            activo=True
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La cuenta bancaria no existe."
            },
            status=404
        )

    cuenta.activo = False

    cuenta.save(
        update_fields=[
            "activo"
        ]
    )

    return JsonResponse({
        "ok": True
    })


@login_required
@require_POST
def reactivar_cuenta_bancaria(request):
    """
    Reactiva una cuenta bancaria inactiva y permite
    actualizar sus datos antes de volver a utilizarla.
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

    cuenta_id = request.POST.get(
        "cuenta"
    )

    banco_id = request.POST.get(
        "banco"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_cuenta = (
        request.POST.get("tipo_cuenta") or ""
    ).strip()

    moneda = (
        request.POST.get("moneda") or ""
    ).strip()

    numero_cuenta = (
        request.POST.get("numero_cuenta") or ""
    ).strip()

    cbu = (
        request.POST.get("cbu") or ""
    ).strip()

    alias = (
        request.POST.get("alias") or ""
    ).strip().upper()

    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa=empresa,
            activo=False
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "La cuenta bancaria inactiva "
                    "no existe."
                )
            },
            status=404
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
            "mensaje": "Seleccione un banco válido."
        })

    duplicada = CuentaBancaria.objects.filter(
        empresa=empresa,
        banco=banco,
        nombre=nombre,
        activo=True
    ).exclude(
        id=cuenta.id
    ).exists()

    if duplicada:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra cuenta bancaria activa "
                "con ese nombre para ese banco."
            )
        })

    cuenta.banco = banco
    cuenta.nombre = nombre
    cuenta.tipo_cuenta = tipo_cuenta
    cuenta.moneda = moneda
    cuenta.numero_cuenta = numero_cuenta
    cuenta.cbu = cbu
    cuenta.alias = alias
    cuenta.activo = True

    cuenta.save(
        update_fields=[
            "banco",
            "nombre",
            "tipo_cuenta",
            "moneda",
            "numero_cuenta",
            "cbu",
            "alias",
            "activo",
        ]
    )

    return JsonResponse({
        "ok": True
    })
