from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from usuarios.modelo_intentos_login import IntentoLoginOrigen
from usuarios.services.limite_login import MAX_FALLOS, _origen


class LimiteLoginA2Tests(TestCase):
    def setUp(self):
        self.url = reverse('login')
        self.user = User.objects.create_user(username='acceso_a2', password='Seguro-A2-2026!')

    def post(self, password, ip='192.0.2.22'):
        return self.client.post(self.url, {'username': 'acceso_a2', 'password': password}, REMOTE_ADDR=ip)

    def test_fallos_se_contabilizan(self):
        self.post('incorrecta')
        self.assertEqual(IntentoLoginOrigen.objects.get().fallos, 1)

    def test_usuario_correcto_entra_normalmente(self):
        resp = self.post('Seguro-A2-2026!')
        self.assertEqual(resp.status_code, 302)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_exito_tras_fallo_limpia_contador(self):
        self.post('incorrecta')
        self.post('Seguro-A2-2026!')
        self.assertFalse(IntentoLoginOrigen.objects.exists())

    def test_limite_no_valida_contrasena_correcta(self):
        for _ in range(MAX_FALLOS):
            self.post('incorrecta')
        resp = self.post('Seguro-A2-2026!')
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_otro_origen_no_queda_bloqueado(self):
        for _ in range(MAX_FALLOS):
            self.post('incorrecta')
        resp = self.post('Seguro-A2-2026!', ip='192.0.2.23')
        self.assertEqual(resp.status_code, 302)

    def test_limite_expira(self):
        for _ in range(MAX_FALLOS):
            self.post('incorrecta')
        IntentoLoginOrigen.objects.update(inicio_ventana=timezone.now() - timedelta(minutes=11))
        self.assertEqual(self.post('Seguro-A2-2026!').status_code, 302)

    def test_no_guarda_ip_en_claro(self):
        self.post('incorrecta')
        item = IntentoLoginOrigen.objects.get()
        self.assertNotIn('192.0.2.22', item.origen)
        self.assertEqual(len(item.origen), 64)

    def test_no_confia_en_x_forwarded_for_sin_proxy_permitido(self):
        self.post('incorrecta')
        self.client.post(self.url, {'username': 'acceso_a2', 'password': 'mala'},
                         REMOTE_ADDR='192.0.2.22', HTTP_X_FORWARDED_FOR='203.0.113.9')
        self.assertEqual(IntentoLoginOrigen.objects.count(), 1)
        self.assertEqual(IntentoLoginOrigen.objects.get().fallos, 2)
