from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from usuarios.services.financiero import (
    ESTADO_PAGADO,
    ESTADO_PARCIAL,
    ESTADO_PENDIENTE,
    estado_financiero_movimiento,
    saldo_pendiente_movimiento,
    total_aplicado_movimiento,
)


class ServicioFinancieroMovimientoTests(SimpleTestCase):
    """
    Prueba las reglas financieras centrales aplicadas
    sobre un Movimiento.

    Estos tests verifican exclusivamente la lógica de:

    - Total documental.
    - Importe aplicado.
    - Saldo pendiente.
    - Estado financiero.

    Los distintos medios de pago no deben alterar estas
    reglas: la fuente de verdad para cancelar un Movimiento
    es siempre AplicacionPago.importe.
    """

    def crear_movimiento(
        self,
        total,
        total_aplicado,
    ):
        """
        Crea un Movimiento controlado para probar el servicio
        financiero sin depender de datos persistidos.

        La relación aplicaciones_pago simula el resultado de
        la agregación que realizaría Django sobre AplicacionPago.
        """

        aplicaciones_pago = MagicMock()

        aplicaciones_pago.aggregate.return_value = {
            "total": Decimal(total_aplicado)
        }

        return SimpleNamespace(
            total=Decimal(total),
            aplicaciones_pago=aplicaciones_pago,
        )

    def test_movimiento_sin_pagos_esta_pendiente(self):
        """
        Un Movimiento sin aplicaciones conserva todo
        su importe como saldo pendiente.
        """

        movimiento = self.crear_movimiento(
            "100000.00",
            "0.00",
        )

        self.assertEqual(
            total_aplicado_movimiento(movimiento),
            Decimal("0.00"),
        )

        self.assertEqual(
            saldo_pendiente_movimiento(movimiento),
            Decimal("100000.00"),
        )

        self.assertEqual(
            estado_financiero_movimiento(movimiento),
            ESTADO_PENDIENTE,
        )

    def test_movimiento_con_pago_parcial_esta_parcial(self):
        """
        Una aplicación inferior al total reduce el saldo
        y deja al Movimiento en estado Parcial.
        """

        movimiento = self.crear_movimiento(
            "100000.00",
            "40000.00",
        )

        self.assertEqual(
            saldo_pendiente_movimiento(movimiento),
            Decimal("60000.00"),
        )

        self.assertEqual(
            estado_financiero_movimiento(movimiento),
            ESTADO_PARCIAL,
        )

    def test_movimiento_totalmente_pagado_esta_pagado(self):
        """
        Cuando las aplicaciones alcanzan exactamente el total,
        el Movimiento no mantiene saldo pendiente.
        """

        movimiento = self.crear_movimiento(
            "100000.00",
            "100000.00",
        )

        self.assertEqual(
            saldo_pendiente_movimiento(movimiento),
            Decimal("0.00"),
        )

        self.assertEqual(
            estado_financiero_movimiento(movimiento),
            ESTADO_PAGADO,
        )

    def test_multiples_aplicaciones_utilizan_su_suma(self):
        """
        El servicio utiliza el total agregado de todas las
        AplicacionPago asociadas al Movimiento.
        """

        movimiento = self.crear_movimiento(
            "100000.00",
            "75000.00",
        )

        self.assertEqual(
            total_aplicado_movimiento(movimiento),
            Decimal("75000.00"),
        )

        self.assertEqual(
            saldo_pendiente_movimiento(movimiento),
            Decimal("25000.00"),
        )

        self.assertEqual(
            estado_financiero_movimiento(movimiento),
            ESTADO_PARCIAL,
        )

    def test_retencion_cancela_solo_lo_aplicado(self):
        """
        Una retención forma parte del importe aplicado cuando
        fue incorporada a AplicacionPago.

        La naturaleza del medio de pago no modifica el cálculo
        central del saldo.
        """

        movimiento = self.crear_movimiento(
            "100000.00",
            "15000.00",
        )

        self.assertEqual(
            saldo_pendiente_movimiento(movimiento),
            Decimal("85000.00"),
        )

        self.assertEqual(
            estado_financiero_movimiento(movimiento),
            ESTADO_PARCIAL,
        )

    def test_interes_mora_no_incrementa_importe_aplicado(self):
        """
        Un débito bancario puede ser mayor al total documental
        por intereses de mora.

        Solamente el importe registrado en AplicacionPago
        cancela la obligación del Movimiento.
        """

        importe_debitado = Decimal("103500.00")
        interes_mora = Decimal("3500.00")

        importe_aplicado = (
            importe_debitado -
            interes_mora
        )

        movimiento = self.crear_movimiento(
            "100000.00",
            str(importe_aplicado),
        )

        self.assertEqual(
            importe_aplicado,
            Decimal("100000.00"),
        )

        self.assertEqual(
            saldo_pendiente_movimiento(movimiento),
            Decimal("0.00"),
        )

        self.assertEqual(
            estado_financiero_movimiento(movimiento),
            ESTADO_PAGADO,
        )

    def test_saldo_nunca_es_negativo(self):
        """
        Una eventual sobreaplicación no debe producir
        un saldo pendiente negativo.
        """

        movimiento = self.crear_movimiento(
            "100000.00",
            "105000.00",
        )

        self.assertEqual(
            saldo_pendiente_movimiento(movimiento),
            Decimal("0.00"),
        )

        self.assertEqual(
            estado_financiero_movimiento(movimiento),
            ESTADO_PAGADO,
        )