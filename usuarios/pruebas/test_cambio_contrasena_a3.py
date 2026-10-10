from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import PerfilUsuario


class CambioContrasenaA3Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="a3_usuario", email="actual@example.com", password="ClaveActual!9347"
        )
        PerfilUsuario.objects.create(
            user=self.user, nombre="Ana", apellido="Prueba", estado_acceso="activo"
        )
        self.url = reverse("modificar_usuario")
        self.client.force_login(self.user)

    def datos(self, **extras):
        return {
            "nombre": "Ana", "apellido": "Prueba", "email": "actual@example.com",
            "telefono_personal": "", "telefono_laboral": "", "direccion_laboral": "",
            "password": "", "password_actual": "", **extras,
        }

    def test_datos_personales_no_requieren_contrasena(self):
        respuesta = self.client.post(self.url, self.datos(nombre="Beatriz"))
        self.assertRedirects(respuesta, reverse("home"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Beatriz")
        self.assertTrue(self.user.check_password("ClaveActual!9347"))

    def test_nueva_contrasena_exige_actual(self):
        respuesta = self.client.post(self.url, self.datos(password="NuevaClave!9347"))
        self.assertEqual(respuesta.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("ClaveActual!9347"))

    def test_contrasena_actual_incorrecta_no_guarda_otros_datos(self):
        respuesta = self.client.post(self.url, self.datos(
            nombre="NombreNoGuardado", password="NuevaClave!9347", password_actual="incorrecta"
        ))
        self.assertEqual(respuesta.status_code, 200)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.first_name, "NombreNoGuardado")
        self.assertTrue(self.user.check_password("ClaveActual!9347"))

    def test_nueva_contrasena_debil_rechazada(self):
        respuesta = self.client.post(self.url, self.datos(
            password="123", password_actual="ClaveActual!9347"
        ))
        self.assertEqual(respuesta.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("ClaveActual!9347"))

    def test_cambio_valido_preserva_sesion(self):
        respuesta = self.client.post(self.url, self.datos(
            password="NuevaClave!9347", password_actual="ClaveActual!9347"
        ))
        self.assertRedirects(respuesta, reverse("home"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NuevaClave!9347"))
        self.assertEqual(str(self.client.session.get("_auth_user_id")), str(self.user.pk))
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_formulario_incluye_campo_actual(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'name="password_actual"')

    def test_repetir_contrasena_actual_no_guarda_y_atiende_el_error(self):
        original_hash = self.user.password
        respuesta = self.client.post(self.url, self.datos(
            nombre="CambioNoGuardado", password="ClaveActual!9347",
            password_actual="ClaveActual!9347",
        ))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "debe ser distinta")
        self.user.refresh_from_db()
        self.assertEqual(self.user.password, original_hash)
        self.assertNotEqual(self.user.first_name, "CambioNoGuardado")

    def test_contrasena_erronea_conserva_datos_ingresados(self):
        respuesta = self.client.post(self.url, self.datos(
            nombre="Nombre Editado", apellido="Apellido Editado",
            email="editado@example.com", telefono_personal="1155566677",
            telefono_laboral="1144455566", direccion_laboral="Oficina Nueva",
            password="NuevaClave!9347", password_actual="erronea",
        ))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'value="Nombre Editado"')
        self.assertContains(respuesta, 'value="Apellido Editado"')
        self.assertContains(respuesta, 'value="editado@example.com"')
        self.assertContains(respuesta, 'value="1155566677"')
        self.assertContains(respuesta, 'value="1144455566"')
        self.assertContains(respuesta, 'value="Oficina Nueva"')
        self.assertNotContains(respuesta, 'value="erronea"')
        self.assertNotContains(respuesta, 'value="NuevaClave!9347"')
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.first_name, "Nombre Editado")

    def test_password_debil_preserva_datos_ingresados(self):
        respuesta = self.client.post(self.url, self.datos(
            nombre="Persistir Nombre", password="123",
            password_actual="ClaveActual!9347",
        ))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'value="Persistir Nombre"')

    def test_anonimo_redirigido(self):
        self.client.logout()
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 302)
