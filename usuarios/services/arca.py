"""
Integración técnica de OrdenaClick con los Web Services de ARCA.

La identidad utilizada ante ARCA pertenece a la instalación completa de
OrdenaClick y no a una Empresa concreta.

Los certificados, claves privadas y tickets de acceso deben permanecer
fuera del repositorio, static y media. Este módulo tampoco debe exponer
credenciales al frontend ni registrarlas en logs.
"""

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree
from urllib import error, request
from xml.sax.saxutils import escape
import os
import time

from .configuracion_instalacion import (
    obtener_directorio_privado,
    obtener_valor_privado,
    guardar_valor_privado,
)

import base64

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7  


AMBIENTE_HOMOLOGACION = "homologacion"
AMBIENTE_PRODUCCION = "produccion"

AMBIENTES_VALIDOS = {
    AMBIENTE_HOMOLOGACION,
    AMBIENTE_PRODUCCION,
}

SERVICIO_CONSTANCIA_INSCRIPCION = (
    "ws_sr_constancia_inscripcion"
)

CLAVE_ARCA_AMBIENTE = "arca_ambiente"
CLAVE_ARCA_CUIT_REPRESENTADA = "arca_cuit_representada"

CUIT_REPRESENTADA_PREDETERMINADA = 20323907693


@dataclass(frozen=True)
class ConfiguracionArca:
    """
    Describe la configuración técnica necesaria para un ambiente ARCA.

    Las rutas apuntan siempre al directorio privado de la instalación.
    No contienen información perteneciente a una Empresa de OrdenaClick.
    """

    ambiente: str
    cuit_representada: int
    servicio: str
    directorio: Path
    certificado: Path
    clave_privada: Path
    ticket_acceso: Path
    url_wsaa: str
    url_padron: str

def obtener_ambiente_operativo_arca():
    """
    Obtiene el ambiente ARCA seleccionado para esta instalación.

    Si todavía no fue persistido, conserva homologación como valor seguro
    predeterminado.
    """
    ambiente = obtener_valor_privado(
        CLAVE_ARCA_AMBIENTE,
        AMBIENTE_HOMOLOGACION,
    )

    if ambiente not in AMBIENTES_VALIDOS:
        raise RuntimeError(
            "El ambiente ARCA configurado para la instalación no es válido."
        )

    return ambiente


def obtener_cuit_representada_arca():
    """
    Obtiene el CUIT representado configurado globalmente para ARCA.
    """
    valor = obtener_valor_privado(
        CLAVE_ARCA_CUIT_REPRESENTADA,
        CUIT_REPRESENTADA_PREDETERMINADA,
    )

    cuit = str(valor).strip()

    if not cuit.isdigit() or len(cuit) != 11:
        raise RuntimeError(
            "El CUIT representado configurado para ARCA no es válido."
        )

    return int(cuit)


def guardar_configuracion_general_arca(
    ambiente,
    cuit_representada,
):
    """
    Guarda la configuración global no criptográfica de ARCA.

    Las credenciales se administran separadamente y nunca se almacenan
    dentro del archivo JSON de configuración.
    """
    ambiente = str(ambiente).strip()
    cuit = str(cuit_representada).strip()

    if ambiente not in AMBIENTES_VALIDOS:
        raise ValueError(
            "El ambiente ARCA seleccionado no es válido."
        )

    if not cuit.isdigit() or len(cuit) != 11:
        raise ValueError(
            "El CUIT representado debe contener exactamente 11 dígitos."
        )

    guardar_valor_privado(
        CLAVE_ARCA_AMBIENTE,
        ambiente,
    )

    guardar_valor_privado(
        CLAVE_ARCA_CUIT_REPRESENTADA,
        cuit,
    )


def guardar_credenciales_arca(
    ambiente,
    certificado_contenido,
    clave_privada_contenido,
):
    """
    Valida y guarda certificado y clave privada para un ambiente ARCA.

    Antes de persistirlos comprueba que ambos archivos sean válidos y que
    la clave privada corresponda al certificado suministrado.
    """
    if ambiente not in AMBIENTES_VALIDOS:
        raise ValueError(
            "El ambiente ARCA seleccionado no es válido."
        )

    if not certificado_contenido:
        raise ValueError(
            "El certificado de ARCA está vacío."
        )

    if not clave_privada_contenido:
        raise ValueError(
            "La clave privada de ARCA está vacía."
        )

    try:
        certificado = x509.load_pem_x509_certificate(
            certificado_contenido
        )

        clave_privada = serialization.load_pem_private_key(
            clave_privada_contenido,
            password=None,
        )

    except (
        ValueError,
        TypeError,
    ) as error:
        raise ValueError(
            "El certificado o la clave privada de ARCA no son válidos."
        ) from error

    clave_publica_certificado = (
        certificado.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    clave_publica_privada = (
        clave_privada.public_key().public_bytes(
            serialization.Encoding.DER,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    if clave_publica_certificado != clave_publica_privada:
        raise ValueError(
            "La clave privada no corresponde al certificado de ARCA."
        )

    configuracion = obtener_configuracion_arca(
        ambiente
    )

    try:
        configuracion.directorio.mkdir(
            parents=True,
            exist_ok=True,
        )

        if os.name != "nt":
            os.chmod(
                configuracion.directorio,
                0o700,
            )

        ruta_certificado_temporal = (
            configuracion.certificado.with_suffix(
                ".crt.tmp"
            )
        )

        ruta_clave_temporal = (
            configuracion.clave_privada.with_suffix(
                ".key.tmp"
            )
        )

        ruta_certificado_temporal.write_bytes(
            certificado_contenido
        )

        ruta_clave_temporal.write_bytes(
            clave_privada_contenido
        )

        if os.name != "nt":
            os.chmod(
                ruta_certificado_temporal,
                0o600,
            )

            os.chmod(
                ruta_clave_temporal,
                0o600,
            )

        ruta_certificado_temporal.replace(
            configuracion.certificado
        )

        ruta_clave_temporal.replace(
            configuracion.clave_privada
        )

        if os.name != "nt":
            os.chmod(
                configuracion.certificado,
                0o600,
            )

            os.chmod(
                configuracion.clave_privada,
                0o600,
            )

    except OSError as error:
        raise RuntimeError(
            "No se pudieron guardar las credenciales privadas de ARCA."
        ) from error

def obtener_configuracion_arca(
    ambiente=None,
):
    """
    Construye la configuración técnica de ARCA.

    Cuando no se indica explícitamente un ambiente, utiliza el ambiente
    operativo configurado globalmente para la instalación.

    Homologación y producción mantienen directorios y credenciales
    independientes.
    """
    if ambiente is None:
        ambiente = obtener_ambiente_operativo_arca()

    if ambiente not in AMBIENTES_VALIDOS:
        raise ValueError(
            "El ambiente de ARCA solicitado no es válido."
        )

    directorio = (
        obtener_directorio_privado()
        / "arca"
        / ambiente
    )

    if ambiente == AMBIENTE_HOMOLOGACION:
        nombre_certificado = "ordenaclick_homo.crt"
        nombre_clave = "ordenaclick_homo.key"

        url_wsaa = (
            "https://wsaahomo.afip.gov.ar/"
            "ws/services/LoginCms"
        )

        url_padron = (
            "https://awshomo.afip.gov.ar/"
            "sr-padron/webservices/personaServiceA5"
        )

    else:
        nombre_certificado = "ordenaclick_prod.crt"
        nombre_clave = "ordenaclick_prod.key"

        url_wsaa = (
            "https://wsaa.afip.gov.ar/"
            "ws/services/LoginCms"
        )

        url_padron = (
            "https://aws.afip.gov.ar/"
            "sr-padron/webservices/personaServiceA5"
        )

    return ConfiguracionArca(
        ambiente=ambiente,
        cuit_representada=obtener_cuit_representada_arca(),
        servicio=SERVICIO_CONSTANCIA_INSCRIPCION,
        directorio=directorio,
        certificado=directorio / nombre_certificado,
        clave_privada=directorio / nombre_clave,
        ticket_acceso=directorio / "TA_response.xml",
        url_wsaa=url_wsaa,
        url_padron=url_padron,
    )


def validar_credenciales_arca(
    configuracion,
):
    """
    Verifica que certificado y clave privada existan y sean archivos.

    No lee, imprime ni devuelve el contenido de ninguno de los dos.
    """
    faltantes = []

    if not configuracion.certificado.is_file():
        faltantes.append("certificado")

    if not configuracion.clave_privada.is_file():
        faltantes.append("clave privada")

    if faltantes:
        raise RuntimeError(
            "Falta configuración privada de ARCA: "
            + ", ".join(faltantes)
            + "."
        )

def leer_ticket_acceso_arca(
    configuracion,
):
    """
    Lee un Ticket de Acceso de WSAA previamente guardado.

    El archivo contiene la respuesta SOAP de WSAA. El Ticket de Acceso
    propiamente dicho viene como XML dentro de loginCmsReturn, por lo
    que deben procesarse ambas capas.

    Devuelve únicamente los datos necesarios para autenticar llamadas
    posteriores a ARCA. Nunca registra token ni sign.
    """
    if not configuracion.ticket_acceso.is_file():
        raise RuntimeError(
            "No existe un Ticket de Acceso de ARCA guardado."
        )

    try:
        raiz_soap = ElementTree.parse(
            configuracion.ticket_acceso
        ).getroot()
    except (
        OSError,
        ElementTree.ParseError,
    ) as error:
        raise RuntimeError(
            "No se pudo leer el Ticket de Acceso de ARCA."
        ) from error

    login_cms_return = next(
        (
            elemento
            for elemento in raiz_soap.iter()
            if elemento.tag.rsplit("}", 1)[-1]
            == "loginCmsReturn"
        ),
        None,
    )

    if (
        login_cms_return is None
        or not login_cms_return.text
        or not login_cms_return.text.strip()
    ):
        raise RuntimeError(
            "La respuesta de WSAA no contiene "
            "un Ticket de Acceso."
        )

    try:
        raiz_ticket = ElementTree.fromstring(
            login_cms_return.text.strip()
        )
    except ElementTree.ParseError as error:
        raise RuntimeError(
            "El Ticket de Acceso contenido en la "
            "respuesta de WSAA es inválido."
        ) from error

    token = raiz_ticket.findtext(
        ".//credentials/token"
    )
    sign = raiz_ticket.findtext(
        ".//credentials/sign"
    )
    expiration_time = raiz_ticket.findtext(
        ".//header/expirationTime"
    )

    if not token or not sign or not expiration_time:
        raise RuntimeError(
            "El Ticket de Acceso de ARCA está incompleto."
        )

    try:
        vencimiento = datetime.fromisoformat(
            expiration_time
        )
    except ValueError as error:
        raise RuntimeError(
            "El Ticket de Acceso de ARCA tiene "
            "una fecha de vencimiento inválida."
        ) from error

    return {
        "token": token,
        "sign": sign,
        "vencimiento": vencimiento,
    }

def ticket_acceso_vigente(
    ticket,
    margen_minutos=10,
):
    """
    Indica si un Ticket de Acceso puede reutilizarse de forma segura.

    Se considera vencido unos minutos antes de su expiración real para
    evitar iniciar una consulta a ARCA con credenciales próximas a
    caducar.
    """
    vencimiento = ticket.get("vencimiento")

    if (
        vencimiento is None
        or vencimiento.tzinfo is None
    ):
        return False

    ahora = datetime.now(
        vencimiento.tzinfo
    )

    limite_seguro = (
        vencimiento
        - timedelta(minutes=margen_minutos)
    )

    return ahora < limite_seguro

def _obtener_texto_por_nombre_local(
    raiz,
    nombre,
):
    """
    Obtiene el texto del primer elemento XML con el nombre local dado.

    Permite leer respuestas SOAP aunque ARCA utilice namespaces
    diferentes en el sobre y en el contenido.
    """
    for elemento in raiz.iter():
        nombre_local = elemento.tag.rsplit("}", 1)[-1]

        if nombre_local == nombre:
            return (
                elemento.text.strip()
                if elemento.text
                else ""
            )

    return ""


def consultar_persona_arca(
    cuit,
    configuracion=None,
):
    """
    Consulta una persona en el servicio de constancia de ARCA.

    Obtiene un Ticket de Acceso reutilizable, renovándolo mediante WSAA
    cuando resulte necesario, y devuelve únicamente los datos que
    OrdenaClick necesita actualmente: razón social y dirección.

    No persiste datos de la persona ni expone token, sign o credenciales.
    """
    if configuracion is None:
        configuracion = obtener_configuracion_arca()

    validar_credenciales_arca(
        configuracion
    )

    ticket = obtener_ticket_acceso_arca(
        configuracion
    )

    cuit_texto = str(cuit).strip()

    if (
        not cuit_texto.isdigit()
        or len(cuit_texto) != 11
    ):
        raise ValueError(
            "El CUIT debe contener exactamente 11 dígitos."
        )

    soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:a5="http://a5.soap.ws.server.puc.sr/">
    <soapenv:Header/>
    <soapenv:Body>
        <a5:getPersona_v2>
            <token>{escape(ticket["token"])}</token>
            <sign>{escape(ticket["sign"])}</sign>
            <cuitRepresentada>{configuracion.cuit_representada}</cuitRepresentada>
            <idPersona>{cuit_texto}</idPersona>
        </a5:getPersona_v2>
    </soapenv:Body>
</soapenv:Envelope>
"""

    solicitud = request.Request(
        configuracion.url_padron,
        data=soap.encode("utf-8"),
        headers={
            "Content-Type": "text/xml; charset=utf-8",
        },
        method="POST",
    )

    try:
        with request.urlopen(
            solicitud,
            timeout=15,
        ) as respuesta:
            contenido = respuesta.read()

    except error.HTTPError as error_http:
        try:
            detalle = error_http.read().decode(
                "utf-8",
                errors="replace",
            )
        except OSError:
            detalle = ""

        if "No existe persona con ese Id" in detalle:
            raise LookupError(
                "ARCA no encontró una persona para ese CUIT."
            ) from error_http

        raise RuntimeError(
            "ARCA rechazó la consulta de la persona."
        ) from error_http

    except (
        error.URLError,
        TimeoutError,
        OSError,
    ) as error_conexion:
        raise RuntimeError(
            "No se pudo conectar con ARCA."
        ) from error_conexion

    try:
        raiz = ElementTree.fromstring(
            contenido
        )
    except ElementTree.ParseError as error_xml:
        raise RuntimeError(
            "ARCA devolvió una respuesta inválida."
        ) from error_xml

    razon_social = _obtener_texto_por_nombre_local(
        raiz,
        "razonSocial",
    )

    direccion = _obtener_texto_por_nombre_local(
        raiz,
        "direccion",
    )

    if not razon_social:
        raise RuntimeError(
            "ARCA no devolvió la razón social esperada."
        )

    return {
        "razon_social": razon_social,
        "direccion": direccion,
    }

def generar_tra_arca(
    configuracion,
):
    """
    Genera el Login Ticket Request requerido por WSAA.

    Las fechas se expresan con zona horaria explícita y se limita la
    vigencia solicitada para evitar reutilizaciones innecesariamente
    prolongadas.
    """
    ahora_utc = datetime.now(timezone.utc)

    generacion = (
        ahora_utc
        - timedelta(minutes=10)
    )

    expiracion = (
        ahora_utc
        + timedelta(hours=1)
    )

    unique_id = int(
        ahora_utc.timestamp()
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<loginTicketRequest version="1.0">
<header>
<uniqueId>{unique_id}</uniqueId>
<generationTime>{generacion.isoformat(timespec="milliseconds")}</generationTime>
<expirationTime>{expiracion.isoformat(timespec="milliseconds")}</expirationTime>
</header>
<service>{configuracion.servicio}</service>
</loginTicketRequest>"""


def firmar_tra_arca(
    tra,
    configuracion,
):
    """
    Firma un Login Ticket Request mediante PKCS#7/CMS.

    Utiliza exclusivamente el certificado y la clave privada del
    directorio privado de la instalación. Devuelve el CMS codificado
    en Base64 requerido por WSAA.
    """
    validar_credenciales_arca(
        configuracion
    )

    try:
        certificado_bytes = (
            configuracion.certificado.read_bytes()
        )

        clave_bytes = (
            configuracion.clave_privada.read_bytes()
        )

        certificado = x509.load_pem_x509_certificate(
            certificado_bytes
        )

        clave_privada = serialization.load_pem_private_key(
            clave_bytes,
            password=None,
        )

    except (
        OSError,
        ValueError,
        TypeError,
    ) as error_credenciales:
        raise RuntimeError(
            "No se pudieron cargar las credenciales "
            "privadas de ARCA."
        ) from error_credenciales

    try:
        constructor = (
            pkcs7.PKCS7SignatureBuilder()
            .set_data(
                tra.encode("utf-8")
            )
            .add_signer(
                certificado,
                clave_privada,
                hashes.SHA256(),
            )
        )

        cms = constructor.sign(
            serialization.Encoding.DER,
            [
                pkcs7.PKCS7Options.Binary,
            ],
        )

    except (
        ValueError,
        TypeError,
    ) as error_firma:
        raise RuntimeError(
            "No se pudo firmar el Ticket Request de ARCA."
        ) from error_firma

    return base64.b64encode(
        cms
    ).decode("ascii")

def _adquirir_bloqueo_ticket_arca(
    configuracion,
    espera_maxima_segundos=20,
    antiguedad_maxima_segundos=60,
):
    """
    Adquiere un bloqueo exclusivo entre procesos para renovar el TA.

    El bloqueo se crea atómicamente dentro del directorio privado de
    ARCA. Si quedó abandonado por una interrupción del proceso y supera
    la antigüedad máxima permitida, se elimina y vuelve a intentarse.
    """
    configuracion.directorio.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_bloqueo = (
        configuracion.directorio
        / "TA_response.lock"
    )

    limite = (
        time.monotonic()
        + espera_maxima_segundos
    )

    while True:
        try:
            descriptor = os.open(
                ruta_bloqueo,
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY,
                0o600,
            )

            return descriptor, ruta_bloqueo

        except FileExistsError:
            try:
                antiguedad = (
                    time.time()
                    - ruta_bloqueo.stat().st_mtime
                )
            except FileNotFoundError:
                continue
            except OSError as error:
                raise RuntimeError(
                    "No se pudo comprobar el bloqueo "
                    "de renovación de ARCA."
                ) from error

            if antiguedad >= antiguedad_maxima_segundos:
                try:
                    ruta_bloqueo.unlink()
                except FileNotFoundError:
                    pass
                except OSError as error:
                    raise RuntimeError(
                        "No se pudo liberar un bloqueo "
                        "abandonado de ARCA."
                    ) from error

                continue

            if time.monotonic() >= limite:
                raise RuntimeError(
                    "No se pudo obtener el bloqueo "
                    "para renovar el acceso a ARCA."
                )

            time.sleep(0.1)

def obtener_ticket_acceso_arca(
    configuracion=None,
):
    """
    Obtiene un Ticket de Acceso reutilizable para ARCA.

    Reutiliza el TA privado mientras conserve margen suficiente de
    vigencia. Si debe renovarlo, adquiere un bloqueo entre procesos y
    vuelve a comprobar el archivo antes de contactar WSAA.
    """
    if configuracion is None:
        configuracion = obtener_configuracion_arca()

    try:
        ticket = leer_ticket_acceso_arca(
            configuracion
        )
    except RuntimeError:
        ticket = None

    if (
        ticket is not None
        and ticket_acceso_vigente(ticket)
    ):
        return ticket

    descriptor = None
    ruta_bloqueo = None

    try:
        (
            descriptor,
            ruta_bloqueo,
        ) = _adquirir_bloqueo_ticket_arca(
            configuracion
        )

        try:
            ticket = leer_ticket_acceso_arca(
                configuracion
            )
        except RuntimeError:
            ticket = None

        if (
            ticket is not None
            and ticket_acceso_vigente(ticket)
        ):
            return ticket

        ticket = solicitar_ticket_acceso_arca(
            configuracion
        )

        if not ticket_acceso_vigente(ticket):
            raise RuntimeError(
                "WSAA devolvió un Ticket de Acceso "
                "sin vigencia suficiente."
            )

        return ticket

    finally:
        if descriptor is not None:
            os.close(descriptor)

        if ruta_bloqueo is not None:
            try:
                ruta_bloqueo.unlink(
                    missing_ok=True
                )
            except OSError:
                pass

def _guardar_respuesta_wsaa(
    contenido,
    configuracion,
):
    """
    Guarda atómicamente la respuesta SOAP de WSAA en el directorio
    privado de ARCA.

    El archivo contiene token y sign, por lo que nunca debe ubicarse
    dentro del repositorio, static o media.
    """
    configuracion.directorio.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_temporal = (
        configuracion.ticket_acceso.with_suffix(
            ".xml.tmp"
        )
    )

    try:
        ruta_temporal.write_bytes(
            contenido
        )

        if ruta_temporal.stat().st_size == 0:
            raise RuntimeError(
                "WSAA devolvió una respuesta vacía."
            )

        ruta_temporal.replace(
            configuracion.ticket_acceso
        )

    except OSError as error:
        try:
            ruta_temporal.unlink(
                missing_ok=True
            )
        except OSError:
            pass

        raise RuntimeError(
            "No se pudo guardar el Ticket de Acceso de ARCA."
        ) from error


def solicitar_ticket_acceso_arca(
    configuracion,
):
    """
    Solicita un nuevo Ticket de Acceso al WSAA de ARCA.

    Genera y firma el TRA localmente, envía únicamente el CMS requerido
    por WSAA y guarda la respuesta SOAP en el directorio privado de la
    instalación. Nunca expone token, sign ni la clave privada.
    """
    tra = generar_tra_arca(
        configuracion
    )

    cms = firmar_tra_arca(
        tra,
        configuracion,
    )

    soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:wsaa="http://wsaa.view.sua.dvadac.desein.afip.gov">
    <soapenv:Header/>
    <soapenv:Body>
        <wsaa:loginCms>
            <wsaa:in0>{escape(cms)}</wsaa:in0>
        </wsaa:loginCms>
    </soapenv:Body>
</soapenv:Envelope>
"""

    solicitud = request.Request(
        configuracion.url_wsaa,
        data=soap.encode("utf-8"),
        headers={
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": '""',
        },
        method="POST",
    )

    try:
        with request.urlopen(
            solicitud,
            timeout=15,
        ) as respuesta:
            contenido = respuesta.read()

    except error.HTTPError as error_http:
        try:
            detalle = error_http.read().decode(
                "utf-8",
                errors="replace",
            )
        except OSError:
            detalle = ""

        if "alreadyAuthenticated" in detalle:
            raise RuntimeError(
                "WSAA informa que ya existe un Ticket "
                "de Acceso vigente."
            ) from error_http

        raise RuntimeError(
            "WSAA rechazó la autenticación de ARCA."
        ) from error_http

    except (
        error.URLError,
        TimeoutError,
        OSError,
    ) as error_conexion:
        raise RuntimeError(
            "No se pudo conectar con WSAA de ARCA."
        ) from error_conexion

    try:
        raiz = ElementTree.fromstring(
            contenido
        )
    except ElementTree.ParseError as error_xml:
        raise RuntimeError(
            "WSAA devolvió una respuesta inválida."
        ) from error_xml

    login_cms_return = next(
        (
            elemento
            for elemento in raiz.iter()
            if elemento.tag.rsplit("}", 1)[-1]
            == "loginCmsReturn"
        ),
        None,
    )

    if (
        login_cms_return is None
        or not login_cms_return.text
        or not login_cms_return.text.strip()
    ):
        raise RuntimeError(
            "WSAA no devolvió un Ticket de Acceso."
        )

    _guardar_respuesta_wsaa(
        contenido,
        configuracion,
    )

    return leer_ticket_acceso_arca(
        configuracion
    )