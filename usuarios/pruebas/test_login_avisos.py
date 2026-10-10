from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.modelo_intentos_login import IntentoLoginOrigen
from usuarios.services.limite_login import MAX_FALLOS


class AvisosLoginTests(TestCase):
    def setUp(self):
        self.url = reverse('login')
        self.user = User.objects.create_user(username='usuario_aviso', password='Segura-Login-2026!')

    def test_login_inicial_sin_aviso(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'role="alert"')

    def test_error_visible_con_usuario_y_sin_contrasena(self):
        response = self.client.post(self.url, {'username': '  usuario_aviso  ', 'password': 'secreto-que-no-debe-aparecer'})
        self.assertContains(response, 'Usuario o contraseña incorrectos.')
        self.assertContains(response, 'value="usuario_aviso"')
        self.assertContains(response, 'role="alert"')
        self.assertNotContains(response, 'secreto-que-no-debe-aparecer')

    def test_bloqueo_visible_y_conserva_usuario(self):
        for _ in range(MAX_FALLOS):
            self.client.post(self.url, {'username': 'usuario_aviso', 'password': 'incorrecta'}, REMOTE_ADDR='192.0.2.55')
        response = self.client.post(self.url, {'username': 'usuario_aviso', 'password': 'Segura-Login-2026!'}, REMOTE_ADDR='192.0.2.55')
        self.assertContains(response, 'Demasiados intentos de acceso.')
        self.assertContains(response, 'value="usuario_aviso"')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(IntentoLoginOrigen.objects.count(), 1)

    def test_login_correcto_sigue_redirigiendo(self):
        response = self.client.post(self.url, {'username': 'usuario_aviso', 'password': 'Segura-Login-2026!'})
        self.assertEqual(response.status_code, 302)
