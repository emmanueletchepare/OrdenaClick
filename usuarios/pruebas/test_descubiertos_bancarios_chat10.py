"""Chat 10: descubierto, avisos y edición por cuenta sin alterar Caja o Pendientes."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.models import (AsignacionUsuarioEmpresa, Banco, CuentaBancaria,
    DestinatarioAlerta, Empresa, EventoAcuerdoDescubierto,
    PermisoAccesoColaborador, SaldoInformadoCuentaBancaria)
from usuarios.services.alertas_bancos import (avisos_bancos_visibles,
    fuentes_bancos, avisos_bancos_publicos)
from usuarios.services.caja_bancos_informados import resumen_bancos
from usuarios.services.cuentas_bancarias_descubierto import leer_acuerdo
from usuarios.services.backup_empresa.specs import SPEC_BY_KEY, OPTIONAL_NEW_KEYS


class DescubiertosBancariosChat10Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dueno = User.objects.create_user('limite_dueno', password='Prueba123!')
        cls.ajeno = User.objects.create_user('limite_ajeno', password='Prueba123!')
        cls.empresa = Empresa.objects.create(propietario=cls.dueno, razon_social='Empresa Descubierto')
        cls.otra = Empresa.objects.create(propietario=cls.ajeno, razon_social='Empresa Ajena Descubierto')
        cls.banco = Banco.objects.create(empresa=cls.empresa, nombre='BANCO UNO', activo=True)
        cls.banco_ajeno = Banco.objects.create(empresa=cls.otra, nombre='BANCO PRIVADO', activo=True)
        cls.cuenta = CuentaBancaria.objects.create(empresa=cls.empresa, banco=cls.banco,
            nombre='Corriente ARS', moneda='ARS', tipo_cuenta='CuentaCorriente', activo=True)
        cls.cuenta_ajena = CuentaBancaria.objects.create(empresa=cls.otra,
            banco=cls.banco_ajeno, nombre='Cuenta ajena', moneda='ARS',
            tipo_cuenta='CuentaCorriente', activo=True)

    def datos(self, importe='1.250.000,50', vencimiento=None, dias='7', habilitada='1'):
        return {
            'empresa': str(self.empresa.pk), 'cuenta': str(self.cuenta.pk),
            'nombre': self.cuenta.nombre, 'banco': str(self.banco.pk),
            'tipo_cuenta': self.cuenta.tipo_cuenta, 'moneda': self.cuenta.moneda,
            'numero_cuenta': '', 'cbu': '', 'alias': '',
            'descubierto_importe': importe,
            'descubierto_vencimiento': vencimiento or (timezone.localdate()+timedelta(days=5)).isoformat(),
            'descubierto_alerta_dias': dias,
            'descubierto_alerta_habilitada': habilitada,
        }

    def modificar(self, datos=None, usuario=None):
        self.client.force_login(usuario or self.dueno)
        return self.client.post(reverse('modificar_cuenta_bancaria'), data=datos or self.datos())

    def test_abm_edita_es_ar_fecha_nativa_y_audita_sin_modificar_saldo(self):
        r = self.modificar()
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.json()['ok'])
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.descubierto_importe, Decimal('1250000.50'))
        self.assertEqual(self.cuenta.descubierto_alerta_dias, 7)
        self.assertTrue(self.cuenta.descubierto_alerta_habilitada)
        self.assertEqual(EventoAcuerdoDescubierto.objects.filter(empresa=self.empresa).count(), 1)
        evento = EventoAcuerdoDescubierto.objects.get(empresa=self.empresa)
        self.assertIsNone(evento.antes['importe'])
        self.assertEqual(evento.despues['importe'], '1250000.50')
        self.assertEqual(SaldoInformadoCuentaBancaria.objects.count(), 0)
        listado = self.client.get(reverse('listar_cuentas_bancarias'), {'empresa': self.empresa.pk}).json()
        self.assertEqual(listado['cuentas'][0]['descubierto_importe'], '1250000.50')
        self.assertIn('id="descubiertoVencimientoCuenta"', listado['html'])
        self.assertIn('type="date"', listado['html'])
        self.assertEqual(listado['cuentas'][0]['descubierto_alerta_dias'], 7)

    def test_no_agrega_evento_duplicado_ni_pierde_acuerdo_con_cliente_legacy(self):
        self.modificar()
        self.modificar()
        self.assertEqual(EventoAcuerdoDescubierto.objects.count(), 1)
        datos = self.datos()
        for campo in ('descubierto_importe','descubierto_vencimiento',
                      'descubierto_alerta_dias','descubierto_alerta_habilitada'):
            datos.pop(campo)
        self.modificar(datos)
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.descubierto_importe, Decimal('1250000.50'))
        self.assertTrue(self.cuenta.descubierto_alerta_habilitada)
        self.assertEqual(EventoAcuerdoDescubierto.objects.count(), 1)

    def test_validacion_atomica_de_importe_fecha_y_checkbox(self):
        for cambio in [dict(importe='1.234.567,891'),
                       dict(importe='-20'), dict(importe='0'),
                       dict(importe='100,00', vencimiento='2026-02-30'),
                       dict(importe='', habilitada='1'),
                       dict(dias='366'), dict(dias='-1'),
                       dict(habilitada='cualquier cosa')]:
            with self.subTest(cambio=cambio):
                r = self.modificar(self.datos(**cambio))
                self.assertEqual(r.status_code, 400, r.content)
                self.cuenta.refresh_from_db()
                self.assertIsNone(self.cuenta.descubierto_importe)
        self.assertEqual(EventoAcuerdoDescubierto.objects.count(), 0)

    def test_vencimiento_no_se_suma_y_expira_automaticamente(self):
        hoy = timezone.localdate()
        self.modificar(self.datos(vencimiento=(hoy+timedelta(days=1)).isoformat()))
        self.assertTrue(resumen_bancos(self.empresa)['filas'][0]['descubierto_vigente'])
        self.assertEqual(resumen_bancos(self.empresa)['totales']['ARS'], Decimal('0.00'))
        self.modificar(self.datos(vencimiento=(hoy-timedelta(days=1)).isoformat()))
        resumen = resumen_bancos(self.empresa)
        self.assertFalse(resumen['filas'][0]['descubierto_vigente'])
        self.assertEqual(resumen['totales']['ARS'], Decimal('0.00'))
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.descubierto_importe, Decimal('1250000.50'))

    def test_alertas_por_anticipacion_con_permiso_de_origen_y_suscripcion(self):
        hoy = timezone.localdate()
        self.modificar(self.datos(vencimiento=(hoy+timedelta(days=5)).isoformat(), dias='4'))
        self.assertEqual(fuentes_bancos(self.empresa, hoy), [])
        self.modificar(self.datos(vencimiento=(hoy+timedelta(days=5)).isoformat(), dias='5'))
        aviso = avisos_bancos_publicos(self.dueno, self.empresa, hoy)
        self.assertEqual(len(aviso), 1)
        self.assertEqual(aviso[0]['codigo'], 'FIN-05')
        self.assertNotIn('importe', aviso[0])
        self.assertEqual(avisos_bancos_visibles(self.ajeno, self.empresa, hoy), [])
        self.client.force_login(self.dueno)
        r = self.client.get(reverse('listar_alertas'), {'empresa': self.empresa.pk})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['alertas_bancarias'][0]['codigo'], 'FIN-05')
        DestinatarioAlerta.objects.create(empresa=self.empresa, usuario=self.dueno,
                                         codigo='FIN-05', activo=True, configurado_por=self.dueno)
        llamada = self.client.get(reverse('estado_llamador_alertas'), {'empresa': self.empresa.pk})
        self.assertTrue(llamada.json()['mostrar_llamador'])
        self.cuenta.descubierto_alerta_habilitada = False
        self.cuenta.save(update_fields=['descubierto_alerta_habilitada'])
        self.assertEqual(fuentes_bancos(self.empresa, hoy), [])

    def test_cuentas_ajenas_no_se_exponen_ni_editan(self):
        self.client.force_login(self.ajeno)
        self.assertEqual(self.client.get(reverse('listar_cuentas_bancarias'),
            {'empresa': self.empresa.pk}).status_code, 403)
        self.assertEqual(self.client.post(reverse('modificar_cuenta_bancaria'),
            data=self.datos()).status_code, 403)
        self.assertEqual(EventoAcuerdoDescubierto.objects.count(), 0)
        self.assertEqual(fuentes_bancos(self.otra), [])

    def test_checkbox_desactivado_no_alerta_y_fecha_con_formato_iso(self):
        valores = leer_acuerdo(self.datos(habilitada='0'))
        self.assertFalse(valores['descubierto_alerta_habilitada'])
        self.assertEqual(valores['descubierto_vencimiento'], timezone.localdate()+timedelta(days=5))
        self.modificar(self.datos(habilitada='0'))
        self.assertEqual(fuentes_bancos(self.empresa), [])

    def test_abm_colaborador_no_lee_ni_cambia_acuerdo_sin_permiso_bancos(self):
        """El ABM genérico no concede acceso al acuerdo de descubierto."""
        colaborador = User.objects.create_user('abm_banco_colab', password='Prueba123!')
        AsignacionUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=colaborador,
            jerarquia='colaborador', activo=True)
        PermisoAccesoColaborador.objects.create(empresa=self.empresa, usuario=colaborador,
            codigo='abm.cuentas', activo=True, otorgado_por=self.dueno)
        self.modificar()
        evento_count = EventoAcuerdoDescubierto.objects.count()
        self.client.force_login(colaborador)
        lista = self.client.get(reverse('listar_cuentas_bancarias'),
                                {'empresa': self.empresa.pk})
        self.assertEqual(lista.status_code, 200)
        self.assertNotIn('descubierto_importe', lista.json()['cuentas'][0])
        self.assertNotIn('data-cuenta-descubierto=', lista.json()['html'])
        self.assertNotIn('id="descubiertoImporteCuenta"', lista.json()['html'])
        r = self.client.post(reverse('modificar_cuenta_bancaria'), self.datos())
        self.assertEqual(r.status_code, 403)
        self.assertEqual(EventoAcuerdoDescubierto.objects.count(), evento_count)
        datos_legacy = self.datos()
        for campo in ('descubierto_importe','descubierto_vencimiento',
                      'descubierto_alerta_dias','descubierto_alerta_habilitada'):
            datos_legacy.pop(campo)
        r = self.client.post(reverse('modificar_cuenta_bancaria'), datos_legacy)
        self.assertEqual(r.status_code, 200, r.content)
        self.cuenta.refresh_from_db()
        self.assertEqual(self.cuenta.descubierto_importe, Decimal('1250000.50'))
        self.assertEqual(EventoAcuerdoDescubierto.objects.count(), evento_count)

    def test_backup_v1_restauracion_conserva_acuerdo_y_evento(self):
        """La historia y vencimiento sobreviven a exportar/restaurar Empresa."""
        import io
        import json
        import uuid
        import zipfile
        from usuarios.services.backup_empresa.exportacion import construir_backup_empresa
        from usuarios.services.backup_empresa.importacion import inspeccionar_backup
        from usuarios.services.backup_empresa.restauracion import restaurar_empresa
        from usuarios.services.backup_empresa.common import import_path

        self.modificar()
        blob, _ = construir_backup_empresa(self.empresa)
        with zipfile.ZipFile(io.BytesIO(blob)) as paquete:
            datos = json.loads(paquete.read('data/eventos_acuerdos_descubierto.json'))
            self.assertEqual(len(datos), 1)
        token = str(uuid.uuid4())
        with open(import_path(token), 'wb') as salida:
            salida.write(blob)
        info = inspeccionar_backup(token, self.dueno)
        restaurada = restaurar_empresa(token, self.dueno, {
            'empresa_existente_id': self.empresa.pk, 'empresa': info['empresa'],
            'documentos': {}, 'documentos_nombres': {}, 'usuarios': {},
        })
        cuenta = CuentaBancaria.objects.get(empresa=restaurada, nombre='CORRIENTE ARS')
        self.assertEqual(cuenta.descubierto_importe, Decimal('1250000.50'))
        self.assertTrue(cuenta.descubierto_alerta_habilitada)
        evento = EventoAcuerdoDescubierto.objects.get(empresa=restaurada)
        self.assertEqual(evento.cuenta_bancaria_id, cuenta.pk)
        self.assertEqual(evento.despues['importe'], '1250000.50')

    def test_backup_opcional_y_formulario_modal_sin_inlines_nuevos(self):
        from django.conf import settings
        from pathlib import Path
        self.assertIn('eventos_acuerdos_descubierto', SPEC_BY_KEY)
        self.assertIn('eventos_acuerdos_descubierto', OPTIONAL_NEW_KEYS)
        root = Path(settings.BASE_DIR)
        tpl = (root/'templates/usuarios/caja/dashboard.html').read_text(encoding='utf-8')
        self.assertIn('Descubierto disponible', tpl)
        self.assertIn('data-caja-banco-abrir', tpl)
        self.assertIn('id="cajaBancosForm"', tpl)
        self.assertNotIn('<script', tpl)
        abm = (root/'templates/usuarios/maestros/cuentas_bancarias.html').read_text(encoding='utf-8')
        self.assertIn('descubiertoAlertaActivaCuenta', abm)
        self.assertIn('descubiertoVencimientoCuenta', abm)
        self.assertNotIn('onchange=', abm)
