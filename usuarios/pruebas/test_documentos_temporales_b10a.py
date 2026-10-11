"""B10a: la carga documental temporal no confía en size del navegador."""
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from usuarios.http import empresa_backup
from usuarios.services.backup_empresa.common import BackupEmpresaError


class DocumentosTemporalesB10aTests(SimpleTestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.directorio.cleanup)
        self.destino = Path(self.directorio.name) / "documento.bin"

    def test_documento_dentro_del_limite_se_guarda(self):
        class Upload:
            def chunks(self):
                yield b"ab"
                yield b"cd"
        with patch.object(empresa_backup, "MAX_SINGLE_ENTRY_BYTES", 4):
            empresa_backup._guardar_documento_temporal(Upload(), str(self.destino))
        self.assertEqual(self.destino.read_bytes(), b"abcd")

    def test_tamano_real_excedido_preserva_documento_anterior(self):
        self.destino.write_bytes(b"anterior")
        class Upload:
            size = 1
            def chunks(self):
                yield b"abc"
                yield b"def"
        with patch.object(empresa_backup, "MAX_SINGLE_ENTRY_BYTES", 5):
            with self.assertRaises(BackupEmpresaError):
                empresa_backup._guardar_documento_temporal(Upload(), str(self.destino))
        self.assertEqual(self.destino.read_bytes(), b"anterior")
        self.assertEqual(sorted(p.name for p in self.destino.parent.iterdir()), ["documento.bin"])

    def test_upload_interrumpido_no_deja_parcial(self):
        class Upload:
            def chunks(self):
                yield b"dato"
                raise OSError("interrumpido")
        with self.assertRaises(OSError):
            empresa_backup._guardar_documento_temporal(Upload(), str(self.destino))
        self.assertEqual(list(self.destino.parent.iterdir()), [])
