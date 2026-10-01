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

class ValidarPagoMovimientoTests(TestCase):
    """
    Prueba la validación común de Pagos manuales
    antes de su persistencia financiera.

    Estos tests verifican que la validación:

    - normalice correctamente un Pago válido;
    - rechace importes inexistentes o negativos;
    - no permita utilizar entidades de otra Empresa.

    La persistencia de Pago y AplicacionPago se prueba
    separadamente del proceso de validación.
    """

    def setUp(self):
        """
        Crea dos Empresas para verificar también que
        la validación respete el aislamiento empresarial.
        """

        self.usuario = User.objects.create_user(
            username="usuario_pago_validacion",
            password="clave-prueba-123",
        )

        self.empresa = Empresa.objects.create(
            razon_social="Empresa Pago Validación",
            propietario=self.usuario,
        )

        self.otra_empresa = Empresa.objects.create(
            razon_social="Otra Empresa Pago Validación",
            propietario=self.usuario,
        )


    def test_pago_solo_efectivo_es_valido(self):
        """
        Un Pago compuesto únicamente por efectivo debe
        normalizar fecha e importe correctamente.
        """

        pago = validar_pago_movimiento(
            empresa=self.empresa,
            pago_datos={
                "fecha": "2026-09-14",
                "importe_efectivo": "25000.50",
                "operaciones_bancarias": [],
                "tarjetas": [],
                "cheques": [],
                "retenciones": [],
            },
        )

        self.assertEqual(
            pago["fecha"],
            date(2026, 9, 14),
        )

        self.assertEqual(
            pago["importe_efectivo"],
            Decimal("25000.50"),
        )

        self.assertEqual(
            pago["importe_pago"],
            Decimal("25000.50"),
        )

        self.assertEqual(
            pago["operaciones_bancarias"],
            [],
        )

        self.assertEqual(
            pago["tarjetas"],
            [],
        )

        self.assertEqual(
            pago["cheques"],
            [],
        )

        self.assertEqual(
            pago["retenciones"],
            [],
        )


    def test_pago_sin_importe_es_rechazado(self):
        """
        Un Pago sin ningún medio con importe positivo
        no representa un hecho financiero válido.
        """

        with self.assertRaisesMessage(
            ValueError,
            "El importe total del Pago debe ser mayor a cero.",
        ):

            validar_pago_movimiento(
                empresa=self.empresa,
                pago_datos={
                    "fecha": "2026-09-14",
                    "importe_efectivo": "0.00",
                    "operaciones_bancarias": [],
                    "tarjetas": [],
                    "cheques": [],
                    "retenciones": [],
                },
            )


    def test_pago_con_efectivo_negativo_es_rechazado(self):
        """
        El efectivo nunca puede utilizarse para reducir
        artificialmente el importe de otros medios de Pago.
        """

        with self.assertRaisesMessage(
            ValueError,
            "El efectivo no puede ser negativo.",
        ):

            validar_pago_movimiento(
                empresa=self.empresa,
                pago_datos={
                    "fecha": "2026-09-14",
                    "importe_efectivo": "-100.00",
                    "operaciones_bancarias": [],
                    "tarjetas": [],
                    "cheques": [],
                    "retenciones": [],
                },
            )


    def test_pago_con_fecha_invalida_es_rechazado(self):
        """
        La fecha del Pago debe respetar el formato
        documental esperado por el backend.
        """

        with self.assertRaisesMessage(
            ValueError,
            "La fecha del Pago no es válida.",
        ):

            validar_pago_movimiento(
                empresa=self.empresa,
                pago_datos={
                    "fecha": "14/09/2026",
                    "importe_efectivo": "1000.00",
                    "operaciones_bancarias": [],
                    "tarjetas": [],
                    "cheques": [],
                    "retenciones": [],
                },
            )


    def test_pago_sin_fecha_es_rechazado(self):
        """
        Todo Pago debe identificar la fecha real
        en la que ocurrió el hecho financiero.
        """

        with self.assertRaisesMessage(
            ValueError,
            "El Pago debe tener una fecha.",
        ):

            validar_pago_movimiento(
                empresa=self.empresa,
                pago_datos={
                    "fecha": "",
                    "importe_efectivo": "1000.00",
                    "operaciones_bancarias": [],
                    "tarjetas": [],
                    "cheques": [],
                    "retenciones": [],
                },
            )


    def test_pago_con_formato_general_invalido_es_rechazado(self):
        """
        El servicio no debe aceptar estructuras que no
        representen un diccionario de datos de Pago.
        """

        with self.assertRaisesMessage(
            ValueError,
            "El Pago tiene un formato inválido.",
        ):

            validar_pago_movimiento(
                empresa=self.empresa,
                pago_datos=[],
            )

class RegistrarPagoManualMovimientoTests(TestCase):
    """
    Prueba el endpoint que registra Pagos manuales
    sobre un Movimiento existente.

    Verifica autorización empresarial, persistencia financiera,
    control de saldo y separación respecto del circuito de
    Débito Automático.
    """

    def setUp(self):
        """
        Crea dos usuarios, sus Empresas y el Movimiento manual
        utilizado como base para las pruebas del endpoint.
        """

        self.usuario = User.objects.create_user(
            username="usuario_pago_manual",
            password="clave-prueba-123",
        )

        self.otro_usuario = User.objects.create_user(
            username="otro_usuario_pago_manual",
            password="clave-prueba-123",
        )

        self.empresa = Empresa.objects.create(
            razon_social="Empresa Pago Manual",
            propietario=self.usuario,
        )

        self.empresa_ajena = Empresa.objects.create(
            razon_social="Empresa Ajena Pago Manual",
            propietario=self.otro_usuario,
        )

        self.ejercicio = Ejercicio.objects.create(
            empresa=self.empresa,
            numero=2026,
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 12, 31),
        )

        self.movimiento = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date(2026, 9, 14),
            fecha_vencimiento=date(2026, 9, 30),
            modalidad_pago="Manual",
            total=Decimal("100000.00"),
            importe=Decimal("100000.00"),
            estado="Pendiente",
        )

        self.client.force_login(
            self.usuario
        )

    def datos_pago(
        self,
        importe="40000.00",
    ):
        """
        Construye el payload mínimo de un Pago manual
        compuesto exclusivamente por efectivo.
        """

        import json

        return {
            "empresa": str(self.empresa.id),
            "movimiento": str(self.movimiento.id),
            "pagos": json.dumps(
                [
                    {
                        "fecha": "2026-09-14",
                        "importe_efectivo": importe,
                        "operaciones_bancarias": [],
                        "tarjetas": [],
                        "cheques": [],
                        "retenciones": [],
                    }
                ]
            ),
        }

    def test_registra_pago_manual_parcial(self):
        """
        Un Pago manual válido debe crear Pago y AplicacionPago,
        reducir el saldo y dejar el Movimiento en Parcial.
        """

        respuesta = self.client.post(
            reverse(
                "registrar_pago_manual_movimiento"
            ),
            self.datos_pago(
                "40000.00"
            ),
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
            Pago.objects.filter(
                empresa=self.empresa
            ).count(),
            1,
        )

        aplicacion = AplicacionPago.objects.get(
            movimiento=self.movimiento
        )

        self.assertEqual(
            aplicacion.importe,
            Decimal("40000.00"),
        )

        self.movimiento.refresh_from_db()

        self.assertEqual(
            self.movimiento.estado,
            "Parcial",
        )

        self.assertEqual(
            saldo_pendiente_movimiento(
                self.movimiento
            ),
            Decimal("60000.00"),
        )

    def test_rechaza_sobrepago_sin_crear_registros(self):
        """
        Un Pago que supera el saldo pendiente debe rechazarse
        antes de crear cualquier hecho financiero.
        """

        respuesta = self.client.post(
            reverse(
                "registrar_pago_manual_movimiento"
            ),
            self.datos_pago(
                "100000.01"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            400,
        )

        self.assertFalse(
            respuesta.json()["ok"]
        )

        self.assertEqual(
            Pago.objects.count(),
            0,
        )

        self.assertEqual(
            AplicacionPago.objects.count(),
            0,
        )

        self.movimiento.refresh_from_db()

        self.assertEqual(
            self.movimiento.estado,
            "Pendiente",
        )

    def test_rechaza_empresa_ajena(self):
        """
        El endpoint no debe permitir operar sobre una Empresa
        perteneciente a otro usuario aunque conozca su ID.
        """

        datos = self.datos_pago(
            "10000.00"
        )

        datos["empresa"] = str(
            self.empresa_ajena.id
        )

        respuesta = self.client.post(
            reverse(
                "registrar_pago_manual_movimiento"
            ),
            datos,
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self.assertEqual(
            Pago.objects.count(),
            0,
        )

        self.assertEqual(
            AplicacionPago.objects.count(),
            0,
        )

    def test_rechaza_movimiento_de_otra_empresa(self):
        """
        Un usuario autorizado para una Empresa no puede utilizar
        esa autorización para pagar un Movimiento de otra Empresa.
        """

        ejercicio_ajeno = Ejercicio.objects.create(
            empresa=self.empresa_ajena,
            numero=2026,
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 12, 31),
        )

        movimiento_ajeno = Movimiento.objects.create(
            empresa=self.empresa_ajena,
            ejercicio=ejercicio_ajeno,
            fecha_registro=date(2026, 9, 14),
            modalidad_pago="Manual",
            total=Decimal("50000.00"),
            importe=Decimal("50000.00"),
            estado="Pendiente",
        )

        datos = self.datos_pago(
            "10000.00"
        )

        datos["movimiento"] = str(
            movimiento_ajeno.id
        )

        respuesta = self.client.post(
            reverse(
                "registrar_pago_manual_movimiento"
            ),
            datos,
        )

        self.assertEqual(
            respuesta.status_code,
            404,
        )

        self.assertEqual(
            Pago.objects.count(),
            0,
        )

        self.assertEqual(
            AplicacionPago.objects.count(),
            0,
        )

    def test_rechaza_get(self):
        """
        El registro financiero sólo puede ejecutarse mediante POST.
        """

        respuesta = self.client.get(
            reverse(
                "registrar_pago_manual_movimiento"
            )
        )

        self.assertEqual(
            respuesta.status_code,
            405,
        )

        self.assertEqual(
            Pago.objects.count(),
            0,
        )

        self.assertEqual(
            AplicacionPago.objects.count(),
            0,
        )

    def test_rechaza_movimiento_sin_saldo(self):
        """
        Un Movimiento totalmente pagado no debe admitir
        nuevas aplicaciones.
        """

        pago_existente = Pago.objects.create(
            empresa=self.empresa,
            fecha=date(2026, 9, 14),
            importe_efectivo=Decimal("100000.00"),
        )

        AplicacionPago.objects.create(
            pago=pago_existente,
            movimiento=self.movimiento,
            importe=Decimal("100000.00"),
        )

        self.movimiento.estado = "Pagado"

        self.movimiento.save(
            update_fields=[
                "estado"
            ]
        )

        respuesta = self.client.post(
            reverse(
                "registrar_pago_manual_movimiento"
            ),
            self.datos_pago(
                "1000.00"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            400,
        )

        self.assertFalse(
            respuesta.json()["ok"]
        )

        self.assertEqual(
            Pago.objects.count(),
            1,
        )

        self.assertEqual(
            AplicacionPago.objects.count(),
            1,
        )

    def test_debito_automatico_no_utiliza_endpoint_manual(self):
        """
        Un Movimiento previsto como Débito Automático debe usar
        exclusivamente su endpoint financiero específico.
        """

        self.movimiento.modalidad_pago = (
            "DebitoAutomatico"
        )

        self.movimiento.save(
            update_fields=[
                "modalidad_pago"
            ]
        )

        respuesta = self.client.post(
            reverse(
                "registrar_pago_manual_movimiento"
            ),
            self.datos_pago(
                "10000.00"
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            400,
        )

        self.assertFalse(
            respuesta.json()["ok"]
        )

        self.assertEqual(
            Pago.objects.count(),
            0,
        )

        self.assertEqual(
            AplicacionPago.objects.count(),
            0,
        )

class EliminarPagoMovimientoTests(TestCase):
    """
    Prueba la eliminación controlada de Pagos aplicados
    a un Movimiento.

    Verifica que la operación restaure correctamente el
    saldo y el estado financiero, respete el aislamiento
    entre Empresas y sólo pueda ejecutarse mediante POST.
    """

    def setUp(self):
        """
        Crea usuarios, Empresas y el Movimiento utilizado
        como base para las pruebas de eliminación de Pago.
        """

        self.usuario = User.objects.create_user(
            username="usuario_eliminar_pago",
            password="clave-prueba-123",
        )

        self.otro_usuario = User.objects.create_user(
            username="otro_usuario_eliminar_pago",
            password="clave-prueba-123",
        )

        self.empresa = Empresa.objects.create(
            razon_social="Empresa Eliminar Pago",
            propietario=self.usuario,
        )

        self.empresa_ajena = Empresa.objects.create(
            razon_social="Empresa Ajena Eliminar Pago",
            propietario=self.otro_usuario,
        )

        self.ejercicio = Ejercicio.objects.create(
            empresa=self.empresa,
            numero=2026,
            fecha_inicio=date(2026, 1, 1),
            fecha_cierre=date(2026, 12, 31),
        )

        self.movimiento = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date(2026, 9, 14),
            fecha_vencimiento=date(2026, 9, 30),
            modalidad_pago="Manual",
            total=Decimal("100000.00"),
            importe=Decimal("100000.00"),
            estado="Pendiente",
        )

        self.client.force_login(
            self.usuario
        )


    def crear_pago(
        self,
        importe,
    ):
        """
        Crea un Pago en efectivo y su AplicacionPago
        sobre el Movimiento principal de la prueba.
        """

        pago = Pago.objects.create(
            empresa=self.empresa,
            fecha=date(2026, 9, 14),
            importe_efectivo=Decimal(importe),
        )

        AplicacionPago.objects.create(
            pago=pago,
            movimiento=self.movimiento,
            importe=Decimal(importe),
        )

        return pago


    def datos_eliminacion(
        self,
        pago,
    ):
        """
        Construye el payload mínimo requerido por el
        endpoint de eliminación de Pago.
        """

        return {
            "empresa": str(
                self.empresa.id
            ),
            "movimiento": str(
                self.movimiento.id
            ),
            "pago": str(
                pago.id
            ),
        }


    def test_elimina_unico_pago_y_restaura_saldo(self):
        """
        Eliminar el único Pago aplicado debe borrar Pago y
        AplicacionPago, restaurar todo el saldo y dejar el
        Movimiento en estado Pendiente.
        """

        pago = self.crear_pago(
            "100000.00"
        )

        self.movimiento.estado = "Pagado"

        self.movimiento.save(
            update_fields=[
                "estado"
            ]
        )

        respuesta = self.client.post(
            reverse(
                "eliminar_pago_movimiento"
            ),
            self.datos_eliminacion(
                pago
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        datos = respuesta.json()

        self.assertTrue(
            datos["ok"]
        )

        self.assertFalse(
            Pago.objects.filter(
                id=pago.id
            ).exists()
        )

        self.assertFalse(
            AplicacionPago.objects.filter(
                pago_id=pago.id
            ).exists()
        )

        self.movimiento.refresh_from_db()

        self.assertEqual(
            self.movimiento.estado,
            "Pendiente",
        )

        self.assertEqual(
            saldo_pendiente_movimiento(
                self.movimiento
            ),
            Decimal("100000.00"),
        )

        self.assertEqual(
            datos["saldo_pendiente"],
            "100000.00",
        )


    def test_elimina_un_pago_y_movimiento_queda_parcial(self):
        """
        Si existen varios Pagos, eliminar sólo uno debe conservar
        los restantes y recalcular el Movimiento como Parcial.
        """

        pago_conservado = self.crear_pago(
            "40000.00"
        )

        pago_eliminado = self.crear_pago(
            "60000.00"
        )

        self.movimiento.estado = "Pagado"

        self.movimiento.save(
            update_fields=[
                "estado"
            ]
        )

        respuesta = self.client.post(
            reverse(
                "eliminar_pago_movimiento"
            ),
            self.datos_eliminacion(
                pago_eliminado
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            200,
        )

        self.assertTrue(
            Pago.objects.filter(
                id=pago_conservado.id
            ).exists()
        )

        self.assertFalse(
            Pago.objects.filter(
                id=pago_eliminado.id
            ).exists()
        )

        self.assertEqual(
            AplicacionPago.objects.filter(
                movimiento=self.movimiento
            ).count(),
            1,
        )

        self.movimiento.refresh_from_db()

        self.assertEqual(
            self.movimiento.estado,
            "Parcial",
        )

        self.assertEqual(
            saldo_pendiente_movimiento(
                self.movimiento
            ),
            Decimal("60000.00"),
        )


    def test_rechaza_get(self):
        """
        La eliminación de un hecho financiero sólo puede
        ejecutarse mediante POST.
        """

        pago = self.crear_pago(
            "40000.00"
        )

        respuesta = self.client.get(
            reverse(
                "eliminar_pago_movimiento"
            ),
            self.datos_eliminacion(
                pago
            ),
        )

        self.assertEqual(
            respuesta.status_code,
            405,
        )

        self.assertTrue(
            Pago.objects.filter(
                id=pago.id
            ).exists()
        )

        self.assertTrue(
            AplicacionPago.objects.filter(
                pago=pago
            ).exists()
        )


    def test_rechaza_empresa_ajena(self):
        """
        Conocer los identificadores de Empresa, Movimiento y Pago
        no permite operar utilizando una Empresa no autorizada.
        """

        pago = self.crear_pago(
            "40000.00"
        )

        datos = self.datos_eliminacion(
            pago
        )

        datos["empresa"] = str(
            self.empresa_ajena.id
        )

        respuesta = self.client.post(
            reverse(
                "eliminar_pago_movimiento"
            ),
            datos,
        )

        self.assertEqual(
            respuesta.status_code,
            403,
        )

        self.assertTrue(
            Pago.objects.filter(
                id=pago.id
            ).exists()
        )

        self.assertTrue(
            AplicacionPago.objects.filter(
                pago=pago
            ).exists()
        )


    def test_rechaza_pago_de_otro_movimiento(self):
        """
        Un Pago válido de la Empresa no puede eliminarse indicando
        un Movimiento diferente al que realmente está aplicado.
        """

        pago = self.crear_pago(
            "40000.00"
        )

        otro_movimiento = Movimiento.objects.create(
            empresa=self.empresa,
            ejercicio=self.ejercicio,
            fecha_registro=date(2026, 9, 14),
            fecha_vencimiento=date(2026, 10, 15),
            modalidad_pago="Manual",
            total=Decimal("50000.00"),
            importe=Decimal("50000.00"),
            estado="Pendiente",
        )

        datos = self.datos_eliminacion(
            pago
        )

        datos["movimiento"] = str(
            otro_movimiento.id
        )

        respuesta = self.client.post(
            reverse(
                "eliminar_pago_movimiento"
            ),
            datos,
        )

        self.assertEqual(
            respuesta.status_code,
            400,
        )

        self.assertTrue(
            Pago.objects.filter(
                id=pago.id
            ).exists()
        )

        self.assertTrue(
            AplicacionPago.objects.filter(
                pago=pago
            ).exists()
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
        "usuarios.views.reemplazar_secret_key_privada"
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
        "usuarios.views.reemplazar_secret_key_privada"
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
        "usuarios.views.reemplazar_secret_key_privada"
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
        "usuarios.views.reemplazar_secret_key_privada"
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
        "usuarios.views.reemplazar_secret_key_privada"
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
        "usuarios.views.reemplazar_secret_key_privada"
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
        "usuarios.views.reemplazar_secret_key_privada"
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
        "usuarios.views.reemplazar_secret_key_privada"
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
        from usuarios.services.financiero import crear_cobranza_validada

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
        from usuarios.services.financiero import crear_cobranza_validada

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
        from usuarios.services.financiero import crear_cobranza_validada

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
        from usuarios.services.financiero import crear_cobranza_validada

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
        from usuarios.services.financiero import crear_cobranza_validada

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
        from usuarios.services.financiero import crear_cobranza_validada

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

        return MovimientoCaja.objects.create(
            empresa=caja.empresa,
            caja=caja,
            fecha=date(2026, 9, 23),
            tipo=tipo,
            moneda=moneda,
            importe=Decimal(importe),
            concepto="Movimiento de prueba",
            creado_por=(
                self.usuario
                if caja.empresa_id == self.empresa.id
                else self.otro_usuario
            ),
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
        from usuarios.services.financiero import saldo_efectivo_caja

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
        from usuarios.services.financiero import saldo_efectivo_caja

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
        from usuarios.services.financiero import saldo_efectivo_caja

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
        from usuarios.services.financiero import saldo_efectivo_caja

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
        from usuarios.services.financiero import (
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
        from usuarios.services.financiero import (
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
        from usuarios.services.financiero import (
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
        from usuarios.services.financiero import (
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
        from usuarios.services.financiero import (
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
        from usuarios.services.financiero import (
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