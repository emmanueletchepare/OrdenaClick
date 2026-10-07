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



# Compatibilidad temporal para comandos historicos como:
# python manage.py test usuarios.tests.ValidarPagoMovimientoTests
_PRUEBAS_FINANCIERAS_EXTRAIDAS = {
    "ServicioFinancieroMovimientoTests",
    "ValidarPagoMovimientoTests",
    "RegistrarPagoManualMovimientoTests",
    "EliminarPagoMovimientoTests",
    "ServicioVencimientosMovimientoTests",
}


_PRUEBAS_CAJA_EXTRAIDAS = {
    "CobranzaCajaTests",
    "DisponibilidadCajaTests",
}


def __getattr__(name):
    if name in _PRUEBAS_CAJA_EXTRAIDAS:
        from usuarios.pruebas import test_caja

        return getattr(test_caja, name)

    if name in _PRUEBAS_FINANCIERAS_EXTRAIDAS:
        from usuarios.pruebas import test_financiero

        return getattr(test_financiero, name)

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
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

class ProximosVencimientosViewTests(TestCase):
    """
    Prueba el comportamiento HTTP de la vista
    de Próximos Vencimientos.
    """

    def setUp(self):
        """
        Crea el usuario, la empresa y el ejercicio
        necesarios para probar la vista.
        """

        self.usuario = User.objects.create_user(
            username="usuario_vencimientos",
            password="clave-prueba-123",
        )

        self.empresa = Empresa.objects.create(
            razon_social="Empresa Vencimientos",
            propietario=self.usuario,
        )

        self.ejercicio = Ejercicio.objects.create(
            empresa=self.empresa,
            numero=2026,
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 12, 31),
        )

        self.client.force_login(
            self.usuario
        )

    def test_hoy_incluye_movimiento_vencido_con_saldo(self):
        """
        El período Hoy mantiene visible una obligación
        vencida que todavía posee saldo pendiente.
        """

        from datetime import timedelta

        movimiento = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date.today(),
            fecha_vencimiento=(
                date.today() - timedelta(days=1)
            ),
            total=Decimal("1000.00"),
            importe=Decimal("1000.00"),
            estado="Pendiente",
        )

        respuesta = self.client.get(
            reverse(
                "listar_proximos_vencimientos"
            ),
            {
                "empresa": self.empresa.id,
                "periodo": "hoy",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        datos = respuesta.json()

        ids_movimientos = [
            item["id"]
            for item in datos["movimientos"]
        ]

        self.assertIn(
            movimiento.id,
            ids_movimientos,
        )

    def test_alertas_respeta_politica_de_tres_dias(self):
        """
        El endpoint de Próximos Vencimientos debe utilizar
        la política central de Alertas.

        Un Movimiento que vence dentro de tres días debe
        aparecer y uno que vence dentro de cuatro días no.
        """

        from datetime import timedelta

        movimiento_tres_dias = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date.today(),
            fecha_vencimiento=(
                date.today() + timedelta(days=3)
            ),
            total=Decimal("1000.00"),
            importe=Decimal("1000.00"),
            estado="Pendiente",
        )

        movimiento_cuatro_dias = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date.today(),
            fecha_vencimiento=(
                date.today() + timedelta(days=4)
            ),
            total=Decimal("2000.00"),
            importe=Decimal("2000.00"),
            estado="Pendiente",
        )

        respuesta = self.client.get(
            reverse(
                "listar_proximos_vencimientos"
            ),
            {
                "empresa": self.empresa.id,
                "periodo": "alertas",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        datos = respuesta.json()

        self.assertTrue(
            datos["ok"]
        )

        self.assertEqual(
            datos["periodo"],
            "alertas",
        )

        ids_movimientos = {
            item["id"]
            for item in datos["movimientos"]
        }

        self.assertIn(
            movimiento_tres_dias.id,
            ids_movimientos,
        )

        self.assertNotIn(
            movimiento_cuatro_dias.id,
            ids_movimientos,
        )

    def test_endpoint_informa_estado_de_vencimiento(self):
        """
        El endpoint debe informar explícitamente el estado
        temporal de cada obligación para que la interfaz
        no tenga que recalcular reglas de vencimiento.
        """

        from datetime import timedelta

        movimiento_vencido = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date.today(),
            fecha_vencimiento=(
                date.today() - timedelta(days=1)
            ),
            total=Decimal("1000.00"),
            importe=Decimal("1000.00"),
            estado="Pendiente",
        )

        movimiento_hoy = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date.today(),
            fecha_vencimiento=date.today(),
            total=Decimal("2000.00"),
            importe=Decimal("2000.00"),
            estado="Pendiente",
        )

        respuesta = self.client.get(
            reverse(
                "listar_proximos_vencimientos"
            ),
            {
                "empresa": self.empresa.id,
                "periodo": "alertas",
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        datos = respuesta.json()

        movimientos_por_id = {
            item["id"]: item
            for item in datos["movimientos"]
        }

        self.assertEqual(
            movimientos_por_id[
                movimiento_vencido.id
            ]["estado_vencimiento"],
            "Vencido",
        )

        self.assertEqual(
            movimientos_por_id[
                movimiento_hoy.id
            ]["estado_vencimiento"],
            "Hoy",
        )

class AlertasMovimientoTests(TestCase):
    """
    Prueba la política inicial de Alertas
    para Movimientos con saldo pendiente.
    """

    def setUp(self):
        """
        Crea la Empresa y el Ejercicio necesarios
        para probar la selección de Alertas.
        """

        self.usuario = User.objects.create_user(
            username="usuario_alertas",
            password="clave-prueba-123",
        )

        self.empresa = Empresa.objects.create(
            razon_social="Empresa Alertas",
            propietario=self.usuario,
        )

        self.ejercicio = Ejercicio.objects.create(
            empresa=self.empresa,
            numero=2026,
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 12, 31),
        )

    def test_alertas_respeta_limite_de_tres_dias(self):
        """
        Una obligación vencida y una que vence dentro
        de tres días deben entrar en Alertas.

        Una obligación que vence dentro de cuatro días
        todavía no debe entrar.
        """

        from datetime import timedelta

        fecha_referencia = date(2026, 9, 12)

        movimiento_vencido = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=fecha_referencia,
            fecha_vencimiento=(
                fecha_referencia
                - timedelta(days=1)
            ),
            total=Decimal("1000.00"),
            importe=Decimal("1000.00"),
            estado="Pendiente",
        )

        movimiento_tres_dias = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=fecha_referencia,
            fecha_vencimiento=(
                fecha_referencia
                + timedelta(days=3)
            ),
            total=Decimal("2000.00"),
            importe=Decimal("2000.00"),
            estado="Pendiente",
        )

        movimiento_cuatro_dias = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=fecha_referencia,
            fecha_vencimiento=(
                fecha_referencia
                + timedelta(days=4)
            ),
            total=Decimal("3000.00"),
            importe=Decimal("3000.00"),
            estado="Pendiente",
        )

        movimientos = movimientos_en_alerta(
            empresa=self.empresa,
            fecha_referencia=fecha_referencia,
        )

        ids_movimientos = set(
            movimientos.values_list(
                "id",
                flat=True,
            )
        )

        self.assertIn(
            movimiento_vencido.id,
            ids_movimientos,
        )

        self.assertIn(
            movimiento_tres_dias.id,
            ids_movimientos,
        )

        self.assertNotIn(
            movimiento_cuatro_dias.id,
            ids_movimientos,
        )

class ClienteABMTests(TestCase):
    """
    Prueba las reglas de negocio y seguridad del ABM de Clientes.

    La identificación operativa y fiscal del Cliente se controla
    dentro de cada Centro Operativo de una Empresa.
    """

    def setUp(self):
        """
        Crea usuarios, Empresas y Centros Operativos independientes
        para verificar unicidad y aislamiento empresarial.
        """
        self.usuario = User.objects.create_user(
            username="usuario_clientes",
            password="clave-prueba-123",
        )

        self.otro_usuario = User.objects.create_user(
            username="otro_usuario_clientes",
            password="clave-prueba-123",
        )

        self.empresa = Empresa.objects.create(
            razon_social="Empresa Clientes",
            propietario=self.usuario,
        )

        self.empresa_ajena = Empresa.objects.create(
            razon_social="Empresa Ajena Clientes",
            propietario=self.otro_usuario,
        )

        self.centro_uno = CentroOperativo.objects.create(
            empresa=self.empresa,
            nombre="Casa Central",
            tipo="Casa Central",
            activo=True,
        )

        self.centro_dos = CentroOperativo.objects.create(
            empresa=self.empresa,
            nombre="Sucursal",
            tipo="Sucursal",
            activo=True,
        )

        self.centro_ajeno = CentroOperativo.objects.create(
            empresa=self.empresa_ajena,
            nombre="Centro Ajeno",
            tipo="Sucursal",
            activo=True,
        )

        self.client.force_login(
            self.usuario
        )

    def datos_cliente(
        self,
        centro=None,
        numero_cliente="0001",
        cuit="20-12345678-6",
        razon_social="Cliente de Prueba",
    ):
        """
        Construye el payload estándar utilizado por el ABM.
        """
        if centro is None:
            centro = self.centro_uno

        return {
            "empresa": str(self.empresa.id),
            "centro_operativo": str(centro.id),
            "numero_cliente": numero_cliente,
            "cuit": cuit,
            "razon_social": razon_social,
            "direccion": "Dirección de prueba",
            "celular": "2284000000",
            "telefono": "2284000001",
        }

    def crear_cliente(
        self,
        centro=None,
        numero_cliente="0001",
        cuit="20123456786",
        razon_social="Cliente Existente",
        activo=True,
    ):
        """
        Crea directamente un Cliente para preparar escenarios
        de duplicación, modificación y reactivación.
        """
        if centro is None:
            centro = self.centro_uno

        return Cliente.objects.create(
            empresa=self.empresa,
            centro_operativo=centro,
            numero_cliente=numero_cliente,
            cuit=cuit,
            razon_social=razon_social,
            activo=activo,
        )

    def test_crea_cliente_y_normaliza_cuit(self):
        """
        Un alta válida debe conservar el N.º Cliente manual
        y guardar el CUIT en su representación de 11 dígitos.
        """
        respuesta = self.client.post(
            reverse("guardar_cliente"),
            self.datos_cliente(),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertTrue(
            respuesta.json()["ok"]
        )

        cliente = Cliente.objects.get(
            empresa=self.empresa,
            centro_operativo=self.centro_uno,
            numero_cliente="0001",
        )

        self.assertEqual(
            cliente.numero_cliente,
            "0001",
        )

        self.assertEqual(
            cliente.cuit,
            "20123456786",
        )

    def test_rechaza_numero_cliente_duplicado_en_mismo_centro(self):
        """
        El mismo N.º Cliente no puede identificar dos Clientes
        dentro del mismo Centro Operativo.
        """
        self.crear_cliente(
            numero_cliente="0001",
            cuit="",
        )

        respuesta = self.client.post(
            reverse("guardar_cliente"),
            self.datos_cliente(
                numero_cliente="0001",
                cuit="",
                razon_social="Segundo Cliente",
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertFalse(
            respuesta.json()["ok"]
        )

        self.assertEqual(
            Cliente.objects.filter(
                empresa=self.empresa,
                centro_operativo=self.centro_uno,
                numero_cliente="0001",
            ).count(),
            1,
        )

    def test_permite_mismo_numero_cliente_en_otro_centro(self):
        """
        El N.º Cliente pertenece al sistema operativo de cada Centro,
        por lo que puede repetirse en otro Centro de la misma Empresa.
        """
        self.crear_cliente(
            centro=self.centro_uno,
            numero_cliente="0001",
            cuit="",
        )

        respuesta = self.client.post(
            reverse("guardar_cliente"),
            self.datos_cliente(
                centro=self.centro_dos,
                numero_cliente="0001",
                cuit="",
                razon_social="Cliente Sucursal",
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertTrue(
            respuesta.json()["ok"]
        )

        self.assertEqual(
            Cliente.objects.filter(
                empresa=self.empresa,
                numero_cliente="0001",
            ).count(),
            2,
        )

    def test_rechaza_cuit_duplicado_en_mismo_centro(self):
        """
        Un CUIT informado no puede pertenecer a dos Clientes
        del mismo Centro Operativo.
        """
        self.crear_cliente(
            numero_cliente="0001",
            cuit="20123456786",
        )

        respuesta = self.client.post(
            reverse("guardar_cliente"),
            self.datos_cliente(
                numero_cliente="0002",
                cuit="20-12345678-6",
                razon_social="Segundo Cliente",
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertFalse(
            respuesta.json()["ok"]
        )

        self.assertEqual(
            Cliente.objects.filter(
                empresa=self.empresa,
                centro_operativo=self.centro_uno,
                cuit="20123456786",
            ).count(),
            1,
        )

    def test_permite_mismo_cuit_en_otro_centro(self):
        """
        El mismo CUIT puede estar asociado a números de Cliente
        diferentes en Centros Operativos diferentes.
        """
        self.crear_cliente(
            centro=self.centro_uno,
            numero_cliente="0001",
            cuit="20123456786",
        )

        respuesta = self.client.post(
            reverse("guardar_cliente"),
            self.datos_cliente(
                centro=self.centro_dos,
                numero_cliente="9001",
                cuit="20-12345678-6",
                razon_social="Cliente Otra Sucursal",
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertTrue(
            respuesta.json()["ok"]
        )

        self.assertEqual(
            Cliente.objects.filter(
                empresa=self.empresa,
                cuit="20123456786",
            ).count(),
            2,
        )

    def test_permite_multiples_clientes_sin_cuit(self):
        """
        El CUIT es opcional y su ausencia no debe impedir registrar
        distintos Clientes dentro del mismo Centro Operativo.
        """
        primera_respuesta = self.client.post(
            reverse("guardar_cliente"),
            self.datos_cliente(
                numero_cliente="0001",
                cuit="",
                razon_social="Cliente Sin CUIT Uno",
            ),
        )

        segunda_respuesta = self.client.post(
            reverse("guardar_cliente"),
            self.datos_cliente(
                numero_cliente="0002",
                cuit="",
                razon_social="Cliente Sin CUIT Dos",
            ),
        )

        self.assertTrue(
            primera_respuesta.json()["ok"]
        )

        self.assertTrue(
            segunda_respuesta.json()["ok"]
        )

        self.assertEqual(
            Cliente.objects.filter(
                empresa=self.empresa,
                centro_operativo=self.centro_uno,
                cuit="",
            ).count(),
            2,
        )

    def test_rechaza_cuit_invalido(self):
        """
        Un CUIT con dígito verificador inválido no debe persistirse.
        """
        respuesta = self.client.post(
            reverse("guardar_cliente"),
            self.datos_cliente(
                cuit="20-12345678-0",
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertFalse(
            respuesta.json()["ok"]
        )

        self.assertEqual(
            Cliente.objects.count(),
            0,
        )

    def test_rechaza_centro_operativo_de_otra_empresa(self):
        """
        El navegador no puede asociar un Cliente de la Empresa
        autorizada con un Centro Operativo de otra Empresa.
        """
        respuesta = self.client.post(
            reverse("guardar_cliente"),
            self.datos_cliente(
                centro=self.centro_ajeno,
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertFalse(
            respuesta.json()["ok"]
        )

        self.assertEqual(
            Cliente.objects.count(),
            0,
        )

    def test_rechaza_empresa_ajena(self):
        """
        Conocer el ID de una Empresa ajena no concede autorización
        para crear Clientes dentro de ella.
        """
        datos = self.datos_cliente()

        datos["empresa"] = str(
            self.empresa_ajena.id
        )

        datos["centro_operativo"] = str(
            self.centro_ajeno.id
        )

        respuesta = self.client.post(
            reverse("guardar_cliente"),
            datos,
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self.assertFalse(
            respuesta.json()["ok"]
        )

        self.assertEqual(
            Cliente.objects.count(),
            0,
        )

    def test_baja_cliente_es_logica(self):
        """
        Eliminar desde el ABM debe desactivar el Cliente sin borrar
        físicamente su identidad ni su futura trazabilidad.
        """
        cliente = self.crear_cliente()

        respuesta = self.client.post(
            reverse("eliminar_cliente"),
            {
                "empresa": str(self.empresa.id),
                "cliente": str(cliente.id),
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertTrue(
            respuesta.json()["ok"]
        )

        cliente.refresh_from_db()

        self.assertFalse(
            cliente.activo
        )

        self.assertTrue(
            Cliente.objects.filter(
                id=cliente.id
            ).exists()
        )

    def test_alta_detecta_cliente_inactivo_para_reactivar(self):
        """
        Un alta equivalente a un Cliente inactivo no debe crear
        un duplicado y debe ofrecer la reactivación del existente.
        """
        cliente = self.crear_cliente(
            activo=False,
        )

        respuesta = self.client.post(
            reverse("guardar_cliente"),
            self.datos_cliente(),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        datos = respuesta.json()

        self.assertFalse(
            datos["ok"]
        )

        self.assertTrue(
            datos["requiere_reactivacion"]
        )

        self.assertEqual(
            datos["cliente"]["id"],
            cliente.id,
        )

        self.assertEqual(
            Cliente.objects.count(),
            1,
        )

    def test_reactiva_cliente_inactivo(self):
        """
        La reactivación debe recuperar el mismo registro histórico
        en lugar de crear una nueva identidad de Cliente.
        """
        cliente = self.crear_cliente(
            activo=False,
        )

        respuesta = self.client.post(
            reverse("reactivar_cliente"),
            {
                "empresa": str(self.empresa.id),
                "cliente": str(cliente.id),
            },
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertTrue(
            respuesta.json()["ok"]
        )

        cliente.refresh_from_db()

        self.assertTrue(
            cliente.activo
        )

        self.assertEqual(
            Cliente.objects.count(),
            1,
        )

    def test_modificacion_no_admite_duplicado(self):
        """
        Modificar un Cliente tampoco puede violar la identificación
        única del Centro Operativo.
        """
        self.crear_cliente(
            numero_cliente="0001",
            cuit="",
            razon_social="Cliente Uno",
        )

        cliente_dos = self.crear_cliente(
            numero_cliente="0002",
            cuit="",
            razon_social="Cliente Dos",
        )

        datos = self.datos_cliente(
            numero_cliente="0001",
            cuit="",
            razon_social="Cliente Dos Modificado",
        )

        datos["cliente"] = str(
            cliente_dos.id
        )

        respuesta = self.client.post(
            reverse("modificar_cliente"),
            datos,
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertFalse(
            respuesta.json()["ok"]
        )

        cliente_dos.refresh_from_db()

        self.assertEqual(
            cliente_dos.numero_cliente,
            "0002",
        )

    def test_eliminar_cliente_rechaza_get(self):
        """
        La baja lógica es una modificación y no puede ejecutarse
        mediante una petición GET.
        """
        cliente = self.crear_cliente()

        respuesta = self.client.get(
            reverse("eliminar_cliente"),
            {
                "empresa": str(self.empresa.id),
                "cliente": str(cliente.id),
            },
        )

        self.assertEqual(
            respuesta.status_code,
            405,
        )

        cliente.refresh_from_db()

        self.assertTrue(
            cliente.activo
        )

class SeguridadInstalacionDesarrolladorTests(TestCase):
    """
    Prueba la seguridad del endpoint que prepara una nueva SECRET_KEY.

    La escritura real de configuración privada se reemplaza por un mock
    para que la suite nunca modifique los secretos de la instalación.
    """

    def setUp(self):
        """
        Crea un usuario normal y un superusuario independientes.
        """
        self.usuario = User.objects.create_user(
            username="usuario_seguridad_instalacion",
            password="clave-prueba-123",
        )

        self.superusuario = User.objects.create_superuser(
            username="superusuario_seguridad_instalacion",
            email="seguridad@example.com",
            password="clave-prueba-123",
        )

        self.url = reverse(
            "reemplazar_secret_key_desarrollador"
        )

    def test_requiere_autenticacion(self):
        """
        Un usuario anónimo no puede acceder a la operación sensible.
        """
        respuesta = self.client.post(
            self.url
        )

        self.assertEqual(
            respuesta.status_code,
            302,
        )

    @patch(
        "usuarios.http.desarrollador.reemplazar_secret_key_privada"
    )
    def test_usuario_normal_es_rechazado(
        self,
        reemplazar_mock,
    ):
        """
        Estar autenticado no alcanza: la operación exige superusuario.
        """
        self.client.force_login(
            self.usuario
        )

        respuesta = self.client.post(
            self.url
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        reemplazar_mock.assert_not_called()

    @patch(
        "usuarios.http.desarrollador.reemplazar_secret_key_privada"
    )
    def test_superusuario_no_puede_utilizar_get(
        self,
        reemplazar_mock,
    ):
        """
        La preparación de una nueva clave sólo puede ejecutarse por POST.
        """
        self.client.force_login(
            self.superusuario
        )

        respuesta = self.client.get(
            self.url
        )

        self.assertEqual(
            respuesta.status_code,
            405,
        )

        reemplazar_mock.assert_not_called()

    @patch.dict(
        "os.environ",
        {
            "ORDENACLICK_SECRET_KEY":
                "clave-administrada-externamente"
        },
    )
    @patch(
        "usuarios.http.desarrollador.reemplazar_secret_key_privada"
    )
    def test_variable_de_entorno_impide_reemplazo(
        self,
        reemplazar_mock,
    ):
        """
        Una clave administrada externamente tiene prioridad y bloquea
        cualquier intento de reemplazo desde OrdenaClick.
        """
        self.client.force_login(
            self.superusuario
        )

        respuesta = self.client.post(
            self.url
        )

        self.assertEqual(
            respuesta.status_code,
            409,
        )

        self.assertFalse(
            respuesta.json()["ok"]
        )

        reemplazar_mock.assert_not_called()

    @patch.dict(
        "os.environ",
        {},
        clear=True,
    )
    @patch(
        "usuarios.http.desarrollador.reemplazar_secret_key_privada"
    )
    def test_superusuario_puede_preparar_nueva_clave_privada(
        self,
        reemplazar_mock,
    ):
        """
        Un superusuario puede preparar una nueva clave cuando no existe
        una variable de entorno que administre SECRET_KEY.
        """
        reemplazar_mock.return_value = True

        self.client.force_login(
            self.superusuario
        )

        respuesta = self.client.post(
            self.url
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        datos = respuesta.json()

        self.assertTrue(
            datos["ok"]
        )

        self.assertTrue(
            datos["requiere_reinicio"]
        )

        reemplazar_mock.assert_called_once_with()

    @patch.dict(
        "os.environ",
        {},
        clear=True,
    )
    @patch(
        "usuarios.http.desarrollador.reemplazar_secret_key_privada"
    )
    def test_respuesta_no_expone_secret_key(
        self,
        reemplazar_mock,
    ):
        """
        La respuesta HTTP nunca debe contener el secreto generado.
        """
        secreto_prueba = (
            "SECRETO-QUE-NUNCA-DEBE-APARECER"
        )

        reemplazar_mock.return_value = True

        self.client.force_login(
            self.superusuario
        )

        respuesta = self.client.post(
            self.url
        )

        contenido = respuesta.content.decode(
            "utf-8"
        )

        self.assertNotIn(
            secreto_prueba,
            contenido,
        )

        self.assertNotIn(
            "ordenaclick_secret_key",
            contenido.lower(),
        )

    @patch.dict(
        "os.environ",
        {},
        clear=True,
    )
    @patch(
        "usuarios.http.desarrollador.reemplazar_secret_key_privada"
    )
    def test_error_de_escritura_se_informa_sin_exponer_detalles(
        self,
        reemplazar_mock,
    ):
        """
        Un fallo del almacenamiento privado devuelve un error controlado
        sin propagar detalles internos al navegador.
        """
        reemplazar_mock.side_effect = RuntimeError(
            "ruta privada sensible de prueba"
        )

        self.client.force_login(
            self.superusuario
        )

        respuesta = self.client.post(
            self.url
        )

        self.assertEqual(
            respuesta.status_code,
            500,
        )

        datos = respuesta.json()

        self.assertFalse(
            datos["ok"]
        )

        self.assertNotIn(
            "ruta privada sensible de prueba",
            respuesta.content.decode("utf-8"),
        )

    @patch.dict(
        "os.environ",
        {},
        clear=True,
    )
    @patch(
        "usuarios.http.desarrollador.reemplazar_secret_key_privada"
    )
    def test_reinicio_pendiente_devuelve_conflicto_controlado(
        self,
        reemplazar_mock,
    ):
        """
        Una nueva rotación pendiente de reinicio se informa como
        conflicto operativo y no como un fallo interno del servidor.
        """
        reemplazar_mock.side_effect = RuntimeError(
            "Ya existe una SECRET_KEY pendiente de reinicio."
        )

        self.client.force_login(
            self.superusuario
        )

        respuesta = self.client.post(
            self.url
        )

        self.assertEqual(
            respuesta.status_code,
            409,
        )

        datos = respuesta.json()

        self.assertFalse(
            datos["ok"]
        )

        self.assertTrue(
            datos["requiere_reinicio"]
        )

        self.assertIn(
            "Reinicie OrdenaClick",
            datos["error"],
        )

    @patch(
        "usuarios.http.desarrollador.reemplazar_secret_key_privada"
    )
    def test_post_sin_csrf_es_rechazado(
        self,
        reemplazar_mock,
    ):
        """
        La operación sensible rechaza un POST autenticado
        cuando falta una validación CSRF correcta.
        """
        cliente_csrf = Client(
            enforce_csrf_checks=True
        )

        cliente_csrf.force_login(
            self.superusuario
        )

        respuesta = cliente_csrf.post(
            self.url
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        reemplazar_mock.assert_not_called()

class SeguridadInstalacionServicioTests(SimpleTestCase):
    """
    Prueba la rotación controlada de SECRET_KEY sin acceder
    a la configuración privada real de la instalación.
    """

    @patch(
        "usuarios.services.seguridad_instalacion."
        "obtener_valor_privado"
    )
    @patch(
        "usuarios.services.seguridad_instalacion.settings.SECRET_KEY",
        "clave-activa-prueba",
    )
    def test_sin_diferencia_no_hay_reinicio_pendiente(
        self,
        obtener_valor_mock,
    ):
        """
        Una clave privada igual a la activa no representa
        un reinicio pendiente.
        """
        from usuarios.services.seguridad_instalacion import (
            secret_key_tiene_reinicio_pendiente,
        )

        obtener_valor_mock.return_value = (
            "clave-activa-prueba"
        )

        self.assertFalse(
            secret_key_tiene_reinicio_pendiente()
        )

    @patch(
        "usuarios.services.seguridad_instalacion."
        "obtener_valor_privado"
    )
    @patch(
        "usuarios.services.seguridad_instalacion.settings.SECRET_KEY",
        "clave-activa-prueba",
    )
    def test_clave_diferente_indica_reinicio_pendiente(
        self,
        obtener_valor_mock,
    ):
        """
        Una clave privada distinta de la activa indica que
        OrdenaClick todavía debe reiniciarse.
        """
        from usuarios.services.seguridad_instalacion import (
            secret_key_tiene_reinicio_pendiente,
        )

        obtener_valor_mock.return_value = (
            "clave-persistida-nueva"
        )

        self.assertTrue(
            secret_key_tiene_reinicio_pendiente()
        )

    @patch(
        "usuarios.services.seguridad_instalacion."
        "obtener_valor_privado"
    )
    @patch(
        "usuarios.services.seguridad_instalacion.settings.SECRET_KEY",
        "clave-activa-prueba",
    )
    def test_sin_clave_privada_no_hay_reinicio_pendiente(
        self,
        obtener_valor_mock,
    ):
        """
        La ausencia de una clave privada no debe interpretarse
        como una rotación pendiente.
        """
        from usuarios.services.seguridad_instalacion import (
            secret_key_tiene_reinicio_pendiente,
        )

        obtener_valor_mock.return_value = ""

        self.assertFalse(
            secret_key_tiene_reinicio_pendiente()
        )

    @patch(
        "usuarios.services.seguridad_instalacion."
        "guardar_valor_privado"
    )
    @patch(
        "usuarios.services.seguridad_instalacion."
        "generar_secret_key"
    )
    @patch(
        "usuarios.services.seguridad_instalacion."
        "secret_key_tiene_reinicio_pendiente"
    )
    def test_reemplazo_guarda_nueva_clave(
        self,
        reinicio_pendiente_mock,
        generar_mock,
        guardar_mock,
    ):
        """
        Sin reinicio pendiente, el servicio genera y persiste
        exactamente una nueva clave.
        """
        from usuarios.services.seguridad_instalacion import (
            reemplazar_secret_key_privada,
        )

        reinicio_pendiente_mock.return_value = False

        generar_mock.return_value = (
            "nueva-clave-controlada-de-prueba"
        )

        resultado = reemplazar_secret_key_privada()

        self.assertTrue(
            resultado
        )

        generar_mock.assert_called_once_with()

        guardar_mock.assert_called_once_with(
            "ordenaclick_secret_key",
            "nueva-clave-controlada-de-prueba",
        )

    @patch(
        "usuarios.services.seguridad_instalacion."
        "guardar_valor_privado"
    )
    @patch(
        "usuarios.services.seguridad_instalacion."
        "generar_secret_key"
    )
    @patch(
        "usuarios.services.seguridad_instalacion."
        "secret_key_tiene_reinicio_pendiente"
    )
    def test_reemplazo_es_bloqueado_si_hay_reinicio_pendiente(
        self,
        reinicio_pendiente_mock,
        generar_mock,
        guardar_mock,
    ):
        """
        Una segunda rotación debe bloquearse antes de generar
        o persistir otra SECRET_KEY.
        """
        from usuarios.services.seguridad_instalacion import (
            reemplazar_secret_key_privada,
        )

        reinicio_pendiente_mock.return_value = True

        with self.assertRaisesMessage(
            RuntimeError,
            "Ya existe una SECRET_KEY pendiente de reinicio.",
        ):
            reemplazar_secret_key_privada()

        generar_mock.assert_not_called()
        guardar_mock.assert_not_called()

class ServicioArcaTests(TestCase):
    """
    Verifica el comportamiento del servicio ARCA sin realizar
    conexiones reales con servicios externos.
    """

    @patch(
        "usuarios.services.arca."
        "solicitar_ticket_acceso_arca"
    )
    @patch(
        "usuarios.services.arca."
        "leer_ticket_acceso_arca"
    )
    def test_reutiliza_ticket_vigente_sin_llamar_wsaa(
        self,
        leer_ticket_mock,
        solicitar_ticket_mock,
    ):
        """
        Un TA vigente debe reutilizarse sin solicitar otro a WSAA.
        """
        from datetime import datetime, timedelta, timezone

        from usuarios.services.arca import (
            obtener_ticket_acceso_arca,
        )

        ticket = {
            "token": "token-prueba",
            "sign": "sign-prueba",
            "vencimiento": (
                datetime.now(timezone.utc)
                + timedelta(hours=1)
            ),
        }

        leer_ticket_mock.return_value = ticket

        resultado = obtener_ticket_acceso_arca()

        self.assertEqual(
            resultado,
            ticket,
        )

        solicitar_ticket_mock.assert_not_called()

    @patch(
        "usuarios.services.arca."
        "obtener_ticket_acceso_arca"
    )
    def test_consulta_rechaza_cuit_invalido_sin_conectar(
        self,
        obtener_ticket_mock,
    ):
        """
        Un CUIT que no tenga exactamente once dígitos debe rechazarse
        antes de intentar consultar el padrón.
        """
        from datetime import datetime, timedelta, timezone

        from usuarios.services.arca import (
            consultar_persona_arca,
        )

        obtener_ticket_mock.return_value = {
            "token": "token-prueba",
            "sign": "sign-prueba",
            "vencimiento": (
                datetime.now(timezone.utc)
                + timedelta(hours=1)
            ),
        }

        with self.assertRaisesMessage(
            ValueError,
            "El CUIT debe contener exactamente 11 dígitos.",
        ):
            consultar_persona_arca(
                "2032390769"
            )

    @patch(
        "usuarios.services.arca."
        "solicitar_ticket_acceso_arca"
    )
    @patch(
        "usuarios.services.arca."
        "leer_ticket_acceso_arca"
    )
    def test_ticket_vencido_solicita_uno_nuevo(
        self,
        leer_ticket_mock,
        solicitar_ticket_mock,
    ):
        """
        Un TA vencido debe provocar una única solicitud nueva a WSAA.
        """
        from datetime import datetime, timedelta, timezone

        from usuarios.services.arca import (
            obtener_ticket_acceso_arca,
        )

        ticket_vencido = {
            "token": "token-vencido",
            "sign": "sign-vencido",
            "vencimiento": (
                datetime.now(timezone.utc)
                - timedelta(minutes=1)
            ),
        }

        ticket_nuevo = {
            "token": "token-nuevo",
            "sign": "sign-nuevo",
            "vencimiento": (
                datetime.now(timezone.utc)
                + timedelta(hours=1)
            ),
        }

        leer_ticket_mock.return_value = (
            ticket_vencido
        )

        solicitar_ticket_mock.return_value = (
            ticket_nuevo
        )

        resultado = obtener_ticket_acceso_arca()

        self.assertEqual(
            resultado,
            ticket_nuevo,
        )

        solicitar_ticket_mock.assert_called_once()

    @patch(
        "usuarios.services.arca."
        "solicitar_ticket_acceso_arca"
    )
    @patch(
        "usuarios.services.arca."
        "leer_ticket_acceso_arca"
    )
    def test_sin_ticket_guardado_solicita_uno_nuevo(
        self,
        leer_ticket_mock,
        solicitar_ticket_mock,
    ):
        """
        La ausencia de un TA guardado debe provocar una única
        solicitud nueva a WSAA.
        """
        from datetime import datetime, timedelta, timezone

        from usuarios.services.arca import (
            obtener_ticket_acceso_arca,
        )

        leer_ticket_mock.side_effect = RuntimeError(
            "No existe un Ticket de Acceso guardado."
        )

        ticket_nuevo = {
            "token": "token-nuevo",
            "sign": "sign-nuevo",
            "vencimiento": (
                datetime.now(timezone.utc)
                + timedelta(hours=1)
            ),
        }

        solicitar_ticket_mock.return_value = (
            ticket_nuevo
        )

        resultado = obtener_ticket_acceso_arca()

        self.assertEqual(
            resultado,
            ticket_nuevo,
        )

        solicitar_ticket_mock.assert_called_once()

    @patch(
        "usuarios.services.arca."
        "_adquirir_bloqueo_ticket_arca"
    )
    @patch(
        "usuarios.services.arca."
        "solicitar_ticket_acceso_arca"
    )
    @patch(
        "usuarios.services.arca."
        "leer_ticket_acceso_arca"
    )
    def test_reutiliza_ticket_renovado_mientras_esperaba_bloqueo(
        self,
        leer_ticket_mock,
        solicitar_ticket_mock,
        adquirir_bloqueo_mock,
    ):
        """
        Si otro proceso renueva el TA mientras se espera el bloqueo,
        debe reutilizarse sin realizar otra solicitud a WSAA.
        """
        import os
        import tempfile
        from datetime import datetime, timedelta, timezone
        from pathlib import Path

        from usuarios.services.arca import (
            obtener_configuracion_arca,
            obtener_ticket_acceso_arca,
        )

        ticket_vencido = {
            "token": "token-vencido",
            "sign": "sign-vencido",
            "vencimiento": (
                datetime.now(timezone.utc)
                - timedelta(minutes=1)
            ),
        }

        ticket_renovado = {
            "token": "token-renovado",
            "sign": "sign-renovado",
            "vencimiento": (
                datetime.now(timezone.utc)
                + timedelta(hours=1)
            ),
        }

        leer_ticket_mock.side_effect = [
            ticket_vencido,
            ticket_renovado,
        ]

        with tempfile.TemporaryDirectory() as directorio:
            ruta_bloqueo = (
                Path(directorio)
                / "TA_response.lock"
            )

            descriptor = os.open(
                ruta_bloqueo,
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY,
            )

            adquirir_bloqueo_mock.return_value = (
                descriptor,
                ruta_bloqueo,
            )

            configuracion = obtener_configuracion_arca()

            resultado = obtener_ticket_acceso_arca(
                configuracion
            )

        self.assertEqual(
            resultado,
            ticket_renovado,
        )

        self.assertEqual(
            leer_ticket_mock.call_count,
            2,
        )

        solicitar_ticket_mock.assert_not_called()

    @patch(
        "usuarios.services.arca."
        "request.urlopen"
    )
    @patch(
        "usuarios.services.arca."
        "obtener_ticket_acceso_arca"
    )
    def test_consulta_persona_devuelve_datos_necesarios(
        self,
        obtener_ticket_mock,
        urlopen_mock,
    ):
        """
        Una respuesta válida del padrón debe devolver únicamente
        razón social y dirección.
        """
        from unittest.mock import MagicMock

        from usuarios.services.arca import (
            consultar_persona_arca,
        )

        obtener_ticket_mock.return_value = {
            "token": "token-prueba",
            "sign": "sign-prueba",
        }

        contenido = b"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <getPersonaResponse>
            <persona>
                <razonSocial>CLIENTE DE PRUEBA</razonSocial>
                <domicilio>
                    <direccion>CALLE 123</direccion>
                </domicilio>
            </persona>
        </getPersonaResponse>
    </soap:Body>
</soap:Envelope>
"""

        respuesta = MagicMock()
        respuesta.read.return_value = contenido

        contexto = MagicMock()
        contexto.__enter__.return_value = respuesta
        contexto.__exit__.return_value = False

        urlopen_mock.return_value = contexto

        resultado = consultar_persona_arca(
            "33693450239"
        )

        self.assertEqual(
            resultado,
            {
                "razon_social": "CLIENTE DE PRUEBA",
                "direccion": "CALLE 123",
            },
        )

        urlopen_mock.assert_called_once()

    @patch(
        "usuarios.services.arca."
        "request.urlopen"
    )
    @patch(
        "usuarios.services.arca."
        "obtener_ticket_acceso_arca"
    )
    def test_consulta_persona_informa_cuit_inexistente(
        self,
        obtener_ticket_mock,
        urlopen_mock,
    ):
        """
        Una respuesta de ARCA indicando persona inexistente debe
        convertirse en un LookupError controlado.
        """
        from io import BytesIO
        from urllib import error

        from usuarios.services.arca import (
            consultar_persona_arca,
        )

        obtener_ticket_mock.return_value = {
            "token": "token-prueba",
            "sign": "sign-prueba",
        }

        contenido_error = (
            b"<soap:Fault>"
            b"<faultstring>"
            b"No existe persona con ese Id"
            b"</faultstring>"
            b"</soap:Fault>"
        )

        urlopen_mock.side_effect = error.HTTPError(
            url="https://arca.test/",
            code=500,
            msg="Internal Server Error",
            hdrs=None,
            fp=BytesIO(contenido_error),
        )

        with self.assertRaisesMessage(
            LookupError,
            "ARCA no encontró una persona para ese CUIT.",
        ):
            consultar_persona_arca(
                "20323907693"
            )

        urlopen_mock.assert_called_once()

    @patch(
        "usuarios.services.arca."
        "request.urlopen"
    )
    @patch(
        "usuarios.services.arca."
        "obtener_ticket_acceso_arca"
    )
    def test_consulta_persona_informa_error_de_conexion(
        self,
        obtener_ticket_mock,
        urlopen_mock,
    ):
        """
        Una falla de conexión con ARCA debe convertirse en un error
        controlado para permitir continuar con la carga manual.
        """
        from urllib import error

        from usuarios.services.arca import (
            consultar_persona_arca,
        )

        obtener_ticket_mock.return_value = {
            "token": "token-prueba",
            "sign": "sign-prueba",
        }

        urlopen_mock.side_effect = error.URLError(
            "servicio no disponible"
        )

        with self.assertRaisesMessage(
            RuntimeError,
            "No se pudo conectar con ARCA.",
        ):
            consultar_persona_arca(
                "33693450239"
            )

        urlopen_mock.assert_called_once()

    @patch(
        "usuarios.services.arca."
        "solicitar_ticket_acceso_arca"
    )
    @patch(
        "usuarios.services.arca."
        "leer_ticket_acceso_arca"
    )
    def test_libera_bloqueo_si_falla_renovacion(
        self,
        leer_ticket_mock,
        solicitar_ticket_mock,
    ):
        """
        El archivo de bloqueo debe eliminarse aunque falle la
        renovación del Ticket de Acceso.
        """
        import tempfile

        from dataclasses import replace
        from pathlib import Path

        from usuarios.services.arca import (
            obtener_configuracion_arca,
            obtener_ticket_acceso_arca,
        )

        leer_ticket_mock.side_effect = RuntimeError(
            "No existe un Ticket de Acceso guardado."
        )

        solicitar_ticket_mock.side_effect = RuntimeError(
            "WSAA no disponible."
        )

        with tempfile.TemporaryDirectory() as directorio:
            directorio = Path(directorio)

            configuracion = replace(
                obtener_configuracion_arca(),
                directorio=directorio,
                ticket_acceso=(
                    directorio
                    / "TA_response.xml"
                ),
            )

            ruta_bloqueo = (
                directorio
                / "TA_response.lock"
            )

            with self.assertRaisesMessage(
                RuntimeError,
                "WSAA no disponible.",
            ):
                obtener_ticket_acceso_arca(
                    configuracion
                )

            self.assertFalse(
                ruta_bloqueo.exists()
            )

    def test_recupera_bloqueo_abandonado(
        self,
    ):
        """
        Un archivo de bloqueo suficientemente antiguo debe considerarse
        abandonado y poder reemplazarse por un bloqueo nuevo.
        """
        import os
        import tempfile
        import time

        from dataclasses import replace
        from pathlib import Path

        from usuarios.services.arca import (
            _adquirir_bloqueo_ticket_arca,
            obtener_configuracion_arca,
        )

        with tempfile.TemporaryDirectory() as directorio:
            directorio = Path(directorio)

            configuracion = replace(
                obtener_configuracion_arca(),
                directorio=directorio,
                ticket_acceso=(
                    directorio
                    / "TA_response.xml"
                ),
            )

            ruta_bloqueo = (
                directorio
                / "TA_response.lock"
            )

            ruta_bloqueo.write_text(
                "",
                encoding="utf-8",
            )

            instante_antiguo = (
                time.time()
                - 120
            )

            os.utime(
                ruta_bloqueo,
                (
                    instante_antiguo,
                    instante_antiguo,
                ),
            )

            descriptor, ruta_obtenida = (
                _adquirir_bloqueo_ticket_arca(
                    configuracion,
                    espera_maxima_segundos=1,
                    antiguedad_maxima_segundos=60,
                )
            )

            try:
                self.assertEqual(
                    ruta_obtenida,
                    ruta_bloqueo,
                )

                self.assertTrue(
                    ruta_bloqueo.exists()
                )

            finally:
                os.close(descriptor)

                ruta_bloqueo.unlink(
                    missing_ok=True
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
