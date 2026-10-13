"""Caja 2: fechas, búsqueda por Empresa, correcciones auditadas y configuración."""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4
import json

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from usuarios.models import (AsignacionUsuarioEmpresa, Banco, CentroOperativo,
    CuentaBancaria, Empresa, PendienteBancario, RevisionPendienteBancario,
    PermisoPendienteBancarioCentro, MovimientoCaja, Pago)
from usuarios.services.pendientes_bancarios import registrar_lote
from usuarios.templatetags.caja_importes import importe_ar

class Caja2AjusteFinalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dueno = User.objects.create_user('c2final_dueno', password='A1.largo.2026')
        cls.admin = User.objects.create_user('c2final_admin', password='A1.largo.2026')
        cls.colab = User.objects.create_user('c2final_colab', password='A1.largo.2026')
        cls.ajeno = User.objects.create_user('c2final_ajeno', password='A1.largo.2026')
        cls.e = Empresa.objects.create(propietario=cls.dueno, razon_social='Prueba Final')
        cls.e2 = Empresa.objects.create(propietario=cls.ajeno, razon_social='Empresa Ajena')
        cls.c = CentroOperativo.objects.create(empresa=cls.e, nombre='Central', tipo='Casa Central')
        cls.c2 = CentroOperativo.objects.create(empresa=cls.e2, nombre='Ajeno', tipo='Sucursal')
        cls.b = Banco.objects.create(empresa=cls.e,nombre='Banco de Prueba')
        cls.b2 = Banco.objects.create(empresa=cls.e2,nombre='Banco de Ajeno')
        cls.cuenta = CuentaBancaria.objects.create(empresa=cls.e,banco=cls.b,nombre='CC',tipo_cuenta='CuentaCorriente')
        cls.cuenta2 = CuentaBancaria.objects.create(empresa=cls.e2,banco=cls.b2,nombre='CC2',tipo_cuenta='CuentaCorriente')
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.e,usuario=cls.admin,jerarquia='admin_general',activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.e,usuario=cls.colab,jerarquia='colaborador',activo=True)
        PermisoPendienteBancarioCentro.objects.create(empresa=cls.e,usuario=cls.colab,centro_operativo=cls.c,activo=True)

    def activar(self, user=None, empresa=None, origen='admin'):
        self.client.force_login(user or self.admin)
        return self.client.post(reverse('entrar_gestion_bancaria'),{
            'empresa': (empresa or self.e).pk, 'origen': origen})

    def bancos(self, identificacion='Nombre Original', importe='1000.00'):
        self.activar()
        ids = registrar_lote(usuario=self.admin,empresa_id=self.e.pk,cuenta_id=self.cuenta.pk,
            clase='bancos',filas=[{'clave':str(uuid4()),'tipo':'Deposito',
                'fecha':timezone.localdate().isoformat(),'identificacion':identificacion,'importe':importe}])
        return PendienteBancario.objects.get(pk=ids[0])

    def echeq(self, dias=0):
        self.activar()
        dia=(timezone.localdate()-timedelta(days=dias)).isoformat()
        datos={'clave':str(uuid4()),'titular':'Titular Ejemplo','numero':'185',
            'banco_id':str(self.b.pk),'banco':self.b.nombre,'importe':'12500,00',
            'acreditacion':dia,'condicion':'Orden'}
        return registrar_lote(usuario=self.admin,empresa_id=self.e.pk,cuenta_id=None,
            clase='echeqs',filas=[datos])

    def revision(self, pendiente, **changes):
        datos={'clave':str(uuid4()),'motivo':'Error de carga en prueba',
            'fecha':pendiente.fecha.isoformat(), 'identificacion':'Titular Modificado',
            'importe':'2500,00','numero':pendiente.echeq_numero,
            'titular':pendiente.echeq_titular,'banco':pendiente.echeq_banco_nombre}
        datos.update(changes)
        return self.client.post(reverse('revisar_pendiente_bancario',args=[pendiente.pk]),datos)

    def test_echeq_hasta_30_dias_incluido(self):
        self.assertEqual(len(self.echeq(dias=30)),1)
        self.assertEqual(PendienteBancario.objects.get().echeq_numero,'00000185')

    def test_echeq_31_dias_rechazado_y_sin_altas(self):
        with self.assertRaisesMessage(ValueError,'30 días'):
            self.echeq(dias=31)
        self.assertFalse(PendienteBancario.objects.exists())

    def test_formato_ar_consistente(self):
        self.assertEqual(importe_ar(Decimal('12522366.00')),'12.522.366,00')
        self.assertEqual(importe_ar(Decimal('150.00')),'150,00')
        self.bancos(importe='12522366.00')
        html=self.client.get(reverse('gestion_bancaria')).content.decode()
        self.assertIn('12.522.366,00',html)
        self.assertNotIn('12522366.00</td>',html)

    def test_buscar_cliente_y_importe_paginados(self):
        self.bancos('Pedro Ejemplo',importe='12522366.00')
        ruta=reverse('gestion_bancaria')
        for buscar in ('Pedro','12522366','12.522.366,00'):
            with self.subTest(buscar=buscar):
                html=self.client.get(ruta,{'buscar':buscar}).content.decode()
                self.assertIn('Pedro Ejemplo',html)
        html=self.client.get(ruta,{'buscar':'inexistente-zzz'}).content.decode()
        self.assertNotIn('Pedro Ejemplo',html)

    def test_buscar_numero_echeq(self):
        self.echeq()
        html=self.client.get(reverse('gestion_bancaria'),{'buscar':'00000185'}).content.decode()
        self.assertIn('00000185',html)

    def test_no_cruce_empresas_en_busqueda(self):
        self.bancos('Banco Local')
        self.client.force_login(self.ajeno)
        self.client.post(reverse('entrar_gestion_bancaria'),{'empresa':self.e2.pk,'origen':'admin'})
        respuesta=self.client.get(reverse('gestion_bancaria'),{'buscar':'Banco Local'})
        self.assertEqual(respuesta.status_code,200)
        # El texto del buscador se refleja en su value: eso NO es una fila filtrada.
        # La prueba de aislamiento debe inspeccionar la consulta, no todo el HTML.
        self.assertEqual(respuesta.context['pagina'].paginator.count,0)
        self.assertIn('No hay movimientos para esta consulta.',respuesta.content.decode())
        self.assertEqual(self.client.post(reverse('revisar_pendiente_bancario',args=[PendienteBancario.objects.first().pk]),
            {'clave':str(uuid4()),'motivo':'Intento en empresa ajena'}).status_code,403)

    def test_editar_pendiente_audita_antes_y_despues(self):
        pendiente=self.bancos()
        r=self.revision(pendiente)
        self.assertEqual(r.status_code,302,r.content)
        pendiente.refresh_from_db()
        self.assertEqual(pendiente.importe, Decimal('2500.00'))
        self.assertEqual(pendiente.identificacion,'Titular Modificado')
        revision=RevisionPendienteBancario.objects.get()
        self.assertEqual(revision.tipo,'Editado')
        self.assertEqual(revision.anterior['importe'],'1000.00')
        self.assertEqual(revision.nuevo['importe'],'2500.00')
        self.assertEqual(revision.actor.usuario_id,self.admin.pk)
        self.assertFalse(MovimientoCaja.objects.exists())
        self.assertFalse(Pago.objects.exists())

    def test_repetir_clave_no_crea_segunda_revision(self):
        p=self.bancos()
        clave=str(uuid4())
        self.assertEqual(self.revision(p,clave=clave).status_code,302)
        self.assertEqual(self.revision(p,clave=clave).status_code,302)
        self.assertEqual(RevisionPendienteBancario.objects.count(),1)
        self.assertEqual(self.revision(p,clave=clave,motivo='Otro motivo que cambia').status_code,400)

    def test_usuario_no_creador_no_modifica_pendiente(self):
        p=self.bancos()
        self.activar(self.colab,origen='colaborador')
        self.assertEqual(self.revision(p).status_code,403)
        self.assertFalse(RevisionPendienteBancario.objects.exists())

    def test_resuelto_se_informa_pero_no_se_modifica(self):
        p=self.bancos()
        self.client.post(reverse('resolver_pendiente_bancario',args=[p.pk]),{
            'centro':self.c.pk,'identificacion':'Cliente Real','tipo_resolucion':'YaImputado'})
        p.refresh_from_db()
        original=(p.importe,p.identificacion,p.centro_operativo_id,p.estado)
        self.assertEqual(self.revision(p).status_code,302)
        p.refresh_from_db()
        self.assertEqual((p.importe,p.identificacion,p.centro_operativo_id,p.estado),original)
        self.assertEqual(RevisionPendienteBancario.objects.get().estado,'Abierto')
        html=self.client.get(reverse('configurar_permisos_bancarios')).content.decode()
        self.assertIn('Error de carga en prueba',html)

    def test_colaborador_que_resolvio_puede_reportar_error(self):
        p=self.bancos()
        self.activar(self.colab,origen='colaborador')
        self.client.post(reverse('resolver_pendiente_bancario',args=[p.pk]),{
            'centro':self.c.pk,'identificacion':'Cliente Real','tipo_resolucion':'YaImputado'})
        p.refresh_from_db()
        self.assertEqual(self.revision(p).status_code,302)
        self.assertEqual(RevisionPendienteBancario.objects.get().tipo,'Incidencia')
        self.assertEqual(self.client.get(reverse('configurar_permisos_bancarios')).status_code,403)

    def test_get_y_csrf_no_mutan_revision(self):
        p=self.bancos()
        url=reverse('revisar_pendiente_bancario',args=[p.pk])
        self.assertEqual(self.client.get(url).status_code,405)
        c=Client(enforce_csrf_checks=True)
        c.force_login(self.admin)
        self.assertEqual(c.post(url,{'clave':str(uuid4()),'motivo':'Intento sin CSRF'}).status_code,403)
        self.assertFalse(RevisionPendienteBancario.objects.exists())

    def test_titular_cliente_aparece_en_ambas_cargas(self):
        self.activar()
        html=self.client.get(reverse('gestion_bancaria')).content.decode()
        self.assertGreaterEqual(html.count('Titular / Cliente'),2)
        self.assertIn('gbClienteDeposito',html)
        self.assertIn('data-destino-abm="bancos"',html)
        self.assertIn('data-destino-abm="echeqs"',html)

    def test_permisos_estan_dentro_de_designar_perfiles(self):
        self.activar()
        resultado=self.client.get(reverse('gestionar_relaciones_empresa',args=[self.e.pk]),
            {'fragment':'1'},HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resultado.status_code,200)
        html=resultado.content.decode()
        self.assertIn('Configurar permisos por Centro',html)
        self.assertIn('name="destino" value="permisos"',html)
        self.assertIn(reverse('entrar_gestion_bancaria'),html)

    def test_backup_json_snapshot_serializa_y_restaura(self):
        from usuarios.services.backup_empresa.common import serialize_scalar,deserialize_scalar
        from usuarios.models import RevisionPendienteBancario
        original={'importe':'2500.00','fecha':'2026-10-12','cliente':None}
        self.assertEqual(serialize_scalar(original),original)
        field=RevisionPendienteBancario._meta.get_field('anterior')
        self.assertEqual(deserialize_scalar(field, original), original)

    def test_backup_revisiones_sin_importar_permisos(self):
        from usuarios.services.backup_empresa.specs import MODEL_SPECS,OPTIONAL_NEW_KEYS
        self.assertIn('RevisionPendienteBancario',{s.model.__name__ for s in MODEL_SPECS})
        self.assertIn('revisiones_pendientes_bancarios',OPTIONAL_NEW_KEYS)
        self.assertNotIn('PermisoPendienteBancarioCentro',{s.model.__name__ for s in MODEL_SPECS})
