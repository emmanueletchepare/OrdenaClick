import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from usuarios.models import AsignacionUsuarioEmpresa, RolFuncionalUsuarioEmpresa
from usuarios.services.backup_empresa import (
    BackupEmpresaError,
    buscar_candidatos_usuarios,
    construir_backup_empresa,
    guardar_upload_temporal,
    inspeccionar_backup,
    restaurar_empresa,
)
from usuarios.services.backup_empresa.common import (
    MAX_SINGLE_ENTRY_BYTES,
    cleanup_import,
    document_path,
    safe_backup_filename,
)
from usuarios.services.seguridad import obtener_empresa_administrable


SESSION_KEY = "importacion_empresa_v1"


@login_required
@require_GET
def exportar_empresa_v1(request, empresa_id):
    empresa = obtener_empresa_administrable(request.user, empresa_id)
    contenido, _manifest = construir_backup_empresa(empresa)
    nombre_base = empresa.nombre_fantasia or empresa.razon_social or "empresa"
    nombre_base = safe_backup_filename(nombre_base).replace(".zip", "")
    response = HttpResponse(contenido, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{nombre_base}_backup_v1.zip"'
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
@require_POST
def importar_empresa_v1(request):
    upload = request.FILES.get("archivo_zip")
    if not upload:
        messages.error(request, "Seleccioná un backup de Empresa.")
        return redirect("panel_admin")

    previous = request.session.pop(SESSION_KEY, None)
    if previous:
        cleanup_import(previous.get("token"))

    try:
        token = guardar_upload_temporal(upload)
        inspection = inspeccionar_backup(token, request.user)
    except (BackupEmpresaError, ValidationError) as error:
        messages.error(request, _validation_message(error))
        return redirect("panel_admin")

    request.session[SESSION_KEY] = {
        "token": token,
        "inspection": inspection,
        "empresa": {},
        "documentos": {},
        "documentos_nombres": {},
        "usuarios": {},
    }
    request.session.modified = True
    return redirect("importar_empresa_wizard", paso="empresa")


@login_required
@require_http_methods(["GET", "POST"])
def importar_empresa_wizard(request, paso):
    state = request.session.get(SESSION_KEY)
    if not state:
        messages.info(request, "No hay una importación en curso.")
        return redirect("panel_admin")

    if paso not in {"empresa", "usuarios", "resumen"}:
        return redirect("importar_empresa_wizard", paso="empresa")

    token = state.get("token")
    try:
        inspection = inspeccionar_backup(token, request.user)
    except (BackupEmpresaError, ValidationError) as error:
        cleanup_import(token)
        request.session.pop(SESSION_KEY, None)
        messages.error(request, _validation_message(error))
        return redirect("panel_admin")

    if request.method == "POST":
        if paso == "empresa":
            try:
                _guardar_paso_empresa(request, state, inspection)
            except (BackupEmpresaError, ValidationError) as error:
                messages.error(request, _validation_message(error))
            else:
                request.session[SESSION_KEY] = state
                request.session.modified = True
                return redirect("importar_empresa_wizard", paso="usuarios")
        elif paso == "usuarios":
            try:
                _guardar_paso_usuarios(request, state, inspection)
            except (BackupEmpresaError, ValidationError) as error:
                messages.error(request, _validation_message(error))
            else:
                request.session[SESSION_KEY] = state
                request.session.modified = True
                return redirect("importar_empresa_wizard", paso="resumen")
        elif paso == "resumen" and request.POST.get("confirmar_importacion") == "1":
            config = {
                "empresa_existente_id": inspection.get("empresa_existente_id"),
                "empresa": state.get("empresa", {}),
                "documentos": state.get("documentos", {}),
                "documentos_nombres": state.get("documentos_nombres", {}),
                "usuarios": state.get("usuarios", {}),
            }
            try:
                empresa = restaurar_empresa(token, request.user, config)
            except Exception as error:
                messages.error(request, _validation_message(error))
            else:
                request.session.pop(SESSION_KEY, None)
                request.session["empresa_id"] = empresa.pk
                messages.success(request, "La Empresa fue restaurada correctamente desde Backup v1.")
                return redirect(f'{reverse("panel_admin")}?empresa={empresa.pk}')

    context = _wizard_context(request, state, inspection, paso)
    return render(request, "usuarios/empresa/importacion_wizard.html", context)


@login_required
@require_POST
def cancelar_importacion_empresa(request):
    state = request.session.pop(SESSION_KEY, None)
    if state:
        cleanup_import(state.get("token"))
    messages.info(request, "La importación fue cancelada sin modificar la Empresa.")
    return redirect("panel_admin")


def _guardar_paso_empresa(request, state, inspection):
    source = inspection["empresa"]
    fields = (
        "razon_social",
        "nombre_fantasia",
        "condicion_fiscal",
        "cuit",
        "inicio_actividades",
        "inicio_contable",
        "direccion_fiscal",
        "direccion_real",
        "telefono1",
        "telefono2",
        "email",
        "presidente",
        "vicepresidente",
    )
    data = {}
    for field in fields:
        value = request.POST.get(field, source.get(field))
        value = value.strip() if isinstance(value, str) else value
        data[field] = value or None
    if not data["razon_social"]:
        raise BackupEmpresaError("La razón social es obligatoria.")
    if data["condicion_fiscal"] not in {"Responsable inscripto", "Monotributo", "Exento", "Consumidor final", None}:
        raise BackupEmpresaError("La condición fiscal seleccionada no es válida.")
    state["empresa"] = data

    for field_name in ("estatuto", "acta", "designacion"):
        upload = request.FILES.get(field_name)
        if not upload:
            continue
        if upload.size > MAX_SINGLE_ENTRY_BYTES:
            raise BackupEmpresaError(f"El archivo de {field_name} supera el límite permitido.")
        path = document_path(state["token"], field_name)
        with open(path, "wb") as target:
            for chunk in upload.chunks():
                target.write(chunk)
        state.setdefault("documentos", {})[field_name] = path
        state.setdefault("documentos_nombres", {})[field_name] = safe_backup_filename(upload.name)


def _guardar_paso_usuarios(request, state, inspection):
    candidates = buscar_candidatos_usuarios(inspection["usuarios"])
    centers = {item["backup_id"]: item for item in inspection["centros"]}
    choices = {}
    allowed_roles = {
        AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
        AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO,
        AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR,
    }
    functional_role_values = {
        RolFuncionalUsuarioEmpresa.ROL_CONTABLE,
        RolFuncionalUsuarioEmpresa.ROL_LEGAL,
    }

    for item in inspection["usuarios"]:
        actor_id = str(item.get("actor_id") or "")
        candidate = candidates.get(item.get("actor_id"))
        functional_roles = []
        if candidate:
            for functional_role in functional_role_values:
                if request.POST.get(
                    f"usuario_{actor_id}_funcional_{functional_role}"
                ) == "1":
                    functional_roles.append(functional_role)

        propietario_actual_id = inspection.get("propietario_actual_id")
        if candidate and candidate.pk == propietario_actual_id:
            choices[actor_id] = {
                "activo": False,
                "user_id": candidate.pk,
                "jerarquia": None,
                "centro_ref": None,
                "propietario": True,
                "roles_funcionales": functional_roles,
            }
            continue

        active = request.POST.get(f"usuario_{actor_id}_activo") == "1"
        if not candidate:
            active = False
            functional_roles = []

        role = request.POST.get(f"usuario_{actor_id}_jerarquia") or None
        center_ref = request.POST.get(f"usuario_{actor_id}_centro") or None
        if active and role not in allowed_roles:
            raise BackupEmpresaError("Seleccioná una jerarquía válida para cada usuario activo.")
        if active and role == AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO:
            if center_ref not in centers:
                raise BackupEmpresaError("Cada Administrador debe tener un Centro Operativo válido.")
        else:
            center_ref = None

        choices[actor_id] = {
            "activo": active,
            "user_id": candidate.pk if candidate else None,
            "jerarquia": role if active else None,
            "centro_ref": center_ref,
            "propietario": False,
            "roles_funcionales": functional_roles,
        }
    state["usuarios"] = choices


def _wizard_context(request, state, inspection, paso):
    candidates = buscar_candidatos_usuarios(inspection["usuarios"])
    choices = state.get("usuarios", {})
    users = []
    for item in inspection["usuarios"]:
        actor_id = str(item.get("actor_id") or "")
        candidate = candidates.get(item.get("actor_id"))
        source_assignment = item.get("assignment") or {}
        source_functional_roles = {
            role.get("rol")
            for role in (item.get("functional_roles") or [])
            if role.get("activo")
        }
        choice = choices.get(actor_id, {})
        selected_functional_roles = set(
            choice.get("roles_funcionales", source_functional_roles)
        )
        users.append({
            **item,
            "actor_id": actor_id,
            "candidate": candidate,
            "is_owner": bool(
                candidate
                and candidate.pk == inspection.get("propietario_actual_id")
            ),
            "selected_active": choice.get(
                "activo",
                bool(
                    source_assignment.get("activo")
                    and candidate
                    and candidate.pk != inspection.get("propietario_actual_id")
                ),
            ),
            "selected_role": choice.get("jerarquia") or source_assignment.get("jerarquia") or AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR,
            "selected_center": choice.get("centro_ref") or source_assignment.get("centro_ref"),
            "selected_contable": RolFuncionalUsuarioEmpresa.ROL_CONTABLE in selected_functional_roles,
            "selected_legal": RolFuncionalUsuarioEmpresa.ROL_LEGAL in selected_functional_roles,
        })
    empresa = dict(inspection["empresa"])
    empresa.update(state.get("empresa", {}))
    return {
        "paso": paso,
        "inspection": inspection,
        "empresa": empresa,
        "usuarios": users,
        "centros": inspection["centros"],
        "roles": AsignacionUsuarioEmpresa.JERARQUIAS,
        "config_usuarios": choices,
        "documentos_reemplazados": state.get("documentos_nombres", {}),
    }


def _validation_message(error):
    if isinstance(error, ValidationError):
        if hasattr(error, "messages") and error.messages:
            return " ".join(str(message) for message in error.messages)
    return str(error) or "No fue posible completar la operación."
