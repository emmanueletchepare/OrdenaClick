from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase

from usuarios.http.movimientos_pagos import registrar_pago_manual_movimiento


class ArchivoTamanoFalso:
    name = "comprobante.jpg"
    size = 1

    def __init__(self):
        self._stream = BytesIO(b"x")

    def tell(self):
        return self._stream.tell()

    def seek(self, position):
        return self._stream.seek(position)

    def chunks(self):
        yield b"a" * (20 * 1024 * 1024 + 1)


class PagoManualAdjuntosB10aTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, archivo, clave=""):
        request = self.factory.post(
            "/movimientos/registrar-pago/",
            {"empresa": "1", "movimiento": "1", "pagos": '[{}]',
             "clave_idempotencia": clave},
        )
        request.user = SimpleNamespace(is_authenticated=True)
        request.FILES.setlist("comprobante", [archivo])
        return request

    @patch("usuarios.http.movimientos_pagos._huella_pago_manual")
    def test_rechaza_tamano_declarado_antes_de_huella(self, huella):
        archivo = SimpleUploadedFile("foto.jpg", b"x")
        archivo.size = 20 * 1024 * 1024 + 1
        request = self._request(archivo, "12345678-1234-1234-1234-123456789abc")
        response = registrar_pago_manual_movimiento(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"20 MB", response.content)
        huella.assert_not_called()

    @patch("usuarios.http.movimientos_pagos._huella_pago_manual")
    def test_rechaza_tamano_real_falsificado_antes_de_huella(self, huella):
        request = self._request(ArchivoTamanoFalso())
        response = registrar_pago_manual_movimiento(request)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"20 MB", response.content)
        huella.assert_not_called()

    def test_validador_no_cambia_posicion_del_archivo(self):
        from django.utils.datastructures import MultiValueDict
        from usuarios.services.adjuntos_financieros_b10a import validar_adjuntos_financieros
        archivo = SimpleUploadedFile("foto.jpg", b"123456")
        archivo.seek(2)
        validar_adjuntos_financieros(MultiValueDict({"comprobante": [archivo]}))
        self.assertEqual(archivo.tell(), 2)
