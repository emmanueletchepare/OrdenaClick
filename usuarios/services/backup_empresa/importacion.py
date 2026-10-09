import json
import os
import stat
import uuid
import zipfile

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from usuarios.models import Empresa
from usuarios.services.seguridad import obtener_empresa_administrable

from .common import (
    MAX_COMPRESSION_RATIO,
    MAX_ENTRIES,
    MAX_SINGLE_ENTRY_BYTES,
    MAX_UNCOMPRESSED_BYTES,
    MAX_UPLOAD_BYTES,
    BackupEmpresaError,
    cleanup_stale_imports,
    import_path,
    sha256_bytes,
    validate_zip_entry_name,
)
from .specs import FORMAT_ID, FORMAT_VERSION, MODEL_SPECS


REQUIRED_JSONS = {"data/empresa.json", "data/usuarios.json"} | {
    f"data/{spec.key}.json" for spec in MODEL_SPECS
}


def guardar_upload_temporal(upload):
    cleanup_stale_imports()
    if getattr(upload, "size", 0) > MAX_UPLOAD_BYTES:
        raise BackupEmpresaError("El archivo supera el tamaño máximo permitido para importación.")
    token = str(uuid.uuid4())
    path = import_path(token)
    total = 0
    # O_EXCL impide sobrescribir archivos existentes, incluso enlaces simbolicos.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as target:
            for chunk in upload.chunks():
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise BackupEmpresaError(
                        "El archivo supera el tamaño máximo permitido para importación."
                    )
                target.write(chunk)
    except BaseException:
        # No conservar ZIP incompleto ante un error o upload interrumpido.
        try:
            os.remove(path)
        except OSError:
            pass
        raise
    return token


def inspeccionar_backup(token, usuario):
    path = import_path(token)
    if not os.path.isfile(path):
        raise BackupEmpresaError("La importación ya no está disponible. Volvé a seleccionar el archivo.")

    try:
        archive = zipfile.ZipFile(path, "r")
    except zipfile.BadZipFile as error:
        raise BackupEmpresaError("El archivo seleccionado no es un ZIP válido.") from error

    with archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        if len(infos) > MAX_ENTRIES:
            raise BackupEmpresaError("El ZIP contiene demasiadas entradas.")

        names = set()
        uncompressed = 0
        for info in infos:
            validate_zip_entry_name(info.filename)
            if info.filename in names:
                raise BackupEmpresaError("El ZIP contiene nombres de archivo duplicados.")
            names.add(info.filename)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise BackupEmpresaError("El ZIP contiene enlaces simbólicos no permitidos.")
            if info.flag_bits & 0x1:
                raise BackupEmpresaError("No se admiten entradas ZIP cifradas.")
            if info.file_size > MAX_SINGLE_ENTRY_BYTES:
                raise BackupEmpresaError("Una entrada del ZIP supera el tamaño máximo permitido.")
            uncompressed += info.file_size
            if uncompressed > MAX_UNCOMPRESSED_BYTES:
                raise BackupEmpresaError("El contenido descomprimido supera el límite permitido.")
            if info.compress_size and info.file_size / max(info.compress_size, 1) > MAX_COMPRESSION_RATIO:
                raise BackupEmpresaError("El ZIP presenta una relación de compresión no permitida.")

        if "manifest.json" not in names:
            raise BackupEmpresaError("Falta manifest.json. Sólo se admiten backups Empresa v1.")
        if not REQUIRED_JSONS.issubset(names):
            raise BackupEmpresaError("El backup está incompleto para el formato Empresa v1.")
        unexpected = {name for name in names if name != "manifest.json" and name not in REQUIRED_JSONS and not name.startswith("files/")}
        if unexpected:
            raise BackupEmpresaError("El ZIP contiene componentes no previstos por Backup Empresa v1.")

        manifest = _read_json(archive, "manifest.json")
        if manifest.get("format") != FORMAT_ID or manifest.get("version") != FORMAT_VERSION:
            raise BackupEmpresaError("La versión del backup no es compatible con esta instalación.")

        expected = {entry.get("path"): entry for entry in manifest.get("entries", [])}
        if set(expected) != (names - {"manifest.json"}):
            raise BackupEmpresaError("El manifest no coincide con el contenido real del ZIP.")

        for entry_path, metadata in expected.items():
            content = archive.read(entry_path)
            if sha256_bytes(content) != metadata.get("sha256"):
                raise BackupEmpresaError(f"Falló la validación de integridad de {entry_path}.")
            if len(content) != metadata.get("size"):
                raise BackupEmpresaError(f"El tamaño declarado de {entry_path} no coincide.")

        validated = _validate_structure(archive, manifest, names)
        empresa_record = validated["empresa"]
        usuarios = validated["usuarios"]
        centros = validated["componentes"]["centros_operativos"]

        empresa_fields = empresa_record.get("fields", {})
        cuit = empresa_fields.get("cuit")
        existente = Empresa.objects.filter(cuit=cuit).first() if cuit else None
        if existente:
            try:
                obtener_empresa_administrable(
                    usuario,
                    existente.pk,
                )
            except PermissionDenied as error:
                raise BackupEmpresaError(
                    "Ya existe una Empresa con ese CUIT y no tenés autorización para restaurarla."
                ) from error

        propietario_actual_id = (
            existente.propietario_id
            if existente
            else usuario.pk
        )

        return {
            "manifest": manifest,
            "empresa": empresa_fields,
            "empresa_existente_id": existente.pk if existente else None,
            "propietario_actual_id": propietario_actual_id,
            "usuarios": usuarios,
            "centros": [
                {
                    "backup_id": item.get("backup_id"),
                    "nombre": item.get("fields", {}).get("nombre", ""),
                    "tipo": item.get("fields", {}).get("tipo", ""),
                    "activo": item.get("fields", {}).get("activo", True),
                }
                for item in centros
            ],
            "componentes": manifest.get("components", {}),
            "gestion_claves_requiere_reconfiguracion": bool(
                manifest.get("security", {}).get("gestion_claves_requires_reconfiguration")
            ),
        }


def cargar_json_backup(token, path):
    with zipfile.ZipFile(import_path(token), "r") as archive:
        return _read_json(archive, path)


def leer_archivo_backup(token, path):
    validate_zip_entry_name(path)
    with zipfile.ZipFile(import_path(token), "r") as archive:
        try:
            return archive.read(path)
        except KeyError as error:
            raise BackupEmpresaError("Falta un archivo requerido por el backup.") from error


def buscar_candidatos_usuarios(backup_users):
    candidates = {}
    for item in backup_users:
        user = None
        email = (item.get("email") or "").strip()
        username = (item.get("username") or "").strip()
        if email:
            user = User.objects.filter(email__iexact=email).order_by("pk").first()
        if user is None and username:
            user = User.objects.filter(username__iexact=username).first()
        candidates[item.get("actor_id")] = user
    return candidates


def _validate_structure(archive, manifest, names):
    empresa = _read_json(archive, "data/empresa.json")
    usuarios = _read_json(archive, "data/usuarios.json")
    if not isinstance(empresa, dict) or not isinstance(empresa.get("fields", {}), dict):
        raise BackupEmpresaError("data/empresa.json tiene una estructura inválida.")
    if not isinstance(usuarios, list):
        raise BackupEmpresaError("data/usuarios.json tiene una estructura inválida.")

    componentes = {}
    all_ids = set()
    for spec in MODEL_SPECS:
        path = f"data/{spec.key}.json"
        records = _read_json(archive, path)
        if not isinstance(records, list):
            raise BackupEmpresaError(f"{path} debe contener una lista.")
        declared = manifest.get("components", {}).get(spec.key)
        if declared != len(records):
            raise BackupEmpresaError(f"El conteo declarado para {spec.key} no coincide.")
        for record in records:
            if not isinstance(record, dict):
                raise BackupEmpresaError(f"{path} contiene un registro inválido.")
            backup_id = record.get("backup_id")
            if not isinstance(backup_id, str) or not backup_id or backup_id in all_ids:
                raise BackupEmpresaError("El backup contiene identificadores internos inválidos o duplicados.")
            all_ids.add(backup_id)
            if not isinstance(record.get("fields", {}), dict) or not isinstance(record.get("refs", {}), dict) or not isinstance(record.get("files", {}), dict):
                raise BackupEmpresaError(f"{path} contiene campos internos inválidos.")
            for metadata in record.get("files", {}).values():
                if metadata and metadata.get("path") and metadata["path"] not in names:
                    raise BackupEmpresaError("El backup referencia un archivo adjunto inexistente.")
        componentes[spec.key] = records

    if manifest.get("components", {}).get("usuarios") != len(usuarios):
        raise BackupEmpresaError("El conteo declarado de usuarios no coincide.")

    for records in componentes.values():
        for record in records:
            for ref in record.get("refs", {}).values():
                if ref in (None, "empresa"):
                    continue
                if ref not in all_ids:
                    raise BackupEmpresaError("El backup contiene una referencia interna inexistente.")

    return {"empresa": empresa, "usuarios": usuarios, "componentes": componentes}


def _read_json(archive, path):
    try:
        content = archive.read(path)
        return json.loads(content.decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
        raise BackupEmpresaError(f"El archivo {path} no contiene JSON válido.") from error
