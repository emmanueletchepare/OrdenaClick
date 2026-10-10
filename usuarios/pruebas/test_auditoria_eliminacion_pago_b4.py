"""B4: escenarios adversariales adicionales para revertir Pagos.

No sustituye una auditoria completa ni pruebas de concurrencia PostgreSQL.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import AplicacionPago, Ejercicio, Empresa, Movimiento, Pago


class AuditoriaEliminacionPagoB4Tests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='b4_propietario', password='B4-Prueba-123!')
        self.empresa = Empresa.objects.create(propietario=self.usuario, razon_social='B4 Empresa')
        ejercicio = Ejercicio.objects.create(
            empresa=self.empresa, numero=2026,
            fecha_inicio=date(2026, 1, 1), fecha_cierre=date(2026, 12, 31),
        )
        self.movimiento = self.crear_movimiento(ejercicio)
        self.otro_movimiento = self.crear_movimiento(ejercicio)
        self.client.force_login(self.usuario)

    def crear_movimiento(self, ejercicio):
        return Movimiento.objects.create(
            empresa=self.empresa, ejercicio=ejercicio,
            fecha_registro=date(2026, 10, 10), modalidad_pago='Manual',
            total=Decimal('100.00'), importe=Decimal('100.00'), estado='Pendiente',
        )

    def crear_pago(self, importe='30.00'):
        return Pago.objects.create(
            empresa=self.empresa, fecha=date(2026, 10, 10),
            importe_efectivo=Decimal(importe),
        )

    def datos(self, pago):
        return {
            'empresa': str(self.empresa.pk),
            'movimiento': str(self.movimiento.pk),
            'pago': str(pago.pk),
        }

    def comprobar_sin_cambios(self, pago, cantidad_aplicaciones):
        self.assertTrue(Pago.objects.filter(pk=pago.pk).exists())
        self.assertEqual(AplicacionPago.objects.filter(pago=pago).count(), cantidad_aplicaciones)
        self.movimiento.refresh_from_db()
        self.otro_movimiento.refresh_from_db()
        self.assertEqual(self.movimiento.estado, 'Pendiente')
        self.assertEqual(self.otro_movimiento.estado, 'Pendiente')

    def test_anonimo_no_puede_eliminar_pago(self):
        pago = self.crear_pago()
        AplicacionPago.objects.create(pago=pago, movimiento=self.movimiento, importe=Decimal('30.00'))
        self.client.logout()
        respuesta = self.client.post(reverse('eliminar_pago_movimiento'), self.datos(pago))
        self.assertEqual(respuesta.status_code, 302)
        self.comprobar_sin_cambios(pago, 1)

    def test_pago_sin_aplicaciones_no_se_elimina(self):
        pago = self.crear_pago()
        respuesta = self.client.post(reverse('eliminar_pago_movimiento'), self.datos(pago))
        self.assertEqual(respuesta.status_code, 400)
        self.comprobar_sin_cambios(pago, 0)

    def test_pago_aplicado_a_dos_movimientos_no_se_elimina(self):
        pago = self.crear_pago('50.00')
        AplicacionPago.objects.create(pago=pago, movimiento=self.movimiento, importe=Decimal('30.00'))
        AplicacionPago.objects.create(pago=pago, movimiento=self.otro_movimiento, importe=Decimal('20.00'))
        respuesta = self.client.post(reverse('eliminar_pago_movimiento'), self.datos(pago))
        self.assertEqual(respuesta.status_code, 400)
        self.comprobar_sin_cambios(pago, 2)

    def test_error_en_servicio_no_elimina_pago_ni_aplicacion(self):
        pago = self.crear_pago()
        AplicacionPago.objects.create(pago=pago, movimiento=self.movimiento, importe=Decimal('30.00'))
        with patch('usuarios.services.pagos.eliminar_pago_movimiento', side_effect=RuntimeError('B4 fallo simulado')):
            respuesta = self.client.post(reverse('eliminar_pago_movimiento'), self.datos(pago))
        self.assertEqual(respuesta.status_code, 500)
        self.comprobar_sin_cambios(pago, 1)
