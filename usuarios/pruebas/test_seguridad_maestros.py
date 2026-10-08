from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    Banco,
    CuentaBancaria,
    CentroOperativo,
    Empresa,
    Proveedor,
    RecursoOperativo,
    RecursoOperativoCentro,
    Retencion,
    Tarjeta,
)


class SeguridadMaestrosEmpresaTests(TestCase):

    def setUp(self):
        self.propietario = User.objects.create_user(
            username="seg_maestros_propietario",
            password="prueba123",
        )
        self.otro = User.objects.create_user(
            username="seg_maestros_otro",
            password="prueba123",
        )
        self.admin_general = User.objects.create_user(
            username="seg_maestros_admin_general",
            password="prueba123",
        )

        self.empresa = Empresa.objects.create(
            propietario=self.propietario,
            razon_social="Empresa Maestros",
        )
        self.empresa_ajena = Empresa.objects.create(
            propietario=self.otro,
            razon_social="Empresa Maestros Ajena",
        )

        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin_general,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=True,
        )

        self.proveedor = Proveedor.objects.create(
            empresa=self.empresa,
            razon_social="Proveedor Propio",
            cuit="30-11111111-1",
        )
        self.proveedor_ajeno = Proveedor.objects.create(
            empresa=self.empresa_ajena,
            razon_social="Proveedor Ajeno",
            cuit="30-22222222-2",
        )

        self.banco = Banco.objects.create(
            empresa=self.empresa,
            nombre="BANCO PROPIO",
        )
        self.banco_ajeno = Banco.objects.create(
            empresa=self.empresa_ajena,
            nombre="BANCO AJENO",
        )

        self.cuenta = CuentaBancaria.objects.create(
            empresa=self.empresa,
            banco=self.banco,
            nombre="CUENTA PROPIA",
            tipo_cuenta="CuentaCorriente",
            moneda="ARS",
        )
        self.cuenta_ajena = CuentaBancaria.objects.create(
            empresa=self.empresa_ajena,
            banco=self.banco_ajeno,
            nombre="CUENTA AJENA",
            tipo_cuenta="CuentaCorriente",
            moneda="ARS",
        )


        self.tarjeta = Tarjeta.objects.create(
            empresa=self.empresa,
            nombre="TARJETA PROPIA",
            tipo_tarjeta="Credito",
            cuenta_bancaria=self.cuenta,
        )
        self.tarjeta_ajena = Tarjeta.objects.create(
            empresa=self.empresa_ajena,
            nombre="TARJETA AJENA",
            tipo_tarjeta="Credito",
            cuenta_bancaria=self.cuenta_ajena,
        )

        self.retencion = Retencion.objects.create(
            empresa=self.empresa,
            tipo="GANANCIAS",
            descripcion="Retención propia",
        )
        self.retencion_ajena = Retencion.objects.create(
            empresa=self.empresa_ajena,
            tipo="IIBB",
            descripcion="Retención ajena",
        )

        self.centro = CentroOperativo.objects.create(
            empresa=self.empresa,
            nombre="CENTRO PROPIO",
            tipo="Casa Central",
            activo=True,
        )
        self.centro_ajeno = CentroOperativo.objects.create(
            empresa=self.empresa_ajena,
            nombre="CENTRO AJENO",
            tipo="Sucursal",
            activo=True,
        )

        self.recurso = RecursoOperativo.objects.create(
            empresa=self.empresa,
            nombre="RECURSO PROPIO",
            tipo_recurso="Equipo",
            descripcion="Recurso propio",
            activo=True,
        )
        self.recurso_ajeno = RecursoOperativo.objects.create(
            empresa=self.empresa_ajena,
            nombre="RECURSO AJENO",
            tipo_recurso="Equipo",
            descripcion="Recurso ajeno",
            activo=True,
        )

        RecursoOperativoCentro.objects.create(
            recurso_operativo=self.recurso,
            centro_operativo=self.centro,
        )
        RecursoOperativoCentro.objects.create(
            recurso_operativo=self.recurso_ajeno,
            centro_operativo=self.centro_ajeno,
        )

    def test_listados_rechazan_empresa_ajena(self):
        self.client.force_login(self.propietario)

        for nombre_url in (
            "listar_proveedores",
            "listar_bancos",
            "listar_cuentas_bancarias",
            "listar_tarjetas",
            "listar_retenciones",
            "listar_centros_operativos",
            "listar_recursos_operativos",
        ):
            with self.subTest(url=nombre_url):
                respuesta = self.client.get(
                    reverse(nombre_url),
                    {"empresa": self.empresa_ajena.pk},
                )
                self.assertEqual(respuesta.status_code, 403)

    def test_id_ajeno_no_modifica_proveedor(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("modificar_proveedor"),
            {
                "empresa": self.empresa.pk,
                "proveedor": self.proveedor_ajeno.pk,
                "razon_social": "PROVEEDOR FORZADO",
                "cuit": "30-22222222-2",
            },
        )

        self.assertEqual(respuesta.status_code, 404)
        self.proveedor_ajeno.refresh_from_db()
        self.assertEqual(self.proveedor_ajeno.razon_social, "Proveedor Ajeno")

    def test_id_ajeno_no_elimina_banco(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("eliminar_banco"),
            {
                "empresa": self.empresa.pk,
                "banco": self.banco_ajeno.pk,
            },
        )

        self.assertEqual(respuesta.status_code, 404)
        self.banco_ajeno.refresh_from_db()
        self.assertTrue(self.banco_ajeno.activo)

    def test_id_ajeno_no_modifica_cuenta(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("modificar_cuenta_bancaria"),
            {
                "empresa": self.empresa.pk,
                "cuenta": self.cuenta_ajena.pk,
                "banco": self.banco.pk,
                "nombre": "CUENTA FORZADA",
                "tipo_cuenta": "CuentaCorriente",
                "moneda": "ARS",
                "numero_cuenta": "",
                "cbu": "",
                "alias": "",
            },
        )

        self.assertEqual(respuesta.status_code, 404)
        self.cuenta_ajena.refresh_from_db()
        self.assertEqual(self.cuenta_ajena.nombre, "CUENTA AJENA")

    def test_admin_general_activo_puede_listar_maestros(self):
        self.client.force_login(self.admin_general)

        for nombre_url in (
            "listar_proveedores",
            "listar_bancos",
            "listar_cuentas_bancarias",
            "listar_tarjetas",
            "listar_retenciones",
            "listar_centros_operativos",
            "listar_recursos_operativos",
        ):
            with self.subTest(url=nombre_url):
                respuesta = self.client.get(
                    reverse(nombre_url),
                    {"empresa": self.empresa.pk},
                )
                self.assertEqual(respuesta.status_code, 200)

    def test_asignacion_inactiva_no_concede_acceso(self):
        AsignacionUsuarioEmpresa.objects.filter(
            empresa=self.empresa,
            usuario=self.admin_general,
        ).update(activo=False)

        self.client.force_login(self.admin_general)

        respuesta = self.client.get(
            reverse("listar_bancos"),
            {"empresa": self.empresa.pk},
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_ids_ajenos_no_modifican_tarjeta_retencion_centro_recurso(self):
        self.client.force_login(self.propietario)

        casos = (
            (
                "modificar_tarjeta",
                {
                    "empresa": self.empresa.pk,
                    "tarjeta": self.tarjeta_ajena.pk,
                    "nombre": "TARJETA FORZADA",
                    "tipo_tarjeta": "Credito",
                    "cuenta_bancaria": self.cuenta.pk,
                },
            ),
            (
                "modificar_retencion",
                {
                    "empresa": self.empresa.pk,
                    "retencion": self.retencion_ajena.pk,
                    "tipo": "RETENCION FORZADA",
                    "descripcion": "",
                },
            ),
            (
                "modificar_centro_operativo",
                {
                    "empresa": self.empresa.pk,
                    "centro": self.centro_ajeno.pk,
                    "nombre": "CENTRO FORZADO",
                    "tipo": "Sucursal",
                    "direccion": "",
                },
            ),
            (
                "modificar_recurso_operativo",
                {
                    "empresa": self.empresa.pk,
                    "recurso": self.recurso_ajeno.pk,
                    "nombre": "RECURSO FORZADO",
                    "tipo_recurso": "Equipo",
                    "descripcion": "",
                    "centros_operativos": [str(self.centro.pk)],
                },
            ),
        )

        for nombre_url, datos in casos:
            with self.subTest(url=nombre_url):
                respuesta = self.client.post(
                    reverse(nombre_url),
                    datos,
                )
                self.assertEqual(respuesta.status_code, 404)

        self.tarjeta_ajena.refresh_from_db()
        self.retencion_ajena.refresh_from_db()
        self.centro_ajeno.refresh_from_db()
        self.recurso_ajeno.refresh_from_db()

        self.assertEqual(self.tarjeta_ajena.nombre, "TARJETA AJENA")
        self.assertEqual(self.retencion_ajena.tipo, "IIBB")
        self.assertEqual(self.centro_ajeno.nombre, "CENTRO AJENO")
        self.assertEqual(self.recurso_ajeno.nombre, "RECURSO AJENO")

    def test_recurso_rechaza_centro_operativo_de_empresa_ajena(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("guardar_recurso_operativo"),
            {
                "empresa": self.empresa.pk,
                "nombre": "RECURSO NUEVO",
                "tipo_recurso": "Equipo",
                "descripcion": "",
                "centros_operativos": [str(self.centro_ajeno.pk)],
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.json()["ok"])
        self.assertFalse(
            RecursoOperativo.objects.filter(
                empresa=self.empresa,
                nombre="RECURSO NUEVO",
            ).exists()
        )
