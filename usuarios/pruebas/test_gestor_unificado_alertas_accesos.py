"""Gestor único: persistencia atómica, alcance, legados y no escalación."""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from usuarios.models import (AsignacionUsuarioEmpresa, CentroOperativo,
    DestinatarioAlerta, Empresa, Ejercicio, EventoConfiguracionAlerta,
    EventoPermisoAccesoColaborador, Movimiento, PermisoAccesoColaborador)
from usuarios.services.accesos_colaborador import puede


class GestorUnificadoTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('unif_dueno',password='Clave123!')
        self.usuario = User.objects.create_user('unif_operador',password='Clave123!')
        self.otro = User.objects.create_user('unif_ajeno',password='Clave123!')
        self.e = Empresa.objects.create(propietario=self.owner,razon_social='Empresa unificada')
        self.ajena = Empresa.objects.create(propietario=self.otro,razon_social='Empresa ajena')
        AsignacionUsuarioEmpresa.objects.create(empresa=self.e, usuario=self.usuario,
            jerarquia='colaborador',activo=True)
        self.c = CentroOperativo.objects.create(empresa=self.e,nombre='Central',tipo='Casa Central')
        self.client.force_login(self.owner)
        self.url=reverse('gestion_accesos_colaborador',args=[self.e.pk])

    def post(self, usuario=None, accesos=(), alertas=()):
        return self.client.post(self.url, {
            'formulario':'accesos-alertas',
            'usuario':usuario or self.usuario.pk,
            'capacidad':list(accesos), 'alerta':list(alertas),
        })

    def test_guarda_acceso_y_alerta_en_una_transaccion(self):
        res=self.post(accesos=['alertas.ver','vencimientos.ver'],alertas=['FIN-01'])
        self.assertEqual(res.status_code,302)
        self.assertTrue(puede(self.usuario,self.e.pk,'vencimientos.ver'))
        self.assertTrue(DestinatarioAlerta.objects.get(
            empresa=self.e,usuario=self.usuario,codigo='FIN-01').activo)
        self.assertEqual(EventoConfiguracionAlerta.objects.filter(
            empresa=self.e,usuario=self.usuario,codigo='FIN-01').count(),1)

    def test_deniega_alerta_sin_fuente_con_rollback_total(self):
        r=self.post(accesos=['alertas.ver'],alertas=['FIN-01'])
        self.assertEqual(r.status_code,403)
        self.assertFalse(PermisoAccesoColaborador.objects.filter(
            empresa=self.e,usuario=self.usuario,codigo='alertas.ver',activo=True).exists())
        self.assertFalse(EventoPermisoAccesoColaborador.objects.filter(empresa=self.e).exists())
        self.assertFalse(DestinatarioAlerta.objects.filter(empresa=self.e).exists())

    def test_revoca_permiso_y_aviso_juntos(self):
        self.post(accesos=['alertas.ver','vencimientos.ver'],alertas=['FIN-01'])
        self.assertEqual(self.post(accesos=['alertas.ver']).status_code,302)
        self.assertFalse(puede(self.usuario,self.e.pk,'vencimientos.ver'))
        self.assertFalse(DestinatarioAlerta.objects.get(
            empresa=self.e,usuario=self.usuario,codigo='FIN-01').activo)

    def test_guardado_legacy_acceso_no_borra_alertas(self):
        self.post(accesos=['alertas.ver','vencimientos.ver'],alertas=['FIN-01'])
        r=self.client.post(self.url,{'usuario':self.usuario.pk,
                                     'capacidad':['alertas.ver','vencimientos.ver']})
        self.assertEqual(r.status_code,302)
        self.assertTrue(DestinatarioAlerta.objects.get(
            empresa=self.e,usuario=self.usuario,codigo='FIN-01').activo)

    def test_propietario_solo_alertas_sin_editar_permisos(self):
        self.assertEqual(self.post(usuario=self.owner.pk,alertas=['FIN-01']).status_code,302)
        self.assertTrue(DestinatarioAlerta.objects.get(
            empresa=self.e,usuario=self.owner,codigo='FIN-01').activo)
        self.assertEqual(self.post(usuario=self.owner.pk,accesos=['caja.total']).status_code,403)

    def test_otro_usuario_y_empresa_ajena_denegados(self):
        self.assertEqual(self.post(usuario=self.otro.pk,alertas=['FIN-01']).status_code,403)
        self.assertEqual(self.client.get(reverse('gestion_accesos_colaborador',
            args=[self.ajena.pk])).status_code,403)
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(self.url).status_code,403)

    def test_get_con_selector_y_columnas_no_escribe(self):
        r=self.client.get(self.url,{'usuario':self.usuario.pk})
        self.assertEqual(r.status_code,200)
        self.assertContains(r,'Gestión de accesos y alertas')
        self.assertContains(r,'data-oc-seleccionar-usuario')
        self.assertContains(r,'name="alerta"')
        self.assertContains(r,'FIN-02')
        self.assertFalse(EventoConfiguracionAlerta.objects.exists())

    def test_mantiene_alertas_de_otro_destinatario(self):
        self.post(usuario=self.owner.pk,alertas=['FIN-01'])
        self.post(accesos=['alertas.ver','vencimientos.ver'],alertas=['FIN-01'])
        self.post(accesos=['alertas.ver','vencimientos.ver'],alertas=[])
        self.assertTrue(DestinatarioAlerta.objects.get(
            empresa=self.e,usuario=self.owner,codigo='FIN-01').activo)

    def test_administrador_general_conserva_gestor_unico_en_sidebar(self):
        """Un admin_general con panel restringido conserva acceso al Gestor."""
        general = User.objects.create_user('unif_general_sidebar', password='Clave123!')
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.e, usuario=general, jerarquia='admin_general', activo=True)
        self.client.force_login(general)
        panel = self.client.get(reverse('panel_administrar'), {'empresa': self.e.pk})
        self.assertEqual(panel.status_code, 200)
        self.assertContains(panel, 'Gestión de accesos y alertas')
        self.assertContains(panel, 'data-oc-gestion-accesos-url')
        self.assertNotContains(panel, 'data-oc-gestion-alertas-url')
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_no_concede_caja_por_asignar_alertas(self):
        self.post(accesos=['alertas.ver','vencimientos.ver','registros.ver'],
                  alertas=['FIN-02','FIN-03'])
        self.assertFalse(puede(self.usuario,self.e.pk,'caja.total'))
        self.assertFalse(puede(self.usuario,self.e.pk,'pendientes.ver'))
        self.assertTrue(DestinatarioAlerta.objects.filter(
            empresa=self.e,usuario=self.usuario,codigo='FIN-02',activo=True).exists())
