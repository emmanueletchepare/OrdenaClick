import os
import tempfile
import time
import uuid
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from usuarios.services.backup_empresa import common


class LimpiezaTemporales14CTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        patcher = patch.object(common, "import_root", return_value=str(self.root))
        patcher.start()
        self.addCleanup(patcher.stop)

    def viejo(self, nombre):
        ruta = self.root / nombre
        ruta.write_bytes(b"contenido")
        anterior = time.time() - common.IMPORT_TTL_SECONDS - 120
        os.utime(ruta, (anterior, anterior))
        return ruta

    def test_elimina_solamente_temporales_con_nombres_validos(self):
        token = uuid.uuid4()
        zip_viejo = self.viejo(f"{token}.zip")
        documento_viejo = self.viejo(f"{token}-acta.bin")
        ajeno = self.viejo("documento_importante.txt")
        common.cleanup_stale_imports()
        self.assertFalse(zip_viejo.exists())
        self.assertFalse(documento_viejo.exists())
        self.assertTrue(ajeno.exists())

    def test_no_elimina_nombres_parecidos_ni_archivos_recientes(self):
        token = uuid.uuid4()
        parecido = self.viejo(f"{token}-otra-cosa.bin")
        reciente = self.root / f"{uuid.uuid4()}.zip"
        reciente.write_bytes(b"nuevo")
        common.cleanup_stale_imports()
        self.assertTrue(parecido.exists())
        self.assertTrue(reciente.exists())

    def test_no_sigue_enlaces_simbolicos(self):
        destino = self.viejo("original_no_borrar.txt")
        enlace = self.root / f"{uuid.uuid4()}.zip"
        try:
            enlace.symlink_to(destino)
        except (OSError, NotImplementedError):
            self.skipTest("Sistema sin permisos para symlinks")
        common.cleanup_stale_imports()
        self.assertTrue(enlace.is_symlink())
        self.assertTrue(destino.exists())
