"""B10b: ZIP adversariales y rollback de restauraciones."""
import io
import json
import hashlib
import warnings
import zipfile
import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from usuarios.models import Empresa, CentroOperativo
from usuarios.services.backup_empresa.common import (
    BackupEmpresaError, cleanup_import, import_path,
)
from usuarios.services.backup_empresa.importacion import (
    inspeccionar_backup, REQUIRED_JSONS,
)
from usuarios.services.backup_empresa.specs import FORMAT_ID, FORMAT_VERSION, MODEL_SPECS
from usuarios.services.backup_empresa.exportacion import construir_backup_empresa
from usuarios.services.backup_empresa.restauracion import restaurar_empresa, RestauradorEmpresaV1


class ZipAdversarialB10bTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="auditor_b10b", password="test")
        self.tokens = []

    def tearDown(self):
        for token in self.tokens:
            cleanup_import(token)

    def _guardar(self, blob):
        token = str(uuid.uuid4())
        with open(import_path(token), "wb") as destino:
            destino.write(blob)
        self.tokens.append(token)
        return token

    def _zip_minimo(self, entries_override=None):
        data = {path: b"[]" for path in REQUIRED_JSONS}
        data["data/empresa.json"] = b'{"fields": {"cuit": "30-00000000-1"}}'
        data["data/usuarios.json"] = b'["MARCADOR-B10B"]'
        entries = [
            {"path": path, "sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)}
            for path, payload in sorted(data.items())
        ]
        manifest = {
            "format": FORMAT_ID,
            "version": FORMAT_VERSION,
            "entries": entries if entries_override is None else entries_override,
            "components": {spec.key: 0 for spec in MODEL_SPECS} | {"usuarios": 1},
        }
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest))
            for path, payload in data.items():
                archive.writestr(path, payload)
        return buffer.getvalue()

    def test_crc_corrupto_se_rechaza_con_error_controlado(self):
        blob = self._zip_minimo()
        self.assertIn(b"MARCADOR-B10B", blob)
        blob = blob.replace(b"MARCADOR-B10B", b"MARCADOR-B10C", 1)
        with self.assertRaises(BackupEmpresaError):
            inspeccionar_backup(self._guardar(blob), self.usuario)

    def test_manifest_entries_no_lista_se_rechaza(self):
        with self.assertRaises(BackupEmpresaError):
            inspeccionar_backup(self._guardar(self._zip_minimo(entries_override="invalido")), self.usuario)

    def test_zip_con_entrada_duplicada_se_rechaza(self):
        buffer = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("manifest.json", "{}")
                archive.writestr("data/usuarios.json", "[]")
                archive.writestr("data/usuarios.json", "[]")
        with self.assertRaises(BackupEmpresaError):
            inspeccionar_backup(self._guardar(buffer.getvalue()), self.usuario)

    def test_error_durante_restauracion_revierte_base_de_datos(self):
        empresa = Empresa.objects.create(
            propietario=self.usuario, razon_social="Original B10b",
            nombre_fantasia="Original", cuit="30-55555555-5",
            condicion_fiscal="Responsable inscripto",
        )
        centro = CentroOperativo.objects.create(
            empresa=empresa, nombre="Centro que debe seguir", tipo="Casa Central", activo=True,
        )
        blob, _ = construir_backup_empresa(empresa)
        token = self._guardar(blob)
        info = inspeccionar_backup(token, self.usuario)
        config = {
            "empresa_existente_id": empresa.pk, "empresa": info["empresa"],
            "documentos": {}, "documentos_nombres": {}, "usuarios": {},
        }
        with patch.object(RestauradorEmpresaV1, "_restaurar_spec", side_effect=RuntimeError("fallo controlado")):
            with self.assertRaises(RuntimeError):
                restaurar_empresa(token, self.usuario, config)
        self.assertTrue(CentroOperativo.objects.filter(pk=centro.pk, empresa=empresa).exists())
        self.assertEqual(Empresa.objects.get(pk=empresa.pk).razon_social, "Original B10b")
