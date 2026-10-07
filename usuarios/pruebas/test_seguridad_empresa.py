import json
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from django.urls import reverse

from django.test import SimpleTestCase

from usuarios.services.financiero import (
    ESTADO_PAGADO,
    ESTADO_PARCIAL,
    ESTADO_PENDIENTE,
    estado_financiero_movimiento,
    saldo_pendiente_movimiento,
    total_aplicado_movimiento,
    VENCIMIENTO_FUTURO,
    VENCIMIENTO_HOY,
    VENCIMIENTO_PAGADO,
    VENCIMIENTO_SIN_FECHA,
    VENCIMIENTO_VENCIDO,
    estado_vencimiento_movimiento,
    resumen_financiero_movimiento,
    DIAS_ANTICIPACION_ALERTA,
    movimientos_en_alerta,
)

from usuarios.services.pagos import (
    validar_pago_movimiento,
)

from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.test import Client, TestCase

from usuarios.models import (
    AplicacionPago,
    CentroOperativo,
    Cliente,
    Empresa,
    Ejercicio,
    Movimiento,
    Pago,
)

from usuarios.services.seguridad import (
    cajas_autorizadas,
    empresas_autorizadas,
    obtener_caja_autorizada,
    obtener_centro_autorizado,
    obtener_empresa_administrable,
    obtener_empresa_autorizada,
)

class SeguridadEmpresaTests(TestCase):
    """
    Verifica que el acceso a una Empresa dependa de permisos reales
    y no solamente de conocer su identificador.
    """

    def setUp(self):
        """
        Crea usuarios y empresas para probar autorización empresarial.
        """

        self.propietario = User.objects.create_user(
            username="propietario",
            password="prueba123",
        )

        self.otro_usuario = User.objects.create_user(
            username="otro_usuario",
            password="prueba123",
        )

        self.superusuario = User.objects.create_superuser(
            username="superusuario",
            email="superusuario@example.com",
            password="prueba123",
        )

        self.empresa_propietario = Empresa.objects.create(
            propietario=self.propietario,
            razon_social="Empresa Propietario",
        )

        self.empresa_ajena = Empresa.objects.create(
            propietario=self.otro_usuario,
            razon_social="Empresa Ajena",
        )


    def test_propietario_puede_acceder_a_su_empresa(self):
        """
        El propietario normal puede operar sobre su propia Empresa.
        """

        empresa = obtener_empresa_autorizada(
            self.propietario,
            self.empresa_propietario.id,
        )

        self.assertEqual(
            empresa,
            self.empresa_propietario,
        )


    def test_usuario_no_puede_acceder_a_empresa_ajena(self):
        """
        Conocer el ID de otra Empresa no concede autorización.
        """

        with self.assertRaises(
            PermissionDenied
        ):
            obtener_empresa_autorizada(
                self.propietario,
                self.empresa_ajena.id,
            )


    def test_superusuario_puede_acceder_a_cualquier_empresa(self):
        """
        El superusuario puede operar sobre cualquier Empresa.
        """

        empresa = obtener_empresa_autorizada(
            self.superusuario,
            self.empresa_ajena.id,
        )

        self.assertEqual(
            empresa,
            self.empresa_ajena,
        )


    def test_empresa_inexistente_es_denegada(self):
        """
        Una Empresa inexistente no debe considerarse autorizada.
        """

        with self.assertRaises(
            PermissionDenied
        ):
            obtener_empresa_autorizada(
                self.propietario,
                999999,
            )


    def test_usuario_anonimo_es_denegado(self):
        """
        Un usuario no autenticado nunca puede acceder a una Empresa.
        """

        with self.assertRaises(
            PermissionDenied
        ):
            obtener_empresa_autorizada(
                AnonymousUser(),
                self.empresa_propietario.id,
            )

    def test_empresas_autorizadas_devuelve_solo_las_propias(self):
        """
        Un usuario normal sólo debe listar las Empresas que le pertenecen.
        """

        empresas = empresas_autorizadas(
            self.propietario
        )

        self.assertIn(
            self.empresa_propietario,
            empresas,
        )

        self.assertNotIn(
            self.empresa_ajena,
            empresas,
        )


    def test_superusuario_lista_todas_las_empresas(self):
        """
        El superusuario puede listar todas las Empresas existentes.
        """

        empresas = empresas_autorizadas(
            self.superusuario
        )

        self.assertIn(
            self.empresa_propietario,
            empresas,
        )

        self.assertIn(
            self.empresa_ajena,
            empresas,
        )


    def test_panel_admin_rechaza_empresa_ajena(self):
        """
        El panel Administrador no debe permitir seleccionar
        una Empresa perteneciente a otro usuario.
        """

        self.client.force_login(
            self.propietario
        )

        respuesta = self.client.get(
            reverse(
                "panel_admin"
            ),
            {
                "empresa":
                    self.empresa_ajena.id,
            },
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )


    def test_panel_admin_lista_solo_empresas_autorizadas(self):
        """
        El panel Administrador no debe exponer Empresas ajenas
        dentro del listado disponible para el usuario.
        """

        self.client.force_login(
            self.propietario
        )

        respuesta = self.client.get(
            reverse(
                "panel_admin"
            )
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        empresas = list(
            respuesta.context[
                "empresas"
            ]
        )

        self.assertIn(
            self.empresa_propietario,
            empresas,
        )

        self.assertNotIn(
            self.empresa_ajena,
            empresas,
        )

    def test_empresa_nueva_queda_asociada_al_usuario_creador(self):
        """
        Una Empresa creada desde el panel Administrador debe quedar
        asociada automáticamente al usuario que realizó el alta.
        """

        self.client.force_login(
            self.propietario
        )

        respuesta = self.client.post(
            reverse(
                "panel_admin"
            ),
            {
                "guardar_empresa": "1",
                "razon_social": "Empresa Nueva Segura",
                "nombre_fantasia": "Empresa Nueva",
                "cuit": "30-12345678-9",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

        empresa = Empresa.objects.get(
            cuit="30-12345678-9"
        )

        self.assertEqual(
            empresa.propietario,
            self.propietario,
        )

class JerarquiasSeguridadTests(TestCase):
    """
    Verifica el alcance backend de las jerarquías vigentes sin ampliar
    accidentalmente el panel administrativo histórico.
    """

    def setUp(self):
        from usuarios.models import AsignacionUsuarioEmpresa, Caja

        self.propietario = User.objects.create_user(
            username="fundador_seguridad",
            password="prueba123",
        )
        self.admin_general = User.objects.create_user(
            username="admin_general_seguridad",
            password="prueba123",
        )
        self.admin_centro = User.objects.create_user(
            username="admin_centro_seguridad",
            password="prueba123",
        )
        self.colaborador = User.objects.create_user(
            username="colaborador_seguridad",
            password="prueba123",
        )
        self.inactivo = User.objects.create_user(
            username="inactivo_seguridad",
            password="prueba123",
        )
        self.ajeno = User.objects.create_user(
            username="ajeno_seguridad",
            password="prueba123",
        )

        self.empresa = Empresa.objects.create(
            razon_social="Empresa Jerarquías",
            propietario=self.propietario,
        )
        self.empresa_ajena = Empresa.objects.create(
            razon_social="Empresa Ajena Jerarquías",
            propietario=self.ajeno,
        )

        self.centro_uno = CentroOperativo.objects.create(
            empresa=self.empresa,
            nombre="Casa Central Jerarquías",
            tipo="Casa Central",
            activo=True,
        )
        self.centro_dos = CentroOperativo.objects.create(
            empresa=self.empresa,
            nombre="Sucursal Jerarquías",
            tipo="Sucursal",
            activo=True,
        )
        self.centro_ajeno = CentroOperativo.objects.create(
            empresa=self.empresa_ajena,
            nombre="Centro Ajeno Jerarquías",
            tipo="Sucursal",
            activo=True,
        )

        self.caja_uno = Caja.objects.create(
            empresa=self.empresa,
            centro_operativo=self.centro_uno,
            nombre="Caja Uno Jerarquías",
            activo=True,
        )
        self.caja_dos = Caja.objects.create(
            empresa=self.empresa,
            centro_operativo=self.centro_dos,
            nombre="Caja Dos Jerarquías",
            activo=True,
        )
        self.caja_ajena = Caja.objects.create(
            empresa=self.empresa_ajena,
            centro_operativo=self.centro_ajeno,
            nombre="Caja Ajena Jerarquías",
            activo=True,
        )

        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin_general,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=True,
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin_centro,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO,
            centro_operativo=self.centro_uno,
            activo=True,
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.colaborador,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR,
            activo=True,
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.inactivo,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=False,
        )

    def test_empresa_administrable_permite_fundador_y_admin_general(self):
        self.assertEqual(
            obtener_empresa_administrable(
                self.propietario,
                self.empresa.pk,
            ),
            self.empresa,
        )
        self.assertEqual(
            obtener_empresa_administrable(
                self.admin_general,
                self.empresa.pk,
            ),
            self.empresa,
        )

    def test_empresa_administrable_rechaza_admin_centro_colaborador_e_inactivo(self):
        for usuario in (
            self.admin_centro,
            self.colaborador,
            self.inactivo,
        ):
            with self.subTest(usuario=usuario.username):
                with self.assertRaises(PermissionDenied):
                    obtener_empresa_administrable(
                        usuario,
                        self.empresa.pk,
                    )

    def test_admin_centro_solo_accede_a_su_centro(self):
        empresa, centro = obtener_centro_autorizado(
            self.admin_centro,
            self.empresa.pk,
            self.centro_uno.pk,
        )
        self.assertEqual(empresa, self.empresa)
        self.assertEqual(centro, self.centro_uno)

        with self.assertRaises(PermissionDenied):
            obtener_centro_autorizado(
                self.admin_centro,
                self.empresa.pk,
                self.centro_dos.pk,
            )

    def test_admin_general_accede_a_todos_los_centros_de_su_empresa(self):
        for centro in (self.centro_uno, self.centro_dos):
            with self.subTest(centro=centro.nombre):
                empresa, autorizado = obtener_centro_autorizado(
                    self.admin_general,
                    self.empresa.pk,
                    centro.pk,
                )
                self.assertEqual(empresa, self.empresa)
                self.assertEqual(autorizado, centro)

        with self.assertRaises(PermissionDenied):
            obtener_centro_autorizado(
                self.admin_general,
                self.empresa.pk,
                self.centro_ajeno.pk,
            )

    def test_admin_centro_solo_ve_cajas_de_su_centro(self):
        empresa, cajas = cajas_autorizadas(
            self.admin_centro,
            self.empresa.pk,
        )
        self.assertEqual(empresa, self.empresa)
        self.assertEqual(list(cajas), [self.caja_uno])

        empresa, caja = obtener_caja_autorizada(
            self.admin_centro,
            self.empresa.pk,
            self.caja_uno.pk,
        )
        self.assertEqual(empresa, self.empresa)
        self.assertEqual(caja, self.caja_uno)

        with self.assertRaises(PermissionDenied):
            obtener_caja_autorizada(
                self.admin_centro,
                self.empresa.pk,
                self.caja_dos.pk,
            )

    def test_colaborador_no_tiene_acceso_a_caja(self):
        with self.assertRaises(PermissionDenied):
            cajas_autorizadas(
                self.colaborador,
                self.empresa.pk,
            )

        with self.assertRaises(PermissionDenied):
            obtener_caja_autorizada(
                self.colaborador,
                self.empresa.pk,
                self.caja_uno.pk,
            )

    def test_asignacion_inactiva_no_concede_caja(self):
        with self.assertRaises(PermissionDenied):
            cajas_autorizadas(
                self.inactivo,
                self.empresa.pk,
            )

    def test_panel_caja_filtra_por_centro_y_bloquea_colaborador(self):
        self.client.force_login(self.admin_centro)
        respuesta = self.client.get(
            reverse("panel_caja"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta.status_code, 200)
        contenido = respuesta.json()["html"]
        self.assertIn(self.caja_uno.nombre, contenido)
        self.assertNotIn(self.caja_dos.nombre, contenido)

        self.client.force_login(self.colaborador)
        respuesta = self.client.get(
            reverse("panel_caja"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta.status_code, 403)

    def test_nueva_cobranza_respeta_alcance_de_caja(self):
        self.client.force_login(self.admin_centro)

        respuesta = self.client.get(
            reverse("nueva_cobranza"),
            {
                "empresa": self.empresa.pk,
                "caja": self.caja_uno.pk,
            },
        )
        self.assertEqual(respuesta.status_code, 200)

        respuesta = self.client.get(
            reverse("nueva_cobranza"),
            {
                "empresa": self.empresa.pk,
                "caja": self.caja_dos.pk,
            },
        )
        self.assertEqual(respuesta.status_code, 403)

        self.client.force_login(self.colaborador)
        respuesta = self.client.get(
            reverse("nueva_cobranza"),
            {
                "empresa": self.empresa.pk,
                "caja": self.caja_uno.pk,
            },
        )
        self.assertEqual(respuesta.status_code, 403)

    def test_post_nueva_cobranza_admin_centro_guarda_en_caja_autorizada(self):
        from usuarios.models import Cobranza, MovimientoCaja

        self.client.force_login(self.admin_centro)

        respuesta = self.client.post(
            reverse("nueva_cobranza"),
            data=json.dumps({
                "empresa_id": self.empresa.pk,
                "caja_id": self.caja_uno.pk,
                "cobranza": {
                    "fecha": "2026-10-04",
                    "referencia": "Cobranza HTTP autorizada",
                    "vendedor_referencia": "",
                    "total_declarado": "1500.00",
                    "observaciones": "Prueba de POST real.",
                    "efectivo": {
                        "ARS": "1500.00",
                        "USD": "0.00",
                    },
                    "cheques": [],
                },
            }),
            content_type="application/json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertTrue(respuesta.json()["ok"])

        cobranza = Cobranza.objects.get(
            referencia="Cobranza HTTP autorizada"
        )
        self.assertEqual(cobranza.empresa, self.empresa)
        self.assertEqual(cobranza.caja, self.caja_uno)
        self.assertEqual(cobranza.creado_por.usuario, self.admin_centro)

        movimiento = MovimientoCaja.objects.get(
            cobranza=cobranza
        )
        self.assertEqual(movimiento.importe, Decimal("1500.00"))

    def test_post_nueva_cobranza_rechaza_caja_fuera_del_alcance(self):
        from usuarios.models import Cobranza

        self.client.force_login(self.admin_centro)

        respuesta = self.client.post(
            reverse("nueva_cobranza"),
            data=json.dumps({
                "empresa_id": self.empresa.pk,
                "caja_id": self.caja_dos.pk,
                "cobranza": {
                    "fecha": "2026-10-04",
                    "referencia": "Cobranza no autorizada",
                    "total_declarado": "100.00",
                    "efectivo": {
                        "ARS": "100.00",
                        "USD": "0.00",
                    },
                    "cheques": [],
                },
            }),
            content_type="application/json",
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(respuesta.json()["ok"])
        self.assertFalse(
            Cobranza.objects.filter(
                referencia="Cobranza no autorizada"
            ).exists()
        )

    def test_panel_admin_no_se_abre_implicitamente_por_asignacion(self):
        empresas = empresas_autorizadas(self.admin_general)
        self.assertNotIn(self.empresa, empresas)

        with self.assertRaises(PermissionDenied):
            obtener_empresa_autorizada(
                self.admin_general,
                self.empresa.pk,
            )
