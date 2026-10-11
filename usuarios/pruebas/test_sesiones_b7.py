"""B7: pruebas HTTP de ciclo de sesion y estados de acceso.

No implementa recuperacion de cuenta ni prueba expiracion real del navegador.
"""
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from usuarios.models import PerfilUsuario


class AuditoriaSesionesB7Tests(TestCase):
    def setUp(self):
        self.password = 'ClaveSeguraB7!2834'
        self.usuario = User.objects.create_user(
            username='usuario_b7', email='b7@example.test', password=self.password,
        )
        self.perfil = PerfilUsuario.objects.create(
            user=self.usuario, nombre='Usuario', apellido='B7', estado_acceso='activo',
        )

    def iniciar(self):
        return self.client.post(reverse('login'), {
            'username': self.usuario.username, 'password': self.password,
        })

    def test_login_valido_abre_sesion(self):
        respuesta = self.iniciar()
        self.assertRedirects(respuesta, reverse('home'))
        self.assertEqual(str(self.client.session.get('_auth_user_id')), str(self.usuario.pk))
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)

    def test_logout_invalida_sesion_y_home_requiere_login(self):
        self.iniciar()
        respuesta = self.client.post(reverse('logout'))
        self.assertRedirects(respuesta, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get(reverse('home')).status_code, 302)

    def test_contrasena_incorrecta_no_abre_sesion(self):
        respuesta = self.client.post(reverse('login'), {
            'username': self.usuario.username, 'password': 'Incorrecta!2834',
        })
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get(reverse('home')).status_code, 302)

    def test_perfil_bloqueado_no_abre_sesion(self):
        self.perfil.estado_acceso = 'bloqueado'
        self.perfil.save(update_fields=['estado_acceso'])
        respuesta = self.iniciar()
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_perfil_pendiente_no_abre_sesion(self):
        self.perfil.estado_acceso = 'pendiente'
        self.perfil.save(update_fields=['estado_acceso'])
        respuesta = self.iniciar()
        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_baja_desactiva_cuenta_y_cierra_sesion(self):
        self.iniciar()
        respuesta = self.client.post(reverse('baja_usuario'))
        self.assertRedirects(respuesta, reverse('login'))
        self.usuario.refresh_from_db()
        self.perfil.refresh_from_db()
        self.assertFalse(self.usuario.is_active)
        self.assertEqual(self.perfil.estado_acceso, 'bloqueado')
        self.assertNotIn('_auth_user_id', self.client.session)
        respuesta_nueva = self.iniciar()
        self.assertEqual(respuesta_nueva.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    @override_settings(SESSION_EXPIRE_AT_BROWSER_CLOSE=True)
    def test_sesion_configurada_para_cierre_de_navegador(self):
        self.iniciar()
        self.assertTrue(self.client.session.get_expire_at_browser_close())
