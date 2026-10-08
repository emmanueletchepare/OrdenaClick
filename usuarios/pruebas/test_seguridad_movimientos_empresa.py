from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    Empresa,
    Movimiento,
    Proveedor,
)


class SeguridadMovimientosEmpresaTests(TestCase):

    def setUp(self):
        self.propietario = User.objects.create_user(
            username="seg_mov_propietario",
            password="prueba123",
        )
        self.otro = User.objects.create_user(
            username="seg_mov_otro",
            password="prueba123",
        )
        self.admin_general = User.objects.create_user(
            username="seg_mov_admin_general",
            password="prueba123",
        )

        self.empresa = Empresa.objects.create(
            propietario=self.propietario,
            razon_social="Empresa Seguridad Movimiento",
        )
        self.empresa_ajena = Empresa.objects.create(
            propietario=self.otro,
            razon_social="Empresa Ajena Seguridad Movimiento",
        )

        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin_general,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=True,
        )

        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            razon_social="Proveedor Seguridad",
            cuit="30-33333333-3",
        )
        self.proveedor_ajeno = Proveedor.objects.create(
            empresa=self.empresa_ajena,
            razon_social="Proveedor Seguridad Ajeno",
            cuit="30-44444444-4",
        )

    def test_guardar_movimiento_rechaza_empresa_ajena_antes_de_operar(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("guardar_movimiento"),
            {
                "empresa": self.empresa_ajena.pk,
                "tipo_gasto": "999999",
                "proveedor": self.proveedor_ajeno.pk,
                "fecha_registro": "2026-10-08",
            },
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(
            Movimiento.objects.filter(
                empresa=self.empresa_ajena,
            ).exists()
        )

    def test_admin_general_no_gana_alta_movimiento_por_asignacion(self):
        self.client.force_login(self.admin_general)

        respuesta = self.client.post(
            reverse("guardar_movimiento"),
            {
                "empresa": self.empresa.pk,
                "tipo_gasto": "999999",
                "proveedor": self.proveedor.pk,
                "fecha_registro": "2026-10-08",
            },
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(
            Movimiento.objects.filter(
                empresa=self.empresa,
            ).exists()
        )

    def test_verificar_comprobante_rechaza_empresa_ajena(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.get(
            reverse("verificar_comprobante_duplicado"),
            {
                "empresa": self.empresa_ajena.pk,
                "proveedor": self.proveedor_ajeno.pk,
                "tipo_comprobante": "Factura",
                "numero_comprobante": "0001-00000001",
            },
        )
        self.assertEqual(respuesta.status_code, 403)

    def test_verificar_comprobante_no_acepta_proveedor_de_otra_empresa(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.get(
            reverse("verificar_comprobante_duplicado"),
            {
                "empresa": self.empresa.pk,
                "proveedor": self.proveedor_ajeno.pk,
                "tipo_comprobante": "Factura",
                "numero_comprobante": "0001-00000001",
            },
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(respuesta.json()["ok"])

    def test_eliminar_empresa_requiere_post(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.get(
            reverse("eliminar_empresa", args=[self.empresa.pk])
        )
        self.assertEqual(respuesta.status_code, 405)
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())

    def test_eliminar_empresa_rechaza_empresa_ajena(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.post(
            reverse("eliminar_empresa", args=[self.empresa_ajena.pk])
        )
        self.assertEqual(respuesta.status_code, 403)
        self.assertTrue(Empresa.objects.filter(pk=self.empresa_ajena.pk).exists())

    def test_admin_general_no_gana_eliminacion_por_asignacion(self):
        self.client.force_login(self.admin_general)
        respuesta = self.client.post(
            reverse("eliminar_empresa", args=[self.empresa.pk])
        )
        self.assertEqual(respuesta.status_code, 403)
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())

    def test_propietario_puede_eliminar_su_empresa_por_post(self):
        empresa_eliminar = Empresa.objects.create(
            propietario=self.propietario,
            razon_social="Empresa Para Eliminar",
        )
        self.client.force_login(self.propietario)
        respuesta = self.client.post(
            reverse("eliminar_empresa", args=[empresa_eliminar.pk])
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse(Empresa.objects.filter(pk=empresa_eliminar.pk).exists())
