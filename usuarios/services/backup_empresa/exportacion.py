import io
import zipfile
from collections import defaultdict
from datetime import datetime, timezone as datetime_timezone

from django.db import models

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    Empresa,
    IdentidadUsuarioEmpresa,
    RolFuncionalUsuarioEmpresa,
)

from .common import json_bytes, portable_id, safe_backup_filename, serialize_scalar, sha256_bytes
from .specs import FORMAT_ID, FORMAT_VERSION, MODEL_SPECS, MODEL_TO_SPEC


class ExportadorEmpresaV1:
    def __init__(self, empresa):
        self.empresa = empresa
        self.object_ids = {}
        self.entries = {}
        self.counts = {}

    def construir(self):
        self._indexar_objetos()
        self._agregar_json("data/empresa.json", self._serializar_empresa())

        for spec in MODEL_SPECS:
            records = [self._serializar_objeto(spec, obj) for obj in self._queryset(spec)]
            self.counts[spec.key] = len(records)
            self._agregar_json(f"data/{spec.key}.json", records)

        users = self._serializar_usuarios()
        self.counts["usuarios"] = len(users)
        self._agregar_json("data/usuarios.json", users)

        manifest = {
            "format": FORMAT_ID,
            "version": FORMAT_VERSION,
            "generated_at": datetime.now(datetime_timezone.utc).isoformat(),
            "empresa": {
                "cuit": self.empresa.cuit,
                "razon_social": self.empresa.razon_social,
                "nombre_fantasia": self.empresa.nombre_fantasia,
            },
            "components": self.counts,
            "security": {
                "contains_passwords": False,
                "contains_django_permissions": False,
                "gestion_claves_requires_reconfiguration": True,
            },
            "entries": [
                {
                    "path": path,
                    "sha256": sha256_bytes(content),
                    "size": len(content),
                }
                for path, content in sorted(self.entries.items())
            ],
        }

        manifest_bytes = json_bytes(manifest)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", manifest_bytes)
            for path, content in sorted(self.entries.items()):
                archive.writestr(path, content)
        return buffer.getvalue(), manifest

    def _queryset(self, spec):
        return spec.model.objects.filter(**{spec.company_lookup: self.empresa}).order_by("pk")

    def _indexar_objetos(self):
        for spec in MODEL_SPECS:
            for obj in self._queryset(spec):
                self.object_ids[(spec.model, obj.pk)] = portable_id(spec.key, obj.pk)

    def _serializar_empresa(self):
        data = {"backup_id": portable_id("empresa", self.empresa.pk), "fields": {}, "files": {}}
        for field in self.empresa._meta.concrete_fields:
            if field.primary_key or field.name == "propietario":
                continue
            if isinstance(field, models.FileField):
                self._agregar_archivo(data, "empresa", self.empresa, field)
            elif not field.is_relation:
                data["fields"][field.name] = serialize_scalar(field.value_from_object(self.empresa))
        return data

    def _serializar_objeto(self, spec, obj):
        record = {
            "backup_id": self.object_ids[(spec.model, obj.pk)],
            "fields": {},
            "refs": {},
            "files": {},
        }
        for field in obj._meta.concrete_fields:
            if field.primary_key or field.name in spec.exclude_fields:
                continue
            if isinstance(field, models.FileField):
                self._agregar_archivo(record, spec.key, obj, field)
                continue
            if field.is_relation:
                related_id = getattr(obj, field.attname)
                if field.remote_field.model is Empresa:
                    record["refs"][field.name] = "empresa"
                    continue
                if related_id is None:
                    record["refs"][field.name] = None
                    continue
                related_model = field.remote_field.model
                related_spec = MODEL_TO_SPEC.get(related_model)
                if related_spec is None:
                    # Relaciones globales (ej. auth.User) se excluyen del formato.
                    continue
                record["refs"][field.name] = self.object_ids.get((related_model, related_id))
                continue
            record["fields"][field.name] = serialize_scalar(field.value_from_object(obj))

        if spec.key == "gestion_claves":
            record["fields"]["requiere_reconfiguracion"] = True
        return record

    def _agregar_archivo(self, record, model_key, obj, field):
        file_value = getattr(obj, field.name)
        if not file_value or not file_value.name:
            return
        try:
            with file_value.open("rb") as source:
                content = source.read()
        except (FileNotFoundError, OSError):
            record["files"][field.name] = {"missing": True, "original_name": file_value.name}
            return
        filename = safe_backup_filename(file_value.name)
        backup_id = record["backup_id"]
        path = f"files/{model_key}/{backup_id}/{field.name}/{filename}"
        self.entries[path] = content
        record["files"][field.name] = {
            "path": path,
            "original_name": file_value.name,
            "sha256": sha256_bytes(content),
        }

    def _serializar_usuarios(self):
        identities = {
            identity.usuario_id: identity
            for identity in IdentidadUsuarioEmpresa.objects.filter(
                empresa=self.empresa,
                usuario__isnull=False,
            ).select_related("usuario")
        }

        assignments = {
            assignment.usuario_id: assignment
            for assignment in AsignacionUsuarioEmpresa.objects.filter(
                empresa=self.empresa,
            ).select_related("usuario", "centro_operativo")
        }

        functional_roles = defaultdict(list)
        for role in RolFuncionalUsuarioEmpresa.objects.filter(
            empresa=self.empresa,
        ).select_related("usuario").order_by("usuario__username", "rol"):
            functional_roles[role.usuario_id].append({
                "rol": role.rol,
                "activo": role.activo,
            })

        user_ids = set(identities) | set(assignments) | set(functional_roles)
        result = []

        for user_id in sorted(user_ids):
            identity = identities.get(user_id)
            assignment = assignments.get(user_id)
            user = None
            if assignment:
                user = assignment.usuario
            elif identity:
                user = identity.usuario
            else:
                role = (
                    RolFuncionalUsuarioEmpresa.objects
                    .filter(empresa=self.empresa, usuario_id=user_id)
                    .select_related("usuario")
                    .first()
                )
                user = role.usuario if role else None

            if not user:
                continue

            actor_id = (
                str(identity.uuid)
                if identity
                else portable_id("usuario_snapshot", user.pk)
            )

            assignment_data = None
            if assignment:
                assignment_data = {
                    "jerarquia": assignment.jerarquia,
                    "activo": assignment.activo,
                    "centro_ref": (
                        self.object_ids.get(
                            (
                                assignment.centro_operativo.__class__,
                                assignment.centro_operativo_id,
                            )
                        )
                        if assignment.centro_operativo_id
                        else None
                    ),
                }

            result.append({
                "actor_id": actor_id,
                "username": user.username,
                "email": user.email or "",
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "assignment": assignment_data,
                "functional_roles": functional_roles.get(user_id, []),
            })

        # Identidades restaurables que ya no están vinculadas a una cuenta.
        for identity in IdentidadUsuarioEmpresa.objects.filter(
            empresa=self.empresa,
            usuario__isnull=True,
        ).order_by("username_historico"):
            result.append({
                "actor_id": str(identity.uuid),
                "username": identity.username_historico,
                "email": identity.email_historico,
                "first_name": identity.nombre_historico,
                "last_name": "",
                "assignment": None,
                "functional_roles": [],
            })

        return result

    def _agregar_json(self, path, data):
        self.entries[path] = json_bytes(data)


def construir_backup_empresa(empresa):
    return ExportadorEmpresaV1(empresa).construir()
