from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
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
)

from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from usuarios.models import Empresa, Ejercicio, Movimiento

from usuarios.services.seguridad import (
    empresas_autorizadas,
    obtener_empresa_autorizada,
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