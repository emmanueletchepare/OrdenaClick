"""Caja 1: ingreso/egreso manual seguro, alcances e idempotencia.

Los tests utilizan una BD de prueba descartable; no afectan la Caja real.
"""
import json
import uuid
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import Client, TestCase
from django.utils import timezone
from django.urls import reverse

from usuarios.models import (
    AsignacionUsuarioEmpresa, Caja, CentroOperativo, Empresa,
    IdempotenciaMovimientoCaja, MovimientoCaja,
)
from usuarios.services.caja_disponibilidad import saldo_efectivo_caja
from usuarios.services.caja_movimientos import registrar_movimiento_caja


class MovimientosOperativosCaja1Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dueno = User.objects.create_user(username='caja1_dueno', password='Caja1!2026-test')
        cls.otro = User.objects.create_user(username='caja1_otro', password='Caja1!2026-test')
        cls.general = User.objects.create_user(username='caja1_general', password='Caja1!2026-test')
        cls.admin_centro = User.objects.create_user(username='caja1_centro', password='Caja1!2026-test')
        cls.colaborador = User.objects.create_user(username='caja1_colaborador', password='Caja1!2026-test')
        cls.inactivo = User.objects.create_user(username='caja1_inactivo', password='Caja1!2026-test')
        cls.superusuario = User.objects.create_superuser(username='caja1_super', password='Caja1!2026-test', email='super@example.test')
        cls.empresa = Empresa.objects.create(razon_social='Empresa Caja 1', propietario=cls.dueno)
        cls.ajena = Empresa.objects.create(razon_social='Empresa Aparte Caja 1', propietario=cls.otro)
        cls.central = CentroOperativo.objects.create(empresa=cls.empresa, tipo='Casa Central', nombre='Olavarria', activo=True)
        cls.sucursal = CentroOperativo.objects.create(empresa=cls.empresa, tipo='Sucursal', nombre='Tandil', activo=True)
        cls.centro_ajeno = CentroOperativo.objects.create(empresa=cls.ajena, tipo='Sucursal', nombre='Otra empresa', activo=True)
        cls.caja_central = Caja.objects.create(empresa=cls.empresa, centro_operativo=cls.central, nombre='Principal', activo=True)
        cls.caja_sucursal = Caja.objects.create(empresa=cls.empresa, centro_operativo=cls.sucursal, nombre='Sucursal', activo=True)
        cls.caja_ajena = Caja.objects.create(empresa=cls.ajena, centro_operativo=cls.centro_ajeno, nombre='Ajena', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.general,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL, activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.admin_centro,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO, centro_operativo=cls.sucursal, activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.colaborador,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR, activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.inactivo,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL, activo=False)

    @staticmethod
    def movimiento(**kwargs):
        return {
            'fecha': timezone.localdate().isoformat(), 'tipo': 'Ingreso',
            'moneda': 'ARS', 'importe': '100.00', 'concepto': 'Entrada manual',
            'clave_idempotencia': str(uuid.uuid4()), **kwargs,
        }

    def post(self, *, user=None, empresa=None, caja=None, movimiento=None, client=None):
        (client or self.client).force_login(user or self.dueno)
        datos = {
            'empresa_id': (empresa or self.empresa).pk,
            'caja_id': (caja or self.caja_central).pk,
            'movimiento': self.movimiento() if movimiento is None else movimiento,
        }
        return (client or self.client).post(reverse('registrar_movimiento_caja'),
            data=json.dumps(datos), content_type='application/json')

    def test_ingreso_suma_saldo_y_registra_identidad_historica(self):
        respuesta = self.post()
        self.assertEqual(respuesta.status_code, 201, respuesta.content)
        mov = MovimientoCaja.objects.get(pk=respuesta.json()['movimiento_id'])
        self.assertIsNone(mov.cobranza_id)
        self.assertEqual(mov.creado_por.usuario_id, self.dueno.pk)
        self.assertEqual(saldo_efectivo_caja(self.empresa, self.caja_central, 'ARS'), Decimal('100.00'))
        self.assertEqual(IdempotenciaMovimientoCaja.objects.count(), 1)

    def test_egreso_valido_descuenta_y_no_toca_otra_moneda(self):
        self.post(movimiento=self.movimiento(importe='500.00'))
        self.post(movimiento=self.movimiento(moneda='USD', importe='200.00'))
        salida = self.post(movimiento=self.movimiento(tipo='Egreso', importe='120.00'))
        self.assertEqual(salida.status_code, 201)
        self.assertEqual(saldo_efectivo_caja(self.empresa, self.caja_central, 'ARS'), Decimal('380.00'))
        self.assertEqual(saldo_efectivo_caja(self.empresa, self.caja_central, 'USD'), Decimal('200.00'))

    def test_egreso_sin_saldo_no_escribe_movimiento_ni_idempotencia(self):
        respuesta = self.post(movimiento=self.movimiento(tipo='Egreso', importe='0.01'))
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(MovimientoCaja.objects.count(), 0)
        self.assertEqual(IdempotenciaMovimientoCaja.objects.count(), 0)

    def test_egreso_con_saldo_insuficiente_no_modifica_saldo(self):
        self.post(movimiento=self.movimiento(importe='100.00'))
        respuesta = self.post(movimiento=self.movimiento(tipo='Egreso', importe='100.01'))
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(MovimientoCaja.objects.count(), 1)
        self.assertEqual(saldo_efectivo_caja(self.empresa, self.caja_central, 'ARS'), Decimal('100.00'))

    def test_importe_local_y_decimal_estandar(self):
        self.assertEqual(self.post(movimiento=self.movimiento(importe='1.234,56')).status_code, 201)
        self.assertEqual(self.post(movimiento=self.movimiento(importe='12.50')).status_code, 201)
        self.assertEqual(saldo_efectivo_caja(self.empresa, self.caja_central, 'ARS'), Decimal('1247.06'))

    def test_importes_y_fechas_invalidos_no_persisten(self):
        for valor in ('0', '-1', 'NaN', 'Infinity', '1.2345', '1000000000000', '1e10'):
            with self.subTest(valor=valor):
                self.assertEqual(self.post(movimiento=self.movimiento(importe=valor)).status_code, 400)
        self.assertEqual(self.post(movimiento=self.movimiento(fecha='ayer')).status_code, 400)
        self.assertEqual(self.post(movimiento=self.movimiento(concepto=' ')).status_code, 400)
        self.assertFalse(MovimientoCaja.objects.exists())

    def test_clave_repetida_devuelve_resultado_sin_duplicar(self):
        datos = self.movimiento()
        a = self.post(movimiento=datos)
        b = self.post(movimiento=datos)
        self.assertEqual((a.status_code, b.status_code), (201, 200))
        self.assertEqual(a.json(), b.json())
        self.assertEqual(MovimientoCaja.objects.count(), 1)
        self.assertEqual(IdempotenciaMovimientoCaja.objects.count(), 1)

    def test_clave_reutilizada_con_otros_datos_se_rechaza(self):
        datos = self.movimiento()
        self.assertEqual(self.post(movimiento=datos).status_code, 201)
        modificado = {**datos, 'importe': '200.00'}
        self.assertEqual(self.post(movimiento=modificado).status_code, 409)
        self.assertEqual(MovimientoCaja.objects.count(), 1)

    def test_clave_reutilizada_por_otro_usuario_se_rechaza(self):
        datos = self.movimiento()
        self.assertEqual(self.post(movimiento=datos).status_code, 201)
        self.assertEqual(self.post(user=self.general, movimiento=datos).status_code, 409)

    def test_reintento_de_egreso_no_descuenta_dos_veces(self):
        self.post(movimiento=self.movimiento(importe='100.00'))
        egreso = self.movimiento(tipo='Egreso', importe='80.00')
        self.assertEqual(self.post(movimiento=egreso).status_code, 201)
        self.assertEqual(self.post(movimiento=egreso).status_code, 200)
        self.assertEqual(saldo_efectivo_caja(self.empresa, self.caja_central, 'ARS'), Decimal('20.00'))

    def test_admin_centro_solo_accede_y_opera_su_caja(self):
        self.client.force_login(self.admin_centro)
        bien = self.client.get(reverse('vista_movimientos_caja'), {
            'empresa': self.empresa.pk, 'caja': self.caja_sucursal.pk})
        mal = self.client.get(reverse('vista_movimientos_caja'), {
            'empresa': self.empresa.pk, 'caja': self.caja_central.pk})
        self.assertEqual(bien.status_code, 200)
        self.assertEqual(mal.status_code, 403)
        self.assertEqual(self.post(user=self.admin_centro, caja=self.caja_central).status_code, 403)
        self.assertEqual(self.post(user=self.admin_centro, caja=self.caja_sucursal).status_code, 201)
        self.assertFalse(MovimientoCaja.objects.filter(caja=self.caja_central).exists())

    def test_admin_general_puede_elegir_cualquier_caja_pero_no_empresa_ajena(self):
        self.assertEqual(self.post(user=self.general, caja=self.caja_central).status_code, 201)
        self.assertEqual(self.post(user=self.general, caja=self.caja_sucursal).status_code, 201)
        self.assertEqual(self.post(user=self.general, empresa=self.ajena, caja=self.caja_ajena).status_code, 403)

    def test_colaborador_e_inactivo_no_operan_caja(self):
        for usuario in (self.colaborador, self.inactivo):
            with self.subTest(usuario=usuario.username):
                self.assertEqual(self.post(user=usuario).status_code, 403)
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(reverse('vista_movimientos_caja'), {
                    'empresa': self.empresa.pk, 'caja': self.caja_central.pk}).status_code, 403)

    def test_caja_ajena_no_es_consultable_por_id(self):
        self.assertEqual(self.post(empresa=self.empresa, caja=self.caja_ajena).status_code, 403)
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(reverse('vista_movimientos_caja'), {
            'empresa': self.empresa.pk, 'caja': self.caja_ajena.pk}).status_code, 403)

    def test_superusuario_conserva_acceso_a_empresa_ajena(self):
        self.assertEqual(self.post(user=self.superusuario, empresa=self.ajena, caja=self.caja_ajena).status_code, 201)

    def test_metodos_http_no_permitidos_no_graban(self):
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(reverse('registrar_movimiento_caja')).status_code, 405)
        self.assertEqual(self.client.post(reverse('vista_movimientos_caja')).status_code, 405)
        self.assertEqual(MovimientoCaja.objects.count(), 0)

    def test_anonimos_redirigidos_en_get_y_post(self):
        self.assertEqual(self.client.get(reverse('vista_movimientos_caja')).status_code, 302)
        self.assertEqual(self.client.post(reverse('registrar_movimiento_caja')).status_code, 302)

    def test_csrf_obligatorio_en_registro(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.dueno)
        self.assertEqual(cliente.post(reverse('registrar_movimiento_caja'),
            data=json.dumps({'empresa_id': self.empresa.pk, 'caja_id': self.caja_central.pk,
                             'movimiento': self.movimiento()}), content_type='application/json').status_code, 403)
        self.assertFalse(MovimientoCaja.objects.exists())

    def test_formulario_incluye_token_y_historial_filtrado(self):
        self.post(caja=self.caja_central, movimiento=self.movimiento(concepto='Visible central'))
        self.post(caja=self.caja_sucursal, movimiento=self.movimiento(concepto='No visible central'))
        self.client.force_login(self.general)
        resp = self.client.get(reverse('vista_movimientos_caja'),
                               {'empresa': self.empresa.pk, 'caja': self.caja_central.pk})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('name="csrfmiddlewaretoken"', resp.json()['html'])
        self.assertNotIn('Visible central', resp.json()['html'])
        historial = self.client.get(reverse('historial_movimientos_caja'), {
            'empresa': self.empresa.pk, 'caja': self.caja_central.pk})
        self.assertEqual(historial.status_code, 200)
        self.assertIn('Visible central', historial.json()['html'])
        self.assertNotIn('No visible central', historial.json()['html'])

    def test_historial_paginado(self):
        for i in range(28):
            self.post(movimiento=self.movimiento(concepto=f'Movimiento-{i}'))
        self.client.force_login(self.dueno)
        pagina1 = self.client.get(reverse('historial_movimientos_caja'), {
            'empresa': self.empresa.pk, 'caja': self.caja_central.pk, 'pagina': 1}).json()['html']
        pagina2 = self.client.get(reverse('historial_movimientos_caja'), {
            'empresa': self.empresa.pk, 'caja': self.caja_central.pk, 'pagina': 2}).json()['html']
        self.assertIn('Página 1 de 2', pagina1)
        self.assertIn('Página 2 de 2', pagina2)
        self.assertIn('Movimiento-0', pagina2)

    def test_servicio_tambien_impide_bypass_de_permisos(self):
        with self.assertRaises(PermissionDenied):
            registrar_movimiento_caja(empresa=self.empresa, caja=self.caja_central,
                usuario=self.colaborador, datos=self.movimiento())
        self.assertFalse(MovimientoCaja.objects.exists())

    def test_idempotencia_no_bloquea_restauracion_caja_y_se_elimina_en_limpieza(self):
        self.assertEqual(self.post().status_code, 201)
        self.assertTrue(IdempotenciaMovimientoCaja.objects.filter(caja=self.caja_central).exists())
        MovimientoCaja.objects.filter(caja=self.caja_central).delete()
        self.caja_central.delete()
        self.assertFalse(IdempotenciaMovimientoCaja.objects.exists())

    def test_request_json_no_valido_o_excesivo(self):
        self.client.force_login(self.dueno)
        url = reverse('registrar_movimiento_caja')
        self.assertEqual(self.client.post(url, 'xxx', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post(url, '[2]', content_type='application/json').status_code, 400)
        self.assertEqual(self.client.post(url, ' '*8200+'x', content_type='application/json').status_code, 400)
        self.assertFalse(MovimientoCaja.objects.exists())
