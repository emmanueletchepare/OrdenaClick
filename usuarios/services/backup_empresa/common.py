import hashlib
import json
import os
import re
import tempfile
import time
import uuid
from datetime import date, datetime
from decimal import Decimal
from pathlib import PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 250 * 1024 * 1024
MAX_ENTRIES = 2500
MAX_SINGLE_ENTRY_BYTES = 50 * 1024 * 1024
MAX_COMPRESSION_RATIO = 150
IMPORT_TTL_SECONDS = 24 * 60 * 60


class BackupEmpresaError(ValidationError):
    pass


def json_bytes(data):
    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8")


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def serialize_scalar(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def deserialize_scalar(field, value):
    if value is None:
        return None
    try:
        return field.to_python(value)
    except (TypeError, ValueError, ValidationError) as error:
        raise BackupEmpresaError(
            f"Valor inválido para {field.model.__name__}.{field.name}."
        ) from error


def portable_id(model_key, pk):
    namespace = uuid.UUID("01f72d8e-d985-4a23-bc4c-8f65c8ae2cf3")
    return str(uuid.uuid5(namespace, f"ordenaclick:{model_key}:{pk}"))


def safe_backup_filename(name):
    base = os.path.basename(name or "archivo")
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._")
    return base[:160] or "archivo"


def validate_zip_entry_name(name):
    if not name or "\\" in name:
        raise BackupEmpresaError("El ZIP contiene una ruta inválida.")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise BackupEmpresaError("El ZIP contiene una ruta no permitida.")
    if name.startswith("/"):
        raise BackupEmpresaError("El ZIP contiene una ruta absoluta.")


def import_root():
    root = os.path.join(tempfile.gettempdir(), "ordenaclick_importaciones")
    os.makedirs(root, mode=0o700, exist_ok=True)
    return root


def cleanup_stale_imports():
    root = import_root()
    cutoff = time.time() - IMPORT_TTL_SECONDS
    # Nunca borrar archivos ajenos ni seguir enlaces simbolicos en temporales.
    patron = re.compile(
        r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}"
        r"(?:\.zip|-(?:estatuto|acta|designacion)\.bin)$"
    )
    for name in os.listdir(root):
        if not patron.fullmatch(name):
            continue
        path = os.path.join(root, name)
        try:
            if (
                not os.path.islink(path)
                and os.path.isfile(path)
                and os.path.getmtime(path) < cutoff
            ):
                os.remove(path)
        except OSError:
            pass


def import_path(token):
    try:
        parsed = uuid.UUID(str(token))
    except (TypeError, ValueError) as error:
        raise BackupEmpresaError("Importación inválida o vencida.") from error
    return os.path.join(import_root(), f"{parsed}.zip")


def document_path(token, field_name):
    if field_name not in {"estatuto", "acta", "designacion"}:
        raise BackupEmpresaError("Documento de importación inválido.")
    return os.path.join(import_root(), f"{uuid.UUID(str(token))}-{field_name}.bin")


def cleanup_import(token):
    for suffix in (".zip", "-estatuto.bin", "-acta.bin", "-designacion.bin"):
        try:
            os.remove(os.path.join(import_root(), f"{uuid.UUID(str(token))}{suffix}"))
        except (OSError, TypeError, ValueError):
            pass


def company_file_fields():
    from usuarios.models import Empresa
    return {
        field.name
        for field in Empresa._meta.concrete_fields
        if isinstance(field, models.FileField)
    }
