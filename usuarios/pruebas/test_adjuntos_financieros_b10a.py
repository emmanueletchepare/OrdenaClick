from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from unittest.mock import MagicMock

from usuarios.services.adjuntos_financieros_b10a import (
    MAX_ADJUNTO_BYTES,
    validar_adjuntos_financieros,
)


class AdjuntosFinancierosB10aTests(SimpleTestCase):
    def test_admite_archivo_pequeno(self):
        archivo = SimpleUploadedFile("factura.jpg", b"contenido")
        validar_adjuntos_financieros(Coleccion(archivo))
        self.assertEqual(archivo.read(), b"contenido")

    def test_rechaza_tamano_declarado_excesivo(self):
        archivo = MagicMock()
        archivo.size = MAX_ADJUNTO_BYTES + 1
        try:
            with self.assertRaises(ValueError):
                validar_adjuntos_financieros(Coleccion(archivo))
        finally:
            archivo.chunks.assert_not_called()

    def test_rechaza_bytes_reales_excesivos(self):
        archivo = MagicMock()
        archivo.size = 1
        archivo.tell.return_value = 0
        archivo.chunks.return_value = iter([b"x" * (MAX_ADJUNTO_BYTES + 1)])
        with self.assertRaises(ValueError):
            validar_adjuntos_financieros(Coleccion(archivo))
        archivo.seek.assert_called_once_with(0)

    def test_restaura_posicion_cuando_es_valido(self):
        archivo = SimpleUploadedFile("factura.pdf", b"abc")
        archivo.read(1)
        validar_adjuntos_financieros(Coleccion(archivo))
        self.assertEqual(archivo.read(), b"bc")


class Coleccion:
    def __init__(self, archivo):
        self.archivo = archivo

    def __iter__(self):
        return iter(["archivo"])

    def getlist(self, nombre):
        return [self.archivo]
