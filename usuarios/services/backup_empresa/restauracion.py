import os
from copy import deepcopy

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.db import transaction
from django.db import models

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    Empresa,
    IdentidadUsuarioEmpresa,
    RolFuncionalUsuarioEmpresa,
)
from usuarios.services.seguridad import obtener_empresa_administrable

from .common import BackupEmpresaError, cleanup_import, deserialize_scalar, document_path, safe_backup_filename
from .importacion import cargar_json_backup, leer_archivo_backup
from .specs import MODEL_SPECS


class RestauradorEmpresaV1:
    def __init__(self, token, usuario, configuracion):
        self.token = token
        self.usuario = usuario
        self.config = configuracion
        self.maps = {"empresa": None}
        self.created_files = []
        self.pending_identity_uuids = []

    def restaurar(self):
        existing = None
        existing_id = self.config.get("empresa_existente_id")
        if existing_id:
            existing = Empresa.objects.filter(pk=existing_id).first()
            if existing:
                try:
                    obtener_empresa_administrable(
                        self.usuario,
                        existing.pk,
                    )
                except Exception as error:
                    raise BackupEmpresaError(
                        "No tenés autorización para restaurar sobre esa Empresa."
                    ) from error

        try:
            with transaction.atomic():
                if existing:
                    self._limpiar_empresa_existente(existing)
                    empresa = self._crear_empresa(existing=existing)
                else:
                    empresa = self._crear_empresa()
                self.maps["empresa"] = empresa
                for spec in MODEL_SPECS:
                    self._restaurar_spec(spec)
                self._aplicar_usuarios()
                self._normalizar_uuids_identidades()
                result_id = empresa.pk
        except Exception:
            self._limpiar_archivos_creados()
            raise
        cleanup_import(self.token)
        return Empresa.objects.get(pk=result_id)

    def _limpiar_empresa_existente(self, empresa):
        RolFuncionalUsuarioEmpresa.objects.filter(empresa=empresa).delete()
        AsignacionUsuarioEmpresa.objects.filter(empresa=empresa).delete()
        for spec in reversed(MODEL_SPECS):
            spec.model.objects.filter(**{spec.company_lookup: empresa}).delete()

    def _crear_empresa(self, existing=None):
        source = cargar_json_backup(self.token, "data/empresa.json")
        fields = deepcopy(source.get("fields", {}))
        fields.update(self.config.get("empresa", {}))
        kwargs = {}
        for field in Empresa._meta.concrete_fields:
            if field.primary_key or field.name in {"propietario", "estatuto", "acta", "designacion", "fecha_estatuto", "fecha_acta", "fecha_designacion"}:
                continue
            if field.name in fields:
                kwargs[field.name] = deserialize_scalar(field, fields[field.name])
        if existing is None:
            empresa = Empresa.objects.create(propietario=self.usuario, **kwargs)
        else:
            empresa = existing
            propietario_actual_id = empresa.propietario_id
            for field_name, value in kwargs.items():
                setattr(empresa, field_name, value)
            empresa.propietario_id = propietario_actual_id
            empresa.save()
        self._restaurar_archivos_empresa(empresa, source)
        return empresa

    def _restaurar_archivos_empresa(self, empresa, source):
        replacements = self.config.get("documentos", {})
        for field_name in ("estatuto", "acta", "designacion"):
            replacement_path = replacements.get(field_name)
            content = None
            filename = None
            if replacement_path and os.path.isfile(replacement_path):
                with open(replacement_path, "rb") as stream:
                    content = stream.read()
                filename = safe_backup_filename(self.config.get("documentos_nombres", {}).get(field_name) or field_name)
            else:
                metadata = source.get("files", {}).get(field_name)
                if metadata and metadata.get("path"):
                    content = leer_archivo_backup(self.token, metadata["path"])
                    filename = safe_backup_filename(metadata.get("original_name") or field_name)
            if content is not None:
                file_field = getattr(empresa, field_name)
                file_field.save(filename, ContentFile(content), save=False)
                self.created_files.append(file_field.name)
            else:
                setattr(empresa, field_name, None)
        empresa.save()
        # Preservamos las fechas documentales de origen sólo si no se reemplazó el archivo.
        updates = {}
        for field_name in ("estatuto", "acta", "designacion"):
            date_name = f"fecha_{field_name}"
            if field_name not in replacements and date_name in source.get("fields", {}):
                field = Empresa._meta.get_field(date_name)
                updates[date_name] = deserialize_scalar(field, source["fields"][date_name])
        if updates:
            Empresa.objects.filter(pk=empresa.pk).update(**updates)

    def _restaurar_spec(self, spec):
        records = cargar_json_backup(self.token, f"data/{spec.key}.json")
        spec_map = self.maps.setdefault(spec.key, {})
        for record in records:
            kwargs = {}
            deferred_updates = {}
            for field in spec.model._meta.concrete_fields:
                if field.primary_key or field.name in spec.exclude_fields:
                    continue
                if isinstance(field, models.FileField):
                    continue
                if field.is_relation:
                    ref = record.get("refs", {}).get(field.name)
                    if field.remote_field.model is Empresa:
                        kwargs[field.name] = self.maps["empresa"]
                    elif ref is None:
                        kwargs[field.name] = None
                    else:
                        related = self._resolve_ref(field.remote_field.model, ref)
                        kwargs[field.name] = related
                    continue
                if field.name not in record.get("fields", {}):
                    continue
                if spec.key == "gestion_claves" and field.name == "contrasena_cifrada":
                    continue
                value = deserialize_scalar(field, record["fields"][field.name])
                if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
                    deferred_updates[field.name] = value
                else:
                    kwargs[field.name] = value

            if spec.key == "identidades_usuarios":
                kwargs["usuario"] = self._usuario_para_identidad(record)
                desired_uuid = kwargs.get("uuid")
                if desired_uuid and IdentidadUsuarioEmpresa.objects.filter(uuid=desired_uuid).exists():
                    import uuid as uuid_module
                    kwargs["uuid"] = uuid_module.uuid4()
                else:
                    desired_uuid = None
            else:
                desired_uuid = None
            if spec.key == "gestion_claves":
                kwargs["contrasena_cifrada"] = ""

            existing_auto = None
            if spec.key == "recursos_operativos" and kwargs.get("nombre") == "GENERAL":
                existing_auto = spec.model.objects.filter(
                    empresa=self.maps["empresa"],
                    nombre="GENERAL",
                ).first()
            elif spec.key == "recursos_centros":
                existing_auto = spec.model.objects.filter(
                    recurso_operativo=kwargs.get("recurso_operativo"),
                    centro_operativo=kwargs.get("centro_operativo"),
                ).first()

            if existing_auto is not None:
                obj = existing_auto
                for field_name, value in kwargs.items():
                    setattr(obj, field_name, value)
                obj.full_clean(exclude=[f.name for f in spec.model._meta.concrete_fields if isinstance(f, models.FileField)])
                obj.save()
            else:
                obj = spec.model(**kwargs)
                obj.full_clean(exclude=[f.name for f in spec.model._meta.concrete_fields if isinstance(f, models.FileField)])
                obj.save()
            if desired_uuid is not None:
                self.pending_identity_uuids.append((obj, desired_uuid))
            self._restaurar_files_objeto(spec, obj, record)
            if deferred_updates:
                spec.model.objects.filter(pk=obj.pk).update(**deferred_updates)
            spec_map[record.get("backup_id")] = obj

    def _restaurar_files_objeto(self, spec, obj, record):
        changed = False
        for field_name, metadata in record.get("files", {}).items():
            if not metadata or metadata.get("missing") or not metadata.get("path"):
                continue
            field = spec.model._meta.get_field(field_name)
            if not isinstance(field, models.FileField):
                continue
            content = leer_archivo_backup(self.token, metadata["path"])
            filename = safe_backup_filename(metadata.get("original_name") or field_name)
            file_value = getattr(obj, field_name)
            file_value.save(filename, ContentFile(content), save=False)
            self.created_files.append(file_value.name)
            changed = True
        if changed:
            obj.save()

    def _resolve_ref(self, model, ref):
        for spec in MODEL_SPECS:
            if spec.model is model:
                try:
                    return self.maps[spec.key][ref]
                except KeyError as error:
                    raise BackupEmpresaError(
                        f"El backup contiene una referencia interna inexistente para {model.__name__}."
                    ) from error
        raise BackupEmpresaError(f"El backup referencia un modelo no restaurable: {model.__name__}.")

    def _usuario_para_identidad(self, record):
        uuid_value = record.get("fields", {}).get("uuid")
        choices = self.config.get("usuarios", {})
        choice = choices.get(str(uuid_value))
        if not choice:
            return None
        user_id = choice.get("user_id")
        if not user_id:
            return None
        return User.objects.filter(pk=user_id).first()

    def _aplicar_usuarios(self):
        centers = self.maps.get("centros_operativos", {})
        for actor_id, choice in self.config.get("usuarios", {}).items():
            user_id = choice.get("user_id")
            if not user_id:
                continue
            user = User.objects.filter(pk=user_id, is_active=True).first()
            if not user:
                raise BackupEmpresaError("Uno de los usuarios seleccionados ya no está disponible.")

            if choice.get("activo"):
                jerarquia = choice.get("jerarquia")
                centro = None
                if jerarquia == AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO:
                    centro_ref = choice.get("centro_ref")
                    centro = centers.get(centro_ref)
                    if not centro:
                        raise BackupEmpresaError("Un Administrador requiere un Centro Operativo válido.")
                AsignacionUsuarioEmpresa.objects.create(
                    empresa=self.maps["empresa"],
                    usuario=user,
                    jerarquia=jerarquia,
                    centro_operativo=centro,
                    activo=True,
                )

            for role in choice.get("roles_funcionales", []):
                if role not in {
                    RolFuncionalUsuarioEmpresa.ROL_CONTABLE,
                    RolFuncionalUsuarioEmpresa.ROL_LEGAL,
                }:
                    raise BackupEmpresaError("El backup contiene un rol funcional no soportado.")
                RolFuncionalUsuarioEmpresa.objects.create(
                    empresa=self.maps["empresa"],
                    usuario=user,
                    rol=role,
                    activo=True,
                )

            # Si existe una identidad histórica con el mismo UUID del actor, se vincula a la cuenta elegida.
            try:
                identity = IdentidadUsuarioEmpresa.objects.get(
                    empresa=self.maps["empresa"],
                    uuid=actor_id,
                )
            except (IdentidadUsuarioEmpresa.DoesNotExist, ValueError):
                continue
            if identity.usuario_id != user.pk:
                identity.usuario = user
                identity.save(update_fields=["usuario", "actualizado"])


    def _normalizar_uuids_identidades(self):
        for identity, desired_uuid in self.pending_identity_uuids:
            IdentidadUsuarioEmpresa.objects.filter(pk=identity.pk).update(uuid=desired_uuid)
            identity.uuid = desired_uuid

    def _limpiar_archivos_creados(self):
        # Django no revierte archivos del storage con la transacción de DB.
        from django.core.files.storage import default_storage
        for name in reversed(self.created_files):
            try:
                default_storage.delete(name)
            except Exception:
                pass


def restaurar_empresa(token, usuario, configuracion):
    return RestauradorEmpresaV1(token, usuario, configuracion).restaurar()
