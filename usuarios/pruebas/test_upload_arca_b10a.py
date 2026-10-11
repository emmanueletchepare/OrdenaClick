"""B10a: límite de tamaño real para certificados y claves ARCA."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from usuarios.http.desarrollador import (
    _leer_credencial_arca_limitada, MAX_CREDENCIAL_ARCA_BYTES,
)


class CredencialesArcaLimitadasB10aTests(SimpleTestCase):
    def test_lectura_valida(self):
        archivo = SimpleUploadedFile("cert.pem", b"datos PEM")
        self.assertEqual(_leer_credencial_arca_limitada(archivo), b"datos PEM")

    def test_rechaza_tamano_declarado_excesivo(self):
        archivo = SimpleUploadedFile("cert.pem", b"x" * (MAX_CREDENCIAL_ARCA_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "1 MiB"):
            _leer_credencial_arca_limitada(archivo)

    def test_rechaza_tamano_real_si_declarado_es_falso(self):
        class CargaEnganosa:
            size = 1
            def chunks(self):
                yield b"x" * MAX_CREDENCIAL_ARCA_BYTES
                yield b"x"
        with self.assertRaisesRegex(ValueError, "1 MiB"):
            _leer_credencial_arca_limitada(CargaEnganosa())
