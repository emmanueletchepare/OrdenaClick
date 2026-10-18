"""Salidas reales de e-Cheqs; exclusivamente DB de pruebas Django."""
import json
from datetime import timedelta
from uuid import uuid4
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from usuarios.models import (Empresa, Banco, CuentaBancaria, Proveedor, PendienteBancario,
    OperacionSalidaECheq, ItemSalidaECheq, AsignacionUsuarioEmpresa, CentroOperativo,
    PermisoPendienteBancarioCentro)
from usuarios.services.pendientes_bancarios import registrar_lote

class SalidaECheqTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user=User.objects.create_user('dueno_salida',password='test.2026')
        cls.otro=User.objects.create_user('otro_salida',password='test.2026')
        cls.colab=User.objects.create_user('colab_salida',password='test.2026')
        cls.empresa=Empresa.objects.create(propietario=cls.user,razon_social='Empresa salida')
        cls.ajena=Empresa.objects.create(propietario=cls.otro,razon_social='Empresa ajena salida')
        cls.centro=CentroOperativo.objects.create(empresa=cls.empresa,nombre='Central',tipo='Casa Central')
        cls.banco=Banco.objects.create(empresa=cls.empresa,nombre='Banco eCheq salida')
        cls.cuenta=CuentaBancaria.objects.create(empresa=cls.empresa,banco=cls.banco,nombre='Cuenta propia',tipo_cuenta='CuentaCorriente',activo=True)
        cls.proveedor=Proveedor.objects.create(empresa=cls.empresa,razon_social='Proveedor destino',cuit='30-12345678-9',activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa,usuario=cls.colab,jerarquia='colaborador',activo=True)
        PermisoPendienteBancarioCentro.objects.create(empresa=cls.empresa,usuario=cls.colab,centro_operativo=cls.centro,activo=True)

    def crear(self,condicion='Orden',dias=0):
        fecha=(timezone.localdate()+timedelta(days=dias)).isoformat()
        ids=registrar_lote(usuario=self.user,empresa_id=self.empresa.pk,cuenta_id=None,clase='echeqs',filas=[{
          'clave':str(uuid4()),'titular':'Prueba salida','numero':'185','banco_id':str(self.banco.pk),
          'banco':self.banco.nombre,'importe':'125000,00','acreditacion':fecha,'condicion':condicion}])
        return PendienteBancario.objects.get(pk=ids[0])

    def activar(self,usuario=None,empresa=None):
        self.client.force_login(usuario or self.user)
        r=self.client.post(reverse('entrar_gestion_bancaria'),{'empresa':(empresa or self.empresa).pk,'origen':'admin'})
        self.assertEqual(r.status_code,302)

    def salida(self,ids,tipo='Depositar',clave=None,**kwargs):
        payload={'clave':clave or str(uuid4()),'tipo':tipo,'ids':ids}
        payload.update(kwargs)
        return self.client.post(reverse('echeq_salidas_confirmar'),data=json.dumps(payload),content_type='application/json')

    def test_listado_incluye_ambas_condiciones_y_diagnostica_salidas(self):
        a=self.crear('Orden')
        b=self.crear('NoOrden')
        c=self.crear('NoOrden')
        c.estado_cartera='Devuelto'
        c.save(update_fields=['estado_cartera'])
        self.activar()
        r=self.client.get(reverse('echeq_salidas_listar'))
        self.assertEqual(r.status_code,200)
        self.assertEqual({(v['id'],v['condicion']) for v in r.json()['instrumentos']},
                         {(a.pk,'Orden'),(b.pk,'NoOrden')})
        self.assertEqual(r.json()['diagnostico']['otros_estados_no_orden'],1)

    def test_deposito_y_reenvio_idempotente(self):
        p=self.crear();self.activar();clave=str(uuid4())
        r=self.salida([p.pk],clave=clave,cuenta=str(self.cuenta.pk));self.assertEqual(r.status_code,200,r.content)
        self.assertTrue(r.json()['creada'])
        r2=self.salida([p.pk],clave=clave,cuenta=str(self.cuenta.pk));self.assertEqual(r2.status_code,200,r2.content)
        self.assertFalse(r2.json()['creada'])
        p.refresh_from_db();self.assertEqual(p.estado_cartera,'Depositado')
        self.assertEqual(ItemSalidaECheq.objects.filter(pendiente=p).count(),1)
        self.assertEqual(self.salida([p.pk],cuenta=str(self.cuenta.pk)).status_code,400)

    def test_endoso_y_cesion_segundo_lote(self):
        a=self.crear('Orden');b=self.crear('NoOrden');self.activar()
        r=self.salida([a.pk,b.pk],tipo='EndosarCeder',proveedor=str(self.proveedor.pk),banco=str(self.banco.pk),destino='CBU de destino')
        self.assertEqual(r.status_code,200,r.content)
        a.refresh_from_db();b.refresh_from_db();self.assertEqual(a.estado_cartera,'Endosado');self.assertEqual(b.estado_cartera,'Cedido')
        self.assertEqual(OperacionSalidaECheq.objects.count(),1)
        self.assertEqual(ItemSalidaECheq.objects.count(),2)
        self.assertEqual(self.client.get(reverse('estado_echeq_detalle',args=[a.pk])).json()['estado'],'Endosado')

    def test_fecha_no_admite_deposito_futuro_o_vencido(self):
        futuro=self.crear(dias=2);vencido=self.crear(dias=0);vencido.echeq_fecha_acreditacion=timezone.localdate()-timedelta(days=31);vencido.save(update_fields=['echeq_fecha_acreditacion']);self.activar()
        for p in (futuro,vencido):self.assertEqual(self.salida([p.pk],cuenta=str(self.cuenta.pk)).status_code,400)
        self.assertEqual(OperacionSalidaECheq.objects.count(),0)

    def test_colaborador_denegado(self):
        p=self.crear();self.activar(self.colab)
        self.assertEqual(self.client.get(reverse('echeq_salidas_listar')).status_code,403)
        self.assertEqual(self.salida([p.pk],cuenta=str(self.cuenta.pk)).status_code,403)

    def test_otra_empresa_no_puede_disponer(self):
        p=self.crear();self.activar(self.otro,self.ajena)
        self.assertEqual(self.salida([p.pk],cuenta=str(self.cuenta.pk)).status_code,400)
        self.assertEqual(ItemSalidaECheq.objects.count(),0)

    def test_lote_atómico_si_un_valor_no_esta_disponible(self):
        a=self.crear();b=self.crear();self.activar()
        self.assertEqual(self.salida([a.pk],cuenta=str(self.cuenta.pk)).status_code,200)
        self.assertEqual(self.salida([a.pk,b.pk],cuenta=str(self.cuenta.pk)).status_code,400)
        b.refresh_from_db();self.assertEqual(b.estado_cartera,'EnCartera')
        self.assertEqual(OperacionSalidaECheq.objects.count(),1)

    def test_clave_no_puede_cambiar_de_operacion(self):
        p=self.crear();self.activar();clave=str(uuid4())
        self.assertEqual(self.salida([p.pk],clave=clave,cuenta=str(self.cuenta.pk)).status_code,200)
        self.assertEqual(self.salida([p.pk],clave=clave,tipo='EndosarCeder',proveedor=str(self.proveedor.pk),banco=str(self.banco.pk),destino='Otro').status_code,400)
        self.assertEqual(ItemSalidaECheq.objects.count(),1)

    def test_pdf_salida_autorizada_y_no_disponible_para_otro_usuario(self):
        from django.urls import reverse
        from unittest.mock import patch
        a=self.crear('Orden');b=self.crear('NoOrden');self.activar()
        resp=self.salida([a.pk,b.pk],tipo='EndosarCeder',proveedor=str(self.proveedor.pk),banco=str(self.banco.pk),destino='CBU prueba')
        self.assertEqual(resp.status_code,200)
        pk=resp.json()['operacion']
        with patch('usuarios.services.documentos_pdf.crear_documento',return_value=b'%PDF-1.4\ncontenido') as crear:
            pdf=self.client.get(reverse('echeq_salida_pdf',args=[pk]))
            self.assertEqual(pdf.status_code,200)
            self.assertEqual(pdf['Content-Type'],'application/pdf')
            self.assertIn('Cheques a endosar',str(crear.call_args))
            self.assertIn('Cheques a ceder',str(crear.call_args))
        self.client.force_login(self.otro)
        self.assertNotEqual(self.client.get(reverse('echeq_salida_pdf',args=[pk])).status_code,200)

    def test_pdf_salida_autorizada_y_no_disponible_para_otro_usuario(self):
        from django.urls import reverse
        from unittest.mock import patch
        a=self.crear('Orden');b=self.crear('NoOrden');self.activar()
        resp=self.salida([a.pk,b.pk],tipo='EndosarCeder',proveedor=str(self.proveedor.pk),banco=str(self.banco.pk),destino='CBU prueba')
        self.assertEqual(resp.status_code,200)
        pk=resp.json()['operacion']
        with patch('usuarios.services.documentos_pdf.crear_documento',return_value=b'%PDF-1.4\ncontenido') as crear:
            pdf=self.client.get(reverse('echeq_salida_pdf',args=[pk]))
            self.assertEqual(pdf.status_code,200)
            self.assertEqual(pdf['Content-Type'],'application/pdf')
            self.assertIn('Cheques a endosar',str(crear.call_args))
            self.assertIn('Cheques a ceder',str(crear.call_args))
        self.client.force_login(self.otro)
        self.assertNotEqual(self.client.get(reverse('echeq_salida_pdf',args=[pk])).status_code,200)

    def test_destino_largo_se_rechaza_sin_mutar_cartera(self):
        cheque=self.crear('NoOrden')
        self.activar()
        respuesta=self.salida([cheque.pk],tipo='EndosarCeder',
            proveedor=str(self.proveedor.pk),banco=str(self.banco.pk),destino='X'*81)
        self.assertEqual(respuesta.status_code,400)
        cheque.refresh_from_db()
        self.assertEqual(cheque.estado_cartera,'EnCartera')
        self.assertEqual(OperacionSalidaECheq.objects.count(),0)

    def test_error_de_precarga_informa_fila_y_campo_y_lote_atomico(self):
        self.activar()
        fecha=timezone.localdate().isoformat()
        filas=[{'clave':str(uuid4()),'titular':'Primero','numero':'441',
                'banco_id':str(self.banco.pk),'importe':'120.000,00',
                'acreditacion':fecha,'condicion':'Orden'},
               {'clave':str(uuid4()),'titular':'Segundo','numero':'442',
                'banco_id':str(self.banco.pk),'importe':'importe equivocado',
                'acreditacion':fecha,'condicion':'NoOrden'}]
        respuesta=self.client.post(reverse('registrar_lote_bancario'),
             data=json.dumps({'clase':'echeqs','cuenta':None,'filas':filas}),
             content_type='application/json')
        self.assertEqual(respuesta.status_code,400,respuesta.content)
        self.assertEqual(respuesta.json()['fila'],2)
        self.assertEqual(respuesta.json()['campo'],'importe')
        self.assertFalse(PendienteBancario.objects.filter(echeq_numero__in=['00000441','00000442']).exists())

    def test_abm_proveedores_contiene_token_y_script_para_panel(self):
        self.activar()
        respuesta=self.client.get(reverse('abm_contextual_echeq',args=['proveedores']))
        self.assertEqual(respuesta.status_code,200)
        self.assertContains(respuesta,'gbAbmCsrf')
        self.assertContains(respuesta,'pendientes_en_panel.js')
