from usuarios.services.accesos_colaborador import exigir_abm
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import Banco, CuentaBancaria
from usuarios.services.caja_bancos_informados import puede_ver_bancos
from usuarios.services.cuentas_bancarias_descubierto import (
    CAMPOS, leer_acuerdo, aplicar_acuerdo, auditar_acuerdo,
)
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

    contexto = exigir_abm(
            request.user,
            empresa_id,
            'abm.cuentas',
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

    acceso_descubierto = puede_ver_bancos(request.user, empresa.pk)
    html = render_to_string(
        "usuarios/maestros/cuentas_bancarias.html",
        {
            "empresa": empresa,
            "cuentas": cuentas,
            "bancos": bancos,
            "tipos_cuenta": CuentaBancaria.TIPOS_CUENTA,
            "monedas": CuentaBancaria.MONEDAS,
            "acceso_descubierto": acceso_descubierto,
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
                **({
                    "descubierto_importe": str(cuenta.descubierto_importe) if cuenta.descubierto_importe is not None else "",
                    "descubierto_vencimiento": cuenta.descubierto_vencimiento.isoformat() if cuenta.descubierto_vencimiento else "",
                    "descubierto_alerta_dias": cuenta.descubierto_alerta_dias,
                    "descubierto_alerta_habilitada": cuenta.descubierto_alerta_habilitada,
                } if acceso_descubierto else {}),
            }
            for cuenta in cuentas
        ]
    })


@login_required
@require_POST
@transaction.atomic
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

    contexto = exigir_abm(
            request.user,
            empresa_id,
            'abm.cuentas',
        )
    empresa = contexto.empresa
    acceso_descubierto = puede_ver_bancos(request.user, empresa.pk)
    if not acceso_descubierto and any(campo in request.POST for campo in CAMPOS):
        raise PermissionDenied('No autorizado a modificar acuerdos de descubierto.')

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
                **({
                    "descubierto_importe": str(cuenta_existente.descubierto_importe) if cuenta_existente.descubierto_importe is not None else "",
                    "descubierto_vencimiento": cuenta_existente.descubierto_vencimiento.isoformat() if cuenta_existente.descubierto_vencimiento else "",
                    "descubierto_alerta_dias": cuenta_existente.descubierto_alerta_dias,
                    "descubierto_alerta_habilitada": cuenta_existente.descubierto_alerta_habilitada,
                } if acceso_descubierto else {}),
            },
            "mensaje": (
                "La cuenta bancaria ya existe pero está inactiva. "
                "Puede reactivarla."
            )
        })

    try:
        acuerdo = leer_acuerdo(request.POST)
    except ValueError as exc:
        return JsonResponse({"ok": False, "mensaje": str(exc)}, status=400)

    cuenta = CuentaBancaria.objects.create(
        empresa=empresa,
        banco=banco,
        nombre=nombre,
        tipo_cuenta=tipo_cuenta,
        moneda=moneda,
        numero_cuenta=numero_cuenta,
        cbu=cbu,
        alias=alias,
        **acuerdo,
    )
    auditar_acuerdo(cuenta, {'importe': None, 'vencimiento': None,
        'dias': 3, 'alerta': False}, request.user)

    return JsonResponse({
        "ok": True,
        "cuenta": {
            "id": cuenta.id,
            "nombre": cuenta.nombre
        }
    })


@login_required
@require_POST
@transaction.atomic
def modificar_cuenta_bancaria(request):
    """
    Modifica una cuenta bancaria activa perteneciente
    a la empresa indicada.
    """

    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_abm(
            request.user,
            empresa_id,
            'abm.cuentas',
        )
    empresa = contexto.empresa
    acceso_descubierto = puede_ver_bancos(request.user, empresa.pk)
    if not acceso_descubierto and any(campo in request.POST for campo in CAMPOS):
        raise PermissionDenied('No autorizado a modificar acuerdos de descubierto.')

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

        cuenta = CuentaBancaria.objects.select_for_update().get(
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

    try:
        acuerdo = leer_acuerdo(request.POST, cuenta)
    except ValueError as exc:
        return JsonResponse({"ok": False, "mensaje": str(exc)}, status=400)
    antes_acuerdo = aplicar_acuerdo(cuenta, acuerdo)

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
            *CAMPOS,
        ]
    )

    auditar_acuerdo(cuenta, antes_acuerdo, request.user)

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

    contexto = exigir_abm(
            request.user,
            empresa_id,
            'abm.cuentas',
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
@transaction.atomic
def reactivar_cuenta_bancaria(request):
    """
    Reactiva una cuenta bancaria inactiva y permite
    actualizar sus datos antes de volver a utilizarla.
    """

    empresa_id = request.POST.get(
        "empresa"
    )

    contexto = exigir_abm(
            request.user,
            empresa_id,
            'abm.cuentas',
        )
    empresa = contexto.empresa
    acceso_descubierto = puede_ver_bancos(request.user, empresa.pk)
    if not acceso_descubierto and any(campo in request.POST for campo in CAMPOS):
        raise PermissionDenied('No autorizado a modificar acuerdos de descubierto.')

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

        cuenta = CuentaBancaria.objects.select_for_update().get(
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

    try:
        acuerdo = leer_acuerdo(request.POST, cuenta)
    except ValueError as exc:
        return JsonResponse({"ok": False, "mensaje": str(exc)}, status=400)
    antes_acuerdo = aplicar_acuerdo(cuenta, acuerdo)

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
            *CAMPOS,
            "activo",
        ]
    )

    auditar_acuerdo(cuenta, antes_acuerdo, request.user)

    return JsonResponse({
        "ok": True
    })
