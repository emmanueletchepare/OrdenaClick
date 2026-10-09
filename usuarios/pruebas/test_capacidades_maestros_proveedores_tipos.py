from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import AsignacionUsuarioEmpresa, CentroOperativo, Empresa, Proveedor, TipoGasto


class CapacidadesProveedoresTiposTests(TestCase):
    """Cubre permisos y mÃ©todos de los dos ABM, sin conceder acceso lateral."""

    def setUp(self):
        self.propietario = User.objects.create_user(username="cm_prop", password="Segura123!")
        self.otro = User.objects.create_user(username="cm_otro", password="Segura123!")
        self.admin = User.objects.create_user(username="cm_admin", password="Segura123!")
        self.centro = User.objects.create_user(username="cm_centro", password="Segura123!")
        self.colaborador = User.objects.create_user(username="cm_colab", password="Segura123!")
        self.superusuario = User.objects.create_superuser(username="cm_super", email="cm@example.com", password="Segura123!")
        self.empresa = Empresa.objects.create(propietario=self.propietario, razon_social="Empresa CM")
        self.ajena = Empresa.objects.create(propietario=self.otro, razon_social="Empresa CM ajena")
        self.centro_operativo = CentroOperativo.objects.create(empresa=self.empresa, nombre="Centro CM", tipo="Sucursal", activo=True)
        for usuario, jerarquia in (
            (self.admin, AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL),
            (self.centro, AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO),
            (self.colaborador, AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR),
        ):
            AsignacionUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=usuario, jerarquia=jerarquia, centro_operativo=self.centro_operativo if usuario == self.centro else None, activo=True)
        self.proveedor_ajeno = Proveedor.objects.create(empresa=self.ajena, razon_social="Proveedor ajeno", cuit="30-99999999-9")
        self.tipo_ajeno = TipoGasto.objects.create(empresa=self.ajena, nombre="TIPO AJENO", activo=True)

    def test_metodos_listado_y_mutacion(self):
        self.client.force_login(self.propietario)
        for nombre in ("listar_proveedores", "listar_tipos_gasto"):
            with self.subTest(nombre=nombre):
                self.assertEqual(self.client.post(reverse(nombre), {"empresa": self.empresa.pk}).status_code, 405)
        for nombre in ("guardar_proveedor", "modificar_proveedor", "eliminar_proveedor", "reactivar_proveedor", "guardar_tipo_gasto", "modificar_tipo_gasto", "eliminar_tipo_gasto", "reactivar_tipo_gasto"):
            with self.subTest(nombre=nombre):
                self.assertEqual(self.client.get(reverse(nombre), {"empresa": self.empresa.pk}).status_code, 405)

    def test_listado_capacidades_roles(self):
        for usuario, esperado in ((self.propietario, 200), (self.admin, 200), (self.superusuario, 200), (self.centro, 403), (self.colaborador, 403), (self.otro, 403)):
            self.client.force_login(usuario)
            for nombre in ("listar_proveedores", "listar_tipos_gasto"):
                with self.subTest(usuario=usuario.username, nombre=nombre):
                    self.assertEqual(self.client.get(reverse(nombre), {"empresa": self.empresa.pk}).status_code, esperado)

    def test_objetos_ajenos_no_mutan(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.post(reverse("eliminar_proveedor"), {"empresa": self.empresa.pk, "proveedor": self.proveedor_ajeno.pk})
        self.assertEqual(respuesta.status_code, 404)
        respuesta = self.client.post(reverse("eliminar_tipo_gasto"), {"empresa": self.empresa.pk, "tipo_gasto": self.tipo_ajeno.pk})
        self.assertEqual(respuesta.status_code, 404)
        self.proveedor_ajeno.refresh_from_db()
        self.tipo_ajeno.refresh_from_db()
        self.assertTrue(self.proveedor_ajeno.activo)
        self.assertTrue(self.tipo_ajeno.activo)
