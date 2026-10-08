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

    def test_maestros_privados_requieren_autenticacion_explicita(self):
        casos_get = (
            "listar_proveedores",
            "listar_bancos",
            "listar_cuentas_bancarias",
            "listar_centros_operativos",
        )

        for nombre_url in casos_get:
            with self.subTest(metodo="GET", url=nombre_url):
                respuesta = self.client.get(
                    reverse(nombre_url),
                    {"empresa": self.empresa.pk},
                )
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn(
                    reverse("login"),
                    respuesta["Location"],
                )

        casos_post = (
            "guardar_proveedor",
            "guardar_banco",
            "guardar_cuenta_bancaria",
            "guardar_centro_operativo",
        )

        for nombre_url in casos_post:
            with self.subTest(metodo="POST", url=nombre_url):
                respuesta = self.client.post(
                    reverse(nombre_url),
                    {"empresa": self.empresa.pk},
                )
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn(
                    reverse("login"),
                    respuesta["Location"],
                )

    def test_maestros_privados_segundo_bloque_requieren_login(self):
        casos_get = (
            "listar_tarjetas",
            "listar_retenciones",
            "listar_recursos_operativos",
        )

        for nombre_url in casos_get:
            with self.subTest(metodo="GET", url=nombre_url):
                respuesta = self.client.get(
                    reverse(nombre_url),
                    {"empresa": self.empresa.pk},
                )
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn(
                    reverse("login"),
                    respuesta["Location"],
                )

        casos_post = (
            "guardar_tarjeta",
            "modificar_tarjeta",
            "eliminar_tarjeta",
            "reactivar_tarjeta",
            "guardar_retencion",
            "modificar_retencion",
            "eliminar_retencion",
            "reactivar_retencion",
            "guardar_recurso_operativo",
            "modificar_recurso_operativo",
            "eliminar_recurso_operativo",
            "reactivar_recurso_operativo",
        )

        for nombre_url in casos_post:
            with self.subTest(metodo="POST", url=nombre_url):
                respuesta = self.client.post(
                    reverse(nombre_url),
                    {"empresa": self.empresa.pk},
                )
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn(
                    reverse("login"),
                    respuesta["Location"],
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

    def test_bancos_exigen_metodo_http_correcto(self):
        self.client.force_login(self.propietario)

        respuesta_get_mutacion = self.client.get(
            reverse("guardar_banco"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta_get_mutacion.status_code, 405)

        respuesta_post_listado = self.client.post(
            reverse("listar_bancos"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta_post_listado.status_code, 405)

    def test_admin_centro_no_recibe_capacidad_administrar_bancos(self):
        admin_centro = User.objects.create_user(
            username="seg_bancos_admin_centro",
            password="prueba123",
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=admin_centro,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO,
            centro_operativo=self.centro,
            activo=True,
        )

        self.client.force_login(admin_centro)

        respuesta = self.client.get(
            reverse("listar_bancos"),
            {"empresa": self.empresa.pk},
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_superusuario_conserva_capacidad_administrar_bancos(self):
        superusuario = User.objects.create_superuser(
            username="seg_bancos_super",
            email="seg-bancos-super@example.com",
            password="prueba123",
        )
        self.client.force_login(superusuario)

        respuesta = self.client.get(
            reverse("listar_bancos"),
            {"empresa": self.empresa.pk},
        )

        self.assertEqual(respuesta.status_code, 200)

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

    def test_cuentas_bancarias_exigen_metodo_http_correcto(self):
        self.client.force_login(self.propietario)

        respuesta_get_mutacion = self.client.get(
            reverse("guardar_cuenta_bancaria"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta_get_mutacion.status_code, 405)

        respuesta_post_listado = self.client.post(
            reverse("listar_cuentas_bancarias"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta_post_listado.status_code, 405)

    def test_admin_centro_no_administra_cuentas_bancarias(self):
        admin_centro = User.objects.create_user(
            username="seg_cuentas_admin_centro",
            password="prueba123",
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=admin_centro,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO,
            centro_operativo=self.centro,
            activo=True,
        )

        self.client.force_login(admin_centro)

        respuesta = self.client.get(
            reverse("listar_cuentas_bancarias"),
            {"empresa": self.empresa.pk},
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_superusuario_conserva_administracion_de_cuentas_bancarias(self):
        superusuario = User.objects.create_superuser(
            username="seg_cuentas_super",
            email="seg-cuentas-super@example.com",
            password="prueba123",
        )
        self.client.force_login(superusuario)

        respuesta = self.client.get(
            reverse("listar_cuentas_bancarias"),
            {"empresa": self.empresa.pk},
        )

        self.assertEqual(respuesta.status_code, 200)

    def test_cuenta_nueva_rechaza_banco_de_empresa_ajena(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("guardar_cuenta_bancaria"),
            {
                "empresa": self.empresa.pk,
                "banco": self.banco_ajeno.pk,
                "nombre": "CUENTA CON BANCO AJENO",
                "tipo_cuenta": "CuentaCorriente",
                "moneda": "ARS",
                "numero_cuenta": "",
                "cbu": "",
                "alias": "",
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.json()["ok"])
        self.assertFalse(
            CuentaBancaria.objects.filter(
                empresa=self.empresa,
                nombre="CUENTA CON BANCO AJENO",
            ).exists()
        )

    def test_tarjetas_exigen_metodo_http_correcto(self):
        self.client.force_login(self.propietario)

        respuesta_get_mutacion = self.client.get(
            reverse("guardar_tarjeta"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta_get_mutacion.status_code, 405)

        respuesta_post_listado = self.client.post(
            reverse("listar_tarjetas"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta_post_listado.status_code, 405)

    def test_admin_centro_no_administra_tarjetas(self):
        admin_centro = User.objects.create_user(
            username="seg_tarjetas_admin_centro",
            password="prueba123",
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=admin_centro,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO,
            centro_operativo=self.centro,
            activo=True,
        )

        self.client.force_login(admin_centro)

        respuesta = self.client.get(
            reverse("listar_tarjetas"),
            {"empresa": self.empresa.pk},
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_superusuario_conserva_administracion_de_tarjetas(self):
        superusuario = User.objects.create_superuser(
            username="seg_tarjetas_super",
            email="seg-tarjetas-super@example.com",
            password="prueba123",
        )
        self.client.force_login(superusuario)

        respuesta = self.client.get(
            reverse("listar_tarjetas"),
            {"empresa": self.empresa.pk},
        )

        self.assertEqual(respuesta.status_code, 200)

    def test_tarjeta_nueva_rechaza_cuenta_de_empresa_ajena(self):
        self.client.force_login(self.propietario)

        respuesta = self.client.post(
            reverse("guardar_tarjeta"),
            {
                "empresa": self.empresa.pk,
                "nombre": "TARJETA CUENTA AJENA",
                "tipo_tarjeta": "Credito",
                "cuenta_bancaria": self.cuenta_ajena.pk,
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.json()["ok"])
        self.assertFalse(
            Tarjeta.objects.filter(
                empresa=self.empresa,
                nombre="TARJETA CUENTA AJENA",
            ).exists()
        )

    def test_retenciones_y_centros_exigen_metodo_http_correcto(self):
        self.client.force_login(self.propietario)

        casos = (
            ("guardar_retencion", "listar_retenciones"),
            ("guardar_centro_operativo", "listar_centros_operativos"),
        )

        for mutacion, listado in casos:
            with self.subTest(mutacion=mutacion):
                respuesta = self.client.get(
                    reverse(mutacion),
                    {"empresa": self.empresa.pk},
                )
                self.assertEqual(respuesta.status_code, 405)

            with self.subTest(listado=listado):
                respuesta = self.client.post(
                    reverse(listado),
                    {"empresa": self.empresa.pk},
                )
                self.assertEqual(respuesta.status_code, 405)

    def test_admin_centro_no_administra_retenciones_ni_centros(self):
        admin_centro = User.objects.create_user(
            username="seg_ret_cent_admin_centro",
            password="prueba123",
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=admin_centro,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO,
            centro_operativo=self.centro,
            activo=True,
        )

        self.client.force_login(admin_centro)

        for nombre_url in (
            "listar_retenciones",
            "listar_centros_operativos",
        ):
            with self.subTest(url=nombre_url):
                respuesta = self.client.get(
                    reverse(nombre_url),
                    {"empresa": self.empresa.pk},
                )
                self.assertEqual(respuesta.status_code, 403)

    def test_superusuario_conserva_retenciones_y_centros(self):
        superusuario = User.objects.create_superuser(
            username="seg_ret_cent_super",
            email="seg-ret-cent-super@example.com",
            password="prueba123",
        )
        self.client.force_login(superusuario)

        for nombre_url in (
            "listar_retenciones",
            "listar_centros_operativos",
        ):
            with self.subTest(url=nombre_url):
                respuesta = self.client.get(
                    reverse(nombre_url),
                    {"empresa": self.empresa.pk},
                )
                self.assertEqual(respuesta.status_code, 200)

    def test_recursos_operativos_exigen_metodo_http_correcto(self):
        self.client.force_login(self.propietario)

        respuesta_get_mutacion = self.client.get(
            reverse("guardar_recurso_operativo"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta_get_mutacion.status_code, 405)

        respuesta_post_listado = self.client.post(
            reverse("listar_recursos_operativos"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta_post_listado.status_code, 405)

    def test_admin_centro_no_administra_recursos_operativos(self):
        admin_centro = User.objects.create_user(
            username="seg_recursos_admin_centro",
            password="prueba123",
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=admin_centro,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO,
            centro_operativo=self.centro,
            activo=True,
        )

        self.client.force_login(admin_centro)

        respuesta = self.client.get(
            reverse("listar_recursos_operativos"),
            {"empresa": self.empresa.pk},
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_superusuario_conserva_administracion_de_recursos_operativos(self):
        superusuario = User.objects.create_superuser(
            username="seg_recursos_super",
            email="seg-recursos-super@example.com",
            password="prueba123",
        )
        self.client.force_login(superusuario)

        respuesta = self.client.get(
            reverse("listar_recursos_operativos"),
            {"empresa": self.empresa.pk},
        )

        self.assertEqual(respuesta.status_code, 200)

    def test_reactivar_recurso_operativo_activa_recurso_con_centro_activo(self):
        self.client.force_login(self.propietario)

        recurso = RecursoOperativo.objects.create(
            empresa=self.empresa,
            nombre="RECURSO INACTIVO REACTIVABLE",
            tipo_recurso="Equipo",
            descripcion="Para reactivar",
            activo=False,
        )
        RecursoOperativoCentro.objects.create(
            recurso_operativo=recurso,
            centro_operativo=self.centro,
        )

        respuesta = self.client.post(
            reverse("reactivar_recurso_operativo"),
            {
                "empresa": self.empresa.pk,
                "recurso": recurso.pk,
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()["ok"])

        recurso.refresh_from_db()
        self.assertTrue(recurso.activo)

    def test_reactivar_recurso_operativo_no_activa_si_hay_duplicado_activo(self):
        self.client.force_login(self.propietario)

        recurso = RecursoOperativo.objects.create(
            empresa=self.empresa,
            nombre="RECURSO DUPLICADO",
            tipo_recurso="Equipo",
            descripcion="Inactivo",
            activo=False,
        )
        RecursoOperativoCentro.objects.create(
            recurso_operativo=recurso,
            centro_operativo=self.centro,
        )
        RecursoOperativo.objects.create(
            empresa=self.empresa,
            nombre="RECURSO DUPLICADO",
            tipo_recurso="Equipo",
            descripcion="Activo",
            activo=True,
        )

        respuesta = self.client.post(
            reverse("reactivar_recurso_operativo"),
            {
                "empresa": self.empresa.pk,
                "recurso": recurso.pk,
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(respuesta.json()["ok"])

        recurso.refresh_from_db()
        self.assertFalse(recurso.activo)

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
