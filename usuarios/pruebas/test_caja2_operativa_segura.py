"""Caja 2 revisión: alcance global por Empresa, lotes, e-Cheqs y Caja segura."""
import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch
import uuid
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from usuarios.models import (
    AsignacionUsuarioEmpresa, Banco, Caja, CentroOperativo, Cobranza,
    CorreccionMovimientoCaja, CuentaBancaria, Empresa, EventoPendienteBancario,
    EventoPermisoBancario, MovimientoCaja, Pago, PendienteBancario,
    PermisoPendienteBancarioCentro, Cheque,
)
from usuarios.services.caja_disponibilidad import saldo_efectivo_caja
from usuarios.services.identidades import obtener_identidad_usuario_empresa
from usuarios.services.backup_empresa.specs import MODEL_SPECS


class Caja2SeguridadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dueno=User.objects.create_user('c2_dueno',password='Caja2!2026')
        cls.ajeno=User.objects.create_user('c2_ajeno',password='Caja2!2026')
        cls.general=User.objects.create_user('c2_general',password='Caja2!2026')
        cls.centro_admin=User.objects.create_user('c2_centro',password='Caja2!2026')
        cls.colaborador=User.objects.create_user('c2_colab',password='Caja2!2026')
        cls.empresa=Empresa.objects.create(propietario=cls.dueno,razon_social='Caja Dos')
        cls.otra_empresa=Empresa.objects.create(propietario=cls.ajeno,razon_social='Otra Caja Dos')
        cls.central=CentroOperativo.objects.create(empresa=cls.empresa,nombre='Olavarria',tipo='Casa Central')
        cls.tandil=CentroOperativo.objects.create(empresa=cls.empresa,nombre='Tandil',tipo='Sucursal')
        cls.otro_centro=CentroOperativo.objects.create(empresa=cls.otra_empresa,nombre='Otro centro',tipo='Sucursal')
        cls.caja_central=Caja.objects.create(empresa=cls.empresa,centro_operativo=cls.central,nombre='Central')
        cls.caja_tandil=Caja.objects.create(empresa=cls.empresa,centro_operativo=cls.tandil,nombre='Sucursal')
        cls.banco=Banco.objects.create(empresa=cls.empresa,nombre='Banco Prueba')
        cls.otro_banco=Banco.objects.create(empresa=cls.otra_empresa,nombre='Otro Banco')
        cls.cuenta=CuentaBancaria.objects.create(empresa=cls.empresa,banco=cls.banco,nombre='Cuenta corriente',tipo_cuenta='CuentaCorriente')
        cls.cuenta_ajena=CuentaBancaria.objects.create(empresa=cls.otra_empresa,banco=cls.otro_banco,nombre='Ajena',tipo_cuenta='CuentaCorriente')
        for user,rol,centro in ((cls.general,'admin_general',None),(cls.centro_admin,'admin_centro',cls.tandil),(cls.colaborador,'colaborador',None)):
            AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa,usuario=user,jerarquia=rol,centro_operativo=centro,activo=True)

    def activar(self, user=None, empresa=None, origen='admin'):
        self.client.force_login(user or self.general)
        return self.client.post(reverse('entrar_gestion_bancaria'), {'empresa':(empresa or self.empresa).pk,'origen':origen})

    def fila(self, **extra):
        return {**dict(tipo='Transferencia',fecha=date.today().isoformat(),importe='9000.00',identificacion='',clave=str(uuid.uuid4())), **extra}

    def lote(self, filas=None, clase='bancos', cuenta=None):
        return self.client.post(reverse('registrar_lote_bancario'), data=json.dumps({
            'clase':clase,'cuenta': (cuenta or self.cuenta).pk,'filas':filas if filas is not None else [self.fila()]
        }),content_type='application/json')

    def conceder(self, activo='1', usuario=None, centro=None, admin=None):
        self.activar(admin or self.general)
        return self.client.post(reverse('asignar_centro_gestion_bancaria'),{
            'usuario': (usuario or self.colaborador).pk,
            'centro': (centro or self.tandil).pk,'activo':activo,
        })

    def crear(self, filas=None, clase='bancos'):
        self.activar()
        r=self.lote(filas,clase=clase)
        self.assertEqual(r.status_code,200,r.content)
        return PendienteBancario.objects.get(pk=r.json()['ids'][0])

    def test_bandeja_exige_entrada_con_empresa_activa(self):
        self.client.force_login(self.general)
        self.assertEqual(self.client.get(reverse('gestion_bancaria')).status_code,403)
        self.assertEqual(self.activar().status_code,302)
        self.assertEqual(self.client.get(reverse('gestion_bancaria')).status_code,200)

    def test_navegacion_no_tiene_selector_empresa_ni_volver_perfiles(self):
        self.activar()
        html=self.client.get(reverse('gestion_bancaria')).content.decode()
        self.assertNotIn('name="empresa"',html)
        self.assertNotIn('Volver a perfiles',html)
        self.assertIn(reverse('panel_admin'),html)

    def test_usuario_no_puede_entrar_a_empresa_ajena(self):
        self.assertEqual(self.activar(self.general,self.otra_empresa).status_code,403)
        self.assertEqual(self.client.get(reverse('gestion_bancaria')).status_code,403)

    def test_parametros_get_o_post_no_cambian_empresa_activa(self):
        self.activar()
        r=self.client.get(reverse('gestion_bancaria'),{'empresa':self.otra_empresa.pk})
        self.assertEqual(r.status_code,200)
        self.assertIn('Caja Dos',r.content.decode())
        self.assertNotIn('Elegir Empresa',r.content.decode())
        post=self.client.post(reverse('registrar_pendiente_bancario'),{
            'empresa':self.otra_empresa.pk,'cuenta':self.cuenta_ajena.pk,
            'tipo':'Deposito','fecha':date.today().isoformat(),'referencia':'Prueba','importe':'100.00','clave':str(uuid.uuid4())})
        self.assertEqual(post.status_code,400)
        self.assertFalse(PendienteBancario.objects.exists())

    def test_pendientes_son_globales_a_admin_centro(self):
        self.crear([self.fila(identificacion='Ingreso no identificado')])
        self.activar(self.centro_admin)
        html=self.client.get(reverse('gestion_bancaria')).content.decode()
        self.assertIn('Ingreso no identificado',html)
        self.assertNotIn('Todos mis Centros',html)

    def test_pendientes_son_globales_a_colaborador_con_permiso(self):
        self.crear([self.fila(identificacion='Depósito global')])
        self.assertEqual(self.conceder().status_code,302)
        self.activar(self.colaborador,origen='colaborador')
        html=self.client.get(reverse('gestion_bancaria')).content.decode()
        self.assertIn('Depósito global',html)
        self.assertNotIn('name="empresa"',html)
        self.assertNotIn('Permisos de colaboradores',html)
        self.assertEqual(self.client.get(reverse('panel_caja'),{'empresa':self.empresa.pk}).status_code,403)
        self.assertEqual(self.client.get(reverse('historial_movimientos_caja'),{'empresa':self.empresa.pk,'caja':'todas'}).status_code,403)

    def test_colaborador_sin_permiso_no_ve_pendientes(self):
        self.client.force_login(self.colaborador)
        self.assertEqual(self.client.post(reverse('entrar_gestion_bancaria'),{'empresa':self.empresa.pk,'origen':'colaborador'}).status_code,403)

    def test_resolver_exige_cliente_y_centro_autorizado(self):
        p=self.crear()
        self.conceder()
        self.activar(self.colaborador,origen='colaborador')
        url=reverse('resolver_pendiente_bancario',args=[p.pk])
        data={'centro':self.central.pk,'identificacion':'Cliente test','tipo_resolucion':'YaImputado'}
        self.assertEqual(self.client.post(url,data).status_code,403)
        self.assertEqual(self.client.post(url,{**data,'centro':self.tandil.pk,'identificacion':''}).status_code,400)
        self.assertEqual(self.client.post(url,{**data,'centro':self.tandil.pk}).status_code,302)
        p.refresh_from_db()
        self.assertEqual((p.estado,p.centro_operativo_id,p.identificacion),('Resuelto',self.tandil.pk,'Cliente test'))
        self.assertEqual(p.resuelto_por.usuario_id,self.colaborador.pk)
        self.assertEqual(EventoPendienteBancario.objects.filter(accion='Resuelto').count(),1)
        self.assertFalse(MovimientoCaja.objects.exists())
        self.assertFalse(Pago.objects.exists())
        self.assertEqual(self.client.post(url,{**data,'centro':self.tandil.pk}).status_code,409)

    def test_ya_resuelto_no_se_ve_en_otro_centro(self):
        p=self.crear()
        self.activar(self.general)
        self.client.post(reverse('resolver_pendiente_bancario',args=[p.pk]),{
            'centro':self.central.pk,'identificacion':'CLIENTE CENTRAL',
            'tipo_resolucion':'YaImputado','referencia_resolucion':''})
        self.activar(self.centro_admin)
        self.assertNotIn('CLIENTE CENTRAL',self.client.get(reverse('gestion_bancaria'),{'estado':'Resuelto'}).content.decode())
        self.assertIn('No hay movimientos',self.client.get(reverse('gestion_bancaria'),{'estado':'Resuelto'}).content.decode())
        self.assertEqual(self.client.get(reverse('gestion_bancaria'),{'estado':'Resuelto','centro':self.central.pk}).status_code,403)

    def test_resuelto_no_puede_cambiarse_por_get(self):
        self.crear()
        self.activar(self.general)
        self.assertEqual(self.client.get(reverse('resolver_pendiente_bancario',args=[1])).status_code,405)

    def test_lote_atomicidad_fila_mala_no_persiste_ninguna(self):
        self.activar()
        buenas=self.fila();malas=self.fila(importe='NaN')
        r=self.lote([buenas,malas]);self.assertEqual(r.status_code,400)
        self.assertFalse(PendienteBancario.objects.exists())

    def test_lote_idempotente_y_conflicto_reutilizacion(self):
        self.activar()
        filas=[self.fila(),self.fila(importe='200.00')]
        self.assertEqual(self.lote(filas).status_code,200)
        self.assertEqual(self.lote(filas).status_code,200)
        self.assertEqual(PendienteBancario.objects.count(),2)
        filas[1]['importe']='300.00'
        self.assertEqual(self.lote(filas).status_code,400)
        self.assertEqual(PendienteBancario.objects.count(),2)

    def test_echeq_conserva_datos_y_condicion_por_defecto(self):
        self.activar()
        datos={'clave':str(uuid.uuid4()),'titular':'PROVEEDOR PRUEBA','numero':'12345',
            'codigo_banco':'17','banco':'BBVA','importe':'10000.00','acreditacion':date.today().isoformat()}
        self.assertEqual(self.lote([datos],clase='echeqs').status_code,200)
        p=PendienteBancario.objects.get()
        self.assertEqual((p.tipo,p.echeq_condicion,p.echeq_banco_nombre,p.echeq_numero),('ECheq','Orden','BBVA','12345'))
        self.assertFalse(Cheque.objects.exists())
        self.assertFalse(MovimientoCaja.objects.exists())

    def test_echeq_no_a_la_orden_y_reintento_diferente(self):
        self.activar()
        datos={'clave':str(uuid.uuid4()),'titular':'X','numero':'46','banco':'GALICIA',
            'importe':'100.00','acreditacion':date.today().isoformat(),'condicion':'NoOrden'}
        self.assertEqual(self.lote([datos],clase='echeqs').status_code,200)
        self.assertEqual(PendienteBancario.objects.get().echeq_condicion,'NoOrden')
        self.assertEqual(self.lote([{**datos,'condicion':'Orden'}],clase='echeqs').status_code,400)

    def test_echeq_condicion_invalidada_no_persiste(self):
        self.activar()
        datos={'clave':str(uuid.uuid4()),'titular':'X','numero':'99','banco':'BANCO',
            'importe':'100.00','acreditacion':date.today().isoformat(),'condicion':'Libre'}
        self.assertEqual(self.lote([datos],clase='echeqs').status_code,400)
        self.assertFalse(PendienteBancario.objects.exists())

    def test_lote_cuenta_ajena_no_persiste(self):
        self.activar()
        self.assertEqual(self.lote(cuenta=self.cuenta_ajena).status_code,400)
        self.assertFalse(PendienteBancario.objects.exists())

    def test_colaborador_no_registra_lotes(self):
        self.conceder()
        self.activar(self.colaborador,origen='colaborador')
        self.assertEqual(self.lote().status_code,403)

    def test_revocacion_inmediata_y_permisos_fuera_bandeja(self):
        self.conceder()
        self.activar()
        html=self.client.get(reverse('gestion_bancaria')).content.decode()
        self.assertNotIn('Permisos de colaboradores por Centro',html)
        self.assertEqual(self.client.get(reverse('configurar_permisos_bancarios')).status_code,200)
        self.conceder('0')
        self.activar(self.colaborador,origen='colaborador')
        self.assertEqual(self.client.get(reverse('gestion_bancaria')).status_code,403)

    def test_configuracion_solo_administracion_general(self):
        self.activar(self.centro_admin)
        self.assertEqual(self.client.get(reverse('configurar_permisos_bancarios')).status_code,403)
        self.assertEqual(self.client.post(reverse('asignar_centro_gestion_bancaria'),{
            'usuario':self.colaborador.pk,'centro':self.tandil.pk,'activo':'1'}).status_code,403)

    def test_csrf_obligatorio_en_lote_y_resolucion(self):
        c=Client(enforce_csrf_checks=True)
        c.force_login(self.general)
        c.post(reverse('entrar_gestion_bancaria'),{'empresa':self.empresa.pk,'origen':'admin'})
        self.assertEqual(c.post(reverse('registrar_lote_bancario'),data=json.dumps({
            'clase':'bancos','cuenta':self.cuenta.pk,'filas':[self.fila()]}),content_type='application/json').status_code,403)

    def test_backup_exporta_hechos_no_privilegios(self):
        modelos={spec.model.__name__ for spec in MODEL_SPECS}
        self.assertTrue({'PendienteBancario','EventoPendienteBancario','CorreccionMovimientoCaja'}<=modelos)
        self.assertNotIn('PermisoPendienteBancarioCentro',modelos)
        self.assertNotIn('EventoPermisoBancario',modelos)

    def test_backup_v1_antiguo_admite_componentes_nuevos_ausentes(self):
        from usuarios.services.backup_empresa import importacion
        from usuarios.services.backup_empresa.specs import OPTIONAL_NEW_KEYS
        self.assertTrue(OPTIONAL_NEW_KEYS)
        with tempfile.TemporaryDirectory() as tmp:
            zip_path=Path(tmp)/'antiguo.zip'
            with zipfile.ZipFile(zip_path,'w') as archivo:
                archivo.writestr('data/empresa.json','{}')
            with patch.object(importacion,'import_path',return_value=zip_path):
                self.assertEqual(importacion.cargar_json_backup('dummy','data/pendientes_bancarios.json',optional=True),[])

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
