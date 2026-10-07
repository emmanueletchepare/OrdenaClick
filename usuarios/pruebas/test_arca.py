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
