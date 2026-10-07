import os
import re

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render

from usuarios.services.arca import (
    AMBIENTE_HOMOLOGACION,
    AMBIENTE_PRODUCCION,
    guardar_configuracion_general_arca,
    guardar_credenciales_arca,
    obtener_ambiente_operativo_arca,
    obtener_configuracion_arca,
    obtener_cuit_representada_arca,
    validar_credenciales_arca,
)
from usuarios.services.configuracion_instalacion import obtener_valor_privado
from usuarios.services.seguridad_instalacion import (
    reemplazar_secret_key_privada,
    secret_key_tiene_reinicio_pendiente,
)


def _credenciales_arca_configuradas(
    ambiente,
):
    """
    Indica si un ambiente ARCA tiene certificado y clave disponibles.

    No expone ni lee el contenido de las credenciales.
    """
    try:
        configuracion = obtener_configuracion_arca(
            ambiente
        )

        validar_credenciales_arca(
            configuracion
        )

    except RuntimeError:
        return False

    return True

@login_required
def panel_desarrollador(request):
    """
    Muestra la administración técnica de la instalación de OrdenaClick.

    El acceso está reservado exclusivamente a superusuarios. Informa el
    estado de secretos y credenciales sin exponer su contenido.
    """
    if not request.user.is_superuser:
        raise PermissionDenied(
            "No tiene permisos para acceder al Perfil Desarrollador."
        )

    secret_key_entorno = bool(
        os.environ.get(
            "ORDENACLICK_SECRET_KEY",
            "",
        ).strip()
    )

    secret_key_privada = bool(
        obtener_valor_privado(
            "ordenaclick_secret_key",
            "",
        )
    )

    secret_key_reinicio_pendiente = False

    if not secret_key_entorno and secret_key_privada:
        secret_key_reinicio_pendiente = (
            secret_key_tiene_reinicio_pendiente()
        )

    if secret_key_entorno:
        secret_key_origen = "Variable de entorno"
    elif secret_key_privada:
        secret_key_origen = "Configuración privada"
    else:
        secret_key_origen = "No configurada"

    try:
        arca_ambiente = (
            obtener_ambiente_operativo_arca()
        )
    except RuntimeError:
        arca_ambiente = AMBIENTE_HOMOLOGACION

    try:
        arca_cuit_representada = (
            str(
                obtener_cuit_representada_arca()
            )
        )
    except RuntimeError:
        arca_cuit_representada = ""

    return render(
        request,
        "usuarios/perfiles/desarrollador/panel.html",
        {
            "secret_key_configurada": (
                secret_key_entorno
                or secret_key_privada
            ),
            "secret_key_origen": secret_key_origen,
            "secret_key_administrada_externamente":
                secret_key_entorno,
            "secret_key_permite_configuracion_privada": (
                not secret_key_entorno
                and not secret_key_reinicio_pendiente
            ),
            "secret_key_reinicio_pendiente":
                secret_key_reinicio_pendiente,

            "arca_ambiente":
                arca_ambiente,

            "arca_cuit_representada":
                arca_cuit_representada,

            "arca_homologacion_configurada":
                _credenciales_arca_configuradas(
                    AMBIENTE_HOMOLOGACION
                ),

            "arca_produccion_configurada":
                _credenciales_arca_configuradas(
                    AMBIENTE_PRODUCCION
                ),
        },
    )

@login_required
def reemplazar_secret_key_desarrollador(request):
    """
    Prepara una nueva SECRET_KEY privada para la instalación.

    La operación está reservada a superusuarios, requiere POST y no
    devuelve nunca el secreto generado al navegador.

    La nueva clave queda almacenada para el próximo arranque de Django;
    el proceso actual continúa utilizando su SECRET_KEY hasta reiniciarse.
    """
    if not request.user.is_superuser:
        raise PermissionDenied(
            "No tiene permisos para modificar "
            "la configuración de seguridad."
        )

    if request.method != "POST":
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "Método no permitido."
                ),
            },
            status=405,
        )

    secret_key_entorno = bool(
        os.environ.get(
            "ORDENACLICK_SECRET_KEY",
            "",
        ).strip()
    )

    if secret_key_entorno:
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "La SECRET_KEY está administrada mediante "
                    "una variable de entorno y no puede "
                    "reemplazarse desde OrdenaClick."
                ),
            },
            status=409,
        )

    try:
        reemplazar_secret_key_privada()

    except RuntimeError as error:
        if str(error) == (
            "Ya existe una SECRET_KEY pendiente de reinicio."
        ):
            return JsonResponse(
                {
                    "ok": False,
                    "error": (
                        "Ya existe una nueva SECRET_KEY preparada. "
                        "Reinicie OrdenaClick antes de intentar "
                        "otro reemplazo."
                    ),
                    "requiere_reinicio": True,
                },
                status=409,
            )

        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "No se pudo preparar la nueva SECRET_KEY."
                ),
            },
            status=500,
        )

    except (OSError, ValueError):
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "No se pudo preparar la nueva SECRET_KEY."
                ),
            },
            status=500,
        )

    return JsonResponse(
        {
            "ok": True,
            "mensaje": (
                "La nueva SECRET_KEY quedó preparada. "
                "Reinicie OrdenaClick para aplicarla."
            ),
            "requiere_reinicio": True,
        }
    )

@login_required
def guardar_configuracion_arca_desarrollador(request):
    """
    Administra la configuración global de ARCA desde Perfil Desarrollador.

    Permite seleccionar el ambiente operativo y CUIT representado, además
    de reemplazar opcionalmente certificado y clave de cada ambiente.
    Las credenciales nunca son devueltas al navegador.
    """
    if not request.user.is_superuser:
        raise PermissionDenied(
            "No tiene permisos para modificar "
            "la configuración de ARCA."
        )

    if request.method != "POST":
        return JsonResponse(
            {
                "ok": False,
                "error": "Método no permitido.",
            },
            status=405,
        )

    ambiente = (
        request.POST.get("arca_ambiente")
        or ""
    ).strip()

    cuit_representada = re.sub(
        r"\D",
        "",
        request.POST.get(
            "arca_cuit_representada"
        ) or "",
    )

    certificado_homologacion = (
        request.FILES.get(
            "arca_homologacion_certificado"
        )
    )

    clave_homologacion = (
        request.FILES.get(
            "arca_homologacion_clave"
        )
    )

    certificado_produccion = (
        request.FILES.get(
            "arca_produccion_certificado"
        )
    )

    clave_produccion = (
        request.FILES.get(
            "arca_produccion_clave"
        )
    )

    if bool(certificado_homologacion) != bool(
        clave_homologacion
    ):
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "Para actualizar Homologación debe seleccionar "
                    "el certificado y su clave privada."
                ),
            },
            status=400,
        )

    if bool(certificado_produccion) != bool(
        clave_produccion
    ):
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "Para actualizar Producción debe seleccionar "
                    "el certificado y su clave privada."
                ),
            },
            status=400,
        )

    try:
        if certificado_homologacion:
            guardar_credenciales_arca(
                AMBIENTE_HOMOLOGACION,
                certificado_homologacion.read(),
                clave_homologacion.read(),
            )

        if certificado_produccion:
            guardar_credenciales_arca(
                AMBIENTE_PRODUCCION,
                certificado_produccion.read(),
                clave_produccion.read(),
            )

        guardar_configuracion_general_arca(
            ambiente,
            cuit_representada,
        )

    except ValueError as error:
        return JsonResponse(
            {
                "ok": False,
                "error": str(error),
            },
            status=400,
        )

    except RuntimeError:
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "No se pudo guardar la configuración "
                    "privada de ARCA."
                ),
            },
            status=500,
        )

    return JsonResponse(
        {
            "ok": True,
            "mensaje": (
                "La configuración de ARCA se guardó correctamente."
            ),
        }
    )
