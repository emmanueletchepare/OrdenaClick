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
