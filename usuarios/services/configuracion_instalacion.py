"""
Acceso a la configuración privada de la instalación de OrdenaClick.

Este módulo administra únicamente configuración técnica global de la
instalación. No contiene datos pertenecientes a una Empresa.

El directorio privado debe permanecer fuera del repositorio, static y
media. Los secretos nunca deben registrarse en logs ni devolverse al
frontend.
"""

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


NOMBRE_DIRECTORIO_PRIVADO = ".ordenaclick"
NOMBRE_ARCHIVO_CONFIGURACION = "configuracion.json"

PERMISO_DIRECTORIO_PRIVADO = 0o700
PERMISO_ARCHIVO_PRIVADO = 0o600


def obtener_directorio_privado():
    """
    Devuelve el directorio privado de la instalación.

    ORDENACLICK_PRIVATE_DIR permite que producción determine una
    ubicación específica. Si no está definida, se utiliza un directorio
    privado dentro del HOME del usuario que ejecuta OrdenaClick.
    """
    directorio_configurado = os.environ.get(
        "ORDENACLICK_PRIVATE_DIR",
        "",
    ).strip()

    if directorio_configurado:
        return Path(
            directorio_configurado
        ).expanduser().resolve()

    return (
        Path.home()
        / NOMBRE_DIRECTORIO_PRIVADO
    ).resolve()


def obtener_ruta_configuracion():
    """
    Devuelve la ruta del archivo privado de configuración.
    """
    return (
        obtener_directorio_privado()
        / NOMBRE_ARCHIVO_CONFIGURACION
    )


def asegurar_directorio_privado():
    """
    Crea el directorio privado cuando sea necesario e intenta aplicar
    permisos restrictivos compatibles con el sistema operativo.

    La seguridad definitiva también depende de los permisos y de la
    identidad del proceso configurados en el servidor.
    """
    directorio = obtener_directorio_privado()

    try:
        directorio.mkdir(
            parents=True,
            exist_ok=True,
        )

        if os.name != "nt":
            os.chmod(
                directorio,
                PERMISO_DIRECTORIO_PRIVADO,
            )

    except OSError as error:
        raise RuntimeError(
            "No se pudo preparar el directorio privado "
            "de OrdenaClick."
        ) from error

    return directorio


def leer_configuracion_privada():
    """
    Lee la configuración privada de la instalación.

    Si todavía no existe un archivo de configuración, devuelve un
    diccionario vacío. Un archivo inválido genera un error explícito
    para evitar trabajar silenciosamente con configuración corrupta.
    """
    ruta = obtener_ruta_configuracion()

    if not ruta.exists():
        return {}

    if not ruta.is_file():
        raise RuntimeError(
            "La ruta de configuración privada de OrdenaClick "
            "no corresponde a un archivo."
        )

    try:
        with ruta.open(
            "r",
            encoding="utf-8",
        ) as archivo:
            datos = json.load(archivo)

    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            "No se pudo leer la configuración privada "
            "de OrdenaClick."
        ) from error

    if not isinstance(datos, dict):
        raise RuntimeError(
            "La configuración privada de OrdenaClick "
            "tiene un formato inválido."
        )

    return datos


def obtener_valor_privado(
    nombre,
    valor_predeterminado=None,
):
    """
    Obtiene un valor concreto sin exponer el resto de la configuración.
    """
    configuracion = leer_configuracion_privada()

    return configuracion.get(
        nombre,
        valor_predeterminado,
    )


def guardar_configuracion_privada(
    configuracion,
):
    """
    Guarda atómicamente la configuración privada completa.

    El archivo se escribe primero en una ubicación temporal dentro del
    mismo directorio y luego reemplaza al definitivo. En sistemas POSIX
    se aplican permisos 0600 al archivo resultante.
    """
    if not isinstance(
        configuracion,
        dict,
    ):
        raise ValueError(
            "La configuración privada debe ser un diccionario."
        )

    directorio = asegurar_directorio_privado()
    ruta = obtener_ruta_configuracion()

    ruta_temporal = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directorio,
            prefix="configuracion_",
            suffix=".tmp",
            delete=False,
        ) as archivo_temporal:

            json.dump(
                configuracion,
                archivo_temporal,
                ensure_ascii=False,
                indent=4,
            )

            archivo_temporal.flush()

            os.fsync(
                archivo_temporal.fileno()
            )

            ruta_temporal = Path(
                archivo_temporal.name
            )

        if os.name != "nt":
            os.chmod(
                ruta_temporal,
                PERMISO_ARCHIVO_PRIVADO,
            )

        os.replace(
            ruta_temporal,
            ruta,
        )

        if os.name != "nt":
            os.chmod(
                ruta,
                PERMISO_ARCHIVO_PRIVADO,
            )

    except OSError as error:

        if (
            ruta_temporal is not None
            and ruta_temporal.exists()
        ):
            try:
                ruta_temporal.unlink()
            except OSError:
                pass

        raise RuntimeError(
            "No se pudo guardar la configuración privada "
            "de OrdenaClick."
        ) from error


def guardar_valor_privado(
    nombre,
    valor,
):
    """
    Actualiza un único valor conservando el resto de la configuración.

    Esta función no decide qué valores pueden almacenarse. La capa de
    servicio específica de cada secreto debe realizar sus validaciones.
    """
    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError(
            "El nombre de configuración es obligatorio."
        )

    configuracion = leer_configuracion_privada()

    configuracion[
        nombre.strip()
    ] = valor

    guardar_configuracion_privada(
        configuracion
    )