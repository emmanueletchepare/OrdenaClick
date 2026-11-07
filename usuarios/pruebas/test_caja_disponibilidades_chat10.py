"""Chat 10: lectura de e-Cheqs y actualización auditada bancaria sin efectos cruzados."""
import json
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from usuarios.models import (AsignacionUsuarioEmpresa, Banco, Caja, CentroOperativo,
    CuentaBancaria, Empresa, PendienteBancario, PermisoAccesoColaborador,
    SaldoInformadoCuentaBancaria)
from usuarios.services.caja_echeqs import resumen_echeqs_en_cartera
from usuarios.services.identidades import obtener_identidad_usuario_empresa


class CajaDisponibilidadesChat10Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dueno = User.objects.create_user('c10_dueno', password='Prueba123!')
        cls.ajeno = User.objects.create_user('c10_ajeno', password='Prueba123!')
        cls.general = User.objects.create_user('c10_general', password='Prueba123!')
        cls.sucursal = User.objects.create_user('c10_sucursal', password='Prueba123!')
        cls.colab = User.objects.create_user('c10_colab', password='Prueba123!')
        cls.empresa = Empresa.objects.create(propietario=cls.dueno, razon_social='Empresa Chat 10')
        cls.otra_empresa = Empresa.objects.create(propietario=cls.ajeno, razon_social='Empresa Ajena')
        cls.central = CentroOperativo.objects.create(empresa=cls.empresa, tipo='Casa Central', nombre='Central', activo=True)
        cls.suc = CentroOperativo.objects.create(empresa=cls.empresa, tipo='Sucursal', nombre='Tandil', activo=True)
        cls.caja = Caja.objects.create(empresa=cls.empresa, centro_operativo=cls.central, nombre='Principal', activo=True)
        cls.caja_suc = Caja.objects.create(empresa=cls.empresa, centro_operativo=cls.suc, nombre='Principal', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.general, jerarquia='admin_general', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.sucursal,
            jerarquia='admin_centro', centro_operativo=cls.suc, activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.colab,
            jerarquia='colaborador', activo=True)
        cls.banco = Banco.objects.create(empresa=cls.empresa, nombre='BANCO CAJA 10', activo=True)
        cls.cuenta = CuentaBancaria.objects.create(empresa=cls.empresa, banco=cls.banco,
            nombre='Corriente ARS', tipo_cuenta='CuentaCorriente', moneda='ARS', activo=True)
        cls.cuenta_usd = CuentaBancaria.objects.create(empresa=cls.empresa, banco=cls.banco,
            nombre='Ahorro USD', tipo_cuenta='CajaAhorro', moneda='USD', activo=True)
        cls.cuenta_inactiva = CuentaBancaria.objects.create(empresa=cls.empresa, banco=cls.banco,
            nombre='Inactiva', tipo_cuenta='CuentaCorriente', moneda='ARS', activo=False)
        cls.banco_ajeno = Banco.objects.create(empresa=cls.otra_empresa, nombre='BANCO AJENO', activo=True)
        cls.cuenta_ajena = CuentaBancaria.objects.create(empresa=cls.otra_empresa,
            banco=cls.banco_ajeno, nombre='SECRETO AJENO', tipo_cuenta='CuentaCorriente', activo=True)
        cls.actor = obtener_identidad_usuario_empresa(empresa=cls.empresa, usuario=cls.dueno)
        cls.actor_ajeno = obtener_identidad_usuario_empresa(empresa=cls.otra_empresa, usuario=cls.ajeno)

    def crear_echeq(self, *, importe, estado='Pendiente', cartera='EnCartera', empresa=None, actor=None):
        empresa = empresa or self.empresa
        return PendienteBancario.objects.create(empresa=empresa, tipo='ECheq', clave=uuid4(),
            fecha=timezone.localdate(), importe=Decimal(importe), referencia='ECHEQ TEST',
            estado=estado, estado_cartera=cartera, creado_por=actor or self.actor,
            echeq_numero='12345678', echeq_titular='Titular')

    def panel(self, usuario, empresa=None):
        self.client.force_login(usuario)
        return self.client.get(reverse('panel_caja'), {'empresa': (empresa or self.empresa).pk})

    def guardar(self, usuario, filas, clave=None, empresa=None):
        self.client.force_login(usuario)
        return self.client.post(reverse('actualizar_disponibles_bancarios'),
            data=json.dumps({'empresa': (empresa or self.empresa).pk, 'filas': filas,
                             'clave': str(clave or uuid4())}), content_type='application/json')

    def valores(self, **ajustes):
        return [{'cuenta_id': self.cuenta.pk, 'importe': ajustes.get('ars', '1.234,56')},
                {'cuenta_id': self.cuenta_usd.pk, 'importe': ajustes.get('usd', '20.00')}]

    def test_echeqs_cartera_incluye_pendientes_y_resueltos_sin_cambiar_estados(self):
        en_espera = self.crear_echeq(importe='100.00')
        aplicado = self.crear_echeq(importe='250.75', estado='Resuelto')
        fuera = self.crear_echeq(importe='1000.00', cartera='Rechazado')
        salido = self.crear_echeq(importe='2000.00', cartera='Depositado')
        ajeno = self.crear_echeq(importe='3000.00', empresa=self.otra_empresa, actor=self.actor_ajeno)
        resumen = resumen_echeqs_en_cartera(self.empresa)
        self.assertEqual(resumen['total'], Decimal('350.75'))
        self.assertEqual(resumen['cantidad'], 2)
        html = self.panel(self.dueno).json()['html']
        self.assertIn('data-valor="350.75"', html)
        for e, estado, cartera in ((en_espera,'Pendiente','EnCartera'),
                                   (aplicado,'Resuelto','EnCartera'),
                                   (fuera,'Pendiente','Rechazado'),
                                   (salido,'Pendiente','Depositado'),
                                   (ajeno,'Pendiente','EnCartera')):
            e.refresh_from_db()
            self.assertEqual((e.estado,e.estado_cartera),(estado,cartera))

    def test_caja_total_agrupa_por_disponibilidad_y_muestra_tres_pies(self):
        """Cada box contiene las Cajas; el total va en una franja independiente."""
        html = self.panel(self.dueno).json()['html']
        bloque = html.split('data-caja-resumen="todas"', 1)[1].split('</section>', 1)[0]
        self.assertIn('data-caja-total-grid', bloque)
        self.assertEqual(bloque.count('class="caja-total-columna"'), 3)
        self.assertEqual(bloque.count('class="caja-total-renglon"'), 6)
        self.assertEqual(bloque.count('caja-total-pie'), 3)
        self.assertNotIn('caja-total-fila', bloque)
        self.assertNotIn('data-caja-total-detalle', bloque)
        self.assertEqual(bloque.count('data-caja-importe'), 9)
        self.assertIn(f'data-caja-resumen="{self.caja.pk}"', html)
        self.assertIn(f'data-caja-resumen="{self.caja_suc.pk}"', html)
        self.assertIn('data-caja-bancos-detalle', html)  # El detalle ahora está dentro del box.

    def test_bancos_informados_dentro_del_box_y_titulo_echeqs(self):
        """Un solo box bancario, con cuentas dentro, sin tarjetas duplicadas."""
        html = self.panel(self.dueno).json()['html']
        otras = html.split('<h3>Otras disponibilidades</h3>', 1)[1].split('id="cajaBancosEdicion"', 1)[0]
        self.assertIn('E-cheqs en cartera', otras)
        self.assertNotIn('e-Cheqs en cartera\n', otras)
        self.assertEqual(otras.count('caja-bancos-integrados'), 1)
        self.assertEqual(otras.count('data-caja-bancos-detalle'), 1)
        self.assertEqual(otras.count('caja-bancos-renglon'), 2)
        self.assertNotIn('caja-banco-fila', otras)
        self.assertIn('BANCO CAJA 10', otras)
        self.assertIn('Corriente ARS', otras)
        self.assertIn('Ahorro USD', otras)
        self.assertEqual(html.count('id="cajaBancosForm"'), 1)

    def test_bancos_no_filtran_ni_muestran_cuentas_ajenas_y_si_historian_posiciones(self):
        e = self.crear_echeq(importe='100.00')
        r = self.guardar(self.dueno, self.valores())
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(SaldoInformadoCuentaBancaria.objects.count(), 2)
        html = self.panel(self.dueno).json()['html']
        self.assertIn('BANCO CAJA 10', html)
        self.assertNotIn('SECRETO AJENO', html)
        self.assertNotIn('Inactiva', html)
        self.assertIn('data-valor="1234.56"', html)
        self.assertIn('data-valor="20.00"', html)
        self.assertIn('data-caja-bancos-detalle', html)
        e.refresh_from_db()
        self.assertEqual((e.estado,e.estado_cartera),('Pendiente','EnCartera'))
        nuevo = self.guardar(self.dueno, [{'cuenta_id': self.cuenta.pk, 'importe': '-150,00'}])
        self.assertEqual(nuevo.status_code, 200)
        self.assertEqual(SaldoInformadoCuentaBancaria.objects.count(), 3)
        self.assertIn('data-valor="-150.00"', self.panel(self.dueno).json()['html'])

    def test_idempotencia_y_error_no_escriben_parcialmente(self):
        clave = uuid4()
        self.assertEqual(self.guardar(self.dueno,self.valores(),clave).status_code,200)
        self.assertEqual(self.guardar(self.dueno,self.valores(),clave).json()['actualizado'], False)
        self.assertEqual(SaldoInformadoCuentaBancaria.objects.count(), 2)
        self.assertEqual(self.guardar(self.dueno,self.valores(ars='2.000,00'),clave).status_code,400)
        self.assertEqual(self.guardar(self.dueno,self.valores(usd='no importe')).status_code,400)
        self.assertEqual(self.guardar(self.dueno,[{'cuenta_id':self.cuenta.pk,'importe':'100.00'},
            {'cuenta_id':self.cuenta.pk,'importe':'200.00'}]).status_code,400)
        self.assertEqual(SaldoInformadoCuentaBancaria.objects.count(), 2)

    def test_aislamiento_y_permisos_bancos(self):
        PermisoAccesoColaborador.objects.create(empresa=self.empresa, usuario=self.sucursal,
            codigo='caja.total', activo=True, otorgado_por=self.dueno)
        sin_permiso = self.panel(self.sucursal).json()['html']
        self.assertIn('data-caja-accion="actualizar-bancos"',sin_permiso)
        self.assertNotIn('BANCO CAJA 10',sin_permiso)
        self.assertEqual(self.guardar(self.sucursal,self.valores()).status_code,403)
        for codigo in ('caja.bancos_actualizar',):
            PermisoAccesoColaborador.objects.create(empresa=self.empresa, usuario=self.sucursal,
                codigo=codigo, activo=True, otorgado_por=self.dueno)
        html = self.panel(self.sucursal).json()['html']
        self.assertIn('BANCO CAJA 10',html)
        self.assertEqual(self.guardar(self.sucursal,self.valores()).status_code,200)
        self.assertEqual(self.guardar(self.colab,self.valores()).status_code,403)
        self.assertEqual(self.guardar(self.dueno,[{'cuenta_id':self.cuenta_ajena.pk, 'importe':'20'}]).status_code,403)
        self.assertEqual(self.guardar(self.dueno,[{'cuenta_id':self.cuenta_inactiva.pk, 'importe':'20'}]).status_code,403)
        self.assertEqual(self.panel(self.dueno,self.otra_empresa).status_code,403)

    def test_permiso_bancos_independiente_del_abm_y_revocable(self):
        """El ABM no autoriza Bancos; una casilla propia habilita y revoca."""
        from usuarios.services.accesos_colaborador import puede
        PermisoAccesoColaborador.objects.create(empresa=self.empresa, usuario=self.sucursal,
            codigo='caja.total', activo=True, otorgado_por=self.dueno)
        PermisoAccesoColaborador.objects.create(empresa=self.empresa, usuario=self.sucursal,
            codigo='abm.cuentas', activo=True, otorgado_por=self.dueno)
        self.assertEqual(self.guardar(self.sucursal, self.valores()).status_code, 403)
        self.assertNotIn('BANCO CAJA 10', self.panel(self.sucursal).json()['html'])
        self.assertFalse(puede(self.sucursal,self.empresa.pk,'caja.bancos_actualizar'))
        permiso = PermisoAccesoColaborador.objects.create(empresa=self.empresa,
            usuario=self.sucursal, codigo='caja.bancos_actualizar', activo=True,
            otorgado_por=self.dueno)
        self.assertTrue(puede(self.sucursal,self.empresa.pk,'caja.bancos_actualizar'))
        self.assertEqual(self.guardar(self.sucursal, self.valores()).status_code, 200)
        self.assertIn('BANCO CAJA 10', self.panel(self.sucursal).json()['html'])
        permiso.activo = False
        permiso.save(update_fields=['activo'])
        self.assertEqual(self.guardar(self.sucursal,self.valores()).status_code,403)
        self.assertNotIn('BANCO CAJA 10', self.panel(self.sucursal).json()['html'])

    def test_casilla_independiente_usa_gestion_accesos_existente(self):
        """El Admin general concede/revoca en el gestor, sin nuevo sidebar."""
        from usuarios.services.accesos_colaborador import puede
        from usuarios.models import EventoPermisoAccesoColaborador
        url=reverse('gestion_accesos_colaborador', args=[self.empresa.pk])
        self.client.force_login(self.dueno)
        pagina=self.client.get(url, {'usuario':self.sucursal.pk})
        self.assertEqual(pagina.status_code,200)
        self.assertIn('value="caja.bancos_actualizar"',pagina.content.decode())
        self.assertIn('Actualizar Bancos',pagina.content.decode())
        conceder=self.client.post(url, {'usuario':self.sucursal.pk,
            'capacidad':['caja.total','caja.bancos_actualizar']})
        self.assertEqual(conceder.status_code,302)
        self.assertTrue(puede(self.sucursal,self.empresa.pk,'caja.bancos_actualizar'))
        self.assertFalse(puede(self.sucursal,self.empresa.pk,'abm.cuentas'))
        self.assertEqual(self.guardar(self.sucursal,self.valores()).status_code,200)
        self.client.force_login(self.dueno)
        revocar=self.client.post(url, {'usuario':self.sucursal.pk,
            'capacidad':['caja.total']})
        self.assertEqual(revocar.status_code,302)
        self.assertFalse(puede(self.sucursal,self.empresa.pk,'caja.bancos_actualizar'))
        self.assertTrue(puede(self.sucursal,self.empresa.pk,'caja.total'))
        self.assertTrue(EventoPermisoAccesoColaborador.objects.filter(
            empresa=self.empresa, usuario=self.sucursal,
            codigo='caja.bancos_actualizar', activo=False).exists())
        self.assertEqual(self.guardar(self.sucursal,self.valores()).status_code,403)

    def test_colaborador_no_recibe_permiso_bancario_aun_forzando_post(self):
        """La casilla no amplia permisos para Colaborador ni cambia Pendientes."""
        url=reverse('gestion_accesos_colaborador', args=[self.empresa.pk])
        self.client.force_login(self.dueno)
        pagina=self.client.get(url, {'usuario':self.colab.pk})
        self.assertEqual(pagina.status_code,200)
        self.assertIn('Actualizar Bancos · disponible informado', pagina.content.decode())
        self.assertNotIn('value="caja.bancos_actualizar"', pagina.content.decode())
        intento=self.client.post(url, {'usuario':self.colab.pk,
            'capacidad':['caja.bancos_actualizar']})
        self.assertEqual(intento.status_code,403)
        self.assertFalse(PermisoAccesoColaborador.objects.filter(
            empresa=self.empresa,usuario=self.colab,codigo='caja.bancos_actualizar',activo=True).exists())
        self.assertEqual(self.guardar(self.colab,self.valores()).status_code,403)

    def test_modificar_cuenta_de_otra_empresa_es_prohibido_incluso_con_rol_general(self):
        r = self.guardar(self.general,[{'cuenta_id':self.cuenta_ajena.pk,'importe':'10.00'}])
        self.assertEqual(r.status_code,403)
        self.assertFalse(SaldoInformadoCuentaBancaria.objects.exists())

    def test_no_cambia_pendientes_caja_ni_otros_modelos_financieros(self):
        p = self.crear_echeq(importe='999.00')
        self.assertEqual(self.guardar(self.general,self.valores()).status_code,200)
        p.refresh_from_db()
        self.assertEqual((p.estado,p.estado_cartera),('Pendiente','EnCartera'))
        self.assertIn('data-valor="999"',self.panel(self.general).json()['html'])

    def test_backup_v1_conserva_posiciones_con_actor_y_referencias(self):
        """El nuevo componente es portable sin modificar la estructura de Backup v1."""
        import io
        import zipfile
        from django.core.files.uploadedfile import SimpleUploadedFile
        from usuarios.services.backup_empresa.exportacion import construir_backup_empresa
        from usuarios.services.backup_empresa.importacion import guardar_upload_temporal, inspeccionar_backup
        from usuarios.services.backup_empresa.restauracion import restaurar_empresa

        self.assertEqual(self.guardar(self.dueno, self.valores()).status_code, 200)
        original = list(SaldoInformadoCuentaBancaria.objects.filter(empresa=self.empresa)
                        .values_list('cuenta_bancaria__nombre', 'importe', 'creado_por__username_historico'))
        blob, manifest = construir_backup_empresa(self.empresa)
        self.assertEqual(manifest['components']['saldos_bancarios_informados'], 2)
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            items = json.loads(z.read('data/saldos_bancarios_informados.json'))
            self.assertEqual(len(items), 2)
        token = guardar_upload_temporal(SimpleUploadedFile('caja10.zip', blob))
        info = inspeccionar_backup(token, self.dueno)
        empresa = restaurar_empresa(token, self.dueno, {
            'empresa_existente_id': self.empresa.pk, 'empresa': info['empresa'],
            'documentos': {}, 'documentos_nombres': {}, 'usuarios': {},
        })
        restaurados = list(SaldoInformadoCuentaBancaria.objects.filter(empresa=empresa)
                         .values_list('cuenta_bancaria__nombre', 'importe', 'creado_por__username_historico'))
        self.assertCountEqual(restaurados, original)

    def test_depositos_y_transferencias_pendientes_permanecen_globales(self):
        """Informar Bancos nunca clasifica ni confirma pagos bancarios detectados."""
        pendientes = [PendienteBancario.objects.create(
            empresa=self.empresa, cuenta_bancaria=self.cuenta,
            tipo=tipo, clave=uuid4(), fecha=timezone.localdate(),
            importe=Decimal('950.00'), referencia='PENDIENTE SIN CENTRO',
            creado_por=self.actor) for tipo in ('Transferencia', 'Deposito')]
        self.assertEqual(self.guardar(self.dueno, self.valores()).status_code, 200)
        for pendiente in pendientes:
            pendiente.refresh_from_db()
            self.assertEqual(pendiente.estado, 'Pendiente')
            self.assertIsNone(pendiente.centro_operativo_id)
            self.assertEqual(pendiente.importe, Decimal('950.00'))

    def test_solo_post_y_csrf_exigido(self):
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(reverse('actualizar_disponibles_bancarios')).status_code,405)
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.dueno)
        r = c.post(reverse('actualizar_disponibles_bancarios'),
            data=json.dumps({'empresa':self.empresa.pk,'filas':self.valores(),'clave':str(uuid4())}),
            content_type='application/json')
        self.assertEqual(r.status_code,403)
