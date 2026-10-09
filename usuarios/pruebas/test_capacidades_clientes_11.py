from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import AsignacionUsuarioEmpresa, Empresa, CentroOperativo


class CapacidadesClientesTests(TestCase):
    """Verifica permisos del ABM Clientes con capacidad administrativa."""

    def setUp(self):
        self.propietario = User.objects.create_user(username="cc11_prop", password="Segura123!")
        self.otro = User.objects.create_user(username="cc11_otro", password="Segura123!")
        self.admin = User.objects.create_user(username="cc11_admin", password="Segura123!")
        self.centro = User.objects.create_user(username="cc11_centro", password="Segura123!")
        self.colaborador = User.objects.create_user(username="cc11_colab", password="Segura123!")
        self.superusuario = User.objects.create_superuser(username="cc11_super", email="super11@example.com", password="Segura123!")
        self.empresa = Empresa.objects.create(propietario=self.propietario, razon_social="Empresa Clientes 11")
        self.ajena = Empresa.objects.create(propietario=self.otro, razon_social="Empresa Ajena Clientes 11")
        centro = CentroOperativo.objects.create(empresa=self.empresa, nombre="Centro Clientes 11", tipo="Sucursal", activo=True)
        for usuario, jerarquia in (
            (self.admin, AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL),
            (self.centro, AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO),
            (self.colaborador, AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR),
        ):
            AsignacionUsuarioEmpresa.objects.create(
                empresa=self.empresa, usuario=usuario, jerarquia=jerarquia,
                centro_operativo=centro if usuario == self.centro else None, activo=True,
            )

    def test_listado_permite_propietario_admin_general_y_superusuario(self):
        for usuario in (self.propietario, self.admin, self.superusuario):
            with self.subTest(usuario=usuario.username):
                self.client.force_login(usuario)
                respuesta = self.client.get(reverse("listar_clientes"), {"empresa": self.empresa.pk})
                self.assertEqual(respuesta.status_code, 200)

    def test_listado_rechaza_admin_centro_colaborador_y_otro(self):
        for usuario in (self.centro, self.colaborador, self.otro):
            with self.subTest(usuario=usuario.username):
                self.client.force_login(usuario)
                respuesta = self.client.get(reverse("listar_clientes"), {"empresa": self.empresa.pk})
                self.assertEqual(respuesta.status_code, 403)

    def test_listado_rechaza_empresa_ajena(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.get(reverse("listar_clientes"), {"empresa": self.ajena.pk})
        self.assertEqual(respuesta.status_code, 403)

    def test_mutaciones_rechazan_roles_sin_capacidad(self):
        for usuario in (self.centro, self.colaborador):
            self.client.force_login(usuario)
            for nombre in ("guardar_cliente", "modificar_cliente", "eliminar_cliente", "reactivar_cliente"):
                with self.subTest(usuario=usuario.username, endpoint=nombre):
                    respuesta = self.client.post(reverse(nombre), {"empresa": self.empresa.pk})
                    self.assertEqual(respuesta.status_code, 403)

    def test_rutas_requieren_login(self):
        respuesta = self.client.get(reverse("listar_clientes"), {"empresa": self.empresa.pk})
        self.assertEqual(respuesta.status_code, 302)
        for nombre in ("guardar_cliente", "modificar_cliente", "eliminar_cliente", "reactivar_cliente"):
            with self.subTest(endpoint=nombre):
                respuesta = self.client.post(reverse(nombre), {"empresa": self.empresa.pk})
                self.assertEqual(respuesta.status_code, 302)
