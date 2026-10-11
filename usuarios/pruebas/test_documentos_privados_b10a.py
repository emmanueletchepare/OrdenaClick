"""B10a: regresiones adversariales de descarga de documentos legales privados."""
import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from usuarios.models import Empresa


class DescargasPrivadasB10aTests(TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        setting = override_settings(MEDIA_ROOT=Path(tmp.name))
        setting.enable()
        self.addCleanup(setting.disable)
        self.duenio = User.objects.create_user(username="duenio_b10a", password="test12345")
        self.otro = User.objects.create_user(username="otro_b10a", password="test12345")
        self.empresa = Empresa.objects.create(propietario=self.duenio, razon_social="Privada B10a")
        Empresa.objects.create(propietario=self.otro, razon_social="Ajena B10a")

    def test_propietario_de_otra_empresa_no_lee_documento(self):
        self.empresa.estatuto.save("privado.pdf", ContentFile(b"dato interno"), save=True)
        self.client.force_login(self.otro)
        url = reverse("descargar_documento_empresa", args=[self.empresa.pk, "estatuto"])
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 403)

    def test_html_se_ofrece_como_adjunto_no_como_pagina(self):
        self.empresa.estatuto.save("contenido.html", ContentFile(b"<script>alert(1)</script>"), save=True)
        self.client.force_login(self.duenio)
        url = reverse("descargar_documento_empresa", args=[self.empresa.pk, "estatuto"])
        respuesta = self.client.get(url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "application/octet-stream")
        self.assertTrue(respuesta["Content-Disposition"].startswith("attachment;"))
        self.assertEqual(respuesta["X-Content-Type-Options"], "nosniff")
        respuesta.close()
