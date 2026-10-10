from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.test import RequestFactory, SimpleTestCase

from usuarios.http.empresa_claves import ver_gestion_clave


class ClavesNoCacheTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self):
        request = self.factory.get('/gestion-claves/ver/', {'empresa': '7', 'clave': '4'})
        request.user = type('Usuario', (), {'is_authenticated': True})()
        return request

    @patch('usuarios.http.empresa_claves.descifrar_clave', return_value='clave-reservada')
    @patch('usuarios.http.empresa_claves.GestionClave.objects.get')
    @patch('usuarios.http.empresa_claves.obtener_empresa_administrable', return_value=object())
    def test_revelacion_conserva_datos_y_no_cache(self, empresa, get_clave, descifrar):
        clave = type('Clave', (), {
            'id': 4, 'nombre': 'Acceso', 'sitio': '', 'usuario': '', 'correo': '',
            'contrasena_cifrada': 'cifrada', 'referencia_recuperacion_1': '',
            'referencia_recuperacion_2': '', 'observaciones': '',
        })()
        get_clave.return_value = clave
        respuesta = ver_gestion_clave(self._request())
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json() if hasattr(respuesta, 'json') else __import__('json').loads(respuesta.content), {
            'ok': True,
            'clave': {'id': 4, 'nombre': 'Acceso', 'sitio': '', 'usuario': '', 'correo': '',
                      'contrasena': 'clave-reservada', 'referencia_recuperacion_1': '',
                      'referencia_recuperacion_2': '', 'observaciones': ''},
        })
        self.assertIn('no-store', respuesta['Cache-Control'])
        self.assertIn('no-cache', respuesta['Cache-Control'])
        empresa.assert_called_once()
        descifrar.assert_called_once_with('cifrada')

    @patch('usuarios.http.empresa_claves.obtener_empresa_administrable', return_value=object())
    @patch('usuarios.http.empresa_claves.GestionClave.objects.get')
    def test_clave_inexistente_tambien_no_cache(self, get_clave, empresa):
        from usuarios.models import GestionClave
        get_clave.side_effect = GestionClave.DoesNotExist()
        respuesta = ver_gestion_clave(self._request())
        self.assertEqual(respuesta.status_code, 404)
        self.assertIn('no-store', respuesta['Cache-Control'])

    def test_anonimo_no_puede_revelar(self):
        request = self.factory.get('/gestion-claves/ver/', {'empresa': '7', 'clave': '4'})
        request.user = AnonymousUser()
        respuesta = ver_gestion_clave(request)
        self.assertEqual(respuesta.status_code, 302)
        from django.urls import reverse
        from urllib.parse import urlsplit, parse_qs

        destino = urlsplit(respuesta['Location'])
        self.assertEqual(destino.path, reverse('login'))
        self.assertIn('next', parse_qs(destino.query))
