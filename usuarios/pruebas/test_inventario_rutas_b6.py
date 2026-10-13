"""B6: cobertura dinamica de autenticacion de las rutas activas.

Complementa el inventario manual. No certifica permisos entre Empresas,
CSRF, metodos HTTP ni autorizacion de roles: tienen auditorias separadas.
"""

from urllib.parse import parse_qs, urlsplit

from django.test import TestCase
from django.urls import reverse

from usuarios.urls import urlpatterns


class InventarioDinamicoRutasB6Tests(TestCase):
    PUBLICAS = {"login", "registro", "recuperar_contrasena", "recuperar_contrasena_enviada", "recuperar_contrasena_confirmar", "recuperar_contrasena_completada"}
    PARAMETROS = {
        "empresa_id": 999999,
        "pendiente_id": 999999,
        "movimiento_id": 999999,
        "solicitud_id": 999999,
        "perfil": "administrador",
        "accion": "aceptar",
        "paso": "empresa",
        "campo": "estatuto",
        "tipo": "bancos",
    }

    def rutas_privadas(self):
        for patron in urlpatterns:
            nombre = patron.name
            if nombre in self.PUBLICAS:
                continue
            self.assertIsNotNone(nombre, f"Ruta sin nombre: {patron}")
            parametros = {
                clave: self.PARAMETROS[clave]
                for clave in patron.pattern.converters
            }
            yield nombre, reverse(nombre, kwargs=parametros)

    def test_existen_rutas_privadas_para_auditar(self):
        rutas = list(self.rutas_privadas())
        self.assertGreater(len(rutas), 50)
        self.assertEqual(len(rutas), len({nombre for nombre, _ in rutas}))

    def test_todas_las_rutas_privadas_rechazan_anonimos_por_get_y_post(self):
        for nombre, ruta in self.rutas_privadas():
            for metodo in ("get", "post"):
                with self.subTest(ruta=nombre, metodo=metodo):
                    respuesta = getattr(self.client, metodo)(ruta)
                    self.assertEqual(
                        respuesta.status_code, 302,
                        f"{nombre} acepto {metodo.upper()} anonimo: "
                        f"HTTP {respuesta.status_code}",
                    )
                    destino = urlsplit(respuesta["Location"])
                    self.assertEqual(destino.path, reverse("login"))
                    self.assertIn("next", parse_qs(destino.query))
