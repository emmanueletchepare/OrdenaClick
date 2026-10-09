"""Pruebas aisladas de carga temporal privada de Backup Empresa."""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from usuarios.services.backup_empresa.common import BackupEmpresaError
from usuarios.services.backup_empresa import importacion


class CargaTemporalPrivada14BTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = self.tmp.name
        patcher = patch(
            "usuarios.services.backup_empresa.common.import_root",
            return_value=root,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        # import_path es importado en el modulo, pero usa import_root de common.

    def test_zip_se_escribe_integro(self):
        token = importacion.guardar_upload_temporal(
            SimpleUploadedFile("demo.zip", b"datos", content_type="application/zip")
        )
        self.assertEqual(Path(importacion.import_path(token)).read_bytes(), b"datos")

    def test_no_sobrescribe_archivo_existente(self):
        token = "00000000-0000-4000-8000-000000000001"
        path = Path(importacion.import_path(token))
        path.write_bytes(b"original")
        with patch.object(importacion.uuid, "uuid4", return_value=token):
            with self.assertRaises(FileExistsError):
                importacion.guardar_upload_temporal(SimpleUploadedFile("x.zip", b"nuevo"))
        self.assertEqual(path.read_bytes(), b"original")

    def test_limpia_archivo_parcial_si_se_interrumpe(self):
        class UploadInterrumpido:
            size = 1
            def chunks(self):
                yield b"primera parte"
                raise OSError("interrumpido")
        with self.assertRaises(OSError):
            importacion.guardar_upload_temporal(UploadInterrumpido())
        self.assertEqual(os.listdir(self.tmp.name), [])

    def test_limpia_al_superar_limite_real_de_chunks(self):
        class UploadMayor:
            size = 1  # El tamano declarado no es confiable.
            def chunks(self):
                yield b"abcdef"
        with patch.object(importacion, "MAX_UPLOAD_BYTES", 5):
            with self.assertRaises(BackupEmpresaError):
                importacion.guardar_upload_temporal(UploadMayor())
        self.assertEqual(os.listdir(self.tmp.name), [])
