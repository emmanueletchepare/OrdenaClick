import json
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from django.urls import reverse

from django.test import SimpleTestCase

from usuarios.services.financiero import (
    ESTADO_PAGADO,
    ESTADO_PARCIAL,
    ESTADO_PENDIENTE,
    estado_financiero_movimiento,
    saldo_pendiente_movimiento,
    total_aplicado_movimiento,
    VENCIMIENTO_FUTURO,
    VENCIMIENTO_HOY,
    VENCIMIENTO_PAGADO,
    VENCIMIENTO_SIN_FECHA,
    VENCIMIENTO_VENCIDO,
    estado_vencimiento_movimiento,
    resumen_financiero_movimiento,
    DIAS_ANTICIPACION_ALERTA,
    movimientos_en_alerta,
)

from usuarios.services.pagos import (
    validar_pago_movimiento,
)

from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.test import Client, TestCase

from usuarios.models import (
    AplicacionPago,
    CentroOperativo,
    Cliente,
    Empresa,
    Ejercicio,
    Movimiento,
    Pago,
)

from usuarios.services.seguridad import (
    cajas_autorizadas,
    empresas_autorizadas,
    obtener_caja_autorizada,
    obtener_centro_autorizado,
    obtener_empresa_administrable,
    obtener_empresa_autorizada,
)

class ProximosVencimientosViewTests(TestCase):
    """
    Prueba el comportamiento HTTP de la vista
    de Próximos Vencimientos.
    """

    def setUp(self):
        """
        Crea el usuario, la empresa y el ejercicio
        necesarios para probar la vista.
        """

        self.usuario = User.objects.create_user(
            username="usuario_vencimientos",
            password="clave-prueba-123",
        )

        self.empresa = Empresa.objects.create(
            razon_social="Empresa Vencimientos",
            propietario=self.usuario,
        )

        self.ejercicio = Ejercicio.objects.create(
            empresa=self.empresa,
            numero=2026,
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 12, 31),
        )

        self.client.force_login(
            self.usuario
        )

    def test_hoy_incluye_movimiento_vencido_con_saldo(self):
        """
        El período Hoy mantiene visible una obligación
        vencida que todavía posee saldo pendiente.
        """

        from datetime import timedelta

        movimiento = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date.today(),
            fecha_vencimiento=(
                date.today() - timedelta(days=1)
            ),
            total=Decimal("1000.00"),
            importe=Decimal("1000.00"),
            estado="Pendiente",
        )

        respuesta = self.client.get(
            reverse(
                "listar_proximos_vencimientos"
            ),
            {
                "empresa": self.empresa.id,
                "periodo": "hoy",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        datos = respuesta.json()

        ids_movimientos = [
            item["id"]
            for item in datos["movimientos"]
        ]

        self.assertIn(
            movimiento.id,
            ids_movimientos,
        )

    def test_alertas_respeta_politica_de_tres_dias(self):
        """
        El endpoint de Próximos Vencimientos debe utilizar
        la política central de Alertas.

        Un Movimiento que vence dentro de tres días debe
        aparecer y uno que vence dentro de cuatro días no.
        """

        from datetime import timedelta

        movimiento_tres_dias = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date.today(),
            fecha_vencimiento=(
                date.today() + timedelta(days=3)
            ),
            total=Decimal("1000.00"),
            importe=Decimal("1000.00"),
            estado="Pendiente",
        )

        movimiento_cuatro_dias = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date.today(),
            fecha_vencimiento=(
                date.today() + timedelta(days=4)
            ),
            total=Decimal("2000.00"),
            importe=Decimal("2000.00"),
            estado="Pendiente",
        )

        respuesta = self.client.get(
            reverse(
                "listar_proximos_vencimientos"
            ),
            {
                "empresa": self.empresa.id,
                "periodo": "alertas",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        datos = respuesta.json()

        self.assertTrue(
            datos["ok"]
        )

        self.assertEqual(
            datos["periodo"],
            "alertas",
        )

        ids_movimientos = {
            item["id"]
            for item in datos["movimientos"]
        }

        self.assertIn(
            movimiento_tres_dias.id,
            ids_movimientos,
        )

        self.assertNotIn(
            movimiento_cuatro_dias.id,
            ids_movimientos,
        )

    def test_endpoint_informa_estado_de_vencimiento(self):
        """
        El endpoint debe informar explícitamente el estado
        temporal de cada obligación para que la interfaz
        no tenga que recalcular reglas de vencimiento.
        """

        from datetime import timedelta

        movimiento_vencido = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date.today(),
            fecha_vencimiento=(
                date.today() - timedelta(days=1)
            ),
            total=Decimal("1000.00"),
            importe=Decimal("1000.00"),
            estado="Pendiente",
        )

        movimiento_hoy = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date.today(),
            fecha_vencimiento=date.today(),
            total=Decimal("2000.00"),
            importe=Decimal("2000.00"),
            estado="Pendiente",
        )

        respuesta = self.client.get(
            reverse(
                "listar_proximos_vencimientos"
            ),
            {
                "empresa": self.empresa.id,
                "periodo": "alertas",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        datos = respuesta.json()

        movimientos_por_id = {
            item["id"]: item
            for item in datos["movimientos"]
        }

        self.assertEqual(
            movimientos_por_id[
                movimiento_vencido.id
            ]["estado_vencimiento"],
            "Vencido",
        )

        self.assertEqual(
            movimientos_por_id[
                movimiento_hoy.id
            ]["estado_vencimiento"],
            "Hoy",
        )

class AlertasMovimientoTests(TestCase):
    """
    Prueba la política inicial de Alertas
    para Movimientos con saldo pendiente.
    """

    def setUp(self):
        """
        Crea la Empresa y el Ejercicio necesarios
        para probar la selección de Alertas.
        """

        self.usuario = User.objects.create_user(
            username="usuario_alertas",
            password="clave-prueba-123",
        )

        self.empresa = Empresa.objects.create(
            razon_social="Empresa Alertas",
            propietario=self.usuario,
        )

        self.ejercicio = Ejercicio.objects.create(
            empresa=self.empresa,
            numero=2026,
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 12, 31),
        )

    def test_alertas_respeta_limite_de_tres_dias(self):
        """
        Una obligación vencida y una que vence dentro
        de tres días deben entrar en Alertas.

        Una obligación que vence dentro de cuatro días
        todavía no debe entrar.
        """

        from datetime import timedelta

        fecha_referencia = date(2026, 9, 12)

        movimiento_vencido = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=fecha_referencia,
            fecha_vencimiento=(
                fecha_referencia
                - timedelta(days=1)
            ),
            total=Decimal("1000.00"),
            importe=Decimal("1000.00"),
            estado="Pendiente",
        )

        movimiento_tres_dias = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=fecha_referencia,
            fecha_vencimiento=(
                fecha_referencia
                + timedelta(days=3)
            ),
            total=Decimal("2000.00"),
            importe=Decimal("2000.00"),
            estado="Pendiente",
        )

        movimiento_cuatro_dias = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=fecha_referencia,
            fecha_vencimiento=(
                fecha_referencia
                + timedelta(days=4)
            ),
            total=Decimal("3000.00"),
            importe=Decimal("3000.00"),
            estado="Pendiente",
        )

        movimientos = movimientos_en_alerta(
            empresa=self.empresa,
            fecha_referencia=fecha_referencia,
        )

        ids_movimientos = set(
            movimientos.values_list(
                "id",
                flat=True,
            )
        )

        self.assertIn(
            movimiento_vencido.id,
            ids_movimientos,
        )

        self.assertIn(
            movimiento_tres_dias.id,
            ids_movimientos,
        )

        self.assertNotIn(
            movimiento_cuatro_dias.id,
            ids_movimientos,
        )
