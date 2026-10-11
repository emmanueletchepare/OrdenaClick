"""Caja 2 y ajustes de historial: permisos Empresa/Centro, auditoría y no duplicación."""
import json
import tempfile
import zipfile
from unittest.mock import patch
from pathlib import Path
import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from usuarios.models import (AsignacionUsuarioEmpresa, Banco, Caja, CentroOperativo,
    Cobranza, CorreccionMovimientoCaja, CuentaBancaria, Empresa,
    EventoPendienteBancario, EventoPermisoBancario, MovimientoCaja,
    Pago, PendienteBancario, PermisoPendienteBancarioCentro)
from usuarios.services.caja_disponibilidad import saldo_efectivo_caja
from usuarios.services.identidades import obtener_identidad_usuario_empresa
from usuarios.services.backup_empresa.specs import MODEL_SPECS


class Caja2SeguridadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dueno = User.objects.create_user('c2_dueno', password='Caja2!2026')
        cls.ajeno = User.objects.create_user('c2_ajeno', password='Caja2!2026')
        cls.general = User.objects.create_user('c2_general', password='Caja2!2026')
        cls.centro_admin = User.objects.create_user('c2_centro', password='Caja2!2026')
        cls.colaborador = User.objects.create_user('c2_colab', password='Caja2!2026')
        cls.empresa = Empresa.objects.create(propietario=cls.dueno, razon_social='Caja Dos')
        cls.otra_empresa = Empresa.objects.create(propietario=cls.ajeno, razon_social='Otra Caja Dos')
        cls.central = CentroOperativo.objects.create(empresa=cls.empresa, nombre='Olavarria', tipo='Casa Central')
        cls.tandil = CentroOperativo.objects.create(empresa=cls.empresa, nombre='Tandil', tipo='Sucursal')
        cls.otro_centro = CentroOperativo.objects.create(empresa=cls.otra_empresa, nombre='Otro centro', tipo='Sucursal')
        cls.caja_central = Caja.objects.create(empresa=cls.empresa, centro_operativo=cls.central, nombre='Central')
        cls.caja_tandil = Caja.objects.create(empresa=cls.empresa, centro_operativo=cls.tandil, nombre='Sucursal')
        cls.banco = Banco.objects.create(empresa=cls.empresa, nombre='Banco Prueba')
        cls.otro_banco = Banco.objects.create(empresa=cls.otra_empresa, nombre='Otro Banco')
        cls.cuenta = CuentaBancaria.objects.create(empresa=cls.empresa, banco=cls.banco,
            nombre='Cuenta corriente', tipo_cuenta='CuentaCorriente')
        cls.cuenta_ajena = CuentaBancaria.objects.create(empresa=cls.otra_empresa, banco=cls.otro_banco,
            nombre='Cuenta ajena', tipo_cuenta='CuentaCorriente')
        for user, jerarquia, centro in (
            (cls.general, 'admin_general', None),
            (cls.centro_admin, 'admin_centro', cls.tandil),
            (cls.colaborador, 'colaborador', None)):
            AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=user,
                jerarquia=jerarquia, centro_operativo=centro, activo=True)

    def pendiente_data(self, *, centro=None, **extra):
        datos = dict(empresa=self.empresa.pk, cuenta=self.cuenta.pk,
            centro=self.tandil.pk if centro is None else centro, fecha=date.today().isoformat(),
            tipo='Transferencia', importe='9000.00', referencia='Transferencia cliente 12',
            observaciones='Por confirmar con gestión externa', clave=str(uuid.uuid4()))
        datos.update(extra)
        return datos

    def alta(self, user=None, datos=None):
        self.client.force_login(user or self.general)
        return self.client.post(reverse('registrar_pendiente_bancario'),
            datos if datos is not None else self.pendiente_data())

    def conceder(self, activo='1', usuario=None, centro=None, admin=None):
        self.client.force_login(admin or self.general)
        return self.client.post(reverse('asignar_centro_gestion_bancaria'), dict(
            empresa=self.empresa.pk, usuario=(usuario or self.colaborador).pk,
            centro=(centro or self.tandil).pk, activo=activo))

    def test_alta_pendiente_no_contabiliza_efectivo_ni_pago(self):
        self.assertEqual(self.alta().status_code, 302)
        p = PendienteBancario.objects.get()
        self.assertEqual(p.estado, 'Pendiente')
        self.assertEqual(p.importe, Decimal('9000.00'))
        self.assertEqual(EventoPendienteBancario.objects.filter(pendiente=p, accion='Creado').count(), 1)
        self.assertFalse(MovimientoCaja.objects.exists())
        self.assertFalse(Pago.objects.exists())

    def test_colaborador_sin_permiso_no_accede(self):
        self.client.force_login(self.colaborador)
        resp=self.client.get(reverse('gestion_bancaria'), {'empresa':self.empresa.pk})
        self.assertEqual(resp.status_code, 403)

    def test_asignacion_por_centro_no_da_caja(self):
        self.assertEqual(self.conceder().status_code, 302)
        self.client.force_login(self.colaborador)
        self.assertEqual(self.client.get(reverse('gestion_bancaria'), {'empresa':self.empresa.pk}).status_code, 200)
        self.assertEqual(self.client.get(reverse('panel_caja'), {'empresa':self.empresa.pk}).status_code, 403)
        self.assertEqual(self.client.get(reverse('historial_movimientos_caja'),
            {'empresa':self.empresa.pk, 'caja':'todas'}).status_code, 403)
        self.assertEqual(EventoPermisoBancario.objects.count(), 1)

    def test_administrador_centro_no_ve_centro_ajeno(self):
        self.alta()
        self.alta(datos=self.pendiente_data(centro=self.central.pk, clave=str(uuid.uuid4())))
        self.client.force_login(self.centro_admin)
        html = self.client.get(reverse('gestion_bancaria'), {'empresa':self.empresa.pk}).content.decode()
        self.assertIn('Tandil', html)
        self.assertNotIn('Por identificar', html)
        self.assertEqual(self.client.get(reverse('gestion_bancaria'), {
            'empresa':self.empresa.pk,'centro':self.central.pk}).status_code,403)

    def test_colaborador_solo_ve_su_centro(self):
        self.alta(datos=self.pendiente_data(referencia='Visible Tandil'))
        self.alta(datos=self.pendiente_data(centro=self.central.pk, referencia='OCULTO OLAVARRIA'))
        self.conceder()
        self.client.force_login(self.colaborador)
        html = self.client.get(reverse('gestion_bancaria'), {'empresa':self.empresa.pk}).content.decode()
        self.assertIn('Visible Tandil', html)
        self.assertNotIn('OCULTO OLAVARRIA', html)

    def test_colaborador_autorizado_resuelve_sin_crear_pago(self):
        self.alta()
        self.conceder()
        p=PendienteBancario.objects.get()
        self.client.force_login(self.colaborador)
        r=self.client.post(reverse('resolver_pendiente_bancario',args=[p.pk]),{
            'empresa':self.empresa.pk,'tipo_resolucion':'YaImputado','referencia_resolucion':'Recibo externo 82'})
        self.assertEqual(r.status_code,302)
        p.refresh_from_db()
        self.assertEqual(p.estado,'Resuelto')
        self.assertEqual(p.resuelto_por.usuario_id,self.colaborador.pk)
        self.assertEqual(EventoPendienteBancario.objects.count(),2)
        self.assertFalse(Pago.objects.exists())

    def test_clasificacion_era_solo_general_y_desbloquea_colaborador(self):
        self.alta(datos=self.pendiente_data(centro=''))
        p=PendienteBancario.objects.get()
        self.conceder()
        self.client.force_login(self.colaborador)
        self.assertEqual(self.client.post(reverse('clasificar_pendiente_bancario',args=[p.pk]),
            {'empresa':self.empresa.pk,'centro':self.tandil.pk}).status_code,403)
        self.client.force_login(self.general)
        self.assertEqual(self.client.post(reverse('clasificar_pendiente_bancario',args=[p.pk]),
            {'empresa':self.empresa.pk,'centro':self.tandil.pk}).status_code,302)
        p.refresh_from_db();self.assertEqual(p.centro_operativo_id,self.tandil.pk)
        self.client.force_login(self.colaborador)
        html=self.client.get(reverse('gestion_bancaria'),{'empresa':self.empresa.pk}).content.decode()
        self.assertIn('Transferencia cliente 12',html)
        self.assertEqual(EventoPendienteBancario.objects.filter(accion='CentroAsignado').count(),1)

    def test_no_resolver_dos_veces(self):
        self.alta(); p=PendienteBancario.objects.get()
        self.client.force_login(self.general)
        url=reverse('resolver_pendiente_bancario', args=[p.pk]); datos=dict(
            empresa=self.empresa.pk, tipo_resolucion='ReciboGenerado', referencia_resolucion='Recibo 73')
        self.assertEqual(self.client.post(url,datos).status_code,302)
        self.assertEqual(self.client.post(url,datos).status_code,409)
        self.assertEqual(EventoPendienteBancario.objects.count(),2)

    def test_revocacion_inmediata(self):
        self.conceder('1'); self.assertEqual(self.conceder('0').status_code,302)
        self.client.force_login(self.colaborador)
        self.assertEqual(self.client.get(reverse('gestion_bancaria'),{'empresa':self.empresa.pk}).status_code,403)
        self.assertEqual(EventoPermisoBancario.objects.count(),2)

    def test_admin_centro_no_puede_conceder_permisos(self):
        self.assertEqual(self.conceder(admin=self.centro_admin).status_code,403)
        self.assertFalse(PermisoPendienteBancarioCentro.objects.exists())

    def test_colaborador_no_puede_registrar_operacion(self):
        self.conceder()
        self.assertEqual(self.alta(user=self.colaborador).status_code,403)
        self.assertFalse(PendienteBancario.objects.exists())

    def test_cuenta_y_centro_ajenos_se_rechazan(self):
        d=self.pendiente_data()
        d['cuenta']=self.cuenta_ajena.pk
        self.assertEqual(self.alta(datos=d).status_code,400)
        d=self.pendiente_data()
        d['centro']=self.otro_centro.pk
        self.assertEqual(self.alta(datos=d).status_code,403)
        self.assertFalse(PendienteBancario.objects.exists())

    def test_pendiente_sin_centro_solo_admin_general(self):
        d=self.pendiente_data(centro='')
        self.assertEqual(self.alta(datos=d).status_code,302)
        self.assertEqual(self.alta(user=self.centro_admin,datos=self.pendiente_data(centro='')).status_code,403)

    def test_admin_centro_no_registra_en_caja_de_central(self):
        self.assertEqual(self.alta(user=self.centro_admin,datos=self.pendiente_data(centro=self.central.pk)).status_code,403)

    def test_clave_idempotente_no_duplica(self):
        datos=self.pendiente_data()
        self.assertEqual(self.alta(datos=datos).status_code,302)
        self.assertEqual(self.alta(datos=datos).status_code,302)
        self.assertEqual(PendienteBancario.objects.count(),1)
        datos['importe']='99.00'
        self.assertEqual(self.alta(datos=datos).status_code,400)

    def test_empresa_no_autorizada_prohibida(self):
        self.client.force_login(self.general)
        self.assertEqual(self.client.get(reverse('gestion_bancaria'), {'empresa': self.otra_empresa.pk}).status_code,403)

    def test_csrf_y_metodos(self):
        c=Client(enforce_csrf_checks=True)
        c.force_login(self.general)
        self.assertEqual(c.post(reverse('registrar_pendiente_bancario'), self.pendiente_data()).status_code,403)
        self.assertEqual(c.post(reverse('asignar_centro_gestion_bancaria'),
            {'empresa':self.empresa.pk,'usuario':self.colaborador.pk,'centro':self.tandil.pk,'activo':'1'}).status_code,403)
        self.assertEqual(self.client.get(reverse('registrar_pendiente_bancario')).status_code,302) # anon login
        self.client.force_login(self.general)
        self.assertEqual(self.client.get(reverse('registrar_pendiente_bancario')).status_code,405)

    def test_backup_exporta_hechos_pero_no_permisos(self):
        modelos={spec.model.__name__ for spec in MODEL_SPECS}
        for nombre in ('PendienteBancario','EventoPendienteBancario','CorreccionMovimientoCaja'):
            self.assertIn(nombre, modelos)
        self.assertNotIn('PermisoPendienteBancarioCentro', modelos)
        self.assertNotIn('EventoPermisoBancario', modelos)

    def test_backup_v1_antiguo_admite_componentes_nuevos_ausentes(self):
        from usuarios.services.backup_empresa import importacion
        from usuarios.services.backup_empresa.specs import OPTIONAL_NEW_KEYS
        self.assertTrue(OPTIONAL_NEW_KEYS)
        with tempfile.TemporaryDirectory() as tmp:
            archivo_zip = Path(tmp) / 'backup-v1-antiguo.zip'
            with zipfile.ZipFile(archivo_zip, 'w') as archivo:
                archivo.writestr('data/empresa.json', '{}')
            with patch.object(importacion, 'import_path', return_value=archivo_zip):
                self.assertEqual(importacion.cargar_json_backup('dummy',
                    'data/pendientes_bancarios.json', optional=True), [])

    def _movimiento(self, tipo='Ingreso', importe='100.00', caja=None, cobranza=None):
        identidad=obtener_identidad_usuario_empresa(empresa=self.empresa, usuario=self.dueno)
        return MovimientoCaja.objects.create(empresa=self.empresa, caja=caja or self.caja_central,
            cobranza=cobranza, tipo=tipo, moneda='ARS', fecha=date.today(), importe=Decimal(importe),
            concepto='Movimiento original', creado_por=identidad)

    def _corregir(self, mov, *, accion='Editar', monto='75.00', user=None, clave=None):
        self.client.force_login(user or self.dueno)
        datos={'empresa_id':self.empresa.pk,'caja_id':mov.caja_id,'accion':accion,
               'motivo':'Error de monto de prueba','clave':clave or str(uuid.uuid4())}
        if accion=='Editar':
            datos['nuevo']={'fecha':date.today().isoformat(),'tipo':'Ingreso','moneda':'ARS',
                            'importe':monto,'concepto':'Correcto'}
        return self.client.post(reverse('corregir_movimiento_caja', args=[mov.pk]),
            data=json.dumps(datos),content_type='application/json')

    def test_editar_crea_contraasiento_y_reemplazo_sin_borrar_original(self):
        mov=self._movimiento()
        r=self._corregir(mov)
        self.assertEqual(r.status_code,201,r.content)
        self.assertTrue(MovimientoCaja.objects.filter(pk=mov.pk).exists())
        self.assertEqual(MovimientoCaja.objects.count(),3)
        self.assertEqual(saldo_efectivo_caja(self.empresa,self.caja_central,'ARS'),Decimal('75.00'))
        c=CorreccionMovimientoCaja.objects.get()
        self.assertEqual(c.original, mov)
        self.assertEqual(c.reemplazo.importe, Decimal('75.00'))

    def test_anular_crea_contraasiento_sin_borrar(self):
        mov=self._movimiento();r=self._corregir(mov,accion='Anular')
        self.assertEqual(r.status_code,201)
        self.assertEqual(MovimientoCaja.objects.count(),2)
        self.assertEqual(saldo_efectivo_caja(self.empresa,self.caja_central,'ARS'),Decimal('0.00'))

    def test_no_anular_ingreso_si_deja_saldo_negativo(self):
        mov=self._movimiento(importe='100.00')
        self._movimiento(tipo='Egreso', importe='99.00')
        self.assertEqual(self._corregir(mov,accion='Anular').status_code,400)
        self.assertEqual(CorreccionMovimientoCaja.objects.count(),0)
        self.assertEqual(MovimientoCaja.objects.count(),2)

    def test_no_alterar_cobranza_por_tabla_manual(self):
        identidad=obtener_identidad_usuario_empresa(empresa=self.empresa, usuario=self.dueno)
        cobranza=Cobranza.objects.create(empresa=self.empresa,caja=self.caja_central,
            fecha=date.today(),referencia='Cobranza real',creado_por=identidad)
        mov=self._movimiento(cobranza=cobranza)
        self.assertEqual(self._corregir(mov).status_code,403)
        self.assertEqual(MovimientoCaja.objects.count(),1)

    def test_otra_caja_no_se_corrige_por_admin_centro(self):
        mov=self._movimiento(caja=self.caja_central)
        self.assertEqual(self._corregir(mov,user=self.centro_admin).status_code,403)

    def test_segunda_correccion_y_corregir_contraasiento_prohibidos(self):
        mov=self._movimiento()
        self.assertEqual(self._corregir(mov).status_code,201)
        self.assertEqual(self._corregir(mov).status_code,403)
        c=CorreccionMovimientoCaja.objects.get()
        self.assertEqual(self._corregir(c.contraasiento).status_code,403)

    def test_misma_clave_mismo_payload_es_idempotente(self):
        mov=self._movimiento();clave=str(uuid.uuid4())
        self.assertEqual(self._corregir(mov,clave=clave).status_code,201)
        self.assertEqual(self._corregir(mov,clave=clave).status_code,200)
        self.assertEqual(CorreccionMovimientoCaja.objects.count(),1)

    def test_correccion_get_no_modifica_y_csrf(self):
        mov=self._movimiento();url=reverse('corregir_movimiento_caja',args=[mov.pk]);
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(url).status_code,405)
        c=Client(enforce_csrf_checks=True);c.force_login(self.dueno)
        self.assertEqual(c.post(url, data=json.dumps({'empresa_id':self.empresa.pk}), content_type='application/json').status_code,403)
        self.assertEqual(MovimientoCaja.objects.count(),1)
