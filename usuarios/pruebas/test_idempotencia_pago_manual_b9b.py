"""B9b: reintentos con clave explícita; NO valida concurrencia PostgreSQL."""
import json
import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from usuarios.models import AplicacionPago, Ejercicio, Empresa, Movimiento, Pago, IdempotenciaPagoManual


class IdempotenciaPagoManualB9bTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='b9b_user', password='B9b-segura!2026')
        self.empresa = Empresa.objects.create(propietario=self.user, razon_social='B9b Empresa')
        ejercicio = Ejercicio.objects.create(empresa=self.empresa, numero=2026, fecha_inicio=date(2026, 1, 1), fecha_cierre=date(2026, 12, 31))
        self.movimiento = Movimiento.objects.create(empresa=self.empresa, ejercicio=ejercicio, fecha_registro=date(2026, 10, 9), modalidad_pago='Manual', total=Decimal('100.00'), importe=Decimal('100.00'), estado='Pendiente')
        self.client.force_login(self.user)
        self.url = reverse('registrar_pago_manual_movimiento')

    def post(self, clave, importe='30.00'):
        return self.client.post(self.url, {
            'empresa': self.empresa.pk,
            'movimiento': self.movimiento.pk,
            'pagos': json.dumps([{'fecha': '2026-10-09', 'importe_efectivo': importe, 'operaciones_bancarias': [], 'tarjetas': [], 'cheques': [], 'retenciones': []}]),
            'clave_idempotencia': str(clave),
        })

    def test_misma_clave_retorna_resultado_original_sin_duplicar(self):
        clave = uuid.uuid4()
        primera = self.post(clave)
        segunda = self.post(clave)
        self.assertEqual(primera.status_code, 200)
        self.assertEqual(segunda.status_code, 200)
        self.assertEqual(primera.json(), segunda.json())
        self.assertEqual(Pago.objects.count(), 1)
        self.assertEqual(AplicacionPago.objects.count(), 1)
        self.assertEqual(IdempotenciaPagoManual.objects.count(), 1)

    def test_misma_clave_datos_distintos_rechazada(self):
        clave = uuid.uuid4()
        self.assertEqual(self.post(clave).status_code, 200)
        respuesta = self.post(clave, '20.00')
        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(Pago.objects.count(), 1)
        self.assertEqual(AplicacionPago.objects.count(), 1)

    def test_claves_distintas_admiten_pagos_legitimos_iguales(self):
        self.assertEqual(self.post(uuid.uuid4()).status_code, 200)
        self.assertEqual(self.post(uuid.uuid4()).status_code, 200)
        self.assertEqual(Pago.objects.count(), 2)
        self.assertEqual(AplicacionPago.objects.count(), 2)

    def test_clave_malformada_no_persiste(self):
        self.assertEqual(self.post('no-es-uuid').status_code, 400)
        self.assertEqual(Pago.objects.count(), 0)
