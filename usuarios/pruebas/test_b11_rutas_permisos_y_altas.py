"""B11: aislamiento de rutas y alta sin reemplazo destructivo heredado.

Comprueba superficies HTTP reales, usando las capacidades vigentes, sin
ampliar privilegios, modificar las pantallas ni redefinir la experiencia UX.
Complementa las auditorías anteriores B1, B5, B6, B7 y B8.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.http.empresa_legado import (
    confirmar_reemplazo,
    exportar_empresa as exportar_empresa_legacy,
    importar_empresa as importar_empresa_legacy,
)
from usuarios.models import AsignacionUsuarioEmpresa, CentroOperativo, Empresa
from usuarios.urls import urlpatterns


class AuditoriaB11RutasPermisosTests(TestCase):
    """Cubre rutas sensibles sin usar datos reales ni alterar la navegación."""

    LECTURAS_EMPRESA = (
        "panel_admin",
        "listar_bancos",
        "listar_cuentas_bancarias",
        "listar_centros_operativos",
        "listar_clientes",
        "listar_proveedores",
        "listar_tarjetas",
        "listar_retenciones",
        "listar_recursos_operativos",
        "listar_tipos_gasto",
        "listar_gestion_claves",
        "panel_caja",
        "estado_llamador_alertas",
        "listar_proximos_vencimientos",
    )
    LECTURAS_ADMINISTRATIVAS = (
        "listar_bancos",
        "listar_cuentas_bancarias",
        "listar_centros_operativos",
        "listar_clientes",
        "listar_proveedores",
        "listar_tarjetas",
        "listar_retenciones",
        "listar_recursos_operativos",
        "listar_tipos_gasto",
        "listar_gestion_claves",
    )
    ESCRITURAS_EMPRESA = (
        "guardar_banco",
        "eliminar_banco",
        "guardar_centro_operativo",
        "eliminar_centro_operativo",
        "guardar_proveedor",
        "eliminar_proveedor",
        "guardar_tipo_gasto",
        "eliminar_tipo_gasto",
        "eliminar_cuenta_bancaria",
        "eliminar_tarjeta",
        "eliminar_retencion",
        "eliminar_gestion_clave",
    )

    @classmethod
    def setUpTestData(cls):
        cls.propietario = User.objects.create_user(
            username="b11_propietario", password="B11-Seguro-2026!"
        )
        cls.ajeno = User.objects.create_user(
            username="b11_ajeno", password="B11-Seguro-2026!"
        )
        cls.admin_general = User.objects.create_user(
            username="b11_admin_general", password="B11-Seguro-2026!"
        )
        cls.admin_centro = User.objects.create_user(
            username="b11_admin_centro", password="B11-Seguro-2026!"
        )
        cls.colaborador = User.objects.create_user(
            username="b11_colaborador", password="B11-Seguro-2026!"
        )
        cls.superusuario = User.objects.create_superuser(
            username="b11_super", email="b11super@example.test",
            password="B11-Seguro-2026!",
        )
        cls.empresa = Empresa.objects.create(
            propietario=cls.propietario,
            razon_social="Empresa Propia B11",
        )
        cls.otra = Empresa.objects.create(
            propietario=cls.ajeno,
            razon_social="Empresa Ajena B11",
        )
        cls.centro = CentroOperativo.objects.create(
            empresa=cls.empresa, nombre="Casa Central B11",
            tipo="Casa Central", activo=True,
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=cls.empresa, usuario=cls.admin_general,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=True,
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=cls.empresa, usuario=cls.admin_centro,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO,
            centro_operativo=cls.centro, activo=True,
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=cls.empresa, usuario=cls.colaborador,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR,
            activo=True,
        )

    def test_lecturas_de_empresa_ajena_rechazadas(self):
        """Los IDs conocidos de otra Empresa no conceden lectura."""
        self.client.force_login(self.propietario)
        for nombre in self.LECTURAS_EMPRESA:
            with self.subTest(ruta=nombre):
                respuesta = self.client.get(
                    reverse(nombre), {"empresa": self.otra.pk}
                )
                self.assertEqual(respuesta.status_code, 403)

    def test_descargas_relaciones_y_objetos_ajenos_rechazados(self):
        """También están aisladas las rutas que reciben IDs en la URL."""
        self.client.force_login(self.propietario)
        casos = (
            ("gestionar_relaciones_empresa", {"empresa_id": self.otra.pk}),
            ("exportar_empresa", {"empresa_id": self.otra.pk}),
            ("descargar_documento_empresa", {
                "empresa_id": self.otra.pk, "campo": "estatuto",
            }),
        )
        for nombre, argumentos in casos:
            with self.subTest(ruta=nombre):
                respuesta = self.client.get(reverse(nombre, kwargs=argumentos))
                self.assertEqual(respuesta.status_code, 403)

        for nombre, datos in (
            ("ver_gestion_clave", {"empresa": self.otra.pk, "clave": 999999}),
            ("obtener_movimiento_edicion", {
                "empresa": self.otra.pk, "movimiento": 999999,
            }),
            ("verificar_comprobante_duplicado", {
                "empresa": self.otra.pk, "proveedor": 999999,
                "tipo_comprobante": "FA", "numero_comprobante": "0001-00000001",
            }),
        ):
            with self.subTest(ruta=nombre):
                respuesta = self.client.get(reverse(nombre), datos)
                self.assertEqual(respuesta.status_code, 403)

    def test_escrituras_de_empresa_ajena_rechazadas(self):
        """Los endpoints administrativos no aceptan Empresa ajena por POST."""
        self.client.force_login(self.propietario)
        for nombre in self.ESCRITURAS_EMPRESA:
            with self.subTest(ruta=nombre):
                respuesta = self.client.post(
                    reverse(nombre), {"empresa": self.otra.pk, "nombre": "B11"}
                )
                self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(Empresa.objects.filter(pk=self.otra.pk).count(), 1)

    def test_administracion_no_se_otorga_a_centro_ni_colaborador(self):
        """Las asignaciones operativas no elevan autoridad administrativa."""
        for usuario in (self.admin_centro, self.colaborador):
            self.client.force_login(usuario)
            for nombre in self.LECTURAS_ADMINISTRATIVAS:
                with self.subTest(usuario=usuario.username, ruta=nombre):
                    respuesta = self.client.get(
                        reverse(nombre), {"empresa": self.empresa.pk}
                    )
                    self.assertEqual(respuesta.status_code, 403)

    def test_administrador_general_y_superusuario_mantienen_excepciones(self):
        """No se retiran capacidades válidas ni la excepción de superusuario."""
        self.client.force_login(self.admin_general)
        respuesta = self.client.get(
            reverse("listar_bancos"), {"empresa": self.empresa.pk}
        )
        self.assertEqual(respuesta.status_code, 200)
        self.client.force_login(self.superusuario)
        respuesta = self.client.get(
            reverse("listar_bancos"), {"empresa": self.otra.pk}
        )
        self.assertEqual(respuesta.status_code, 200)

    def test_borrado_empresa_ajena_denegado_y_get_inofensivo(self):
        """Eliminar Empresa exige autorización y método POST."""
        self.client.force_login(self.propietario)
        url_ajena = reverse("eliminar_empresa", kwargs={
            "empresa_id": self.otra.pk,
        })
        respuesta = self.client.post(url_ajena)
        self.assertEqual(respuesta.status_code, 403)
        url_propia = reverse("eliminar_empresa", kwargs={
            "empresa_id": self.empresa.pk,
        })
        respuesta = self.client.get(url_propia)
        self.assertEqual(respuesta.status_code, 405)
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())
        self.assertTrue(Empresa.objects.filter(pk=self.otra.pk).exists())

    def test_funciones_legacy_sin_autenticacion_no_estan_publicadas(self):
        """Las antiguas vistas ZIP no deben reaparecer en el enrutador."""
        callbacks = {patron.callback for patron in urlpatterns}
        for funcion in (
            exportar_empresa_legacy,
            importar_empresa_legacy,
            confirmar_reemplazo,
        ):
            with self.subTest(funcion=funcion.__name__):
                self.assertNotIn(funcion, callbacks)

    def _alta_con_sesion_legacy(self, objetivo):
        """Prepara una sesión antigua y comprueba que el alta no borra."""
        self.client.force_login(self.propietario)
        sesion = self.client.session
        sesion["empresa_reemplazar"] = objetivo.pk
        sesion["confirmar_reemplazo"] = True
        sesion.save()
        respuesta = self.client.post(reverse("panel_admin"), {
            "guardar_empresa": "1",
            "razon_social": "Nueva Empresa B11",
            "nombre_fantasia": "Nueva B11",
            "cuit": "30-12345678-9",
        })
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Empresa.objects.filter(pk=objetivo.pk).exists())
        self.assertTrue(Empresa.objects.filter(
            propietario=self.propietario, razon_social="Nueva Empresa B11",
        ).exists())
        self.assertNotIn("empresa_reemplazar", self.client.session)
        self.assertNotIn("confirmar_reemplazo", self.client.session)

    def test_alta_con_sesion_antigua_no_borra_empresa_ajena(self):
        self._alta_con_sesion_legacy(self.otra)

    def test_alta_con_sesion_antigua_no_borra_empresa_propia(self):
        self._alta_con_sesion_legacy(self.empresa)

    def test_alta_ordinaria_sigue_funcionando(self):
        """Conserva el flujo habitual y la propiedad de la nueva Empresa."""
        self.client.force_login(self.propietario)
        respuesta = self.client.post(reverse("panel_admin"), {
            "guardar_empresa": "1",
            "razon_social": "Nueva Empresa B11",
            "nombre_fantasia": "Nueva B11",
            "cuit": "30-12345678-9",
        })
        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Empresa.objects.filter(
            propietario=self.propietario, razon_social="Nueva Empresa B11",
        ).exists())
