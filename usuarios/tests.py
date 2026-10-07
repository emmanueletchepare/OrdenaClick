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


_PRUEBAS_ARCA_EXTRAIDAS = {
    "ServicioArcaTests",
}


_PRUEBAS_CLIENTES_EXTRAIDAS = {
    "ClienteABMTests",
}


_PRUEBAS_INSTALACION_EXTRAIDAS = {
    "SeguridadInstalacionDesarrolladorTests",
    "SeguridadInstalacionServicioTests",
}


_PRUEBAS_SEGURIDAD_EMPRESA_EXTRAIDAS = {
    "SeguridadEmpresaTests",
    "JerarquiasSeguridadTests",
}


_PRUEBAS_ALERTAS_VENCIMIENTOS_EXTRAIDAS = {
    "ProximosVencimientosViewTests",
    "AlertasMovimientoTests",
}


def __getattr__(name):
    if name in _PRUEBAS_SEGURIDAD_EMPRESA_EXTRAIDAS:
        from usuarios.pruebas import test_seguridad_empresa

        return getattr(test_seguridad_empresa, name)

    if name in _PRUEBAS_ALERTAS_VENCIMIENTOS_EXTRAIDAS:
        from usuarios.pruebas import test_alertas_vencimientos

        return getattr(test_alertas_vencimientos, name)

    if name in _PRUEBAS_INSTALACION_EXTRAIDAS:
        from usuarios.pruebas import test_instalacion

        return getattr(test_instalacion, name)

    if name in _PRUEBAS_CLIENTES_EXTRAIDAS:
        from usuarios.pruebas import test_clientes

        return getattr(test_clientes, name)

    if name in _PRUEBAS_ARCA_EXTRAIDAS:
        from usuarios.pruebas import test_arca

        return getattr(test_arca, name)

    if name in _PRUEBAS_CAJA_EXTRAIDAS:
        from usuarios.pruebas import test_caja

        return getattr(test_caja, name)

    if name in _PRUEBAS_FINANCIERAS_EXTRAIDAS:
        from usuarios.pruebas import test_financiero

        return getattr(test_financiero, name)

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )
