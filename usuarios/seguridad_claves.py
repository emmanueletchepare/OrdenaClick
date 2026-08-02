from cryptography.fernet import (
    Fernet,
    InvalidToken
)

from django.conf import settings


def obtener_fernet():

    clave = getattr(
        settings,
        "GESTION_CLAVES_KEY",
        ""
    )

    if not clave:

        raise RuntimeError(
            "No está configurada la clave "
            "de cifrado de Gestión de claves."
        )

    if isinstance(
        clave,
        str
    ):

        clave = clave.encode(
            "utf-8"
        )

    return Fernet(
        clave
    )


def cifrar_clave(valor):

    if valor is None:

        valor = ""

    valor = str(
        valor
    )

    if not valor:

        return ""

    fernet = obtener_fernet()

    return (
        fernet
        .encrypt(
            valor.encode(
                "utf-8"
            )
        )
        .decode(
            "utf-8"
        )
    )


def descifrar_clave(valor):

    if not valor:

        return ""

    fernet = obtener_fernet()

    try:

        return (
            fernet
            .decrypt(
                valor.encode(
                    "utf-8"
                )
            )
            .decode(
                "utf-8"
            )
        )

    except InvalidToken as error:

        raise ValueError(
            "No fue posible descifrar "
            "la contraseña almacenada."
        ) from error