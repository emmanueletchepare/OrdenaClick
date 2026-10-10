"""B3: limites HTTP del registro de debito automatico.

No reemplaza pruebas de concurrencia o de integracion bancaria.
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import AplicacionPago, DebitoAutomaticoPago, Ejercicio, Empresa, Movimiento, Pago


class AuditoriaDebitoB3Tests(TestCase):
    def setUp(self):
        self.dueno = User.objects.create_user(username='b3_dueno', password='B3-prueba-123!')
        self.ajeno = User.objects.create_user(username='b3_ajeno', password='B3-prueba-123!')
        self.empresa = Empresa.objects.create(propietario=self.dueno, razon_social='B3 Empresa')
        self.otra = Empresa.objects.create(propietario=self.ajeno, razon_social='B3 Empresa Ajena')
        ejercicio = Ejercicio.objects.create(
            empresa=self.empresa, numero=2026,
            fecha_inicio=date(2026, 1, 1), fecha_cierre=date(2026, 12, 31),
        )
        ejercicio_ajeno = Ejercicio.objects.create(
            empresa=self.otra, numero=2026,
            fecha_inicio=date(2026, 1, 1), fecha_cierre=date(2026, 12, 31),
        )
        self.movimiento = self.crear_movimiento(self.empresa, ejercicio, 'DebitoAutomatico')
        self.movimiento_ajeno = self.crear_movimiento(self.otra, ejercicio_ajeno, 'DebitoAutomatico')
        self.movimiento_manual = self.crear_movimiento(self.empresa, ejercicio, 'Manual')
        self.client.force_login(self.dueno)

    @staticmethod
    def crear_movimiento(empresa, ejercicio, modalidad):
        return Movimiento.objects.create(
            empresa=empresa, ejercicio=ejercicio,
            fecha_registro=date(2026, 10, 9), fecha_vencimiento=date(2026, 10, 10),
            modalidad_pago=modalidad, total=Decimal('100.00'),
            importe=Decimal('100.00'), estado='Pendiente',
        )

    def datos(self, *, empresa=None, movimiento=None, fecha='2026-10-10', importe='20.00'):
        return {
            'empresa': str(self.empresa.pk if empresa is None else empresa),
            'movimiento': str(self.movimiento.pk if movimiento is None else movimiento),
            'fecha': fecha, 'importe_debitado': importe,
        }

    def sin_cambios(self):
        self.assertFalse(Pago.objects.exists())
        self.assertFalse(AplicacionPago.objects.exists())
        self.assertFalse(DebitoAutomaticoPago.objects.exists())
        for mov in (self.movimiento, self.movimiento_ajeno, self.movimiento_manual):
            mov.refresh_from_db()
            self.assertEqual(mov.estado, 'Pendiente')

    def test_anonimo_no_puede_registrar_debito(self):
        self.client.logout()
        respuesta = self.client.post(reverse('registrar_debito_automatico_movimiento'), self.datos())
        self.assertEqual(respuesta.status_code, 302)
        self.sin_cambios()

    def test_get_no_registra_debito(self):
        respuesta = self.client.get(reverse('registrar_debito_automatico_movimiento'), self.datos())
        self.assertEqual(respuesta.status_code, 405)
        self.sin_cambios()

    def test_empresa_ajena_no_registra_debito(self):
        respuesta = self.client.post(
            reverse('registrar_debito_automatico_movimiento'),
            self.datos(empresa=self.otra.pk),
        )
        self.assertEqual(respuesta.status_code, 403)
        self.sin_cambios()

    def test_movimiento_ajeno_no_registra_debito(self):
        respuesta = self.client.post(
            reverse('registrar_debito_automatico_movimiento'),
            self.datos(movimiento=self.movimiento_ajeno.pk),
        )
        self.assertEqual(respuesta.status_code, 404)
        self.sin_cambios()

    def test_movimiento_manual_no_registra_debito(self):
        respuesta = self.client.post(
            reverse('registrar_debito_automatico_movimiento'),
            self.datos(movimiento=self.movimiento_manual.pk),
        )
        self.assertEqual(respuesta.status_code, 400)
        self.sin_cambios()

    def test_fecha_invalida_no_registra_debito(self):
        respuesta = self.client.post(
            reverse('registrar_debito_automatico_movimiento'),
            self.datos(fecha='10/10/2026'),
        )
        self.assertEqual(respuesta.status_code, 400)
        self.sin_cambios()

    def test_importe_negativo_no_registra_debito(self):
        respuesta = self.client.post(
            reverse('registrar_debito_automatico_movimiento'),
            self.datos(importe='-5.00'),
        )
        self.assertEqual(respuesta.status_code, 400)
        self.sin_cambios()

    def test_movimiento_cancelado_no_registra_debito(self):
        self.movimiento.estado = 'Cancelado'
        self.movimiento.save(update_fields=['estado'])
        respuesta = self.client.post(reverse('registrar_debito_automatico_movimiento'), self.datos())
        self.assertEqual(respuesta.status_code, 400)
        self.movimiento.refresh_from_db()
        self.assertEqual(self.movimiento.estado, 'Cancelado')
        self.assertFalse(Pago.objects.exists())
        self.assertFalse(AplicacionPago.objects.exists())
        self.assertFalse(DebitoAutomaticoPago.objects.exists())
