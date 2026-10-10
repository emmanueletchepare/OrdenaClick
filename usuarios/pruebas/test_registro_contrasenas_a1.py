from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class ValidacionContrasenasRegistroA1Tests(TestCase):
    def setUp(self):
        self.url = reverse("registro")
        self.datos = {
            "username": "usuario_nuevo",
            "email": "nuevo@example.com",
            "password": "ClaveRobusta!2026-XYZ",
            "password2": "ClaveRobusta!2026-XYZ",
            "nombre": "Persona",
            "apellido": "Ejemplo",
        }

    def test_contrasena_robusta_permite_registro(self):
        respuesta = self.client.post(self.url, self.datos)
        self.assertRedirects(respuesta, reverse("login"))
        usuario = User.objects.get(username="usuario_nuevo")
        self.assertTrue(usuario.check_password(self.datos["password"]))

    def test_contrasena_corta_se_rechaza(self):
        datos = {**self.datos, "password": "corta", "password2": "corta"}
        respuesta = self.client.post(self.url, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(User.objects.filter(username="usuario_nuevo").count(), 0)
        self.assertContains(respuesta, "8")

    def test_contrasena_comun_se_rechaza(self):
        datos = {**self.datos, "password": "password", "password2": "password"}
        respuesta = self.client.post(self.url, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.filter(username="usuario_nuevo").exists())

    def test_contrasena_solo_numeros_se_rechaza(self):
        datos = {**self.datos, "password": "123456789123", "password2": "123456789123"}
        respuesta = self.client.post(self.url, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.filter(username="usuario_nuevo").exists())

    def test_contrasena_similar_al_usuario_se_rechaza(self):
        datos = {**self.datos, "password": "usuario_nuevo", "password2": "usuario_nuevo"}
        respuesta = self.client.post(self.url, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.filter(username="usuario_nuevo").exists())

    def test_contrasenas_distintas_siguen_rechazadas(self):
        datos = {**self.datos, "password2": "OtraClaveRobusta!2026"}
        respuesta = self.client.post(self.url, datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.filter(username="usuario_nuevo").exists())
