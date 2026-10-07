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
