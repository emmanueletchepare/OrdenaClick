from datetime import date
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
    VENCIMIENTO_FUTURO,
    VENCIMIENTO_HOY,
    VENCIMIENTO_PAGADO,
    VENCIMIENTO_SIN_FECHA,
    VENCIMIENTO_VENCIDO,
    estado_vencimiento_movimiento,
    resumen_financiero_movimiento,
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

class ServicioVencimientosMovimientoTests(SimpleTestCase):
    """
    Prueba la interpretación temporal de las obligaciones
    financieras asociadas a un Movimiento.
    """

    def crear_movimiento(
        self,
        total,
        total_aplicado,
        fecha_vencimiento,
        modalidad_pago="Manual",
        cuenta_debito=None,
    ):
        """
        Crea un Movimiento controlado con la información
        necesaria para probar vencimientos y resúmenes.
        """

        aplicaciones_pago = MagicMock()

        aplicaciones_pago.aggregate.return_value = {
            "total": Decimal(total_aplicado)
        }

        return SimpleNamespace(
            total=Decimal(total),
            fecha_vencimiento=fecha_vencimiento,
            modalidad_pago=modalidad_pago,
            cuenta_debito=cuenta_debito,
            aplicaciones_pago=aplicaciones_pago,
        )

    def test_movimiento_pendiente_sin_fecha(self):
        """
        Una obligación con saldo pero sin vencimiento
        se identifica como SinFecha.
        """

        movimiento = self.crear_movimiento(
            "100000.00",
            "0.00",
            None,
        )

        estado = estado_vencimiento_movimiento(
            movimiento,
            date(2026, 9, 10),
        )

        self.assertEqual(
            estado,
            VENCIMIENTO_SIN_FECHA,
        )

    def test_movimiento_con_vencimiento_futuro(self):
        """
        Una obligación pendiente posterior a la fecha
        de referencia se considera futura.
        """

        movimiento = self.crear_movimiento(
            "100000.00",
            "0.00",
            date(2026, 9, 15),
        )

        estado = estado_vencimiento_movimiento(
            movimiento,
            date(2026, 9, 10),
        )

        self.assertEqual(
            estado,
            VENCIMIENTO_FUTURO,
        )

    def test_movimiento_que_vence_hoy(self):
        """
        Una obligación pendiente cuya fecha coincide
        con la referencia se identifica como Hoy.
        """

        movimiento = self.crear_movimiento(
            "100000.00",
            "0.00",
            date(2026, 9, 10),
        )

        estado = estado_vencimiento_movimiento(
            movimiento,
            date(2026, 9, 10),
        )

        self.assertEqual(
            estado,
            VENCIMIENTO_HOY,
        )

    def test_movimiento_vencido_permanece_visible(self):
        """
        Una obligación vencida que todavía posee saldo
        conserva su condición de Vencida.
        """

        movimiento = self.crear_movimiento(
            "100000.00",
            "40000.00",
            date(2026, 9, 5),
        )

        estado = estado_vencimiento_movimiento(
            movimiento,
            date(2026, 9, 10),
        )

        self.assertEqual(
            estado,
            VENCIMIENTO_VENCIDO,
        )

        resumen = resumen_financiero_movimiento(
            movimiento,
            date(2026, 9, 10),
        )

        self.assertEqual(
            resumen["saldo_pendiente"],
            Decimal("60000.00"),
        )

        self.assertEqual(
            resumen["estado_financiero"],
            ESTADO_PARCIAL,
        )

    def test_movimiento_pagado_no_es_vencimiento_pendiente(self):
        """
        Una obligación totalmente cancelada deja de ser
        un vencimiento pendiente aunque su fecha sea anterior.
        """

        movimiento = self.crear_movimiento(
            "100000.00",
            "100000.00",
            date(2026, 9, 5),
        )

        estado = estado_vencimiento_movimiento(
            movimiento,
            date(2026, 9, 10),
        )

        self.assertEqual(
            estado,
            VENCIMIENTO_PAGADO,
        )

    def test_resumen_conserva_prevision_de_debito(self):
        """
        El resumen financiero expone la modalidad prevista
        y la cuenta bancaria sin convertirlas en un Pago.
        """

        cuenta = SimpleNamespace(
            id=25,
        )

        movimiento = self.crear_movimiento(
            "100000.00",
            "0.00",
            date(2026, 9, 12),
            modalidad_pago="DebitoAutomatico",
            cuenta_debito=cuenta,
        )

        resumen = resumen_financiero_movimiento(
            movimiento,
            date(2026, 9, 10),
        )

        self.assertEqual(
            resumen["saldo_pendiente"],
            Decimal("100000.00"),
        )

        self.assertEqual(
            resumen["modalidad_pago"],
            "DebitoAutomatico",
        )

        self.assertIs(
            resumen["cuenta_debito"],
            cuenta,
        )

        self.assertEqual(
            resumen["estado_vencimiento"],
            VENCIMIENTO_FUTURO,
        )