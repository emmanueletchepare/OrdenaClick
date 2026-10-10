"""Pruebas HTTP adversariales de rutas privadas y alcances vigentes.

No amplían permisos ni cambian las vistas; verifican reglas existentes.
"""
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import AsignacionUsuarioEmpresa, Caja, CentroOperativo, Empresa


class AuditoriaRutasPrivadasB1Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dueno = User.objects.create_user(username='b1_dueno', password='B1-fuerte-2026!')
        cls.otro = User.objects.create_user(username='b1_otro', password='B1-fuerte-2026!')
        cls.general = User.objects.create_user(username='b1_general', password='B1-fuerte-2026!')
        cls.centro_user = User.objects.create_user(username='b1_centro', password='B1-fuerte-2026!')
        cls.colaborador = User.objects.create_user(username='b1_colaborador', password='B1-fuerte-2026!')
        cls.superusuario = User.objects.create_superuser(username='b1_super', email='b1super@example.test', password='B1-fuerte-2026!')
        cls.empresa = Empresa.objects.create(propietario=cls.dueno, razon_social='Empresa Auditoria B1')
        cls.ajena = Empresa.objects.create(propietario=cls.otro, razon_social='Empresa Ajena Auditoria B1')
        cls.centro = CentroOperativo.objects.create(empresa=cls.empresa, nombre='Centro B1', tipo='Casa Central', activo=True)
        cls.centro_ajeno = CentroOperativo.objects.create(empresa=cls.ajena, nombre='Centro Ajeno B1', tipo='Casa Central', activo=True)
        cls.caja = Caja.objects.create(empresa=cls.empresa, centro_operativo=cls.centro, nombre='Caja B1', activo=True)
        cls.caja_ajena = Caja.objects.create(empresa=cls.ajena, centro_operativo=cls.centro_ajeno, nombre='Caja Ajena B1', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.general, jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL, activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.centro_user, jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO, centro_operativo=cls.centro, activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.empresa, usuario=cls.colaborador, jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR, activo=True)

    def test_anonimo_no_accede_a_rutas_privadas(self):
        casos = (
            ('panel_admin', {}),
            ('panel_caja', {'empresa': self.empresa.pk}),
            ('ver_gestion_clave', {'empresa': self.empresa.pk, 'clave': 999999}),
            ('obtener_movimiento_edicion', {'empresa': self.empresa.pk, 'movimiento': 999999}),
        )
        for nombre, parametros in casos:
            with self.subTest(ruta=nombre):
                respuesta = self.client.get(reverse(nombre), parametros)
                self.assertEqual(respuesta.status_code, 302)
                destino = urlsplit(respuesta['Location'])
                self.assertEqual(destino.path, reverse('login'))
                self.assertIn('next', parse_qs(destino.query))

    def test_empresa_ajena_no_es_consultable_en_movimientos(self):
        self.client.force_login(self.dueno)
        respuesta = self.client.get(reverse('obtener_movimiento_edicion'), {'empresa': self.ajena.pk, 'movimiento': 999999})
        self.assertEqual(respuesta.status_code, 403)

    def test_empresa_ajena_no_es_consultable_en_caja(self):
        self.client.force_login(self.dueno)
        respuesta = self.client.get(reverse('panel_caja'), {'empresa': self.ajena.pk})
        self.assertEqual(respuesta.status_code, 403)

    def test_admin_centro_no_revela_claves_empresa(self):
        self.client.force_login(self.centro_user)
        respuesta = self.client.get(reverse('ver_gestion_clave'), {'empresa': self.empresa.pk, 'clave': 999999})
        self.assertEqual(respuesta.status_code, 403)

    def test_colaborador_no_revela_claves_empresa(self):
        self.client.force_login(self.colaborador)
        respuesta = self.client.get(reverse('ver_gestion_clave'), {'empresa': self.empresa.pk, 'clave': 999999})
        self.assertEqual(respuesta.status_code, 403)

    def test_admin_general_pasa_permiso_claves_sin_revelar_inexistente(self):
        self.client.force_login(self.general)
        respuesta = self.client.get(reverse('ver_gestion_clave'), {'empresa': self.empresa.pk, 'clave': 999999})
        self.assertEqual(respuesta.status_code, 404)

    def test_admin_centro_no_utiliza_caja_ajena(self):
        self.client.force_login(self.centro_user)
        respuesta = self.client.get(reverse('nueva_cobranza'), {'empresa': self.ajena.pk, 'caja': self.caja_ajena.pk})
        self.assertEqual(respuesta.status_code, 403)

    def test_superusuario_conserva_excepcion_empresa(self):
        self.client.force_login(self.superusuario)
        respuesta = self.client.get(reverse('ver_gestion_clave'), {'empresa': self.ajena.pk, 'clave': 999999})
        self.assertEqual(respuesta.status_code, 404)
