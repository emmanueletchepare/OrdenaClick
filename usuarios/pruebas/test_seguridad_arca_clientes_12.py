from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import AsignacionUsuarioEmpresa, CentroOperativo, Empresa


class SeguridadArcaClientes12Tests(TestCase):
    """ARCA se ejecuta solo con autorizacion administrativa de Empresa."""

    def setUp(self):
        self.prop = User.objects.create_user(username="arca12_prop", password="Segura123!")
        self.otro = User.objects.create_user(username="arca12_otro", password="Segura123!")
        self.admin = User.objects.create_user(username="arca12_admin", password="Segura123!")
        self.centro_user = User.objects.create_user(username="arca12_centro", password="Segura123!")
        self.superuser = User.objects.create_superuser(username="arca12_super", email="arca12@example.com", password="Segura123!")
        self.empresa = Empresa.objects.create(propietario=self.prop, razon_social="ARCA 12")
        self.ajena = Empresa.objects.create(propietario=self.otro, razon_social="ARCA Ajena 12")
        centro = CentroOperativo.objects.create(empresa=self.empresa, nombre="Centro ARCA 12", tipo="Sucursal", activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=self.admin, jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL, activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=self.centro_user, jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO, centro_operativo=centro, activo=True)
        self.url = reverse("autocompletar_cliente_arca")

    def test_anonimo_no_llama_arca(self):
        with patch("usuarios.http.clientes.consultar_persona_arca") as api:
            self.assertEqual(self.client.post(self.url, {"empresa": self.empresa.pk, "cuit": "30123456789"}).status_code, 302)
            api.assert_not_called()

    def test_sin_empresa_o_empresa_ajena_no_llama_arca(self):
        self.client.force_login(self.prop)
        with patch("usuarios.http.clientes.consultar_persona_arca") as api:
            for datos in ({"cuit": "30123456789"}, {"empresa": self.ajena.pk, "cuit": "30123456789"}):
                with self.subTest(datos=datos):
                    self.assertEqual(self.client.post(self.url, datos).status_code, 403)
            api.assert_not_called()

    def test_admin_centro_no_llama_arca(self):
        self.client.force_login(self.centro_user)
        with patch("usuarios.http.clientes.consultar_persona_arca") as api:
            self.assertEqual(self.client.post(self.url, {"empresa": self.empresa.pk, "cuit": "30123456789"}).status_code, 403)
            api.assert_not_called()

    def test_propietario_admin_general_y_superusuario_pueden_consultar(self):
        for user in (self.prop, self.admin, self.superuser):
            with self.subTest(usuario=user.username):
                self.client.force_login(user)
                with patch("usuarios.http.clientes.consultar_persona_arca", return_value={"razon_social": "Prueba", "direccion": "Calle"}) as api:
                    respuesta=self.client.post(self.url, {"empresa": self.empresa.pk, "cuit": "30123456789"})
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertTrue(respuesta.json()["ok"])
                    api.assert_called_once_with("30123456789")

    def test_metodos_http(self):
        self.client.force_login(self.prop)
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(self.client.post(reverse("listar_clientes"), {"empresa": self.empresa.pk}).status_code, 405)
