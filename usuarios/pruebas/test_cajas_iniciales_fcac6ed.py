"""Cajas iniciales: alta explícita, aislamiento y no duplicación.

No prueba ni modifica operaciones bancarias, e-Cheqs o movimientos reales.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import Caja, CentroOperativo, Empresa, MovimientoCaja
from usuarios.services.cajas_iniciales import asegurar_caja_inicial
from usuarios.services.seguridad import cajas_autorizadas


class CajasInicialesTests(TestCase):
    def setUp(self):
        self.dueno = User.objects.create_user('cajas_auto_dueno', password='Prueba123!')
        self.otro = User.objects.create_user('cajas_auto_otro', password='Prueba123!')
        self.empresa = Empresa.objects.create(propietario=self.dueno, razon_social='Cajas automáticas')
        self.ajena = Empresa.objects.create(propietario=self.otro, razon_social='Cajas ajenas')

    def centro(self, nombre, tipo='Sucursal', empresa=None):
        return CentroOperativo.objects.create(empresa=empresa or self.empresa,
                                              nombre=nombre, tipo=tipo, activo=True)

    def test_tipos_con_caja_y_deposito_sin_caja(self):
        for tipo in ('Casa Central', 'Sucursal', 'Mostrador'):
            with self.subTest(tipo=tipo):
                centro = self.centro('Centro ' + tipo, tipo)
                caja, creada = asegurar_caja_inicial(centro)
                self.assertTrue(creada)
                self.assertEqual(caja.empresa_id, centro.empresa_id)
                self.assertEqual(caja.centro_operativo_id, centro.pk)
                self.assertEqual(caja.nombre, 'CAJA PRINCIPAL')
                self.assertEqual(caja.movimientos.count(), 0)
        deposito = self.centro('Depósito', 'Deposito')
        self.assertEqual(asegurar_caja_inicial(deposito), (None, False))
        self.assertFalse(Caja.objects.filter(centro_operativo=deposito).exists())
        self.assertEqual(MovimientoCaja.objects.count(), 0)

    def test_no_duplicar_caja_existente_ni_reactivar_inactiva(self):
        centro = self.centro('Sucursal vieja')
        anterior = Caja.objects.create(empresa=self.empresa, centro_operativo=centro,
                                       nombre='CAJA EXISTENTE', activo=False)
        caja, creada = asegurar_caja_inicial(centro)
        self.assertFalse(creada)
        self.assertEqual(caja.pk, anterior.pk)
        self.assertFalse(caja.activo)
        self.assertEqual(Caja.objects.filter(centro_operativo=centro).count(), 1)

    def test_reintento_idempotente(self):
        centro = self.centro('Suc repetida')
        primero, creada = asegurar_caja_inicial(centro)
        segundo, duplicada = asegurar_caja_inicial(centro)
        self.assertTrue(creada)
        self.assertFalse(duplicada)
        self.assertEqual(primero.pk, segundo.pk)
        self.assertEqual(Caja.objects.filter(centro_operativo=centro).count(), 1)

    def test_alta_abm_crea_sucursal_no_deposito(self):
        self.client.force_login(self.dueno)
        for tipo, esperado in (('Sucursal', True), ('Mostrador', True),
                               ('Deposito', False), ('Casa Central', True)):
            with self.subTest(tipo=tipo):
                respuesta = self.client.post(reverse('guardar_centro_operativo'), {
                    'empresa': self.empresa.pk, 'nombre': 'ALTA ' + tipo,
                    'tipo': tipo, 'direccion': 'Calle 1',
                })
                self.assertEqual(respuesta.status_code, 200, respuesta.content)
                self.assertTrue(respuesta.json()['ok'], respuesta.content)
                centro = CentroOperativo.objects.get(empresa=self.empresa,
                                                    nombre='ALTA ' + tipo.upper())
                self.assertEqual(Caja.objects.filter(centro_operativo=centro).exists(), esperado)

    def test_alta_de_empresa_crea_caja_central(self):
        self.client.force_login(self.dueno)
        respuesta = self.client.post(reverse('panel_admin'), {
            'guardar_empresa': '1', 'razon_social': 'Empresa nueva con Caja',
            'nombre_fantasia': 'Nueva', 'cuit': '30-12345678-9',
        })
        self.assertEqual(respuesta.status_code, 302, respuesta.content)
        empresa = Empresa.objects.get(razon_social='Empresa nueva con Caja')
        central = CentroOperativo.objects.get(empresa=empresa, tipo='Casa Central')
        self.assertEqual(Caja.objects.filter(empresa=empresa, centro_operativo=central,
                                             activo=True).count(), 1)
        self.assertFalse(MovimientoCaja.objects.filter(empresa=empresa).exists())

    def test_aislamiento_empresa_y_centro(self):
        propia = self.centro('Propia')
        ajena = self.centro('Ajena', empresa=self.ajena)
        asegurar_caja_inicial(propia)
        asegurar_caja_inicial(ajena)
        empresa, cajas = cajas_autorizadas(self.dueno, self.empresa.pk)
        self.assertEqual(empresa.pk, self.empresa.pk)
        self.assertEqual(set(cajas.values_list('centro_operativo_id', flat=True)), {propia.pk})
