"""DOC-01 a DOC-04: fuentes, alcance, defaults opt-out, sin Caja."""
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import (AsignacionUsuarioEmpresa, CentroOperativo, Empresa,
    HabilitacionCentro, PermisoAccesoColaborador, DestinatarioAlerta)
from usuarios.services.alertas_documentales import (fuentes_documentales,
    avisos_documentales_visibles)
from usuarios.services.destinatarios_alertas import (suscripto_efectivo,
    guardar_destinatarios_usuario)


class DocumentalesTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('doc_owner', password='Prueba77!')
        self.admin = User.objects.create_user('doc_centro', password='Prueba77!')
        self.ajeno = User.objects.create_user('doc_ajeno', password='Prueba77!')
        self.e = Empresa.objects.create(propietario=self.owner, razon_social='Doc Empresa')
        self.otra = Empresa.objects.create(propietario=self.ajeno, razon_social='Otra Doc')
        self.c1 = CentroOperativo.objects.create(empresa=self.e, nombre='Casa', tipo='Casa Central')
        self.c2 = CentroOperativo.objects.create(empresa=self.e, nombre='Sucursal', tipo='Sucursal')
        AsignacionUsuarioEmpresa.objects.create(empresa=self.e, usuario=self.admin,
            jerarquia='admin_centro', centro_operativo=self.c1, activo=True)
        PermisoAccesoColaborador.objects.create(empresa=self.e, usuario=self.admin,
            codigo='alertas.ver', activo=True, otorgado_por=self.owner)

    def test_centros_sin_habilitacion_generan_doc03_solo_en_alcance(self):
        avisos = fuentes_documentales(self.e)
        self.assertEqual(len([a for a in avisos if a['codigo']=='DOC-03']), 2)
        visibles = avisos_documentales_visibles(self.admin, self.e)
        self.assertEqual({a['centro_id'] for a in visibles}, {self.c1.pk})
        self.assertEqual(avisos_documentales_visibles(self.ajeno, self.e), [])

    def test_habilitacion_activa_no_equivale_a_vencida(self):
        HabilitacionCentro.objects.create(centro=self.c1, descripcion='Municipal',
            vencimiento=date.today()+timedelta(days=8))
        avisos = fuentes_documentales(self.e)
        de_casa = [a for a in avisos if a['centro_id']==self.c1.pk]
        self.assertEqual(len(de_casa),1)
        self.assertEqual(de_casa[0]['estado_alerta'],'Proximo')

    def test_archivada_no_oculta_falta_de_habilitacion(self):
        HabilitacionCentro.objects.create(centro=self.c1, descripcion='Anterior', activo=False)
        avisos = fuentes_documentales(self.e)
        self.assertTrue(any(a['centro_id']==self.c1.pk and
            a['estado_alerta']=='Sin habilitacion' for a in avisos))

    def test_tres_documentos_societarios_sin_alcance_admin_centro(self):
        hoy = date.today()
        self.e.vencimiento_acta_directorio = hoy
        self.e.vencimiento_acta = hoy - timedelta(days=3)
        self.e.vencimiento_designacion = hoy + timedelta(days=4)
        self.e.save()
        tipos = {a['codigo'] for a in avisos_documentales_visibles(self.owner, self.e)}
        self.assertTrue({'DOC-01','DOC-04'}.issubset(tipos))
        self.assertNotIn('DOC-02', tipos)
        tipos_centro = {a['codigo'] for a in avisos_documentales_visibles(self.admin, self.e)}
        self.assertEqual(tipos_centro, {'DOC-03'})

    def test_destinatarios_predeterminados_y_opt_out_auditado(self):
        self.assertTrue(suscripto_efectivo(self.owner, self.e, 'DOC-01'))
        self.assertTrue(suscripto_efectivo(self.admin, self.e, 'DOC-03'))
        guardar_destinatarios_usuario(administrador=self.owner, empresa_id=self.e.pk,
            usuario_id=self.admin.pk, codigos=[])
        self.assertFalse(suscripto_efectivo(self.admin, self.e, 'DOC-03'))
        self.assertFalse(DestinatarioAlerta.objects.get(
            empresa=self.e, usuario=self.admin, codigo='DOC-03').activo)

    def test_revocacion_alertas_ver_impacta_de_inmediato(self):
        self.assertTrue(avisos_documentales_visibles(self.admin, self.e))
        PermisoAccesoColaborador.objects.filter(empresa=self.e, usuario=self.admin,
            codigo='alertas.ver').update(activo=False)
        self.assertFalse(suscripto_efectivo(self.admin, self.e, 'DOC-03'))
        self.assertEqual(avisos_documentales_visibles(self.admin, self.e), [])

    def test_registrar_y_archivar_conserva_antecedente(self):
        self.client.force_login(self.owner)
        r = self.client.post(reverse('agregar_habilitacion_centro'), {
            'empresa':self.e.pk, 'centro':self.c1.pk,
            'descripcion':'Municipal', 'vencimiento':date.today().isoformat()})
        self.assertEqual(r.status_code,200)
        hab = HabilitacionCentro.objects.get(centro=self.c1)
        self.assertEqual(hab.creado_por,self.owner.username)
        r = self.client.post(reverse('archivar_habilitacion_centro'), {
            'empresa':self.e.pk, 'centro':self.c1.pk, 'habilitacion':hab.pk})
        self.assertEqual(r.status_code,200)
        hab.refresh_from_db()
        self.assertFalse(hab.activo)
        self.assertEqual(hab.actualizado_por,self.owner.username)
        self.assertTrue(any(a['centro_id']==self.c1.pk and
            a['estado_alerta']=='Sin habilitacion' for a in fuentes_documentales(self.e)))

    def test_centro_de_otra_empresa_no_autorizado(self):
        ajeno_centro = CentroOperativo.objects.create(
            empresa=self.otra, nombre='Ajeno', tipo='Casa Central')
        self.client.force_login(self.owner)
        r = self.client.post(reverse('agregar_habilitacion_centro'), {
            'empresa':self.e.pk, 'centro':ajeno_centro.pk, 'descripcion':'Intruso'})
        self.assertEqual(r.status_code,403)
        self.assertFalse(HabilitacionCentro.objects.exists())

    def test_backup_v1_conserva_habilitaciones_y_backups_antiguos(self):
        from usuarios.services.backup_empresa.specs import MODEL_SPECS, OPTIONAL_NEW_KEYS
        self.assertIn('habilitaciones_centros', [s.key for s in MODEL_SPECS])
        self.assertIn('habilitaciones_centros', OPTIONAL_NEW_KEYS)

    def test_usuario_ajeno_no_es_autorizado_para_registrar(self):
        self.client.force_login(self.ajeno)
        r = self.client.post(reverse('agregar_habilitacion_centro'), {
            'empresa':self.e.pk, 'centro':self.c1.pk, 'descripcion':'Intruso'})
        self.assertEqual(r.status_code, 403)
        self.assertFalse(HabilitacionCentro.objects.exists())
