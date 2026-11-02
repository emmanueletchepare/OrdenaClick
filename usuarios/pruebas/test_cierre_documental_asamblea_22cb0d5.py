"""Cierre de actas: no duplicar el aviso y preservar documentacion legacy."""
from datetime import date, timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from usuarios.models import CentroOperativo, Empresa
from usuarios.services.alertas_documentales import fuentes_documentales


class AsambleaSinDuplicadosTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user('asamblea_prueba', password='ClaveSegura123!')
        self.empresa = Empresa.objects.create(propietario=self.usuario, razon_social='Empresa prueba')
        self.centro = CentroOperativo.objects.create(empresa=self.empresa, nombre='Casa', tipo='Casa Central')

    def test_legacy_conserva_avisos_independientes(self):
        self.empresa.vencimiento_acta = date.today() + timedelta(days=4)
        self.empresa.vencimiento_designacion = date.today() + timedelta(days=6)
        self.empresa.save()
        codigos = [a['codigo'] for a in fuentes_documentales(self.empresa)]
        self.assertNotIn('DOC-02', codigos)
        self.assertIn('DOC-04', codigos)
        self.assertFalse(self.empresa.acta_incluye_designacion)

    def test_asamblea_con_designacion_un_unico_aviso_y_archivos_preservados(self):
        self.empresa.acta = 'documentos/asamblea_historica.pdf'
        self.empresa.designacion = 'documentos/designacion_historica.pdf'
        self.empresa.acta_incluye_designacion = True
        self.empresa.vencimiento_acta = date.today() - timedelta(days=2)
        self.empresa.vencimiento_designacion = date.today() + timedelta(days=5)
        self.empresa.save()
        avisos = fuentes_documentales(self.empresa)
        self.assertEqual(len([a for a in avisos if a['codigo']=='DOC-04']), 1)
        self.assertFalse(any(a['codigo']=='DOC-02' for a in avisos))
        self.assertIn('designación de autoridades', next(a['nombre'] for a in avisos if a['codigo']=='DOC-04'))
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.designacion.name, 'documentos/designacion_historica.pdf')
        self.assertEqual(self.empresa.vencimiento_designacion, date.today() + timedelta(days=5))

    def test_fecha_historica_designacion_no_se_pierde_si_asamblea_sin_fecha(self):
        self.empresa.acta_incluye_designacion = True
        self.empresa.vencimiento_designacion = date.today() + timedelta(days=8)
        self.empresa.save()
        avisos = fuentes_documentales(self.empresa)
        self.assertEqual([a['codigo'] for a in avisos].count('DOC-04'), 1)
        self.assertNotIn('DOC-02', [a['codigo'] for a in avisos])

    def test_documentos_directorio_y_habilitaciones_no_se_alteran(self):
        self.empresa.acta_incluye_designacion = True
        self.empresa.vencimiento_acta_directorio = date.today()
        self.empresa.save()
        codigos = [a['codigo'] for a in fuentes_documentales(self.empresa)]
        self.assertIn('DOC-01', codigos)
        self.assertIn('DOC-03', codigos)

    def test_formulario_guarda_marca_y_no_pierde_pdf_historico(self):
        self.empresa.acta = 'documentos/asamblea_existente.pdf'
        self.empresa.save(update_fields=['acta'])
        self.client.force_login(self.usuario)
        url = reverse('panel_admin') + '?empresa=' + str(self.empresa.pk)
        datos = {'guardar_cambios_empresa':'1', 'razon_social':'Empresa prueba',
                 'acta_incluye_designacion_presente':'1', 'acta_incluye_designacion':'1'}
        respuesta = self.client.post(url, datos)
        self.assertEqual(respuesta.status_code, 302)
        self.empresa.refresh_from_db()
        self.assertTrue(self.empresa.acta_incluye_designacion)
        self.assertEqual(self.empresa.acta.name, 'documentos/asamblea_existente.pdf')
        # Compatibilidad con solicitudes existentes sin campo nuevo.
        respuesta = self.client.post(url, {'guardar_cambios_empresa':'1', 'razon_social':'Empresa prueba'})
        self.assertEqual(respuesta.status_code,302)
        self.empresa.refresh_from_db()
        self.assertTrue(self.empresa.acta_incluye_designacion)
        respuesta = self.client.post(url, {'guardar_cambios_empresa':'1', 'razon_social':'Empresa prueba',
                 'acta_incluye_designacion_presente':'1'})
        self.assertEqual(respuesta.status_code,302)
        self.empresa.refresh_from_db()
        self.assertFalse(self.empresa.acta_incluye_designacion)

    def test_no_se_puede_marcar_sin_acta(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.post(reverse('panel_admin') + '?empresa=' + str(self.empresa.pk),
            {'guardar_cambios_empresa':'1', 'razon_social':'Empresa prueba',
             'acta_incluye_designacion_presente':'1', 'acta_incluye_designacion':'1'})
        self.assertEqual(respuesta.status_code,400)
        self.empresa.refresh_from_db()
        self.assertFalse(self.empresa.acta_incluye_designacion)


class AsambleaVistaTests(SimpleTestCase):
    def test_formulario_solo_tres_documentos_sin_tarjetas_extra(self):
        root = Path(settings.BASE_DIR)
        template = (root / 'templates/usuarios/perfiles/administrador/partials/main.html').read_text(encoding='utf-8')
        css = (root / 'static/css/empresa/vencimientos_documentales.css').read_text(encoding='utf-8')
        self.assertIn('class="form-grid oc-sociedad-simple"', template)
        for campo in ('estatuto', 'acta_directorio', 'designacion',
                      'vencimiento_acta_directorio', 'vencimiento_designacion'):
            self.assertEqual(template.count('name="' + campo + '"'), 1)
        for obsoleto in ('name="acta"', 'name="vencimiento_acta"',
                         'name="acta_incluye_designacion"',
                         'oc-sociedad-complementarios'):
            self.assertNotIn(obsoleto, template)
        self.assertIn('oc-sociedad-estatuto', css)
