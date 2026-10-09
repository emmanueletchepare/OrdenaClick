"""Entrega autorizada de los tres documentos legales de Empresa."""
import mimetypes
import os

from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.utils.http import content_disposition_header
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from usuarios.services.seguridad import obtener_empresa_autorizada


CAMPOS_DOCUMENTO = frozenset({"estatuto", "acta", "designacion"})


@login_required
@require_GET
@never_cache
def descargar_documento_empresa(request, empresa_id, campo):
    # Reutiliza exactamente la autorización del Panel Administrador.
    empresa = obtener_empresa_autorizada(request.user, empresa_id)
    if campo not in CAMPOS_DOCUMENTO:
        raise Http404("Documento inexistente.")

    archivo = getattr(empresa, campo)
    if not archivo or not archivo.name:
        raise Http404("Documento inexistente.")

    try:
        archivo.open("rb")
    except (FileNotFoundError, OSError, ValueError):
        raise Http404("Documento no disponible.")

    nombre = os.path.basename(archivo.name.replace("\\", "/"))
    tipo, _ = mimetypes.guess_type(nombre)
    tipos_vista = {"application/pdf", "image/jpeg", "image/png", "image/webp", "image/gif"}
    tipo = tipo if tipo in tipos_vista else "application/octet-stream"
    respuesta = FileResponse(archivo, content_type=tipo)
    respuesta["Content-Disposition"] = content_disposition_header(tipo == "application/octet-stream", nombre)
    respuesta["X-Content-Type-Options"] = "nosniff"
    return respuesta
