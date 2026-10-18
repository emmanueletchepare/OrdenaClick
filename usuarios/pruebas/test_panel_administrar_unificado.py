"""Entrada compartida sin escalamiento de privilegios."""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import (
    AsignacionUsuarioEmpresa, CentroOperativo, Empresa,
    PermisoPendienteBancarioCentro,
)


class EntradaUnificadaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = User.objects.create_user('usuario_unificado', password='Segura123!')
        cls.ajeno = User.objects.create_user('ajeno_unificado', password='Segura123!')
        cls.propia = Empresa.objects.create(propietario=cls.usuario, razon_social='Mi Empresa Propia')
        cls.colabora = Empresa.objects.create(propietario=cls.ajeno, razon_social='Empresa Colaboración')
        cls.no_autorizada = Empresa.objects.create(propietario=cls.ajeno, razon_social='Empresa Privada')
        cls.centro = CentroOperativo.objects.create(empresa=cls.colabora, nombre='Centro Uno', tipo='Sucursal')
        cls.relacion = AsignacionUsuarioEmpresa.objects.create(
            empresa=cls.colabora, usuario=cls.usuario, jerarquia='colaborador', activo=True)

    def setUp(self):
        self.client.force_login(self.usuario)

    def test_inicio_solo_tres_areas_y_relaciones_accesible(self):
        respuesta = self.client.get(reverse('home'))
        html = respuesta.content.decode()
        self.assertIn('>Administrar', html.replace('\n','').replace(' ','').replace('\r',''))
        self.assertNotIn('>Colaborador', html.replace('\n','').replace(' ','').replace('\r',''))
        self.assertIn(reverse('panel_relaciones'), html)

    def test_selector_muestra_propias_y_asignaciones_activas(self):
        respuesta = self.client.get(reverse('panel_administrar'))
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode()
        self.assertIn('Mi Empresa Propia', html)
        self.assertIn('Empresa Colaboración', html)
        self.assertNotIn('Empresa Privada', html)
        self.assertIn('Colaborador', html)

    def test_colaborador_usa_mismo_panel_sin_admin_ni_datos_sensibles(self):
        respuesta = self.client.get(reverse('panel_administrar'), {'empresa': self.colabora.pk})
        self.assertEqual(respuesta.status_code, 200)
        self.assertTemplateUsed(respuesta, 'usuarios/perfiles/administrador/panel.html')
        html = respuesta.content.decode()
        self.assertIn('Empresa Colaboración', html)
        self.assertNotIn('Guardar Cambios', html)
        self.assertNotIn('Alta nueva empresa', html)
        self.assertNotIn('btnSidebarCaja', html)
        self.assertNotIn('js/perfiles/administrador/panel_abms.js', html)
        self.assertNotIn('Pendientes bancarios', html)

    def test_pendientes_aparece_solo_con_permiso_existente(self):
        PermisoPendienteBancarioCentro.objects.create(
            empresa=self.colabora, usuario=self.usuario, centro_operativo=self.centro, activo=True)
        respuesta = self.client.get(reverse('panel_administrar'), {'empresa': self.colabora.pk})
        self.assertContains(respuesta, 'Pendientes bancarios')
        entrada = self.client.post(reverse('entrar_gestion_bancaria'), {
            'empresa': self.colabora.pk, 'origen': 'colaborador', 'destino': 'pendientes'})
        self.assertEqual(entrada.status_code, 302)

    def test_no_acepta_empresa_ajena(self):
        respuesta = self.client.get(reverse('panel_administrar'), {'empresa': self.no_autorizada.pk})
        self.assertEqual(respuesta.status_code, 403)

    def test_relacion_inactiva_deja_de_mostrar_empresa(self):
        self.relacion.activo = False
        self.relacion.save(update_fields=['activo'])
        respuesta = self.client.get(reverse('panel_administrar'))
        self.assertNotIn('Empresa Colaboración', respuesta.content.decode())
        denegado = self.client.get(reverse('panel_administrar'), {'empresa': self.colabora.pk})
        self.assertEqual(denegado.status_code, 403)

    def test_post_no_procesa_formularios_de_empresa(self):
        respuesta = self.client.post(reverse('panel_administrar') + '?empresa=' + str(self.colabora.pk), {
            'guardar_cambios_empresa': '1', 'razon_social': 'Ataque'})
        self.assertEqual(respuesta.status_code, 405)
        self.colabora.refresh_from_db()
        self.assertEqual(self.colabora.razon_social, 'Empresa Colaboración')

    def test_propietario_conserva_panel_actual(self):
        respuesta = self.client.get(reverse('panel_administrar'), {'empresa': self.propia.pk})
        self.assertRedirects(respuesta, reverse('panel_admin') + '?empresa=' + str(self.propia.pk), fetch_redirect_response=False)

    def test_perfil_legacy_redirige_a_entrada_unica(self):
        respuesta = self.client.get(reverse('seleccionar_perfil', args=['colaborador']))
        self.assertRedirects(respuesta, reverse('panel_administrar'), fetch_redirect_response=False)


    def test_modulo_pendientes_usa_mismo_sidebar_y_frame_compartido(self):
        PermisoPendienteBancarioCentro.objects.create(
            empresa=self.colabora, usuario=self.usuario, centro_operativo=self.centro, activo=True)
        respuesta = self.client.get(reverse('panel_administrar'), {'empresa': self.colabora.pk})
        self.assertContains(respuesta, 'id="formEntrarGestionBancaria"')
        self.assertContains(respuesta, 'js/perfiles/administrador/pendientes_en_panel.js')
        self.assertContains(respuesta, 'id="contenido-operativo"')
        self.assertNotContains(respuesta, 'panel_abms.js')

    def test_roles_de_empresa_con_nombre_principal(self):
        respuesta = self.client.get(reverse('panel_administrar'))
        self.assertContains(respuesta, 'oc-empresa-nombre')
        self.assertContains(respuesta, 'oc-empresa-rol')
