"""B13: pruebas de configuracion productiva, sin DB/proxy/SMTP reales.

La infraestructura no se simula como certificada. Verifica invariantes del codigo.
"""
import os
import runpy
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import Resolver404, resolve


class ConfiguracionProduccionB13Tests(SimpleTestCase):
    def setUp(self):
        self.directorios = tempfile.TemporaryDirectory(prefix="ordena_b13_test_")
        self.addCleanup(self.directorios.cleanup)
        self.root = Path(self.directorios.name)
        self.publico = self.root / "publico" / "static"
        self.privado = self.root / "privado" / "media"
        self.entorno = {
            "ORDENACLICK_ALLOWED_HOSTS": "beta.example.test",
            "ORDENACLICK_CSRF_TRUSTED_ORIGINS": "https://beta.example.test",
            "ORDENACLICK_DB_NAME": "auditoria_b13",
            "ORDENACLICK_DB_USER": "solo_prueba",
            "ORDENACLICK_DB_PASSWORD": "no-es-clave-real",
            "ORDENACLICK_DB_HOST": "127.0.0.1",
            "ORDENACLICK_PRIVATE_MEDIA_ROOT": str(self.privado),
            "ORDENACLICK_STATIC_ROOT": str(self.publico),
            "ORDENACLICK_SMTP_HOST": "localhost",
            "ORDENACLICK_SMTP_USER": "solo_prueba",
            "ORDENACLICK_SMTP_PASSWORD": "no-es-clave-real",
            "ORDENACLICK_EMAIL_FROM": "no-reply@example.test",
        }

    def cargar(self, cambios=None, retirar=()):
        entorno = dict(self.entorno)
        entorno.update(cambios or {})
        for key in retirar:
            entorno.pop(key, None)
        with patch.dict(os.environ, entorno, clear=False):
            for key in retirar:
                os.environ.pop(key, None)
            return runpy.run_module("ordenaclick.settings_production")

    def test_produccion_tiene_directorios_privados_y_publicos_separados(self):
        s = self.cargar()
        self.assertEqual(s["STATIC_ROOT"], self.publico.resolve())
        self.assertEqual(s["MEDIA_ROOT"], self.privado.resolve())
        self.assertFalse(s["DEBUG"])
        self.assertTrue(s["SESSION_COOKIE_SECURE"])
        self.assertTrue(s["CSRF_COOKIE_SECURE"])
        self.assertTrue(s["SECURE_SSL_REDIRECT"])
        self.assertEqual(s["DATABASES"]["default"]["ENGINE"], "django.db.backends.postgresql")
        self.assertIn("django.middleware.csp.ContentSecurityPolicyMiddleware", s["MIDDLEWARE"])
        self.assertTrue(s["SECURE_CSP_REPORT_ONLY"])
        self.assertEqual(s["SECURE_HSTS_SECONDS"], 0)  # Pendiente de HTTPS real.

    def test_sin_static_root_explicito_falla_cerrado(self):
        with self.assertRaisesRegex(RuntimeError, "ORDENACLICK_STATIC_ROOT"):
            self.cargar(retirar=("ORDENACLICK_STATIC_ROOT",))

    def test_publico_no_puede_ser_privado(self):
        with self.assertRaisesRegex(RuntimeError, "no pueden solaparse"):
            self.cargar({"ORDENACLICK_STATIC_ROOT": str(self.privado)})

    def test_publico_no_puede_contener_privado(self):
        with self.assertRaisesRegex(RuntimeError, "no pueden solaparse"):
            self.cargar({"ORDENACLICK_STATIC_ROOT": str(self.root)})

    def test_privado_no_puede_contener_publico(self):
        with self.assertRaisesRegex(RuntimeError, "no pueden solaparse"):
            self.cargar({"ORDENACLICK_PRIVATE_MEDIA_ROOT": str(self.root)})

    def test_static_no_puede_estar_en_proyecto(self):
        from django.conf import settings
        destino = Path(settings.BASE_DIR) / "static_b13_no_crear"
        with self.assertRaisesRegex(RuntimeError, "fuera del proyecto"):
            self.cargar({"ORDENACLICK_STATIC_ROOT": str(destino)})

    def test_no_se_publica_directorio_media_por_urls(self):
        with self.assertRaises(Resolver404):
            resolve("/media/empresa-ajena/documento.pdf")

    def test_hosts_y_origenes_no_admiten_wildcard_global(self):
        with self.assertRaises(RuntimeError):
            self.cargar({"ORDENACLICK_ALLOWED_HOSTS": "*"})
        with self.assertRaises(RuntimeError):
            self.cargar({"ORDENACLICK_CSRF_TRUSTED_ORIGINS": "https://*.example.test"})
