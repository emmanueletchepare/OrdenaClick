from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    Empresa,
    Proveedor,
    TipoGasto,
    TipoGastoProveedor,
)


class SeguridadTiposGastoTests(TestCase):

    def setUp(self):
        self.propietario = User.objects.create_user(
            username="seg_tg_propietario",
            password="prueba123",
        )
        self.otro = User.objects.create_user(
            username="seg_tg_otro",
            password="prueba123",
        )
        self.admin_general = User.objects.create_user(
            username="seg_tg_admin_general",
            password="prueba123",
        )
        self.inactivo = User.objects.create_user(
            username="seg_tg_inactivo",
            password="prueba123",
        )

        self.empresa = Empresa.objects.create(
            propietario=self.propietario,
            razon_social="Empresa Tipos Gasto",
        )
        self.empresa_ajena = Empresa.objects.create(
            propietario=self.otro,
            razon_social="Empresa Tipos Gasto Ajena",
        )

        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin_general,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=True,
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.inactivo,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=False,
        )

        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            razon_social="Proveedor Propio TG",
            cuit="30-55555555-5",
        )
        self.proveedor_ajeno = Proveedor.objects.create(
            empresa=self.empresa_ajena,
            razon_social="Proveedor Ajeno TG",
            cuit="30-66666666-6",
        )

        self.tipo = TipoGasto.objects.create(
            empresa=self.empresa,
            nombre="SERVICIOS",
            descripcion="Propio",
            activo=True,
        )
        self.tipo_ajeno = TipoGasto.objects.create(
            empresa=self.empresa_ajena,
            nombre="AJENO",
            descripcion="Ajeno",
            activo=True,
        )
        self.tipo_ajeno_inactivo = TipoGasto.objects.create(
            empresa=self.empresa_ajena,
            nombre="AJENO INACTIVO",
            descripcion="Ajeno",
            activo=False,
        )

        TipoGastoProveedor.objects.create(
            tipo_gasto=self.tipo,
            proveedor=self.proveedor,
        )

    def test_listado_rechaza_empresa_ajena(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.get(
            reverse("listar_tipos_gasto"),
            {"empresa": self.empresa_ajena.pk},
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_admin_general_activo_puede_listar(self):
        self.client.force_login(self.admin_general)

        respuesta = self.client.get(
            reverse("listar_tipos_gasto"),
            {"empresa": self.empresa.pk},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()["ok"])

    def test_asignacion_inactiva_no_concede_acceso(self):
        self.client.force_login(self.inactivo)

        respuesta = self.client.get(
            reverse("listar_tipos_gasto"),
            {"empresa": self.empresa.pk},
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_no_modifica_tipo_de_empresa_ajena(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("modificar_tipo_gasto"),
            {
                "empresa": self.empresa.pk,
                "tipo_gasto": self.tipo_ajeno.pk,
                "nombre": "FORZADO",
                "descripcion": "",
            },
        )

        self.assertEqual(respuesta.status_code, 404)
        self.tipo_ajeno.refresh_from_db()
        self.assertEqual(self.tipo_ajeno.nombre, "AJENO")

    def test_no_elimina_tipo_de_empresa_ajena(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("eliminar_tipo_gasto"),
            {
                "empresa": self.empresa.pk,
                "tipo_gasto": self.tipo_ajeno.pk,
            },
        )

        self.assertEqual(respuesta.status_code, 404)
        self.tipo_ajeno.refresh_from_db()
        self.assertTrue(self.tipo_ajeno.activo)

    def test_no_reactiva_tipo_de_empresa_ajena(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("reactivar_tipo_gasto"),
            {
                "empresa": self.empresa.pk,
                "tipo_gasto": self.tipo_ajeno_inactivo.pk,
            },
        )

        self.assertEqual(respuesta.status_code, 404)
        self.tipo_ajeno_inactivo.refresh_from_db()
        self.assertFalse(self.tipo_ajeno_inactivo.activo)

    def test_no_crea_relacion_con_proveedor_ajeno(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("guardar_tipo_gasto"),
            {
                "empresa": self.empresa.pk,
                "nombre": "NUEVO",
                "descripcion": "",
                "proveedores": [str(self.proveedor_ajeno.pk)],
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.json()["ok"])
        self.assertFalse(
            TipoGasto.objects.filter(
                empresa=self.empresa,
                nombre="NUEVO",
            ).exists()
        )
