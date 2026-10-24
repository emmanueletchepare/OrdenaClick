"""Caja 1: historial en el dashboard con filtros, alcance y privacidad."""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.models import AsignacionUsuarioEmpresa, CentroOperativo, Caja, Empresa, MovimientoCaja, PermisoAccesoColaborador
from usuarios.services.identidades import obtener_identidad_usuario_empresa


class HistorialPanelCajaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dueno = User.objects.create_user(username='c1hist_dueno', password='PruebaCaja123!')
        cls.ajeno = User.objects.create_user(username='c1hist_ajeno', password='PruebaCaja123!')
        cls.general = User.objects.create_user(username='c1hist_general', password='PruebaCaja123!')
        cls.admin = User.objects.create_user(username='c1hist_admin', password='PruebaCaja123!')
        cls.colaborador = User.objects.create_user(username='c1hist_colab', password='PruebaCaja123!')
        cls.empresa = Empresa.objects.create(propietario=cls.dueno, razon_social='Historial central')
        cls.empresa_ajena = Empresa.objects.create(propietario=cls.ajeno, razon_social='Historial ajena')
        cls.central = CentroOperativo.objects.create(empresa=cls.empresa, nombre='Olavarria', tipo='Casa Central', activo=True)
        cls.tandil = CentroOperativo.objects.create(empresa=cls.empresa, nombre='Tandil', tipo='Sucursal', activo=True)
        cls.otra = CentroOperativo.objects.create(empresa=cls.empresa_ajena, nombre='Otra Empresa', tipo='Casa Central', activo=True)
        cls.caja_central = Caja.objects.create(empresa=cls.empresa, centro_operativo=cls.central, nombre='Principal', activo=True)
        cls.caja_tandil = Caja.objects.create(empresa=cls.empresa, centro_operativo=cls.tandil, nombre='Sucursal', activo=True)
        cls.caja_ajena = Caja.objects.create(empresa=cls.empresa_ajena, centro_operativo=cls.otra, nombre='Ajena', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.general, jerarquia='admin_general', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.admin, jerarquia='admin_centro', centro_operativo=cls.tandil, activo=True)
        PermisoAccesoColaborador.objects.create(empresa=cls.empresa, usuario=cls.admin,
            codigo='caja.total', activo=True, otorgado_por=cls.dueno)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.colaborador, jerarquia='colaborador', activo=True)
        cls.hoy = timezone.localdate()
        cls.ayer = cls.hoy - timedelta(days=1)
        cls.anteayer = cls.hoy - timedelta(days=2)
        identidad = obtener_identidad_usuario_empresa(empresa=cls.empresa, usuario=cls.dueno)
        id_ajena = obtener_identidad_usuario_empresa(empresa=cls.empresa_ajena, usuario=cls.ajeno)
        for caja, empresa, fecha, concepto, id_usuario in (
            (cls.caja_central, cls.empresa, cls.hoy, 'Central hoy', identidad),
            (cls.caja_central, cls.empresa, cls.ayer, 'Central ayer', identidad),
            (cls.caja_tandil, cls.empresa, cls.hoy, 'Tandil hoy', identidad),
            (cls.caja_tandil, cls.empresa, cls.anteayer, 'Tandil antiguo', identidad),
            (cls.caja_ajena, cls.empresa_ajena, cls.hoy, 'SECRETO AJENO', id_ajena),
        ):
            MovimientoCaja.objects.create(empresa=empresa, caja=caja, fecha=fecha,
                tipo='Ingreso', moneda='ARS', importe=Decimal('100.00'), concepto=concepto, creado_por=id_usuario)

    def historial(self, usuario, caja, **extras):
        self.client.force_login(usuario)
        return self.client.get(reverse('historial_movimientos_caja'), {
            'empresa': self.empresa.pk, 'caja': caja, **extras,
        })

    def test_hoy_no_muestra_movimientos_historicos(self):
        html = self.historial(self.dueno, self.caja_central.pk).json()['html']
        self.assertIn('Central hoy', html)
        self.assertNotIn('Central ayer', html)
        self.assertNotIn('Tandil hoy', html)

    def test_rango_por_fecha_real_del_movimiento(self):
        html = self.historial(self.dueno, self.caja_central.pk, modo='rango',
            desde=self.ayer.isoformat(), hasta=self.ayer.isoformat()).json()['html']
        self.assertIn('Central ayer', html)
        self.assertNotIn('Central hoy', html)

    def test_todas_solo_cajas_propias_y_columna_de_ubicacion(self):
        html = self.historial(self.general, 'todas').json()['html']
        self.assertIn('Central hoy', html)
        self.assertIn('Tandil hoy', html)
        self.assertIn('Olavarria', html)
        self.assertNotIn('SECRETO AJENO', html)
        self.assertNotIn('Central ayer', html)

    def test_admin_centro_todas_se_restringe_a_su_centro(self):
        html = self.historial(self.admin, 'todas').json()['html']
        self.assertIn('Tandil hoy', html)
        self.assertNotIn('Central hoy', html)
        self.assertNotIn('SECRETO AJENO', html)

    def test_id_de_caja_fuera_de_alcance_da_403(self):
        self.assertEqual(self.historial(self.admin, self.caja_central.pk).status_code, 403)
        self.assertEqual(self.historial(self.dueno, self.caja_ajena.pk).status_code, 403)

    def test_admin_centro_revocado_no_consulta_historial(self):
        PermisoAccesoColaborador.objects.filter(
            empresa=self.empresa, usuario=self.admin, codigo='caja.total',
        ).update(activo=False)
        self.assertEqual(self.historial(self.admin, 'todas').status_code, 403)

    def test_colaborador_no_gana_acceso_a_caja(self):
        self.assertEqual(self.historial(self.colaborador, 'todas').status_code, 403)

    def test_anonimo_es_redirigido(self):
        self.assertEqual(self.client.get(reverse('historial_movimientos_caja')).status_code, 302)

    def test_modo_y_rango_invalidos_son_rechazados(self):
        for extra in (
            {'modo': 'todo'}, {'modo': 'rango', 'desde': 'ayer', 'hasta': 'hoy'},
            {'modo': 'rango', 'desde': self.hoy.isoformat(), 'hasta': self.ayer.isoformat()},
            {'modo': 'rango', 'desde': '2020-01-01', 'hasta': self.hoy.isoformat()},
        ):
            with self.subTest(extra=extra):
                self.assertEqual(self.historial(self.general, 'todas', **extra).status_code, 400)

    def test_no_acepta_caja_vacia_para_ampliar_consulta(self):
        self.assertEqual(self.historial(self.general, '').status_code, 400)

    def test_no_escribe_por_post(self):
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.post(reverse('historial_movimientos_caja')).status_code, 405)
        self.assertEqual(MovimientoCaja.objects.count(), 5)

    def test_dashboard_contiene_filtros_y_formulario_no_duplicado(self):
        self.client.force_login(self.dueno)
        panel = self.client.get(reverse('panel_caja'), {'empresa': self.empresa.pk})
        self.assertEqual(panel.status_code, 200)
        self.assertIn('id="cajaHistorialModo"', panel.json()['html'])
        self.assertIn('id="cajaHistorialResultados"', panel.json()['html'])
        form = self.client.get(reverse('vista_movimientos_caja'), {
            'empresa': self.empresa.pk, 'caja': self.caja_central.pk})
        self.assertEqual(form.status_code, 200)
        self.assertIn('id="cajaMovimientoFormulario"', form.json()['html'])
        self.assertNotIn('Historial de esta Caja', form.json()['html'])

    def test_el_historial_escapa_conceptos_html(self):
        identidad = obtener_identidad_usuario_empresa(empresa=self.empresa, usuario=self.dueno)
        MovimientoCaja.objects.create(empresa=self.empresa, caja=self.caja_central, fecha=self.hoy,
            tipo='Ingreso', moneda='ARS', importe=Decimal('1.00'), concepto='<script>evil</script>', creado_por=identidad)
        html = self.historial(self.dueno, self.caja_central.pk).json()['html']
        self.assertNotIn('<script>evil</script>', html)
        self.assertIn('&lt;script&gt;', html)
