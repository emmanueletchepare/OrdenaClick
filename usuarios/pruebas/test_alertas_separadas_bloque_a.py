"""Bloque A: Alertas independientes; denegación por defecto y fuentes seguras."""
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase, SimpleTestCase
from django.urls import reverse

from usuarios.models import (AsignacionUsuarioEmpresa, CentroOperativo, Empresa,
                             Ejercicio, Movimiento, PermisoAccesoColaborador)


class AlertasPorPermisoTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('alerta_owner_a', password='Test12!!')
        self.operador = User.objects.create_user('alerta_colab_a', password='Test12!!')
        self.ajeno = User.objects.create_user('alerta_ajeno_a', password='Test12!!')
        self.e = Empresa.objects.create(propietario=self.owner, razon_social='Alerta empresa A')
        self.otro = Empresa.objects.create(propietario=self.ajeno, razon_social='Alerta empresa B')
        self.centro = CentroOperativo.objects.create(empresa=self.e, nombre='Centro principal',
                                                   tipo='Casa Central', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=self.e, usuario=self.operador,
                                               jerarquia='colaborador', activo=True)
        self.ejercicio = Ejercicio.objects.create(empresa=self.e, numero=2026,
            fecha_inicio=date(2026, 1, 1), fecha_cierre=date(2026, 12, 31))
        self.movimiento = Movimiento.objects.create(empresa=self.e, ejercicio=self.ejercicio,
            centro_operativo=self.centro, fecha_registro=date.today(),
            fecha_vencimiento=date.today() + timedelta(days=1),
            importe=Decimal('900.00'), total=Decimal('900.00'), estado='Pendiente')
        self.client.force_login(self.operador)

    def permiso(self, codigo, activo=True):
        PermisoAccesoColaborador.objects.update_or_create(empresa=self.e,
            usuario=self.operador, codigo=codigo,
            defaults={'activo': activo, 'otorgado_por': self.owner})

    def test_requiere_alertas_ver_aunque_tenga_vencimientos(self):
        self.permiso('vencimientos.ver')
        for nombre in ('listar_alertas', 'estado_llamador_alertas'):
            r = self.client.get(reverse(nombre), {'empresa': self.e.pk})
            self.assertEqual(r.status_code, 403)

    def test_alertas_ver_no_revela_datos_financieros(self):
        self.permiso('alertas.ver')
        r = self.client.get(reverse('listar_alertas'), {'empresa': self.e.pk})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['movimientos'], [])
        self.assertEqual(r.json()['licencias_nomina'], [])
        campana = self.client.get(reverse('estado_llamador_alertas'), {'empresa': self.e.pk})
        self.assertEqual(campana.status_code, 200)
        self.assertFalse(campana.json()['mostrar_llamador'])

    def test_doble_permiso_y_revocacion(self):
        self.permiso('alertas.ver')
        self.permiso('vencimientos.ver')
        r = self.client.get(reverse('listar_alertas'), {'empresa': self.e.pk})
        self.assertEqual(r.status_code, 200)
        self.assertIn(self.movimiento.pk, [m['id'] for m in r.json()['movimientos']])
        self.permiso('vencimientos.ver', activo=False)
        r = self.client.get(reverse('listar_alertas'), {'empresa': self.e.pk})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['movimientos'], [])
        self.permiso('alertas.ver', activo=False)
        self.assertEqual(self.client.get(reverse('listar_alertas'), {'empresa': self.e.pk}).status_code, 403)

    def test_admin_centro_no_ve_movimientos_de_otro_centro(self):
        administrador = User.objects.create_user('alerta_admin_centro', password='Test12!!')
        AsignacionUsuarioEmpresa.objects.create(empresa=self.e, usuario=administrador,
            jerarquia='admin_centro', centro_operativo=self.centro, activo=True)
        for codigo in ('alertas.ver', 'vencimientos.ver'):
            PermisoAccesoColaborador.objects.create(empresa=self.e, usuario=administrador,
                codigo=codigo, activo=True, otorgado_por=self.owner)
        otro_centro = CentroOperativo.objects.create(empresa=self.e, nombre='Segundo centro',
            tipo='Sucursal', activo=True)
        movimiento_ajeno = Movimiento.objects.create(empresa=self.e, ejercicio=self.ejercicio,
            centro_operativo=otro_centro, fecha_registro=date.today(),
            fecha_vencimiento=date.today(), importe=Decimal('120.00'),
            total=Decimal('120.00'), estado='Pendiente')
        self.client.force_login(administrador)
        respuesta = self.client.get(reverse('listar_alertas'), {'empresa': self.e.pk})
        self.assertEqual(respuesta.status_code, 200)
        ids = {m['id'] for m in respuesta.json()['movimientos']}
        self.assertIn(self.movimiento.pk, ids)
        self.assertNotIn(movimiento_ajeno.pk, ids)

    def test_alerta_solo_nomina_sin_permiso_financiero(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        from usuarios.models import PermisoNominaCentro
        self.permiso('alertas.ver')
        self.permiso('nomina.total')
        PermisoNominaCentro.objects.create(empresa=self.e, usuario=self.operador,
            centro_operativo=self.centro, otorgado_por=self.owner)
        licencia = SimpleNamespace(empleado_id=42,
            empleado=SimpleNamespace(nombre_apellido='Prueba autorizada'),
            fecha_vencimiento=date.today() + timedelta(days=1))
        with patch('usuarios.http.vencimientos_alertas.alertas_pendientes'),              patch('usuarios.http.vencimientos_alertas.restringir_nomina', return_value=[licencia]):
            respuesta = self.client.get(reverse('listar_alertas'), {'empresa': self.e.pk})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()['movimientos'], [])
        self.assertEqual(respuesta.json()['licencias_nomina'][0]['empleado_id'], 42)

    def test_empresas_ajenas_y_periodo_antiguo_no_acceden(self):
        self.permiso('alertas.ver')
        self.permiso('vencimientos.ver')
        self.assertEqual(self.client.get(reverse('listar_alertas'), {'empresa': self.otro.pk}).status_code, 403)
        r = self.client.get(reverse('listar_proximos_vencimientos'),
                            {'empresa': self.e.pk, 'periodo': 'alertas'})
        self.assertEqual(r.status_code, 400)
        for periodo in ('hoy', 'semana'):
            self.assertEqual(self.client.get(reverse('listar_proximos_vencimientos'),
                         {'empresa': self.e.pk, 'periodo': periodo}).status_code, 200)


class AlertasUIContratoTests(SimpleTestCase):
    def test_panel_conserva_sidebar_y_destino_operativo(self):
        base = Path(settings.BASE_DIR)
        panel = (base/'templates/usuarios/perfiles/administrador/panel.html').read_text(encoding='utf-8')
        main = (base/'templates/usuarios/perfiles/administrador/partials/main.html').read_text(encoding='utf-8')
        menu = (base/'templates/usuarios/perfiles/administrador/partials/sidebar_modulos_empresa.html').read_text(encoding='utf-8')
        llamador = (base/'static/js/componentes/llamador_alertas.js').read_text(encoding='utf-8')
        self.assertIn("partials/sidebar.html", panel)
        self.assertIn("partials/main.html", panel)
        self.assertIn('id="contenido-operativo"', main)
        self.assertIn('id="btnSidebarAlertas"', menu)
        self.assertIn('btnSidebarAlertas', llamador)
        self.assertNotIn('>Acción inmediata</button>', menu)
