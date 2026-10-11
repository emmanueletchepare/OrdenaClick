"""B9a: regresión de reenvíos secuenciales de pagos manuales.

No acredita idempotencia por clave de operación ni concurrencia PostgreSQL.
"""
import json
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import AplicacionPago, Ejercicio, Empresa, Movimiento, Pago


class ReenviosSecuencialesB9Tests(TestCase):
    def setUp(self):
        usuario = User.objects.create_user(username='b9_usuario', password='B9-segura-2026!')
        self.empresa = Empresa.objects.create(propietario=usuario, razon_social='B9 Prueba Empresa')
        ejercicio = Ejercicio.objects.create(
            empresa=self.empresa, numero=2026,
            fecha_inicio=date(2026, 1, 1), fecha_cierre=date(2026, 12, 31),
        )
        self.movimiento = Movimiento.objects.create(
            empresa=self.empresa, ejercicio=ejercicio,
            fecha_registro=date(2026, 10, 9), modalidad_pago='Manual',
            importe=Decimal('100.00'), total=Decimal('100.00'), estado='Pendiente',
        )
        self.client.force_login(usuario)
        self.url = reverse('registrar_pago_manual_movimiento')

    def enviar(self, importe):
        pagos = [{
            'fecha': '2026-10-09', 'importe_efectivo': importe,
            'operaciones_bancarias': [], 'tarjetas': [], 'cheques': [], 'retenciones': [],
        }]
        return self.client.post(self.url, {
            'empresa': self.empresa.pk,
            'movimiento': self.movimiento.pk,
            'pagos': json.dumps(pagos),
        })

    def comprobar_total(self, importe, cantidad):
        self.assertEqual(Pago.objects.count(), cantidad)
        self.assertEqual(AplicacionPago.objects.count(), cantidad)
        total = sum((p.importe for p in AplicacionPago.objects.all()), Decimal('0.00'))
        self.assertEqual(total, Decimal(importe))
        self.movimiento.refresh_from_db()
        return self.movimiento.estado

    def test_reenvio_de_pago_completo_no_duplicar_aplicacion(self):
        primero = self.enviar('100.00')
        self.assertEqual(primero.status_code, 200)
        self.assertTrue(primero.json()['ok'])
        segundo = self.enviar('100.00')
        self.assertEqual(segundo.status_code, 400)
        self.assertFalse(segundo.json()['ok'])
        self.assertEqual(self.comprobar_total('100.00', 1), 'Pagado')

    def test_segundo_pago_que_excede_saldo_restante_no_se_aplica(self):
        primero = self.enviar('70.00')
        self.assertEqual(primero.status_code, 200)
        segundo = self.enviar('70.00')
        self.assertEqual(segundo.status_code, 400)
        self.assertFalse(segundo.json()['ok'])
        self.assertEqual(self.comprobar_total('70.00', 1), 'Parcial')

    def test_pago_parcial_adicional_dentro_del_saldo_es_valido(self):
        self.assertEqual(self.enviar('40.00').status_code, 200)
        segundo = self.enviar('30.00')
        self.assertEqual(segundo.status_code, 200)
        self.assertTrue(segundo.json()['ok'])
        self.assertEqual(self.comprobar_total('70.00', 2), 'Parcial')
