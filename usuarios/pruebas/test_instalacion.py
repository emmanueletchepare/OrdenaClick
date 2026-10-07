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
