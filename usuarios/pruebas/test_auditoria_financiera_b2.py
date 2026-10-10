"""B2: regresión HTTP adversarial de mutaciones financieras.

No sustituye pruebas de concurrencia con PostgreSQL.
"""
import json
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import AplicacionPago, Ejercicio, Empresa, Movimiento, Pago


class AuditoriaFinancieraB2Tests(TestCase):
    def setUp(self):
        self.dueno = User.objects.create_user(username='b2_dueno', password='B2-prueba-123!')
        self.ajeno = User.objects.create_user(username='b2_ajeno', password='B2-prueba-123!')
        self.empresa = Empresa.objects.create(propietario=self.dueno, razon_social='B2 Empresa')
        self.otra = Empresa.objects.create(propietario=self.ajeno, razon_social='B2 Empresa Ajena')
        self.ejercicio = Ejercicio.objects.create(
            empresa=self.empresa, numero=2026,
            fecha_inicio=date(2026, 1, 1), fecha_cierre=date(2026, 12, 31),
        )
        ejercicio_ajeno = Ejercicio.objects.create(
            empresa=self.otra, numero=2026,
            fecha_inicio=date(2026, 1, 1), fecha_cierre=date(2026, 12, 31),
        )
        def crear_mov(empresa, ejercicio):
            return Movimiento.objects.create(
                empresa=empresa, ejercicio=ejercicio,
                fecha_registro=date(2026, 10, 9), modalidad_pago='Manual',
                total=Decimal('100.00'), importe=Decimal('100.00'), estado='Pendiente',
            )
        self.movimiento = crear_mov(self.empresa, self.ejercicio)
        self.movimiento_ajeno = crear_mov(self.otra, ejercicio_ajeno)
        self.client.force_login(self.dueno)

    def pago(self, importe='10.00'):
        return {
            'fecha': '2026-10-09', 'importe_efectivo': importe,
            'operaciones_bancarias': [], 'tarjetas': [], 'cheques': [], 'retenciones': [],
        }

    def datos(self, pagos, *, empresa=None, movimiento=None):
        return {
            'empresa': str(self.empresa.pk if empresa is None else empresa),
            'movimiento': str(self.movimiento.pk if movimiento is None else movimiento),
            'pagos': json.dumps(pagos),
        }

    def sin_cambios(self):
        self.assertFalse(Pago.objects.exists())
        self.assertFalse(AplicacionPago.objects.exists())
        self.movimiento.refresh_from_db()
        self.movimiento_ajeno.refresh_from_db()
        self.assertEqual(self.movimiento.estado, 'Pendiente')
        self.assertEqual(self.movimiento_ajeno.estado, 'Pendiente')

    def test_anonimo_no_puede_registrar_pago(self):
        self.client.logout()
        resp = self.client.post(reverse('registrar_pago_manual_movimiento'), self.datos([self.pago()]))
        self.assertEqual(resp.status_code, 302)
        self.sin_cambios()

    def test_empresa_ajena_no_registra_pago(self):
        resp = self.client.post(
            reverse('registrar_pago_manual_movimiento'),
            self.datos([self.pago()], empresa=self.otra.pk),
        )
        self.assertEqual(resp.status_code, 403)
        self.sin_cambios()

    def test_movimiento_ajeno_no_registra_pago(self):
        resp = self.client.post(
            reverse('registrar_pago_manual_movimiento'),
            self.datos([self.pago()], movimiento=self.movimiento_ajeno.pk),
        )
        self.assertEqual(resp.status_code, 404)
        self.sin_cambios()

    def test_lote_con_segundo_pago_invalido_no_crea_primero(self):
        resp = self.client.post(
            reverse('registrar_pago_manual_movimiento'),
            self.datos([self.pago('10.00'), self.pago('-1.00')]),
        )
        self.assertEqual(resp.status_code, 400)
        self.sin_cambios()

    def test_lote_supera_saldo_y_no_crea_pagos(self):
        resp = self.client.post(
            reverse('registrar_pago_manual_movimiento'),
            self.datos([self.pago('60.00'), self.pago('50.00')]),
        )
        self.assertEqual(resp.status_code, 400)
        self.sin_cambios()

    def test_falla_segundo_pago_revierte_toda_transaccion(self):
        from usuarios.services.pagos import crear_pago_validado_movimiento
        llamadas = 0

        def crear_y_fallar(*args, **kwargs):
            nonlocal llamadas
            llamadas += 1
            if llamadas == 2:
                raise RuntimeError('Fallo simulado durante el segundo pago')
            return crear_pago_validado_movimiento(*args, **kwargs)

        with patch('usuarios.services.pagos.crear_pago_validado_movimiento', side_effect=crear_y_fallar):
            resp = self.client.post(
                reverse('registrar_pago_manual_movimiento'),
                self.datos([self.pago('10.00'), self.pago('20.00')]),
            )
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(llamadas, 2)
        self.sin_cambios()

    def test_eliminar_pago_ajeno_no_lo_modifica(self):
        pago_ajeno = Pago.objects.create(
            empresa=self.otra, fecha=date(2026, 10, 9),
            importe_efectivo=Decimal('30.00'),
        )
        resp = self.client.post(reverse('eliminar_pago_movimiento'), {
            'empresa': self.empresa.pk, 'movimiento': self.movimiento.pk,
            'pago': pago_ajeno.pk,
        })
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Pago.objects.filter(pk=pago_ajeno.pk).exists())
        self.assertFalse(AplicacionPago.objects.exists())
        self.movimiento.refresh_from_db()
        self.assertEqual(self.movimiento.estado, 'Pendiente')

    def test_eliminar_pago_no_acepta_get(self):
        resp = self.client.get(reverse('eliminar_pago_movimiento'))
        self.assertEqual(resp.status_code, 405)
        self.sin_cambios()
