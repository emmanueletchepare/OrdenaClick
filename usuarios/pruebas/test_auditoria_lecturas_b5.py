"""B5: aislamiento HTTP de consultas financieras y alertas.

No modifica vistas ni reemplaza la auditoría integral de rutas.
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Empresa, Ejercicio, Movimiento


class AuditoriaLecturasB5Tests(TestCase):
    def setUp(self):
        self.dueno = User.objects.create_user(username="b5_dueno", password="B5-clave-123!")
        self.ajeno = User.objects.create_user(username="b5_ajeno", password="B5-clave-123!")
        self.empresa = Empresa.objects.create(razon_social="B5 Propia", propietario=self.dueno)
        self.otra = Empresa.objects.create(razon_social="B5 Ajena", propietario=self.ajeno)
        ejercicio = Ejercicio.objects.create(
            empresa=self.otra, numero=2026,
            fecha_inicio=date(2026, 1, 1), fecha_cierre=date(2026, 12, 31),
        )
        self.movimiento_ajeno = Movimiento.objects.create(
            empresa=self.otra, ejercicio=ejercicio,
            fecha_registro=date(2026, 10, 10), fecha_vencimiento=date(2026, 10, 10),
            modalidad_pago="Manual", total=Decimal("12345.67"),
            importe=Decimal("12345.67"), estado="Pendiente",
        )
        self.client.force_login(self.dueno)

    def test_anonimo_no_puede_consultar_vencimientos(self):
        self.client.logout()
        respuesta = self.client.get(reverse("listar_proximos_vencimientos"), {"empresa": self.otra.pk})
        self.assertEqual(respuesta.status_code, 302)

    def test_anonimo_no_puede_consultar_llamador(self):
        self.client.logout()
        respuesta = self.client.get(reverse("estado_llamador_alertas"), {"empresa": self.otra.pk})
        self.assertEqual(respuesta.status_code, 302)

    def test_anonimo_no_puede_consultar_edicion(self):
        self.client.logout()
        respuesta = self.client.get(reverse("obtener_movimiento_edicion"), {
            "empresa": self.otra.pk, "movimiento": self.movimiento_ajeno.pk,
        })
        self.assertEqual(respuesta.status_code, 302)

    def test_no_puede_listar_vencimientos_de_empresa_ajena(self):
        for periodo in ("hoy", "semana", "alertas", "rango"):
            with self.subTest(periodo=periodo):
                respuesta = self.client.get(reverse("listar_proximos_vencimientos"), {
                    "empresa": self.otra.pk, "periodo": periodo,
                    "fecha_desde": "2026-01-01", "fecha_hasta": "2026-12-31",
                })
                self.assertEqual(respuesta.status_code, 403)

    def test_no_puede_consultar_alertas_de_empresa_ajena(self):
        respuesta = self.client.get(reverse("estado_llamador_alertas"), {"empresa": self.otra.pk})
        self.assertEqual(respuesta.status_code, 403)

    def test_no_puede_consultar_movimiento_ajeno_con_empresa_propia(self):
        respuesta = self.client.get(reverse("obtener_movimiento_edicion"), {
            "empresa": self.empresa.pk, "movimiento": self.movimiento_ajeno.pk,
        })
        self.assertEqual(respuesta.status_code, 404)
        self.assertNotIn(b"12345.67", respuesta.content)

    def test_no_puede_consultar_movimiento_ajeno_con_empresa_ajena(self):
        respuesta = self.client.get(reverse("obtener_movimiento_edicion"), {
            "empresa": self.otra.pk, "movimiento": self.movimiento_ajeno.pk,
        })
        self.assertEqual(respuesta.status_code, 403)
        self.assertNotIn(b"12345.67", respuesta.content)
