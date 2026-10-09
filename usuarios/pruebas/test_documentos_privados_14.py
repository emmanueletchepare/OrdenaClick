import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from usuarios.models import Empresa


class DocumentosPrivadosEmpresa14Tests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.override = override_settings(MEDIA_ROOT=Path(self.temp.name))
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.duenio = User.objects.create_user(username="duenio14", password="prueba123")
        self.ajeno = User.objects.create_user(username="ajeno14", password="prueba123")
        self.superusuario = User.objects.create_superuser(username="root14", email="root14@example.com", password="prueba123")
        self.empresa = Empresa.objects.create(propietario=self.duenio, razon_social="Empresa documentada")
        self.empresa.estatuto.save("estatuto.pdf", ContentFile(b"%PDF-1.4 test"), save=True)
        self.url = reverse("descargar_documento_empresa", args=[self.empresa.pk, "estatuto"])

    def test_anonimo_redirigido_al_login(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_usuario_ajeno_denegado(self):
        self.client.force_login(self.ajeno)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_propietario_descarga_sin_cambio_de_flujo(self):
        self.client.force_login(self.duenio)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(b"".join(respuesta.streaming_content), b"%PDF-1.4 test")
        self.assertIn("inline", respuesta["Content-Disposition"])
        self.assertEqual(respuesta["X-Content-Type-Options"], "nosniff")
        self.assertIn("no-cache", respuesta["Cache-Control"])

    def test_superusuario_conserva_excepcion(self):
        self.client.force_login(self.superusuario)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        respuesta.close()

    def test_campo_no_permitido(self):
        self.client.force_login(self.duenio)
        url = reverse("descargar_documento_empresa", args=[self.empresa.pk, "propietario"])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_archivo_ausente(self):
        self.client.force_login(self.duenio)
        url = reverse("descargar_documento_empresa", args=[self.empresa.pk, "acta"])
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_solo_get(self):
        self.client.force_login(self.duenio)
        self.assertEqual(self.client.post(self.url).status_code, 405)
