"""B2: asignación explícita, lectura separada, multiempresa y revocación inmediata."""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from usuarios.models import (AsignacionUsuarioEmpresa, CentroOperativo, DestinatarioAlerta,
    Empresa, Ejercicio, EventoConfiguracionAlerta, Movimiento, PermisoAccesoColaborador)
from usuarios.services.destinatarios_alertas import (alertas_sin_destinatarios,
    guardar_destinatarios_usuario, receptores_efectivos, sonido_habilitado)


class DestinatariosB2Tests(TestCase):
    def setUp(self):
        self.dueno = User.objects.create_user('dueno_alertas_b2', password='Clave123!')
        self.operador = User.objects.create_user('operador_alertas_b2', password='Clave123!')
        self.centro_admin = User.objects.create_user('centro_alertas_b2', password='Clave123!')
        self.ajeno = User.objects.create_user('ajeno_alertas_b2', password='Clave123!')
        self.empresa = Empresa.objects.create(propietario=self.dueno, razon_social='Empresa B2')
        self.otra = Empresa.objects.create(propietario=self.ajeno, razon_social='Otra empresa B2')
        self.c1 = CentroOperativo.objects.create(empresa=self.empresa, nombre='Casa', tipo='Casa Central', activo=True)
        self.c2 = CentroOperativo.objects.create(empresa=self.empresa, nombre='Sucursal', tipo='Sucursal', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=self.operador,
                                               jerarquia='colaborador', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=self.centro_admin,
                                               jerarquia='admin_centro', centro_operativo=self.c1, activo=True)
        ejercicio = Ejercicio.objects.create(empresa=self.empresa, numero=2026,
            fecha_inicio=date(2026,1,1), fecha_cierre=date(2026,12,31))
        for centro in (self.c1, self.c2):
            Movimiento.objects.create(empresa=self.empresa, ejercicio=ejercicio,
                centro_operativo=centro, fecha_registro=date.today(),
                fecha_vencimiento=date.today()+timedelta(days=1),
                importe=Decimal('300.00'), total=Decimal('300.00'), estado='Pendiente')
        self.url = reverse('gestion_alertas', args=[self.empresa.pk])
        self.bell = reverse('estado_llamador_alertas')

    def permiso(self, usuario, codigo, activo=True):
        PermisoAccesoColaborador.objects.update_or_create(
            empresa=self.empresa, usuario=usuario, codigo=codigo,
            defaults={'activo':activo,'otorgado_por':self.dueno})

    def guardar(self, usuario=None, codigos=()):
        self.client.force_login(self.dueno)
        return self.client.post(self.url, {'formulario':'destinatarios-usuario',
            'usuario': usuario or self.operador.pk, 'codigo':list(codigos)})

    def test_denegacion_gestor_y_empresa_ajena(self):
        self.client.force_login(self.operador)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, {'formulario':'destinatarios-usuario'}).status_code,403)
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(reverse('gestion_alertas', args=[self.otra.pk])).status_code,403)

    def test_sin_asignacion_no_hay_llamador_y_consulta_no_cambia(self):
        self.permiso(self.operador, 'alertas.ver')
        self.permiso(self.operador, 'vencimientos.ver')
        self.client.force_login(self.operador)
        self.assertFalse(self.client.get(self.bell, {'empresa':self.empresa.pk}).json()['mostrar_llamador'])
        self.assertEqual(len(self.client.get(reverse('listar_alertas'),
                                 {'empresa':self.empresa.pk}).json()['movimientos']),2)

    def test_otorgamiento_revocacion_y_sonido_por_usuario(self):
        self.permiso(self.operador, 'alertas.ver')
        self.permiso(self.operador, 'vencimientos.ver')
        r = self.guardar(codigos=['FIN-01'])
        self.assertEqual(r.status_code,302)
        self.client.force_login(self.operador)
        datos = self.client.get(self.bell, {'empresa':self.empresa.pk}).json()
        self.assertTrue(datos['mostrar_llamador'])
        self.assertTrue(datos['sonido_habilitado'])
        # El derecho a la fuente se revoca en caliente, aunque persista la asignación.
        self.permiso(self.operador,'vencimientos.ver',activo=False)
        self.assertFalse(self.client.get(self.bell, {'empresa':self.empresa.pk}).json()['mostrar_llamador'])
        self.permiso(self.operador,'vencimientos.ver')
        self.assertEqual(self.guardar(codigos=[]).status_code,302)
        self.client.force_login(self.operador)
        self.assertFalse(self.client.get(self.bell, {'empresa':self.empresa.pk}).json()['mostrar_llamador'])
        self.assertTrue(EventoConfiguracionAlerta.objects.filter(
            empresa=self.empresa, usuario=self.operador, codigo='FIN-01', activo=False).exists())

    def test_destino_no_otorga_permisos_de_origen(self):
        self.assertEqual(self.guardar(codigos=['FIN-01']).status_code,403)
        self.assertFalse(DestinatarioAlerta.objects.filter(empresa=self.empresa, usuario=self.operador).exists())
        self.permiso(self.operador,'alertas.ver')
        self.assertEqual(self.guardar(codigos=['FIN-01']).status_code,403)
        self.permiso(self.operador,'vencimientos.ver')
        self.assertEqual(self.guardar(codigos=['FIN-01']).status_code,302)

    def test_admin_general_puede_abrir_gestor_sin_ampliar_otros_modulos(self):
        general = User.objects.create_user('general_alertas_b2', password='Clave123!')
        AsignacionUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=general,
                                               jerarquia='admin_general', activo=True)
        self.client.force_login(general)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        r = self.client.get(reverse('panel_administrar'), {'empresa':self.empresa.pk})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Gestión de accesos y alertas')
        self.assertContains(r, 'data-oc-gestion-accesos-url')
        self.assertEqual(self.client.get(reverse('gestion_alertas', args=[self.otra.pk])).status_code, 403)

    def test_no_se_configuran_tipos_futuros_o_usuarios_ajenos(self):
        self.permiso(self.operador,'alertas.ver')
        self.permiso(self.operador,'vencimientos.ver')
        self.assertEqual(self.guardar(codigos=['FIN-04']).status_code,403)
        self.assertEqual(self.guardar(usuario=self.ajeno.pk, codigos=['FIN-01']).status_code,403)
        self.assertFalse(DestinatarioAlerta.objects.exists())

    def test_admin_centro_recibe_solo_de_su_centro(self):
        self.permiso(self.centro_admin,'alertas.ver')
        self.permiso(self.centro_admin,'vencimientos.ver')
        self.assertEqual(self.guardar(usuario=self.centro_admin.pk, codigos=['FIN-01']).status_code,302)
        cubiertos = receptores_efectivos(self.empresa,'FIN-01')
        self.assertEqual(len(cubiertos),1)
        self.assertEqual(cubiertos[0][1],frozenset({self.c1.pk}))
        sin = alertas_sin_destinatarios(self.empresa)
        fin = next(x for x in sin if x['codigo']=='FIN-01')
        self.assertEqual(fin['ocurrencias_sin_receptor'], 1)
        self.assertFalse(fin['sin_receptores'])

    def test_sin_destinatarios_y_solo_tipos_operativos(self):
        self.client.force_login(self.dueno)
        r = self.client.get(self.url)
        self.assertContains(r,'Sin destinatarios')
        self.assertContains(r,'FIN-01')
        self.assertContains(r,'NOM-01')
        self.assertContains(r,'DOC-03')
        self.assertContains(r,'Todavía no operativa')
        self.assertIn('no-store',r.get('Cache-Control',''))

    def test_csrf_en_post(self):
        estricto = Client(enforce_csrf_checks=True)
        estricto.force_login(self.dueno)
        r = estricto.post(self.url,{'formulario':'destinatarios-usuario'})
        self.assertEqual(r.status_code,403)

    def test_seleccion_de_usuario_y_guardado_independiente(self):
        for u in (self.operador, self.centro_admin):
            self.permiso(u, 'alertas.ver')
            self.permiso(u, 'vencimientos.ver')
        self.assertEqual(self.guardar(usuario=self.operador.pk, codigos=['FIN-01']).status_code,302)
        self.assertEqual(self.guardar(usuario=self.centro_admin.pk, codigos=['FIN-01']).status_code,302)
        self.assertEqual(self.guardar(usuario=self.operador.pk, codigos=[]).status_code,302)
        self.assertFalse(DestinatarioAlerta.objects.get(
            empresa=self.empresa, usuario=self.operador, codigo='FIN-01').activo)
        self.assertTrue(DestinatarioAlerta.objects.get(
            empresa=self.empresa, usuario=self.centro_admin, codigo='FIN-01').activo)
        self.client.force_login(self.dueno)
        r = self.client.get(self.url, {'usuario':self.centro_admin.pk})
        self.assertContains(r, 'name="usuario"')
        self.assertContains(r, 'name="codigo"')
        self.assertContains(r, 'checked')
        self.assertContains(r, 'FIN-02')
        self.assertNotContains(r, 'name="destinatario"')

    def test_sonido_por_defecto_y_silencio_personal(self):
        self.permiso(self.operador, 'alertas.ver')
        self.permiso(self.operador, 'vencimientos.ver')
        self.assertEqual(self.guardar(codigos=['FIN-01']).status_code,302)
        self.assertTrue(sonido_habilitado(self.operador, self.empresa))
        url = reverse('sonido_alertas_usuario')
        self.client.force_login(self.operador)
        self.assertTrue(self.client.get(url, {'empresa':self.empresa.pk}).json()['habilitado'])
        r = self.client.post(url, {'empresa':self.empresa.pk, 'habilitado':'0'})
        self.assertEqual(r.status_code,200)
        self.assertFalse(r.json()['habilitado'])
        self.assertFalse(self.client.get(self.bell, {'empresa':self.empresa.pk}).json()['sonido_habilitado'])
        r = self.client.post(url, {'empresa':self.empresa.pk, 'habilitado':'1'})
        self.assertEqual(r.status_code,200)
        self.assertTrue(r.json()['habilitado'])
        self.assertTrue(EventoConfiguracionAlerta.objects.filter(
            empresa=self.empresa, usuario=self.operador, actor=self.operador,
            codigo='SONIDO', activo=True).exists())

    def test_sonido_no_cambiable_por_otro_ni_sin_permiso(self):
        url = reverse('sonido_alertas_usuario')
        self.client.force_login(self.ajeno)
        self.assertEqual(self.client.post(url, {'empresa':self.empresa.pk, 'habilitado':'0'}).status_code,403)
        self.client.force_login(self.operador)
        self.assertEqual(self.client.post(url, {'empresa':self.empresa.pk, 'habilitado':'0'}).status_code,403)
        self.permiso(self.operador, 'alertas.ver')
        self.assertEqual(self.client.post(url, {'empresa':self.empresa.pk, 'habilitado':'talvez'}).status_code,400)
        self.assertTrue(sonido_habilitado(self.operador, self.empresa))

    def test_csrf_sonido_propio(self):
        self.permiso(self.operador, 'alertas.ver')
        estricto = Client(enforce_csrf_checks=True)
        estricto.force_login(self.operador)
        self.assertEqual(estricto.post(reverse('sonido_alertas_usuario'),
            {'empresa':self.empresa.pk,'habilitado':'0'}).status_code,403)
