import re

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.template.loader import render_to_string

from usuarios.models import CentroOperativo, Cliente
from usuarios.services.arca import consultar_persona_arca


def normalizar_cuit_cliente(valor):
    """
    Normaliza el CUIT de Cliente al formato canónico de 11 dígitos.

    El formulario puede enviar guiones o espacios, pero la base conserva
    únicamente los dígitos para mantener una representación compatible
    con la futura consulta a ARCA y con las restricciones de unicidad.
    """
    valor = (valor or "").strip()

    if not valor:
        return ""

    return re.sub(r"\D", "", valor)


def validar_cuit_cliente(cuit):
    """
    Valida estructura y dígito verificador de un CUIT argentino.

    El CUIT debe recibirse previamente normalizado a 11 dígitos.
    El CUIT vacío es válido porque el campo es opcional.
    """
    if not cuit:
        return None

    if not re.fullmatch(r"\d{11}", cuit):
        return "El CUIT debe contener exactamente 11 dígitos."

    multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

    suma = sum(
        int(digito) * multiplicador
        for digito, multiplicador
        in zip(cuit[:10], multiplicadores)
    )

    digito_verificador = 11 - (suma % 11)

    if digito_verificador == 11:
        digito_verificador = 0
    elif digito_verificador == 10:
        digito_verificador = 9

    if digito_verificador != int(cuit[-1]):
        return "El CUIT ingresado no es válido."

    return None


def datos_cliente_request(request):
    """
    Obtiene y normaliza los campos editables del ABM de Clientes.
    """
    return {
        "centro_operativo_id": (
            request.POST.get("centro_operativo") or ""
        ).strip(),

        "numero_cliente": (
            request.POST.get("numero_cliente") or ""
        ).strip(),

        "cuit": normalizar_cuit_cliente(
            request.POST.get("cuit")
        ),

        "razon_social": (
            request.POST.get("razon_social") or ""
        ).strip(),

        "direccion": (
            request.POST.get("direccion") or ""
        ).strip(),

        "celular": (
            request.POST.get("celular") or ""
        ).strip(),

        "telefono": (
            request.POST.get("telefono") or ""
        ).strip(),
    }


def validar_datos_cliente(empresa, datos):
    """
    Valida los datos del Cliente y que su Centro pertenezca a la Empresa.

    Devuelve una tupla (centro_operativo, error). Si la validación es
    correcta, error es None.
    """
    if not datos["centro_operativo_id"]:
        return None, "Seleccioná un Centro Operativo."

    try:
        centro_operativo = CentroOperativo.objects.get(
            id=datos["centro_operativo_id"],
            empresa=empresa,
            activo=True,
        )
    except (CentroOperativo.DoesNotExist, ValueError, TypeError):
        return (
            None,
            "El Centro Operativo no existe o no pertenece a la empresa.",
        )

    if not datos["numero_cliente"]:
        return None, "Ingresá el N.º Cliente."

    if not datos["razon_social"]:
        return None, "Ingresá el Nombre / Razón social."

    error_cuit = validar_cuit_cliente(
        datos["cuit"]
    )

    if error_cuit:
        return None, error_cuit

    return centro_operativo, None


@login_required
def listar_clientes(request):
    """
    Devuelve el ABM de Clientes activos pertenecientes
    a una Empresa autorizada.

    Incluye los Centros Operativos activos de la misma Empresa
    para permitir el alta y la edición del Cliente.
    """
    if request.method != "GET":
        return JsonResponse({"ok": False, "mensaje": "Método no permitido."}, status=405)

    empresa_id = request.GET.get("empresa")

    try:
        from usuarios.services.capacidades import (
            CAPACIDAD_EMPRESA_ADMINISTRAR,
            exigir_capacidad_empresa,
        )

        empresa = exigir_capacidad_empresa(
            request.user,
            empresa_id,
            CAPACIDAD_EMPRESA_ADMINISTRAR,
        ).empresa

    except PermissionDenied:
        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No tiene permiso para operar sobre esta empresa."
            ),
        }, status=403)

    clientes = (
        Cliente.objects
        .filter(
            empresa=empresa,
            activo=True,
        )
        .select_related(
            "centro_operativo"
        )
        .order_by(
            "centro_operativo__nombre",
            "numero_cliente",
        )
    )

    centros_operativos = (
        CentroOperativo.objects
        .filter(
            empresa=empresa,
            activo=True,
        )
        .order_by(
            "nombre"
        )
    )

    html = render_to_string(
        "usuarios/maestros/clientes.html",
        {
            "empresa": empresa,
            "clientes": clientes,
            "centros_operativos": centros_operativos,
        },
        request=request,
    )

    return JsonResponse({
        "ok": True,
        "html": html,
        "clientes": [
            {
                "id": cliente.id,
                "centro_operativo_id":
                    cliente.centro_operativo_id,
                "centro_operativo":
                    cliente.centro_operativo.nombre,
                "numero_cliente":
                    cliente.numero_cliente,
                "cuit":
                    cliente.cuit,
                "razon_social":
                    cliente.razon_social,
                "direccion":
                    cliente.direccion,
                "celular":
                    cliente.celular,
                "telefono":
                    cliente.telefono,
            }
            for cliente in clientes
        ],
    })

@login_required
def autocompletar_cliente_arca(request):
    """
    Consulta ARCA por CUIT para asistir la carga manual de un Cliente.

    Devuelve únicamente razón social y dirección. No crea ni modifica
    Clientes y nunca expone las credenciales utilizadas ante ARCA.
    """
    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido.",
        }, status=405)

    empresa_id = request.POST.get("empresa")
    try:
        from usuarios.services.capacidades import (
            CAPACIDAD_EMPRESA_ADMINISTRAR,
            exigir_capacidad_empresa,
        )
        exigir_capacidad_empresa(
            request.user,
            empresa_id,
            CAPACIDAD_EMPRESA_ADMINISTRAR,
        )
    except PermissionDenied:
        return JsonResponse({
            "ok": False,
            "mensaje": "No tiene permiso para operar sobre esta empresa.",
        }, status=403)

    cuit = re.sub(
        r"\D",
        "",
        request.POST.get("cuit") or "",
    )

    if len(cuit) != 11:
        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ingresá un CUIT válido de 11 dígitos."
            ),
        }, status=400)

    try:
        datos = consultar_persona_arca(
            cuit
        )

    except ValueError:
        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ingresá un CUIT válido de 11 dígitos."
            ),
        }, status=400)

    except LookupError:
        return JsonResponse({
            "ok": False,
            "mensaje": (
                "ARCA no encontró una persona para ese CUIT."
            ),
        }, status=404)

    except RuntimeError:
        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No se pudo consultar ARCA en este momento. "
                "Podés continuar cargando el cliente manualmente."
            ),
        }, status=503)

    return JsonResponse({
        "ok": True,
        "razon_social": datos["razon_social"],
        "direccion": datos["direccion"],
    })

@login_required
def guardar_cliente(request):
    """
    Crea un Cliente dentro de una Empresa autorizada.

    Si encuentra un registro inactivo con la misma identificación
    operativa o fiscal, informa que debe reactivarse en lugar de crear
    un duplicado.
    """
    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido.",
        }, status=405)

    empresa_id = request.POST.get("empresa")

    try:
        from usuarios.services.capacidades import (
            CAPACIDAD_EMPRESA_ADMINISTRAR,
            exigir_capacidad_empresa,
        )

        empresa = exigir_capacidad_empresa(
            request.user,
            empresa_id,
            CAPACIDAD_EMPRESA_ADMINISTRAR,
        ).empresa
    except PermissionDenied:
        return JsonResponse({
            "ok": False,
            "mensaje": "No tiene permiso para operar sobre esta empresa.",
        }, status=403)

    datos = datos_cliente_request(request)

    centro_operativo, error = validar_datos_cliente(
        empresa,
        datos,
    )

    if error:
        return JsonResponse({
            "ok": False,
            "mensaje": error,
        })

    numero_existente = (
        Cliente.objects
        .filter(
            empresa=empresa,
            centro_operativo=centro_operativo,
            numero_cliente=datos["numero_cliente"],
        )
        .first()
    )

    if numero_existente:
        if numero_existente.activo:
            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe un cliente activo con ese "
                    "N.º Cliente en el Centro Operativo."
                ),
            })

        return JsonResponse({
            "ok": False,
            "requiere_reactivacion": True,
            "mensaje": (
                "Ese N.º Cliente pertenece a un cliente inactivo "
                "del mismo Centro Operativo. Puede reactivarlo."
            ),
            "cliente": {
                "id": numero_existente.id,
                "numero_cliente":
                    numero_existente.numero_cliente,
                "razon_social":
                    numero_existente.razon_social,
            },
        })

    if datos["cuit"]:
        cuit_existente = (
            Cliente.objects
            .filter(
                empresa=empresa,
                centro_operativo=centro_operativo,
                cuit=datos["cuit"],
            )
            .first()
        )

        if cuit_existente:
            if cuit_existente.activo:
                return JsonResponse({
                    "ok": False,
                    "mensaje": (
                        "Ya existe un cliente activo con ese CUIT "
                        "en el Centro Operativo."
                    ),
                })

            return JsonResponse({
                "ok": False,
                "requiere_reactivacion": True,
                "mensaje": (
                    "Ese CUIT pertenece a un cliente inactivo "
                    "del mismo Centro Operativo. Puede reactivarlo."
                ),
                "cliente": {
                    "id": cuit_existente.id,
                    "numero_cliente":
                        cuit_existente.numero_cliente,
                    "razon_social":
                        cuit_existente.razon_social,
                },
            })

    cliente = Cliente.objects.create(
        empresa=empresa,
        centro_operativo=centro_operativo,
        numero_cliente=datos["numero_cliente"],
        cuit=datos["cuit"],
        razon_social=datos["razon_social"],
        direccion=datos["direccion"],
        celular=datos["celular"],
        telefono=datos["telefono"],
    )

    return JsonResponse({
        "ok": True,
        "cliente": {
            "id": cliente.id,
            "centro_operativo_id":
                cliente.centro_operativo_id,
            "numero_cliente":
                cliente.numero_cliente,
            "cuit":
                cliente.cuit,
            "razon_social":
                cliente.razon_social,
        },
    })


@login_required
def modificar_cliente(request):
    """
    Modifica un Cliente activo de una Empresa autorizada.
    """
    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido.",
        }, status=405)

    empresa_id = request.POST.get("empresa")
    cliente_id = request.POST.get("cliente")

    try:
        from usuarios.services.capacidades import (
            CAPACIDAD_EMPRESA_ADMINISTRAR,
            exigir_capacidad_empresa,
        )

        empresa = exigir_capacidad_empresa(
            request.user,
            empresa_id,
            CAPACIDAD_EMPRESA_ADMINISTRAR,
        ).empresa
    except PermissionDenied:
        return JsonResponse({
            "ok": False,
            "mensaje": "No tiene permiso para operar sobre esta empresa.",
        }, status=403)

    try:
        cliente = Cliente.objects.get(
            id=cliente_id,
            empresa=empresa,
            activo=True,
        )
    except (Cliente.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "ok": False,
            "mensaje": "El cliente no existe.",
        }, status=404)

    datos = datos_cliente_request(request)

    centro_operativo, error = validar_datos_cliente(
        empresa,
        datos,
    )

    if error:
        return JsonResponse({
            "ok": False,
            "mensaje": error,
        })

    numero_duplicado = (
        Cliente.objects
        .filter(
            empresa=empresa,
            centro_operativo=centro_operativo,
            numero_cliente=datos["numero_cliente"],
        )
        .exclude(
            id=cliente.id
        )
        .exists()
    )

    if numero_duplicado:
        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otro cliente, activo o inactivo, "
                "con ese N.º Cliente en el Centro Operativo."
            ),
        })

    if datos["cuit"]:
        cuit_duplicado = (
            Cliente.objects
            .filter(
                empresa=empresa,
                centro_operativo=centro_operativo,
                cuit=datos["cuit"],
            )
            .exclude(
                id=cliente.id
            )
            .exists()
        )

        if cuit_duplicado:
            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe otro cliente, activo o inactivo, "
                    "con ese CUIT en el Centro Operativo."
                ),
            })

    cliente.centro_operativo = centro_operativo
    cliente.numero_cliente = datos["numero_cliente"]
    cliente.cuit = datos["cuit"]
    cliente.razon_social = datos["razon_social"]
    cliente.direccion = datos["direccion"]
    cliente.celular = datos["celular"]
    cliente.telefono = datos["telefono"]

    cliente.save(update_fields=[
        "centro_operativo",
        "numero_cliente",
        "cuit",
        "razon_social",
        "direccion",
        "celular",
        "telefono",
        "modificado",
    ])

    return JsonResponse({
        "ok": True,
    })


@login_required
def eliminar_cliente(request):
    """
    Da de baja lógica a un Cliente de una Empresa autorizada.
    """
    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido.",
        }, status=405)

    empresa_id = request.POST.get("empresa")
    cliente_id = request.POST.get("cliente")

    try:
        from usuarios.services.capacidades import (
            CAPACIDAD_EMPRESA_ADMINISTRAR,
            exigir_capacidad_empresa,
        )

        empresa = exigir_capacidad_empresa(
            request.user,
            empresa_id,
            CAPACIDAD_EMPRESA_ADMINISTRAR,
        ).empresa
    except PermissionDenied:
        return JsonResponse({
            "ok": False,
            "mensaje": "No tiene permiso para operar sobre esta empresa.",
        }, status=403)

    try:
        cliente = Cliente.objects.get(
            id=cliente_id,
            empresa=empresa,
            activo=True,
        )
    except (Cliente.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "ok": False,
            "mensaje": "El cliente no existe.",
        }, status=404)

    cliente.activo = False

    cliente.save(update_fields=[
        "activo",
        "modificado",
    ])

    return JsonResponse({
        "ok": True,
    })


@login_required
def reactivar_cliente(request):
    """
    Reactiva un Cliente inactivo de una Empresa autorizada.
    """
    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido.",
        }, status=405)

    empresa_id = request.POST.get("empresa")
    cliente_id = request.POST.get("cliente")

    try:
        from usuarios.services.capacidades import (
            CAPACIDAD_EMPRESA_ADMINISTRAR,
            exigir_capacidad_empresa,
        )

        empresa = exigir_capacidad_empresa(
            request.user,
            empresa_id,
            CAPACIDAD_EMPRESA_ADMINISTRAR,
        ).empresa
    except PermissionDenied:
        return JsonResponse({
            "ok": False,
            "mensaje": "No tiene permiso para operar sobre esta empresa.",
        }, status=403)

    try:
        cliente = Cliente.objects.select_related(
            "centro_operativo"
        ).get(
            id=cliente_id,
            empresa=empresa,
            activo=False,
        )
    except (Cliente.DoesNotExist, ValueError, TypeError):
        return JsonResponse({
            "ok": False,
            "mensaje": (
                "El cliente inactivo no existe "
                "o ya fue reactivado."
            ),
        }, status=404)

    if not cliente.centro_operativo.activo:
        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No se puede reactivar el cliente porque su "
                "Centro Operativo está inactivo."
            ),
        })

    numero_duplicado = (
        Cliente.objects
        .filter(
            empresa=empresa,
            centro_operativo=cliente.centro_operativo,
            numero_cliente=cliente.numero_cliente,
            activo=True,
        )
        .exclude(
            id=cliente.id
        )
        .exists()
    )

    if numero_duplicado:
        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No se puede reactivar porque ya existe un "
                "cliente activo con ese N.º Cliente en el "
                "Centro Operativo."
            ),
        })

    if cliente.cuit:
        cuit_duplicado = (
            Cliente.objects
            .filter(
                empresa=empresa,
                centro_operativo=cliente.centro_operativo,
                cuit=cliente.cuit,
                activo=True,
            )
            .exclude(
                id=cliente.id
            )
            .exists()
        )

        if cuit_duplicado:
            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "No se puede reactivar porque ya existe un "
                    "cliente activo con ese CUIT en el "
                    "Centro Operativo."
                ),
            })

    cliente.activo = True

    cliente.save(update_fields=[
        "activo",
        "modificado",
    ])

    return JsonResponse({
        "ok": True,
        "cliente": {
            "id": cliente.id,
            "centro_operativo_id":
                cliente.centro_operativo_id,
            "numero_cliente":
                cliente.numero_cliente,
            "cuit":
                cliente.cuit,
            "razon_social":
                cliente.razon_social,
        },
    })
