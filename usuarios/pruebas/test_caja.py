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


def __getattr__(name):
    if name in _PRUEBAS_FINANCIERAS_EXTRAIDAS:
        from usuarios.pruebas import test_financiero

        return getattr(test_financiero, name)

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )

class CobranzaCajaTests(TestCase):
    """
    Prueba la validación y persistencia del ingreso de fondos mediante
    Cobranza, incluyendo efectivo, cheques físicos, aislamiento entre
    Empresas y atomicidad de la operación.
    """

    def setUp(self):
        """
        Crea dos Empresas independientes y los datos mínimos necesarios
        para probar Caja, Cobranza y Cartera de cheques.
        """
        from usuarios.models import Banco, Caja

        self.usuario = User.objects.create_user(
            username="usuario_cobranza",
            password="clave-prueba-123",
        )

        self.otro_usuario = User.objects.create_user(
            username="otro_usuario_cobranza",
            password="clave-prueba-123",
        )

        self.empresa = Empresa.objects.create(
            razon_social="Empresa Cobranza",
            propietario=self.usuario,
        )

        self.empresa_ajena = Empresa.objects.create(
            razon_social="Empresa Ajena Cobranza",
            propietario=self.otro_usuario,
        )

        self.centro = CentroOperativo.objects.create(
            empresa=self.empresa,
            nombre="Casa Central Cobranza",
            tipo="Casa Central",
            activo=True,
        )

        self.centro_ajeno = CentroOperativo.objects.create(
            empresa=self.empresa_ajena,
            nombre="Sucursal Ajena",
            tipo="Sucursal",
            activo=True,
        )

        self.caja = Caja.objects.create(
            empresa=self.empresa,
            centro_operativo=self.centro,
            nombre="Caja Principal",
            activo=True,
        )

        self.caja_ajena = Caja.objects.create(
            empresa=self.empresa_ajena,
            centro_operativo=self.centro_ajeno,
            nombre="Caja Ajena",
            activo=True,
        )

        self.banco = Banco.objects.create(
            empresa=self.empresa,
            nombre="Banco Cobranza",
            activo=True,
        )

        self.banco_ajeno = Banco.objects.create(
            empresa=self.empresa_ajena,
            nombre="Banco Ajeno",
            activo=True,
        )

    def datos_cobranza(
        self,
        *,
        caja=None,
        banco=None,
        efectivo="40000.00",
        importe_cheque="60000.00",
        total_declarado="100000.00",
        cliente_id=None,
    ):
        """
        Construye una Cobranza estándar para reutilizarla en las pruebas.
        """
        if caja is None:
            caja = self.caja

        if banco is None:
            banco = self.banco

        return {
            "caja_id": caja.id,
            "fecha": "2026-09-23",
            "referencia": "Cobranza de prueba",
            "vendedor_referencia": "Vendedor prueba",
            "total_declarado": total_declarado,
            "observaciones": "Prueba automática de Cobranza.",
            "efectivo": {
                "ARS": efectivo,
                "USD": "0.00",
            },
            "cheques": [
                {
                    "numero": "1698",
                    "importe": importe_cheque,
                    "banco_id": banco.id,
                    "cliente_id": cliente_id,
                    "tipo_cheque": "Diferido",
                    "fecha_emision": "2026-09-23",
                    "fecha_acreditacion": "2026-09-30",
                    "fecha_vencimiento": "2026-10-30",
                    "quien_entrega": "Cliente prueba",
                }
            ],
                    }

    def test_crea_cobranza_efectivo_y_cheque_atomicos(self):
        """
        Una Cobranza válida crea su encabezado, el ingreso de efectivo
        y el cheque físico disponible dentro de la misma Caja.
        """
        from usuarios.models import Cobranza, MovimientoCaja, Cheque
        from usuarios.services.caja import crear_cobranza_validada

        resultado = crear_cobranza_validada(
            empresa=self.empresa,
            usuario=self.usuario,
            cobranza_datos=self.datos_cobranza(),
        )

        self.assertEqual(
            Cobranza.objects.count(),
            1,
        )

        cobranza = resultado["cobranza"]

        self.assertEqual(
            cobranza.empresa,
            self.empresa,
        )

        self.assertEqual(
            cobranza.caja,
            self.caja,
        )

        self.assertEqual(
            cobranza.total_declarado,
            Decimal("100000.00"),
        )

        self.assertEqual(
            cobranza.creado_por.usuario,
            self.usuario,
        )
        self.assertEqual(
            cobranza.creado_por.empresa,
            self.empresa,
        )
        self.assertEqual(
            cobranza.creado_por.username_historico,
            self.usuario.username,
        )

        movimiento = MovimientoCaja.objects.get(
            cobranza=cobranza
        )

        self.assertEqual(
            movimiento.tipo,
            "Ingreso",
        )

        self.assertEqual(
            movimiento.moneda,
            "ARS",
        )

        self.assertEqual(
            movimiento.importe,
            Decimal("40000.00"),
        )
        self.assertEqual(
            movimiento.creado_por,
            cobranza.creado_por,
        )

        cheque = Cheque.objects.get(
            cobranza=cobranza
        )

        self.assertEqual(
            cheque.numero,
            "00001698",
        )

        self.assertEqual(
            cheque.caja,
            self.caja,
        )

        self.assertEqual(
            cheque.origen,
            "Tercero",
        )

        self.assertEqual(
            cheque.tipo_instrumento,
            "Cheque",
        )

        self.assertEqual(
            cheque.importe,
            Decimal("60000.00"),
        )

        self.assertEqual(
            cheque.estado,
            "Disponible",
        )

    def test_rechaza_cobranza_que_no_concilia(self):
        """
        El total declarado debe coincidir con el efectivo ARS más los
        cheques recibidos antes de persistir la Cobranza.
        """
        from usuarios.models import Cobranza, MovimientoCaja, Cheque
        from usuarios.services.caja import crear_cobranza_validada

        with self.assertRaisesMessage(
            ValueError,
            "La Cobranza no concilia.",
        ):
            crear_cobranza_validada(
                empresa=self.empresa,
                usuario=self.usuario,
                cobranza_datos=self.datos_cobranza(
                    total_declarado="99999.00",
                ),
            )

        self.assertEqual(
            Cobranza.objects.count(),
            0,
        )

        self.assertEqual(
            MovimientoCaja.objects.count(),
            0,
        )

        self.assertEqual(
            Cheque.objects.count(),
            0,
        )

    def test_rechaza_caja_de_otra_empresa(self):
        """
        Conocer el ID de una Caja ajena no permite utilizarla para
        registrar una Cobranza de otra Empresa.
        """
        from usuarios.models import Cobranza
        from usuarios.services.caja import crear_cobranza_validada

        with self.assertRaises(ValueError):
            crear_cobranza_validada(
                empresa=self.empresa,
                usuario=self.usuario,
                cobranza_datos=self.datos_cobranza(
                    caja=self.caja_ajena,
                ),
            )

        self.assertEqual(
            Cobranza.objects.count(),
            0,
        )

    def test_rechaza_banco_de_otra_empresa(self):
        """
        Un cheque recibido no puede utilizar un Banco perteneciente
        a otra Empresa.
        """
        from usuarios.models import Cobranza, Cheque
        from usuarios.services.caja import crear_cobranza_validada

        with self.assertRaises(ValueError):
            crear_cobranza_validada(
                empresa=self.empresa,
                usuario=self.usuario,
                cobranza_datos=self.datos_cobranza(
                    banco=self.banco_ajeno,
                ),
            )

        self.assertEqual(
            Cobranza.objects.count(),
            0,
        )

        self.assertEqual(
            Cheque.objects.count(),
            0,
        )

    def test_rechaza_cliente_de_otra_empresa(self):
        """
        Un cheque recibido no puede asociarse a un Cliente perteneciente
        a otra Empresa.
        """
        from usuarios.models import Cobranza, Cheque
        from usuarios.services.caja import crear_cobranza_validada

        cliente_ajeno = Cliente.objects.create(
            empresa=self.empresa_ajena,
            centro_operativo=self.centro_ajeno,
            numero_cliente="0001",
            cuit="",
            razon_social="Cliente Ajeno",
            activo=True,
        )

        with self.assertRaises(ValueError):
            crear_cobranza_validada(
                empresa=self.empresa,
                usuario=self.usuario,
                cobranza_datos=self.datos_cobranza(
                    cliente_id=cliente_ajeno.id,
                ),
            )

        self.assertEqual(
            Cobranza.objects.count(),
            0,
        )

        self.assertEqual(
            Cheque.objects.count(),
            0,
        )

    @patch(
        "usuarios.models.Cheque.objects.create",
        side_effect=RuntimeError(
            "Fallo simulado al crear cheque."
        ),
    )
    def test_rollback_si_falla_creacion_del_cheque(
        self,
        crear_cheque_mock,
    ):
        """
        Si falla la creación de un componente después de haberse iniciado
        la Cobranza, la transacción debe revertir también el encabezado
        y el movimiento de efectivo ya creados.
        """
        from usuarios.models import Cobranza, MovimientoCaja, Cheque
        from usuarios.services.caja import crear_cobranza_validada

        with self.assertRaisesMessage(
            RuntimeError,
            "Fallo simulado al crear cheque.",
        ):
            crear_cobranza_validada(
                empresa=self.empresa,
                usuario=self.usuario,
                cobranza_datos=self.datos_cobranza(),
            )

        self.assertEqual(
            Cobranza.objects.count(),
            0,
        )

        self.assertEqual(
            MovimientoCaja.objects.count(),
            0,
        )

        self.assertEqual(
            Cheque.objects.count(),
            0,
        )

class DisponibilidadCajaTests(TestCase):
    """
    Prueba la fuente central de disponibilidad de Caja y Cartera.

    Verifica saldos derivados de MovimientoCaja, separación por moneda
    y Caja, aislamiento empresarial y disponibilidad efectiva de los
    cheques físicos de terceros.
    """

    def setUp(self):
        """
        Crea dos Empresas y varias Cajas para comprobar que la
        disponibilidad nunca mezcle recursos entre ámbitos distintos.
        """
        from usuarios.models import Banco, Caja

        self.usuario = User.objects.create_user(
            username="usuario_disponibilidad",
            password="clave-prueba-123",
        )

        self.otro_usuario = User.objects.create_user(
            username="otro_usuario_disponibilidad",
            password="clave-prueba-123",
        )

        self.empresa = Empresa.objects.create(
            razon_social="Empresa Disponibilidad",
            propietario=self.usuario,
        )

        self.empresa_ajena = Empresa.objects.create(
            razon_social="Empresa Ajena Disponibilidad",
            propietario=self.otro_usuario,
        )

        self.centro = CentroOperativo.objects.create(
            empresa=self.empresa,
            nombre="Casa Central Disponibilidad",
            tipo="Casa Central",
            activo=True,
        )

        self.otro_centro = CentroOperativo.objects.create(
            empresa=self.empresa,
            nombre="Sucursal Disponibilidad",
            tipo="Sucursal",
            activo=True,
        )

        self.centro_ajeno = CentroOperativo.objects.create(
            empresa=self.empresa_ajena,
            nombre="Sucursal Ajena Disponibilidad",
            tipo="Sucursal",
            activo=True,
        )

        self.caja = Caja.objects.create(
            empresa=self.empresa,
            centro_operativo=self.centro,
            nombre="Caja Principal",
            activo=True,
        )

        self.otra_caja = Caja.objects.create(
            empresa=self.empresa,
            centro_operativo=self.otro_centro,
            nombre="Caja Sucursal",
            activo=True,
        )

        self.caja_ajena = Caja.objects.create(
            empresa=self.empresa_ajena,
            centro_operativo=self.centro_ajeno,
            nombre="Caja Ajena",
            activo=True,
        )

        self.banco = Banco.objects.create(
            empresa=self.empresa,
            nombre="Banco Disponibilidad",
            activo=True,
        )

    def crear_movimiento_caja(
        self,
        *,
        caja=None,
        tipo="Ingreso",
        moneda="ARS",
        importe="1000.00",
    ):
        """
        Crea un MovimientoCaja aislado para preparar saldos
        controlados de efectivo.
        """
        from usuarios.models import MovimientoCaja

        if caja is None:
            caja = self.caja

        from usuarios.services.identidades import obtener_identidad_usuario_empresa

        usuario = (
            self.usuario
            if caja.empresa_id == self.empresa.id
            else self.otro_usuario
        )
        identidad = obtener_identidad_usuario_empresa(
            empresa=caja.empresa,
            usuario=usuario,
        )

        return MovimientoCaja.objects.create(
            empresa=caja.empresa,
            caja=caja,
            fecha=date(2026, 9, 23),
            tipo=tipo,
            moneda=moneda,
            importe=Decimal(importe),
            concepto="Movimiento de prueba",
            creado_por=identidad,
        )

    def crear_cheque(
        self,
        *,
        caja=None,
        numero="CHEQUE-DISP-001",
        estado="Disponible",
        fecha_vencimiento=None,
        tipo_instrumento="Cheque",
        origen="Tercero",
        importe="10000.00",
    ):
        """
        Crea un cheque controlado para probar las reglas de
        disponibilidad de la Cartera física.
        """
        from usuarios.models import Cheque

        if caja is None:
            caja = self.caja

        return Cheque.objects.create(
            empresa=caja.empresa,
            caja=caja,
            tipo_instrumento=tipo_instrumento,
            origen=origen,
            tipo_cheque="Diferido",
            banco=(
                self.banco
                if caja.empresa_id == self.empresa.id
                else None
            ),
            numero=numero,
            importe=Decimal(importe),
            fecha_acreditacion=date(2026, 9, 25),
            fecha_vencimiento=fecha_vencimiento,
            estado=estado,
        )

    def test_saldo_efectivo_resta_egresos_de_ingresos(self):
        """
        El saldo de una moneda surge de ingresos menos egresos
        y no de un campo de saldo persistido.
        """
        from usuarios.services.caja import saldo_efectivo_caja

        self.crear_movimiento_caja(
            tipo="Ingreso",
            moneda="ARS",
            importe="100000.00",
        )

        self.crear_movimiento_caja(
            tipo="Ingreso",
            moneda="ARS",
            importe="25000.00",
        )

        self.crear_movimiento_caja(
            tipo="Egreso",
            moneda="ARS",
            importe="40000.00",
        )

        saldo = saldo_efectivo_caja(
            empresa=self.empresa,
            caja=self.caja,
            moneda="ARS",
        )

        self.assertEqual(
            saldo,
            Decimal("85000.00"),
        )

    def test_saldo_separa_ars_y_usd(self):
        """
        Cada moneda conserva un saldo independiente sin realizar
        conversiones ni aplicar un tipo de cambio implícito.
        """
        from usuarios.services.caja import saldo_efectivo_caja

        self.crear_movimiento_caja(
            moneda="ARS",
            importe="50000.00",
        )

        self.crear_movimiento_caja(
            moneda="USD",
            importe="750.00",
        )

        self.assertEqual(
            saldo_efectivo_caja(
                empresa=self.empresa,
                caja=self.caja,
                moneda="ARS",
            ),
            Decimal("50000.00"),
        )

        self.assertEqual(
            saldo_efectivo_caja(
                empresa=self.empresa,
                caja=self.caja,
                moneda="USD",
            ),
            Decimal("750.00"),
        )

    def test_saldo_no_mezcla_otra_caja(self):
        """
        Los movimientos de otra Caja de la misma Empresa no deben
        modificar la disponibilidad de la Caja consultada.
        """
        from usuarios.services.caja import saldo_efectivo_caja

        self.crear_movimiento_caja(
            caja=self.caja,
            importe="10000.00",
        )

        self.crear_movimiento_caja(
            caja=self.otra_caja,
            importe="90000.00",
        )

        saldo = saldo_efectivo_caja(
            empresa=self.empresa,
            caja=self.caja,
            moneda="ARS",
        )

        self.assertEqual(
            saldo,
            Decimal("10000.00"),
        )

    def test_rechaza_caja_de_otra_empresa(self):
        """
        Una Caja ajena no puede utilizarse para consultar
        disponibilidad bajo otra Empresa.
        """
        from usuarios.services.caja import saldo_efectivo_caja

        with self.assertRaisesMessage(
            ValueError,
            "La Caja no pertenece a la Empresa seleccionada.",
        ):
            saldo_efectivo_caja(
                empresa=self.empresa,
                caja=self.caja_ajena,
                moneda="ARS",
            )

    def test_cheque_disponible_y_vigente_aparece_en_cartera(self):
        """
        Un cheque físico de tercero, disponible y todavía vigente
        debe formar parte de la disponibilidad de su Caja.
        """
        from usuarios.services.caja import (
            cheques_fisicos_disponibles_caja,
        )

        cheque = self.crear_cheque(
            fecha_vencimiento=date(2026, 10, 30),
        )

        disponibles = cheques_fisicos_disponibles_caja(
            empresa=self.empresa,
            caja=self.caja,
            fecha_referencia=date(2026, 9, 23),
        )

        self.assertIn(
            cheque,
            disponibles,
        )

    def test_cheque_disponible_pero_vencido_no_aparece(self):
        """
        La fecha efectiva prevalece para la disponibilidad.

        Aunque el registro conserve estado Disponible, un cheque
        cuya fecha de vencimiento ya pasó no puede ofrecerse como
        medio de Pago u Orden de Pago.
        """
        from usuarios.services.caja import (
            cheques_fisicos_disponibles_caja,
        )

        cheque = self.crear_cheque(
            numero="CHEQUE-VENCIDO",
            estado="Disponible",
            fecha_vencimiento=date(2026, 9, 22),
        )

        disponibles = cheques_fisicos_disponibles_caja(
            empresa=self.empresa,
            caja=self.caja,
            fecha_referencia=date(2026, 9, 23),
        )

        self.assertNotIn(
            cheque,
            disponibles,
        )

    def test_cheque_que_vence_hoy_sigue_disponible(self):
        """
        El cheque deja de estar disponible después de su fecha
        de vencimiento, no durante el propio día de vencimiento.
        """
        from usuarios.services.caja import (
            cheques_fisicos_disponibles_caja,
        )

        cheque = self.crear_cheque(
            numero="CHEQUE-VENCE-HOY",
            fecha_vencimiento=date(2026, 9, 23),
        )

        disponibles = cheques_fisicos_disponibles_caja(
            empresa=self.empresa,
            caja=self.caja,
            fecha_referencia=date(2026, 9, 23),
        )

        self.assertIn(
            cheque,
            disponibles,
        )

    def test_cheque_reservado_no_aparece_disponible(self):
        """
        Un cheque reservado continúa existiendo en Cartera pero
        deja de estar disponible para otra operación.
        """
        from usuarios.services.caja import (
            cheques_fisicos_disponibles_caja,
        )

        cheque = self.crear_cheque(
            numero="CHEQUE-RESERVADO",
            estado="Reservado",
            fecha_vencimiento=date(2026, 10, 30),
        )

        disponibles = cheques_fisicos_disponibles_caja(
            empresa=self.empresa,
            caja=self.caja,
            fecha_referencia=date(2026, 9, 23),
        )

        self.assertNotIn(
            cheque,
            disponibles,
        )

    def test_cheque_de_otra_caja_no_aparece(self):
        """
        La Cartera física respeta la custodia real: un cheque ubicado
        en otra Caja no puede utilizarse desde la Caja consultada.
        """
        from usuarios.services.caja import (
            cheques_fisicos_disponibles_caja,
        )

        cheque = self.crear_cheque(
            caja=self.otra_caja,
            numero="CHEQUE-OTRA-CAJA",
            fecha_vencimiento=date(2026, 10, 30),
        )

        disponibles = cheques_fisicos_disponibles_caja(
            empresa=self.empresa,
            caja=self.caja,
            fecha_referencia=date(2026, 9, 23),
        )

        self.assertNotIn(
            cheque,
            disponibles,
        )

    def test_resumen_reune_efectivo_y_cheques_disponibles(self):
        """
        El resumen central expone los saldos por moneda y solamente
        el valor de los cheques realmente utilizables.
        """
        from usuarios.services.caja import (
            resumen_disponibilidad_caja,
        )

        self.crear_movimiento_caja(
            moneda="ARS",
            importe="40000.00",
        )

        self.crear_movimiento_caja(
            moneda="USD",
            importe="500.00",
        )

        cheque_disponible = self.crear_cheque(
            numero="CHEQUE-RESUMEN",
            importe="60000.00",
            fecha_vencimiento=date(2026, 10, 30),
        )

        self.crear_cheque(
            numero="CHEQUE-RESUMEN-VENCIDO",
            importe="20000.00",
            estado="Disponible",
            fecha_vencimiento=date(2026, 9, 22),
        )

        resumen = resumen_disponibilidad_caja(
            empresa=self.empresa,
            caja=self.caja,
            fecha_referencia=date(2026, 9, 23),
        )

        self.assertEqual(
            resumen["efectivo"]["ARS"],
            Decimal("40000.00"),
        )

        self.assertEqual(
            resumen["efectivo"]["USD"],
            Decimal("500.00"),
        )

        self.assertEqual(
            resumen["total_cheques"],
            Decimal("60000.00"),
        )

        self.assertIn(
            cheque_disponible,
            resumen["cheques"],
        )
