from django.shortcuts import (
    render,
    redirect
)

from usuarios.services.financiero import (
    resumen_disponibilidad_caja,
)

from django.contrib.auth import (
    authenticate,
    login,
    logout
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.http import (
    HttpResponse,
    JsonResponse
)

from django.conf import settings

from django.utils import timezone

from datetime import (
    datetime,
    timedelta
)

from io import BytesIO

from django.core.exceptions import ValidationError, PermissionDenied
from django.core.validators import validate_email

import os
import re
import json
import uuid
import zipfile

from .models import (
    Empresa,
    Ejercicio,
    TipoGasto,
    TipoGastoProveedor,
    Movimiento,
    Pago,
    AplicacionPago,
    OperacionBancariaPago,
    DebitoAutomaticoPago,
    TarjetaPago,
    Cheque,
    CentroOperativo,
    Banco,
    CuentaBancaria,
    Tarjeta,
    Retencion,
    RetencionPago,
    GestionClave,
    RecursoOperativo,
    RecursoOperativoCentro,
    Proveedor,
    Cliente,
    Caja,
    AsignacionUsuarioEmpresa,
    PerfilUsuario
)

from .seguridad_claves import (
    cifrar_clave,
    descifrar_clave
)

from usuarios.services.configuracion_instalacion import (
    obtener_valor_privado,
)

from usuarios.services.seguridad_instalacion import (
    reemplazar_secret_key_privada,
    secret_key_tiene_reinicio_pendiente,
)

from usuarios.services.arca import (
    AMBIENTE_HOMOLOGACION,
    AMBIENTE_PRODUCCION,
    consultar_persona_arca,
    guardar_configuracion_general_arca,
    guardar_credenciales_arca,
    obtener_ambiente_operativo_arca,
    obtener_configuracion_arca,
    obtener_cuit_representada_arca,
    validar_credenciales_arca,
)

# =========================================
# AUTENTICACIÓN / PERFILES DE ENTRADA

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

@login_required
def panel_admin(request):

    # =====================================
    # EMPRESA ACTIVA
    # =====================================

    empresa_id = request.GET.get('empresa')

    empresa_actual = None

    if empresa_id:

        try:
            from usuarios.services.seguridad import (
                obtener_empresa_autorizada,
            )

            empresa_actual = obtener_empresa_autorizada(
                request.user,
                empresa_id,
            )

        except Empresa.DoesNotExist:
            empresa_actual = None

    # =====================================
    # GUARDAR EMPRESA
    # =====================================

    if request.method == 'POST':

        # ================================
        # NUEVA EMPRESA
        # ================================

        if request.POST.get('guardar_empresa'):

            cuit = request.POST.get('cuit')

            if not re.match(
                r'^\d{2}-\d{8}-\d{1}$',
                cuit
            ):
                return redirect('panel_admin')

            empresa_reemplazar = request.session.get(
                "empresa_reemplazar"
            )

            confirmar_reemplazo = request.session.get(
                "confirmar_reemplazo"
            )

            if empresa_reemplazar and confirmar_reemplazo:

                try:

                    Empresa.objects.get(
                        id=empresa_reemplazar
                    ).delete()

                except Empresa.DoesNotExist:

                    pass

                request.session.pop(
                    "empresa_reemplazar",
                    None
                )

                request.session.pop(
                    "confirmar_reemplazo",
                    None
                )


            nueva_empresa = Empresa.objects.create(

                propietario=request.user,

                razon_social=request.POST.get(
                    'razon_social'
                ),

                nombre_fantasia=request.POST.get(
                    'nombre_fantasia'
                ).upper() if request.POST.get(
                    'nombre_fantasia'
                ) else '',

                condicion_fiscal=request.POST.get(
                    'condicion_fiscal'
                ),

                cuit=request.POST.get(
                    'cuit'
                ),

                inicio_actividades=request.POST.get(
                    'inicio_actividades'
                ) or None,

                inicio_contable=request.POST.get(
                    'inicio_contable'
                ) or None,

                direccion_fiscal=request.POST.get(
                    'direccion_fiscal'
                ),

                direccion_real=request.POST.get(
                    'direccion_real'
                ),

                telefono1=request.POST.get(
                    'telefono1'
                ),

                telefono2=request.POST.get(
                    'telefono2'
                ),

                email=request.POST.get(
                    'email'
                ),

                presidente=request.POST.get(
                    'presidente'
                ),

                vicepresidente=request.POST.get(
                    'vicepresidente'
                ),

                estatuto=request.FILES.get(
                    'estatuto'
                ),

                fecha_estatuto=timezone.now()
                if request.FILES.get(
                    'estatuto'
                )
                else None,

                acta=request.FILES.get(
                    'acta'
                ),

                fecha_acta=timezone.now()
                if request.FILES.get(
                    'acta'
                )
                else None,

                designacion=request.FILES.get(
                    'designacion'
                ),

                fecha_designacion=timezone.now()
                if request.FILES.get(
                    'designacion'
                )
                else None
            )

            CentroOperativo.objects.create(

                 empresa=nueva_empresa,

                 nombre='CASA CENTRAL',

                 tipo='Casa Central',

                 direccion=nueva_empresa.direccion_real or ''
             )

            if nueva_empresa.inicio_contable:

                fecha_inicio = datetime.strptime(
                    str(nueva_empresa.inicio_contable),
                    "%Y-%m-%d"
                ).date()

                fecha_cierre = fecha_inicio.replace(
                    year=fecha_inicio.year + 1
                ) - timedelta(days=1)

                Ejercicio.objects.create(

                    empresa=nueva_empresa,

                    numero=1,

                    fecha_inicio=fecha_inicio,

                    fecha_cierre=fecha_cierre,

                    presidente=nueva_empresa.presidente,

                    vicepresidente=nueva_empresa.vicepresidente,

                    estado='Abierto'
                )

            return redirect(
                f'/panel-admin/?empresa={nueva_empresa.id}'
            )


        # ================================
        # MODIFICAR EMPRESA
         # ================================

        if request.POST.get('guardar_cambios_empresa'):

            empresa_actual.razon_social = request.POST.get(
                'razon_social'
            )

            empresa_actual.nombre_fantasia = (
               request.POST.get(
                   'nombre_fantasia'
               ).upper()
                if request.POST.get(
                  'nombre_fantasia'
              )
               else ''
            )

            empresa_actual.condicion_fiscal = request.POST.get(
              'condicion_fiscal'
            )

            empresa_actual.cuit = request.POST.get(
                'cuit'
            )

            empresa_actual.inicio_actividades = (
                 request.POST.get(
                     'inicio_actividades'
                ) or None
            )

            empresa_actual.inicio_contable = (
                request.POST.get(
                    'inicio_contable'
                 ) or None
            )

            empresa_actual.direccion_fiscal = request.POST.get(
                'direccion_fiscal'
            )

            empresa_actual.direccion_real = request.POST.get(
               'direccion_real'
            )

            empresa_actual.telefono1 = request.POST.get(
               'telefono1'
            )

            empresa_actual.telefono2 = request.POST.get(
                'telefono2'
            )

            empresa_actual.email = request.POST.get(
               'email'
            )

            empresa_actual.presidente = request.POST.get(
              'presidente'
            )

            empresa_actual.vicepresidente = request.POST.get(
               'vicepresidente'
            )

            # ==========================
            # ARCHIVOS
            # ==========================

            if request.FILES.get('estatuto'):

                empresa_actual.estatuto = request.FILES.get(
                    'estatuto'
                )

                empresa_actual.fecha_estatuto = (
                    timezone.now()
                )

            if request.FILES.get('acta'):

                empresa_actual.acta = request.FILES.get(
                    'acta'
                )

                empresa_actual.fecha_acta = (
                    timezone.now()
                )

            if request.FILES.get('designacion'):

                empresa_actual.designacion = request.FILES.get(
                    'designacion'
                )

                empresa_actual.fecha_designacion = (
                    timezone.now()
                )

            empresa_actual.save()

            return redirect(
               f'/panel-admin/?empresa={empresa_actual.id}'
            )   
    

    # =====================================
    # DATOS
    # =====================================

    empresa_importada = None

    if request.session.get("empresa_importada"):

        empresa_importada = request.session["empresa_importada"]

        request.session.pop(
            "empresa_importada",
            None
        )

    asignaciones_importadas = request.session.get(
        "asignaciones_importadas",
        []
    )

    empresa_existente = request.session.get(
        "empresa_existente"
    )

    request.session.pop(
        "empresa_existente",
        None
    )

    from usuarios.services.seguridad import (
        empresas_autorizadas,
    )

    empresas = empresas_autorizadas(
        request.user
    ).order_by(
        'nombre_fantasia',
        'razon_social'
    )


    movimientos = []

    if empresa_actual:

        ejercicio_abierto = empresa_actual.ejercicios.filter(
            estado='Abierto'
        ).first()

        if ejercicio_abierto:

            movimientos = Movimiento.objects.filter(
                ejercicio=ejercicio_abierto
            ).order_by('-fecha_registro')

    return render(

    request,

    'usuarios/perfiles/administrador/panel.html',

    {

        'empresas': empresas,
        'empresa_actual': empresa_actual,
        'empresa_importada': empresa_importada,

        'empresa_existente': empresa_existente,
        'movimientos': movimientos

    }
)



def exportar_empresa(request, empresa_id):

    empresa = Empresa.objects.get(
        id=empresa_id
    )

    buffer = BytesIO()

    with zipfile.ZipFile(
        buffer,
        'w',
        zipfile.ZIP_DEFLATED
    ) as zip_file:

        # ==========================
        # DATOS EMPRESA
        # ==========================

        datos_empresa = {

            'razon_social':
                empresa.razon_social,

            'nombre_fantasia':
                empresa.nombre_fantasia,

            'condicion_fiscal':
                empresa.condicion_fiscal,

            'cuit':
                empresa.cuit,

            'inicio_actividades':
                str(
                    empresa.inicio_actividades
                ) if empresa.inicio_actividades else None,

            'inicio_contable':
                str(
                    empresa.inicio_contable
                ) if empresa.inicio_contable else None,

            'direccion_fiscal':
                empresa.direccion_fiscal,

            'direccion_real':
                empresa.direccion_real,

            'telefono1':
                empresa.telefono1,

            'telefono2':
                empresa.telefono2,

            'email':
                empresa.email,

            'presidente':
                empresa.presidente,

            'vicepresidente':
                empresa.vicepresidente

        }

        zip_file.writestr(

            'empresa.json',

            json.dumps(
                datos_empresa,
                indent=4,
                ensure_ascii=False
            )
        )

        # ==========================
        # ASIGNACIONES DE USUARIOS
        # ==========================

        asignaciones = (
            AsignacionUsuarioEmpresa.objects
            .filter(
                empresa=empresa,
            )
            .select_related(
                "usuario",
                "centro_operativo",
            )
            .order_by(
                "id",
            )
        )

        datos_asignaciones = []

        for asignacion in asignaciones:

            datos_asignaciones.append(
                {
                    "usuario": {
                        "username":
                            asignacion.usuario.username,
                        "email":
                            asignacion.usuario.email,
                    },
                    "jerarquia":
                        asignacion.jerarquia,
                    "centro_operativo": (
                        {
                            "id":
                                asignacion.centro_operativo_id,
                            "nombre":
                                asignacion.centro_operativo.nombre,
                        }
                        if asignacion.centro_operativo_id
                        else None
                    ),
                    "activo":
                        asignacion.activo,
                }
            )

        zip_file.writestr(
            "asignaciones_usuarios.json",
            json.dumps(
                datos_asignaciones,
                indent=4,
                ensure_ascii=False,
            ),
        )

        # ==========================
        # DOCUMENTOS
        # ==========================

        if empresa.estatuto:

            zip_file.write(

                empresa.estatuto.path,

                arcname='documentos/estatuto' +
                os.path.splitext(
                    empresa.estatuto.name
                )[1]

            )

        if empresa.acta:

            zip_file.write(

                empresa.acta.path,

                arcname='documentos/acta_asamblea' +
                os.path.splitext(
                    empresa.acta.name
                )[1]

            )

        if empresa.designacion:

            zip_file.write(

                empresa.designacion.path,

                arcname='documentos/designacion_autoridades' +
                os.path.splitext(
                    empresa.designacion.name
                )[1]

            )

    buffer.seek(0)

    fecha = timezone.now().strftime(
        '%d-%m-%Y'
    )

    nombre = (
        f'{empresa.nombre_fantasia}_{fecha}.zip'
    )

    response = HttpResponse(

        buffer.getvalue(),

        content_type='application/zip'

    )

    response[
        'Content-Disposition'
    ] = f'attachment; filename="{nombre}"'

    return response

def eliminar_empresa(
    request,
    empresa_id
):

    empresa = Empresa.objects.get(
        id=empresa_id
    )


    # =========================================
    # ARCHIVOS DE LA EMPRESA
    # =========================================

    if empresa.estatuto:

        empresa.estatuto.delete(
            save=False
        )


    if empresa.acta:

        empresa.acta.delete(
            save=False
        )


    if empresa.designacion:

        empresa.designacion.delete(
            save=False
        )


    # =========================================
    # ENTIDADES QUE PROTEGEN OTROS MAESTROS
    # =========================================
    #
    # RecursoOperativo protege CentroOperativo.
    # Por eso debe eliminarse antes de intentar
    # eliminar la Empresa y sus Centros.
    #

    RecursoOperativo.objects.filter(
        empresa=empresa
    ).delete()


    # CuentaBancaria protege Banco.
    # Debe eliminarse antes de que la eliminación
    # en cascada de Empresa intente borrar Bancos.

    CuentaBancaria.objects.filter(
        empresa=empresa
    ).delete()


    # =========================================
    # EMPRESA
    # =========================================

    empresa.delete()


    return redirect(
        'panel_admin'
    )

    empresa = Empresa.objects.get(
        id=empresa_id
    )

    if empresa.estatuto:

        empresa.estatuto.delete(
            save=False
        )

    if empresa.acta:

        empresa.acta.delete(
            save=False
        )

    if empresa.designacion:

        empresa.designacion.delete(
            save=False
        )

    empresa.delete()

    return redirect('panel_admin')

def importar_empresa(request):

    if request.method != "POST":
        return redirect('panel_admin')

    archivo_zip = request.FILES.get(
        "archivo_zip"
    )

    if not archivo_zip:
        return redirect('panel_admin')

    nombre_zip = f"{uuid.uuid4()}.zip"

    carpeta_importaciones = os.path.join(
        settings.MEDIA_ROOT,
        "importaciones"
    )

    os.makedirs(
        carpeta_importaciones,
        exist_ok=True
    )

    ruta_zip = os.path.join(
        carpeta_importaciones,
        nombre_zip
    )

    with open(
        ruta_zip,
        "wb+"
    ) as destino:

        for chunk in archivo_zip.chunks():

            destino.write(chunk)

    with zipfile.ZipFile(
        ruta_zip,
        "r"
    ) as zip_ref:

        with zip_ref.open(
            "empresa.json"
        ) as archivo_json:

            datos_empresa = json.load(
                archivo_json
            )

        datos_asignaciones = []

        if "asignaciones_usuarios.json" in zip_ref.namelist():

            with zip_ref.open(
                "asignaciones_usuarios.json"
            ) as archivo_asignaciones:

                datos_asignaciones = json.load(
                    archivo_asignaciones
                )

    cuit = datos_empresa.get(
        "cuit"
    )

    empresa_existente = Empresa.objects.filter(
        cuit=cuit
    ).first()

    confirmar = request.POST.get(
        "confirmar_reemplazo"
    )

    # -------------------------------------------------
    # Existe y todavía no confirmó
    # -------------------------------------------------

    if empresa_existente and confirmar != "1":

        request.session["empresa_existente"] = empresa_existente.id

        return redirect('panel_admin')

    # -------------------------------------------------
    # No existe o aceptó reemplazar
    # -------------------------------------------------

    request.session["zip_importacion"] = nombre_zip

    request.session["empresa_importada"] = datos_empresa

    request.session["asignaciones_importadas"] = datos_asignaciones

    if empresa_existente:

        request.session[
            "empresa_reemplazar"
        ] = empresa_existente.id

    else:

        request.session.pop(
            "empresa_reemplazar",
            None
        )

    request.session.pop(
        "empresa_existente",
        None
    )

    return redirect('panel_admin')

def confirmar_reemplazo(request):

    request.session[
        "confirmar_reemplazo"
    ] = True

    return redirect('panel_admin')    

# =====================================
# GUARDAR BANCO
# =====================================

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db import transaction

# =========================================
# CUENTAS BANCARIAS
