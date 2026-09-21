"""
Servicios de seguridad global de la instalación de OrdenaClick.

Este módulo administra operaciones sensibles que pertenecen a la
instalación y no a una Empresa concreta.

Los secretos gestionados aquí nunca deben devolverse al frontend
ni registrarse en logs.
"""

import secrets

from usuarios.services.configuracion_instalacion import (
    guardar_valor_privado,
    obtener_valor_privado,
)

from django.conf import settings

NOMBRE_CONFIGURACION_SECRET_KEY = "ordenaclick_secret_key"

LONGITUD_SECRET_KEY_BYTES = 64

def secret_key_tiene_reinicio_pendiente():
    """
    Indica si la SECRET_KEY privada persistida difiere de la clave
    utilizada actualmente por el proceso Django.

    Una diferencia significa que ya se preparó una nueva clave y que
    OrdenaClick debe reiniciarse antes de permitir otro reemplazo.
    """
    clave_privada = obtener_valor_privado(
        NOMBRE_CONFIGURACION_SECRET_KEY,
        "",
    )

    if not clave_privada:
        return False

    return not secrets.compare_digest(
        clave_privada,
        settings.SECRET_KEY,
    )


def generar_secret_key():
    """
    Genera una SECRET_KEY criptográficamente aleatoria.

    La clave se genera exclusivamente en el servidor y nunca debe
    enviarse al navegador ni mostrarse al usuario.
    """
    return secrets.token_urlsafe(
        LONGITUD_SECRET_KEY_BYTES
    )


def reemplazar_secret_key_privada():
    """
    Genera y almacena una nueva SECRET_KEY privada.

    La operación únicamente modifica la configuración persistente.
    La SECRET_KEY efectiva del proceso Django actual no cambia hasta
    que la aplicación sea reiniciada.

    No permite preparar una segunda clave mientras exista un reinicio
    pendiente.

    Devuelve únicamente True para confirmar que la operación terminó;
    nunca devuelve el secreto generado.
    """
    if secret_key_tiene_reinicio_pendiente():
        raise RuntimeError(
            "Ya existe una SECRET_KEY pendiente de reinicio."
        )

    nueva_clave = generar_secret_key()

    guardar_valor_privado(
        NOMBRE_CONFIGURACION_SECRET_KEY,
        nueva_clave,
    )

    return True