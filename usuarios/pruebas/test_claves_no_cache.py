"""Regresiones de lectura de credenciales privadas y cabeceras no-cache.

Los mocks se aplican a la interfaz REAL de autorizacion ``permiso_claves``.
No sustituyen autenticacion ni conceden acceso a usuarios reales.
"""
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase

from usuarios.http.empresa_claves import ver_gestion_clave
from usuarios.models import GestionClave


class ClavesNoCacheTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request(self):
        request = self.factory.get('/gestion-claves/ver/', {'empresa': '7', 'clave': '4'})
        request.user = SimpleNamespace(is_authenticated=True, pk=11)
        return request

    @staticmethod
    def _clave():
        return SimpleNamespace(
            id=4, pk=4, nombre='Acceso', sitio='', usuario='', correo='',
            contrasena_cifrada='cifrada', referencia_recuperacion_1='',
            referencia_recuperacion_2='', observaciones='',
        )

    @patch('usuarios.http.empresa_claves.descifrar_clave', return_value='clave-reservada')
    @patch('usuarios.http.empresa_claves.GestionClave.objects.filter')
    @patch('usuarios.http.empresa_claves.permiso_claves')
    def test_revelacion_conserva_datos_y_no_cache(self, permiso, filtrar, descifrar):
        empresa = SimpleNamespace(pk=7)
        permiso.return_value = (empresa, False)
        filtrar.return_value.get.return_value = self._clave()
        solicitud = self._request()
        respuesta = ver_gestion_clave(solicitud)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(__import__('json').loads(respuesta.content), {
            'ok': True,
            'clave': {'id': 4, 'nombre': 'Acceso', 'sitio': '', 'usuario': '', 'correo': '',
                      'contrasena': 'clave-reservada', 'referencia_recuperacion_1': '',
                      'referencia_recuperacion_2': '', 'observaciones': ''},
        })
        self.assertIn('no-store', respuesta['Cache-Control'])
        self.assertIn('no-cache', respuesta['Cache-Control'])
        permiso.assert_called_once_with(solicitud.user, '7')
        filtrar.assert_called_once_with(empresa=empresa)
        filtrar.return_value.get.assert_called_once_with(id='4', empresa=empresa, activo=True)
        descifrar.assert_called_once_with('cifrada')

    @patch('usuarios.http.empresa_claves.GestionClave.objects.filter')
    @patch('usuarios.http.empresa_claves.permiso_claves')
    def test_clave_inexistente_tambien_no_cache(self, permiso, filtrar):
        permiso.return_value = (object(), False)
        filtrar.return_value.get.side_effect = GestionClave.DoesNotExist()
        respuesta = ver_gestion_clave(self._request())
        self.assertEqual(respuesta.status_code, 404)
        self.assertIn('no-store', respuesta['Cache-Control'])

    @patch('usuarios.http.empresa_claves.descifrar_clave', return_value='clave-reservada')
    @patch('usuarios.http.empresa_claves.GestionClave.objects.filter')
    @patch('usuarios.http.empresa_claves.permiso_claves')
    def test_clave_propia_se_filtra_antes_de_obtenerla(self, permiso, filtrar, descifrar):
        empresa = SimpleNamespace(pk=7)
        permiso.return_value = (empresa, True)
        filtrar.return_value.filter.return_value.get.return_value = self._clave()
        solicitud = self._request()
        respuesta = ver_gestion_clave(solicitud)
        self.assertEqual(respuesta.status_code, 200)
        filtrar.return_value.filter.assert_called_once_with(creado_por=solicitud.user)
        filtrar.return_value.filter.return_value.get.assert_called_once_with(
            id='4', empresa=empresa, activo=True)
        self.assertIn('no-store', respuesta['Cache-Control'])

    @patch('usuarios.http.empresa_claves.permiso_claves', side_effect=PermissionDenied('Sin permiso'))
    def test_sin_permiso_no_se_revela_la_clave(self, permiso):
        with self.assertRaises(PermissionDenied):
            ver_gestion_clave(self._request())
        permiso.assert_called_once()

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
