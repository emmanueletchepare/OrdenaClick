"""B10b: rollback físico y lógico de archivos al fallar una restauración."""
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from usuarios.models import Empresa
from usuarios.services.backup_empresa.common import cleanup_import, document_path, import_path
from usuarios.services.backup_empresa.exportacion import construir_backup_empresa
from usuarios.services.backup_empresa.importacion import inspeccionar_backup
from usuarios.services.backup_empresa.restauracion import (
    RestauradorEmpresaV1,
    restaurar_empresa,
)


class RestauracionArchivosB10bTests(TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory(prefix="oc_b10b_media_")
        self.addCleanup(self.tempdir.cleanup)
        override = override_settings(MEDIA_ROOT=self.tempdir.name)
        override.enable()
        self.addCleanup(override.disable)
        self.usuario = User.objects.create_user(username="b10b_archivos", password="test")
        self.empresa = Empresa.objects.create(
            propietario=self.usuario,
            razon_social="Original B10b",
            nombre_fantasia="Original",
            cuit="30-55555555-5",
            condicion_fiscal="Responsable inscripto",
        )
        self.empresa.estatuto.save("original.pdf", ContentFile(b"%PDF-1.4 ORIGINAL"), save=True)
        self.ruta_original = self.empresa.estatuto.name
        self.token = None
        self.addCleanup(self._limpiar_token)

    def _limpiar_token(self):
        if self.token:
            cleanup_import(self.token)

    def _backup(self):
        contenido, _ = construir_backup_empresa(self.empresa)
        self.token = str(uuid.uuid4())
        with open(import_path(self.token), "wb") as salida:
            salida.write(contenido)
        return inspeccionar_backup(self.token, self.usuario)

    def _config(self, info, *, reemplazo=None, existing=True):
        return {
            "empresa_existente_id": self.empresa.pk if existing else None,
            "empresa": {**info["empresa"], **({"cuit": "30-66666666-6"} if not existing else {})},
            "documentos": {"estatuto": reemplazo} if reemplazo else {},
            "documentos_nombres": {"estatuto": "nuevo.pdf"} if reemplazo else {},
            "usuarios": {},
        }

    def _archivos_en_media(self):
        return {
            str(ruta.relative_to(self.tempdir.name))
            for ruta in Path(self.tempdir.name).rglob("*")
            if ruta.is_file()
        }

    def test_fallo_reemplazo_conserva_documento_original_y_elimina_nuevo(self):
        info = self._backup()
        reemplazo = document_path(self.token, "estatuto")
        with open(reemplazo, "wb") as salida:
            salida.write(b"%PDF-1.4 REEMPLAZO")
        previos = self._archivos_en_media()
        with patch.object(RestauradorEmpresaV1, "_restaurar_spec", side_effect=RuntimeError("interrupcion b10b")):
            with self.assertRaises(RuntimeError):
                restaurar_empresa(self.token, self.usuario, self._config(info, reemplazo=reemplazo))
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.estatuto.name, self.ruta_original)
        with self.empresa.estatuto.open("rb") as original:
            self.assertEqual(original.read(), b"%PDF-1.4 ORIGINAL")
        self.assertEqual(self._archivos_en_media(), previos)
        self.assertEqual(self.empresa.razon_social, "Original B10b")

    def test_fallo_al_crear_empresa_nueva_no_deja_archivos_huerfanos(self):
        info = self._backup()
        previos = self._archivos_en_media()
        with patch.object(RestauradorEmpresaV1, "_restaurar_spec", side_effect=RuntimeError("interrupcion b10b")):
            with self.assertRaises(RuntimeError):
                restaurar_empresa(self.token, self.usuario, self._config(info, existing=False))
        self.assertEqual(self._archivos_en_media(), previos)
        self.assertEqual(Empresa.objects.count(), 1)
