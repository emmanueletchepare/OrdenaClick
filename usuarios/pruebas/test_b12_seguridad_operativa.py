"""B12: recuperación, aislamiento de contadores y privacidad de media.

Ejecutar sobre DB de prueba. Ningún test requiere SMTP, proxy ni servidor público.
"""
import importlib
import os
import re
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import Resolver404, resolve, reverse
from django.utils.csp import CSP
from django.middleware.csp import ContentSecurityPolicyMiddleware

from usuarios.models import PerfilUsuario
from usuarios.services.limite_login import bloqueado, registrar_fallo


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PASSWORD_RESET_TIMEOUT=1800,
)
class RecuperacionB12Tests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="b12_recuperacion", email="usuario-b12@example.test",
            password="ClaveInicialB12!2026",
        )
        PerfilUsuario.objects.create(
            user=self.usuario, nombre="B12", apellido="Prueba",
            estado_acceso="activo",
        )

    def test_enlace_existente_del_login_ya_funciona(self):
        respuesta = self.client.get(reverse("login"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, reverse("recuperar_contrasena"))
        self.assertContains(respuesta, "No recuerdo mi contraseña")

    def test_recuperacion_es_publica_y_usa_metodo_get_para_mostrar_formulario(self):
        respuesta = self.client.get(reverse("recuperar_contrasena"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'name="email"')
        self.assertContains(respuesta, 'name="csrfmiddlewaretoken"')

    def test_respuesta_generica_sin_enumeracion_de_cuentas(self):
        url = reverse("recuperar_contrasena")
        desconocido = self.client.post(url, {"email": "otro-b12@example.test"})
        self.assertRedirects(desconocido, reverse("recuperar_contrasena_enviada"))
        self.assertEqual(len(mail.outbox), 0)
        conocido = self.client.post(url, {"email": self.usuario.email})
        self.assertRedirects(conocido, reverse("recuperar_contrasena_enviada"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.usuario.email])
        self.assertNotIn("ClaveInicialB12!2026", mail.outbox[0].body)

    def test_enlace_de_un_solo_uso_cambia_password_y_no_automaticamente_la_sesion(self):
        with self.assertLogs("ordenaclick.audit", level="INFO") as registros:
            respuesta = self.client.post(
                reverse("recuperar_contrasena"), {"email": self.usuario.email},
            )
        self.assertEqual(respuesta.status_code, 302)
        self.assertNotIn(self.usuario.email, " ".join(registros.output))
        self.assertEqual(len(mail.outbox), 1)
        enlace = re.search(r"https?://testserver(/recuperar-contrasena/confirmar/[^\s]+/)", mail.outbox[0].body)
        self.assertIsNotNone(enlace)
        ruta_token = enlace.group(1)
        primer_acceso = self.client.get(ruta_token)
        self.assertEqual(primer_acceso.status_code, 302)
        ruta_formulario = primer_acceso["Location"]
        self.assertIn("set-password", ruta_formulario)
        nueva = "ClaveRenovadaB12!2030"
        with self.assertLogs("ordenaclick.audit", level="INFO") as registros:
            respuesta = self.client.post(ruta_formulario, {
                "new_password1": nueva, "new_password2": nueva,
            })
        self.assertRedirects(respuesta, reverse("recuperar_contrasena_completada"))
        self.assertIn("auth.password_reset_completed", " ".join(registros.output))
        self.assertNotIn(nueva, " ".join(registros.output))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password(nueva))
        self.assertNotIn("_auth_user_id", self.client.session)
        # El token usado no vuelve a servir para modificar la contraseña.
        respuesta_repetida = self.client.get(ruta_token)
        self.assertEqual(respuesta_repetida.status_code, 200)
        self.assertContains(respuesta_repetida, "no es válido")

    def test_cuenta_inactiva_no_recibe_recuperacion(self):
        self.usuario.is_active = False
        self.usuario.save(update_fields=["is_active"])
        respuesta = self.client.post(
            reverse("recuperar_contrasena"), {"email": self.usuario.email},
        )
        self.assertRedirects(respuesta, reverse("recuperar_contrasena_enviada"))
        self.assertEqual(len(mail.outbox), 0)

    def test_restauracion_rechaza_post_sin_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        respuesta = cliente.post(reverse("recuperar_contrasena"), {"email": self.usuario.email})
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(len(mail.outbox), 0)

    def test_tasa_recuperacion_independiente_del_login_y_registro(self):
        solicitud = RequestFactory().post(
            reverse("recuperar_contrasena"), REMOTE_ADDR="203.0.113.28",
        )
        for _ in range(25):
            registrar_fallo(solicitud, contexto="recuperacion")
        self.assertTrue(bloqueado(solicitud, contexto="recuperacion"))
        self.assertFalse(bloqueado(solicitud))
        self.assertFalse(bloqueado(solicitud, contexto="registro"))

    def test_recuperacion_limitada_no_emite_mas_correos(self):
        url = reverse("recuperar_contrasena")
        # Precargar el bucket para no enviar 25 emails de prueba.
        solicitud = RequestFactory().post(url, REMOTE_ADDR="198.51.100.9")
        for _ in range(25):
            registrar_fallo(solicitud, contexto="recuperacion")
        respuesta = self.client.post(
            url, {"email": self.usuario.email}, REMOTE_ADDR="198.51.100.9",
        )
        self.assertRedirects(respuesta, reverse("recuperar_contrasena_enviada"))
        self.assertEqual(len(mail.outbox), 0)

    def test_registro_limitado_preserva_datos_no_sensibles(self):
        solicitud = RequestFactory().post(reverse("registro"), REMOTE_ADDR="198.51.100.19")
        for _ in range(25):
            registrar_fallo(solicitud, contexto="registro")
        respuesta = self.client.post(reverse("registro"), {
            "username": "usuario_nuevo_b12", "email": "nuevo-b12@example.test",
            "nombre": "Laura", "apellido": "Prueba",
            "password": "NoImprimirB12!", "password2": "NoImprimirB12!",
        }, REMOTE_ADDR="198.51.100.19")
        self.assertEqual(respuesta.status_code, 429)
        self.assertContains(respuesta, "Laura", status_code=429)
        self.assertNotContains(respuesta, 'value="NoImprimirB12!"', status_code=429)
        self.assertFalse(User.objects.filter(username="usuario_nuevo_b12").exists())


class ProteccionMediaB12Tests(SimpleTestCase):
    def test_media_generico_no_tiene_ruta_publica_en_desarrollo(self):
        with self.assertRaises(Resolver404):
            resolve("/media/importaciones/backup-sensible.zip")

    def test_descarga_privada_legal_conserva_su_ruta(self):
        self.assertTrue(reverse("descargar_documento_empresa", kwargs={
            "empresa_id": 13, "campo": "estatuto",
        }).startswith("/empresa/13/documentos/"))

    def test_csp_modo_reporte_no_bloquea_scripts_ni_estilos(self):
        politica = {"default-src": [CSP.SELF], "script-src": [CSP.SELF]}
        with override_settings(SECURE_CSP_REPORT_ONLY=politica, SECURE_CSP={}):
            middleware = ContentSecurityPolicyMiddleware(lambda _request: HttpResponse("ok"))
            respuesta = middleware(RequestFactory().get("/login/"))
        self.assertIn("Content-Security-Policy-Report-Only", respuesta)
        self.assertNotIn("Content-Security-Policy", respuesta)
        self.assertEqual(respuesta.content, b"ok")

    def test_produccion_exige_smtp_y_mantiene_hsts_diferido(self):
        variables = {
            "ORDENACLICK_ALLOWED_HOSTS": "ordenaclick.example.test",
            "ORDENACLICK_CSRF_TRUSTED_ORIGINS": "https://ordenaclick.example.test",
            "ORDENACLICK_DB_NAME": "db_b12",
            "ORDENACLICK_DB_USER": "user_b12",
            "ORDENACLICK_DB_PASSWORD": "dummy-not-real",
            "ORDENACLICK_DB_HOST": "127.0.0.1",
            "ORDENACLICK_PRIVATE_MEDIA_ROOT": str(Path(tempfile.gettempdir()) / "ordenaclick-b12-private"),
            "ORDENACLICK_STATIC_ROOT": str(Path(tempfile.gettempdir()) / "ordenaclick-b12-static"),
            "ORDENACLICK_SMTP_HOST": "smtp.example.test",
            "ORDENACLICK_SMTP_USER": "dummy",
            "ORDENACLICK_SMTP_PASSWORD": "dummy-not-real",
            "ORDENACLICK_EMAIL_FROM": "no-reply@ordenaclick.example.test",
        }
        with patch.dict(os.environ, variables):
            produccion = importlib.import_module("ordenaclick.settings_production")
            produccion = importlib.reload(produccion)
        self.assertFalse(produccion.DEBUG)
        self.assertTrue(produccion.SESSION_COOKIE_SECURE)
        self.assertTrue(produccion.CSRF_COOKIE_SECURE)
        self.assertEqual(produccion.SECURE_HSTS_SECONDS, 0)
        self.assertIn("django.middleware.csp.ContentSecurityPolicyMiddleware", produccion.MIDDLEWARE)
        self.assertIn("default-src", produccion.SECURE_CSP_REPORT_ONLY)
        self.assertEqual(produccion.EMAIL_HOST, "smtp.example.test")
        self.assertNotIn("ContentSecurityPolicyMiddleware", __import__("ordenaclick.settings", fromlist=["MIDDLEWARE"]).MIDDLEWARE)


class CierreSesionB12Tests(TestCase):
    """GET jamás destruye la sesión; los botones actuales usan POST y CSRF."""

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="usuario_b12_logout", password="ClaveB12Logout!2026",
        )
        PerfilUsuario.objects.create(
            user=self.usuario, nombre="B12", apellido="Logout", estado_acceso="activo",
        )

    def test_get_no_cierra_la_sesion(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse("logout"))
        self.assertEqual(respuesta.status_code, 405)
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(self.usuario.pk))
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_post_cierra_y_regresa_al_login(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse("logout"))
        self.assertRedirects(respuesta, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_post_sin_csrf_no_cierra(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.usuario)
        respuesta = cliente.post(reverse("logout"))
        self.assertEqual(respuesta.status_code, 403)
        self.assertIn("_auth_user_id", cliente.session)
        # GET de Home coloca CSRF para el botón existente.
        pagina = cliente.get(reverse("home"))
        self.assertEqual(pagina.status_code, 200)
        token = cliente.cookies["csrftoken"].value
        resultado = cliente.post(reverse("logout"), HTTP_X_CSRFTOKEN=token)
        self.assertRedirects(resultado, reverse("login"))
        self.assertNotIn("_auth_user_id", cliente.session)

    def test_pantallas_tienen_formulario_post_y_no_link_get_logout(self):
        self.client.force_login(self.usuario)
        for nombre in ("home", "panel_admin", "panel_colaborador", "panel_contable", "panel_legal"):
            with self.subTest(pantalla=nombre):
                pagina = self.client.get(reverse(nombre))
                self.assertEqual(pagina.status_code, 200)
                self.assertContains(pagina, f'action="{reverse("logout")}"')
                self.assertNotContains(pagina, f'href="{reverse("logout")}"')
                self.assertContains(pagina, 'name="csrfmiddlewaretoken"')
