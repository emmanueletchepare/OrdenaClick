"""B9c: pruebas simultáneas HTTP reales, EXCLUSIVAS para PostgreSQL.

Correr con --settings=ordenaclick.settings_test_postgres_b9c.
Nunca valida SQLite como evidencia de concurrencia.
"""
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier

from django.contrib.auth.models import User
from django.db import connection, connections
from django.test import Client, TransactionTestCase
from django.urls import reverse

from usuarios.models import (AplicacionPago, Ejercicio, Empresa,
                             IdempotenciaPagoManual, Movimiento, Pago)


class ConcurrenciaPostgresB9cTests(TransactionTestCase):
    def setUp(self):
        if connection.vendor != 'postgresql':
            self.fail('B9c exige PostgreSQL real; NO ejecutar sobre SQLite.')
        self.usuario = User.objects.create_user(
            username='b9c_usuario', password='B9c-segura-2026!')
        self.empresa = Empresa.objects.create(
            propietario=self.usuario, razon_social='B9c Empresa')
        ejercicio = Ejercicio.objects.create(
            empresa=self.empresa, numero=2026,
            fecha_inicio=date(2026, 1, 1), fecha_cierre=date(2026, 12, 31))
        self.movimiento = Movimiento.objects.create(
            empresa=self.empresa, ejercicio=ejercicio,
            fecha_registro=date(2026, 10, 9), modalidad_pago='Manual',
            importe=Decimal('100.00'), total=Decimal('100.00'), estado='Pendiente')
        self.url = reverse('registrar_pago_manual_movimiento')

    def ejecutar_paralelo(self, clave1, clave2, importe):
        # Crear las sesiones ANTES de comenzar los hilos, evitando accesos
        # concurrentes a la misma sesión o conexión de base de datos.
        clientes = [Client(), Client()]
        for cliente in clientes:
            cliente.force_login(self.usuario)
        barrera = Barrier(2, timeout=15)

        def enviar(cliente, clave):
            try:
                barrera.wait()
                respuesta = cliente.post(self.url, {
                    'empresa': str(self.empresa.pk),
                    'movimiento': str(self.movimiento.pk),
                    'clave_idempotencia': str(clave),
                    'pagos': json.dumps([{
                        'fecha': '2026-10-09',
                        'importe_efectivo': importe,
                        'operaciones_bancarias': [], 'tarjetas': [],
                        'cheques': [], 'retenciones': [],
                    }]),
                })
                return respuesta.status_code, respuesta.json()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futuros = [pool.submit(enviar, cliente, clave)
                       for cliente, clave in zip(clientes, (clave1, clave2))]
            return [f.result(timeout=35) for f in futuros]

    def test_misma_clave_simultanea_crea_un_solo_pago(self):
        clave = uuid.uuid4()
        resultados = self.ejecutar_paralelo(clave, clave, '30.00')
        self.assertEqual([estado for estado, _ in resultados], [200, 200], resultados)
        self.assertEqual(resultados[0][1], resultados[1][1])
        self.assertEqual(Pago.objects.count(), 1)
        self.assertEqual(AplicacionPago.objects.count(), 1)
        self.assertEqual(IdempotenciaPagoManual.objects.count(), 1)
        self.assertEqual(AplicacionPago.objects.get().importe, Decimal('30.00'))

    def test_claves_distintas_no_exceden_saldo_en_paralelo(self):
        resultados = self.ejecutar_paralelo(uuid.uuid4(), uuid.uuid4(), '70.00')
        self.assertEqual(sorted(estado for estado, _ in resultados), [200, 400], resultados)
        self.assertEqual(Pago.objects.count(), 1)
        self.assertEqual(AplicacionPago.objects.count(), 1)
        self.assertEqual(IdempotenciaPagoManual.objects.count(), 1)
        self.assertEqual(AplicacionPago.objects.get().importe, Decimal('70.00'))
        self.movimiento.refresh_from_db()
        self.assertEqual(self.movimiento.estado, 'Parcial')
