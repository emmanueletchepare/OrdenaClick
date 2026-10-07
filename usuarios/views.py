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
# =========================================

def login_view(request):
    """Autentica al usuario y lo dirige a la selección de perfil."""
    if request.user.is_authenticated:
        return redirect("home")

    error = None

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            error = "Usuario o contraseña incorrectos."
        else:
            perfil, _ = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={
                    "nombre": user.first_name or user.username,
                    "apellido": user.last_name or "",
                    "estado_acceso": "activo"
                }
            )

            if perfil.estado_acceso == "bloqueado":
                error = "Tu acceso a OrdenaClick se encuentra bloqueado."
            elif perfil.estado_acceso == "pendiente":
                error = "Tu cuenta está pendiente de habilitación."
            else:
                login(request, user)
                return redirect("home")

    return render(
        request,
        "usuarios/auth/login.html",
        {"error": error}
    )


def registro_view(request):
    """Crea la cuenta de usuario y su perfil inicial de OrdenaClick."""
    if request.user.is_authenticated:
        return redirect("home")

    error = None

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        password2 = request.POST.get("password2") or ""
        nombre = (request.POST.get("nombre") or "").strip()
        apellido = (request.POST.get("apellido") or "").strip()

        if not username or not email or not password or not nombre or not apellido:
            error = "Completá todos los campos obligatorios."
        elif password != password2:
            error = "Las contraseñas no coinciden."
        elif User.objects.filter(username__iexact=username).exists():
            error = "Ese nombre de usuario ya está registrado."
        elif User.objects.filter(email__iexact=email).exists():
            error = "Ese correo electrónico ya está registrado."
        else:
            try:
                validate_email(email)
            except ValidationError:
                error = "Ingresá un correo electrónico válido."

        if error is None:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido
            )

            PerfilUsuario.objects.create(
                user=user,
                nombre=nombre,
                apellido=apellido,
                telefono_personal=(request.POST.get("telefono_personal") or "").strip(),
                telefono_laboral=(request.POST.get("telefono_laboral") or "").strip(),
                direccion_laboral=(request.POST.get("direccion_laboral") or "").strip(),
                estado_acceso="demo"
            )

            return redirect("login")

    return render(
        request,
        "usuarios/auth/register.html",
        {"error": error}
    )


@login_required
def logout_view(request):
    """Cierra la sesión actual y vuelve al login."""
    logout(request)
    return redirect("login")


@login_required
def home(request):
    """Muestra los perfiles de plataforma y avisa relaciones pendientes."""
    from usuarios.models import SolicitudRelacionEmpresa

    solicitudes_pendientes_count = SolicitudRelacionEmpresa.objects.filter(
        usuario_destino=request.user,
        estado=SolicitudRelacionEmpresa.ESTADO_PENDIENTE,
    ).count()

    return render(
        request,
        "usuarios/cuenta/home.html",
        {
            "solicitudes_pendientes_count": solicitudes_pendientes_count,
        },
    )


@login_required
def seleccionar_perfil(request, perfil):
    """Dirige al panel correspondiente al perfil elegido."""
    destinos = {
        "administrador": "panel_admin",
        "colaborador": "panel_colaborador",
        "contable": "panel_contable",
        "legal": "panel_legal",
        "relaciones": "panel_relaciones",
    }

    destino = destinos.get(perfil)

    if destino is None:
        return redirect("home")

    return redirect(destino)


@login_required
def modificar_usuario(request):
    """Permite al usuario actualizar sus datos personales y contraseña."""
    perfil, _ = PerfilUsuario.objects.get_or_create(
        user=request.user,
        defaults={
            "nombre": request.user.first_name or request.user.username,
            "apellido": request.user.last_name or "",
            "estado_acceso": "activo"
        }
    )

    error = None

    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        apellido = (request.POST.get("apellido") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        if not nombre or not apellido or not email:
            error = "Nombre, apellido y correo electrónico son obligatorios."
        elif User.objects.filter(email__iexact=email).exclude(id=request.user.id).exists():
            error = "Ese correo electrónico ya está registrado."
        else:
            try:
                validate_email(email)
            except ValidationError:
                error = "Ingresá un correo electrónico válido."

        if error is None:
            request.user.first_name = nombre
            request.user.last_name = apellido
            request.user.email = email

            if password:
                request.user.set_password(password)

            request.user.save()

            perfil.nombre = nombre
            perfil.apellido = apellido
            perfil.telefono_personal = (request.POST.get("telefono_personal") or "").strip()
            perfil.telefono_laboral = (request.POST.get("telefono_laboral") or "").strip()
            perfil.direccion_laboral = (request.POST.get("direccion_laboral") or "").strip()
            perfil.save()

            if password:
                user = authenticate(
                    request,
                    username=request.user.username,
                    password=password
                )
                if user is not None:
                    login(request, user)

            return redirect("home")

    return render(
        request,
        "usuarios/cuenta/modificar_usuario.html",
        {
            "perfil": perfil,
            "error": error
        }
    )


@login_required
def baja_usuario(request):
    """Desactiva la cuenta sin eliminar físicamente su historial."""
    if request.method != "POST":
        return redirect("home")

    perfil, _ = PerfilUsuario.objects.get_or_create(
        user=request.user,
        defaults={
            "nombre": request.user.first_name or request.user.username,
            "apellido": request.user.last_name or ""
        }
    )

    perfil.estado_acceso = "bloqueado"
    perfil.save(update_fields=["estado_acceso", "actualizado"])

    request.user.is_active = False
    request.user.save(update_fields=["is_active"])

    logout(request)
    return redirect("login")


@login_required
def panel_colaborador(request):
    """Muestra la entrada al perfil Colaborador."""
    return render(
        request,
        "usuarios/perfiles/colaborador/panel.html"
    )


@login_required
def panel_contable(request):
    """Muestra la entrada al perfil Contable."""
    return render(
        request,
        "usuarios/perfiles/contable/panel.html"
    )


@login_required
def panel_legal(request):
    """Muestra la entrada al perfil Legal."""
    return render(
        request,
        "usuarios/perfiles/legal/panel.html"
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

@login_required
def guardar_movimiento(request):
    """
    Guarda un Movimiento creado desde Carga Simple.

    Permite registrar:

    - Movimiento sin Pago.
    - Uno o varios Pagos.
    - Efectivo.
    - Transferencias.
    - Depósitos.
    - Tarjetas.
    - Cheques / e-Cheqs.
    - Retenciones.
    - Aplicaciones de Pago.

    Movimiento, Pagos, Aplicaciones, Operaciones Bancarias,
    Tarjetas, Cheques y Retenciones se guardan dentro
    de una única transacción atómica.
    """
    from usuarios.services.financiero import (
        crear_pago_validado_movimiento,
        validar_importe_aplicable,
        validar_pago_movimiento,
    )

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido.",
            },
            status=405,
        )


    try:

        # =========================================
        # DATOS GENERALES
        # =========================================

        empresa_id = request.POST.get(
            "empresa"
        )

        tipo_gasto_id = request.POST.get(
            "tipo_gasto"
        )

        proveedor_id = request.POST.get(
            "proveedor"
        )

        centro_operativo_id = request.POST.get(
            "centro_operativo"
        )

        recurso_operativo_id = request.POST.get(
            "recurso_operativo"
        )

        fecha_registro = request.POST.get(
            "fecha_registro"
        )

        fecha_vencimiento = request.POST.get(
            "fecha_vencimiento"
        )

        modalidad_pago = (
            request.POST.get(
                "modalidad_pago"
            )
            or "Manual"
        ).strip()

        cuenta_debito_id = (
            request.POST.get(
                "cuenta_debito"
            )
            or ""
        ).strip()

        tipo_comprobante = (
            request.POST.get(
                "tipo_comprobante"
            )
            or ""
        ).strip()

        numero_comprobante = (
            request.POST.get(
                "numero_comprobante"
            )
            or ""
        ).strip()


        # =========================================
        # VALIDACIONES GENERALES
        # =========================================

        if not empresa_id:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": "Seleccione una empresa.",
                },
                status=400,
            )


        if not tipo_gasto_id:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": "Seleccione un tipo de gasto.",
                },
                status=400,
            )


        if not proveedor_id:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": "Seleccione un proveedor.",
                },
                status=400,
            )


        if not fecha_registro:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": "Ingrese la fecha del registro.",
                },
                status=400,
            )


        # =========================================
        # EMPRESA
        # =========================================

        empresa = Empresa.objects.filter(
            id=empresa_id
        ).first()


        if not empresa:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "La empresa seleccionada no existe."
                    ),
                },
                status=404,
            )

        # =========================================
        # PREVISIÓN DE PAGO
        # =========================================

        modalidades_validas = {
            valor
            for valor, etiqueta
            in Movimiento.MODALIDADES_PAGO
        }


        if modalidad_pago not in modalidades_validas:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "La forma prevista de pago "
                        "no es válida."
                    ),
                },
                status=400,
            )


        cuenta_debito = None


        if modalidad_pago == "DebitoAutomatico":

            if not cuenta_debito_id:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Seleccione la cuenta prevista "
                            "para el débito automático."
                        ),
                    },
                    status=400,
                )


            cuenta_debito = (
                CuentaBancaria.objects.filter(
                    id=cuenta_debito_id,
                    empresa=empresa,
                    activo=True,
                    moneda="ARS",
                ).first()
            )


            if not cuenta_debito:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "La cuenta seleccionada para "
                            "el débito automático no es válida."
                        ),
                    },
                    status=400,
                )


        elif cuenta_debito_id:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Un Pago manual no debe tener "
                        "una cuenta prevista para débito."
                    ),
                },
                status=400,
            )

        # =========================================
        # EJERCICIO ABIERTO
        # =========================================

        ejercicio = empresa.ejercicios.filter(
            estado="Abierto"
        ).first()


        if not ejercicio:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "La empresa no tiene un ejercicio abierto."
                    ),
                },
                status=400,
            )


        # =========================================
        # TIPO DE GASTO
        # =========================================

        tipo_gasto = TipoGasto.objects.filter(
            id=tipo_gasto_id,
            empresa=empresa,
            activo=True,
        ).first()


        if not tipo_gasto:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El tipo de gasto no es válido."
                    ),
                },
                status=400,
            )


        # =========================================
        # PROVEEDOR
        # =========================================

        proveedor = Proveedor.objects.filter(
            id=proveedor_id,
            empresa=empresa,
            activo=True,
        ).first()


        if not proveedor:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El proveedor no es válido."
                    ),
                },
                status=400,
            )

        # =========================================
        # COMPROBANTE
        # =========================================

        tipos_comprobante_validos = {
            "A",
            "B",
            "C",
            "X",
        }


        if tipo_comprobante not in tipos_comprobante_validos:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Seleccione un tipo de comprobante válido."
                    ),
                },
                status=400,
            )


        if not re.fullmatch(
            r"\d{4}-\d{8}",
            numero_comprobante
        ):

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El número de comprobante no tiene "
                        "un formato válido."
                    ),
                },
                status=400,
            )


        comprobante_duplicado = (
            Movimiento.objects.filter(
                empresa=empresa,
                proveedor=proveedor,
                tipo_comprobante=tipo_comprobante,
                numero_comprobante=numero_comprobante,
            )
            .exists()
        )


        if comprobante_duplicado:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Ese comprobante ya fue registrado "
                        "para este proveedor."
                    ),
                },
                status=400,
            )

        # =========================================
        # CENTRO OPERATIVO
        # =========================================

        centro_operativo = None


        if centro_operativo_id:

            centro_operativo = (
                CentroOperativo.objects.filter(
                    id=centro_operativo_id,
                    empresa=empresa,
                    activo=True,
                ).first()
            )


            if not centro_operativo:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Centro Operativo no es válido."
                        ),
                    },
                    status=400,
                )


        # =========================================
        # RECURSO OPERATIVO
        # =========================================

        recurso_operativo = None


        if recurso_operativo_id:

            recurso_operativo = (
                RecursoOperativo.objects.filter(
                    id=recurso_operativo_id,
                    empresa=empresa,
                    activo=True,
                ).first()
            )


            if not recurso_operativo:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Recurso Operativo no es válido."
                        ),
                    },
                    status=400,
                )


        # =========================================
        # DECIMALES
        # =========================================

        from decimal import (
            Decimal,
            InvalidOperation
        )


        def decimal_post(nombre):
            """
            Convierte un importe recibido mediante POST
            en un Decimal seguro para persistencia.
            """

            valor = (
                request.POST.get(nombre)
                or "0"
            )


            try:

                return Decimal(
                    str(valor)
                )


            except InvalidOperation:

                return Decimal("0")


        # =========================================
        # IMPORTES DEL MOVIMIENTO
        # =========================================

        neto_gravado = decimal_post(
            "neto_gravado"
        )

        no_gravado_exento = decimal_post(
            "no_gravado_exento"
        )

        iva_21 = decimal_post(
            "iva_21"
        )

        iva_27 = decimal_post(
            "iva_27"
        )

        iva_105 = decimal_post(
            "iva_105"
        )

        recargos_intereses = decimal_post(
            "recargos_intereses"
        )

        ajuste_redondeo = decimal_post(
            "ajuste_redondeo"
        )

        percepcion_iibb = decimal_post(
            "percepcion_iibb"
        )

        percepcion_iva = decimal_post(
            "percepcion_iva"
        )

        percepcion_ganancias = decimal_post(
            "percepcion_ganancias"
        )

        percepcion_tasas_municipales = (
            decimal_post(
                "percepcion_tasas_municipales"
            )
        )

        total = decimal_post(
            "total"
        )


        if total <= 0:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El total del registro debe ser mayor a cero."
                    ),
                },
                status=400,
            )


        # =========================================
        # PAGOS
        # =========================================

        pagos_raw = (
            request.POST.get(
                "pagos"
            )
            or "[]"
        )


        try:

            pagos = json.loads(
                pagos_raw
            )

        except json.JSONDecodeError:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Los datos de los Pagos no son válidos."
                    ),
                },
                status=400,
            )


        if not isinstance(
            pagos,
            list
        ):

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El formato de los Pagos no es válido."
                    ),
                },
                status=400,
            )


        # =========================================
        # VALIDAR PAGOS
        # =========================================

        pagos_validados = []

        total_aplicado = Decimal(
            "0.00"
        )


        for pago_datos in pagos:

            try:

                pago_validado = (
                    validar_pago_movimiento(
                        empresa=empresa,
                        pago_datos=pago_datos,
                        archivos=request.FILES,
                    )
                )

            except ValueError as error:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": str(error),
                    },
                    status=400,
                )


            total_aplicado += (
                pago_validado[
                    "importe_pago"
                ]
            )


            pagos_validados.append(
                pago_validado
            )
            
        # =========================================
        # DÉBITO AUTOMÁTICO REAL
        # =========================================
        #
        # La modalidad DebitoAutomatico del Movimiento
        # representa solamente la previsión de pago.
        #
        # Este bloque registra el débito únicamente
        # cuando el usuario confirmó que efectivamente
        # ocurrió.
        #
        # El importe recibido desde el navegador es el
        # total efectivamente debitado por el banco.
        #
        # Si existe interés por mora:
        #
        # importe aplicado al Movimiento
        #     = saldo pendiente
        #
        # intereses_mora
        #     = importe debitado - saldo pendiente
        #
        # El interés nunca incrementa la AplicacionPago.
        #

        debito_automatico_validado = None

        debito_automatico_raw = (
            request.POST.get(
                "debito_automatico"
            )
            or "null"
        )

        try:

            debito_automatico = json.loads(
                debito_automatico_raw
            )

        except json.JSONDecodeError:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Los datos del débito automático "
                        "no son válidos."
                    ),
                },
                status=400,
            )


        if debito_automatico is not None:

            if modalidad_pago != "DebitoAutomatico":

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "No puede registrarse un débito automático "
                            "en un Movimiento configurado como Pago manual."
                        ),
                    },
                    status=400,
                )


            if pagos_validados:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Un Movimiento con débito automático "
                            "no puede contener simultáneamente "
                            "Pagos manuales en esta carga."
                        ),
                    },
                    status=400,
                )


            if not isinstance(
                debito_automatico,
                dict
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El formato del débito automático "
                            "no es válido."
                        ),
                    },
                    status=400,
                )


            # =====================================
            # FECHA REAL DEL DÉBITO
            # =====================================

            fecha_debito = (
                debito_automatico.get(
                    "fecha"
                )
                or ""
            ).strip()


            if not fecha_debito:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Ingrese la fecha real del débito."
                        ),
                    },
                    status=400,
                )


            try:

                fecha_debito_validada = (
                    datetime.strptime(
                        fecha_debito,
                        "%Y-%m-%d"
                    ).date()
                )

            except ValueError:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "La fecha del débito automático "
                            "no es válida."
                        ),
                    },
                    status=400,
                )

            # =====================================
            # FECHA DEL GASTO
            # =====================================

            try:

                fecha_registro_validada = (
                    datetime.strptime(
                        fecha_registro,
                        "%Y-%m-%d"
                    ).date()
                )

            except ValueError:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "La fecha del registro "
                            "no es válida."
                        ),
                    },
                    status=400,
                )


            if (
                fecha_debito_validada <
                fecha_registro_validada
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "La fecha real del débito "
                            "no puede ser anterior a "
                            "la fecha del gasto."
                        ),
                    },
                    status=400,
                )

            # =====================================
            # IMPORTE REAL DEBITADO
            # =====================================

            try:

                importe_debitado = Decimal(
                    str(
                        debito_automatico.get(
                            "importe_debitado",
                            0
                        )
                    )
                )

            except (
                InvalidOperation,
                TypeError,
                ValueError
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El importe del débito automático "
                            "no es válido."
                        ),
                    },
                    status=400,
                )


            if importe_debitado <= 0:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El importe debitado debe ser "
                            "mayor a cero."
                        ),
                    },
                    status=400,
                )


            confirmar_intereses_mora = (
                debito_automatico.get(
                    "confirmar_intereses_mora"
                )
                is True
            )


            # =====================================
            # IMPORTE APLICADO / INTERÉS
            # =====================================

            intereses_mora = Decimal(
                "0.00"
            )

            importe_aplicado_debito = (
                importe_debitado
            )


            if importe_debitado > total:

                if not fecha_vencimiento:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "El débito supera el total del registro "
                                "y no existe una fecha de vencimiento "
                                "que permita clasificar la diferencia "
                                "como interés por mora."
                            ),
                        },
                        status=400,
                    )


                try:

                    fecha_vencimiento_validada = (
                        datetime.strptime(
                            fecha_vencimiento,
                            "%Y-%m-%d"
                        ).date()
                    )

                except ValueError:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "La fecha de vencimiento "
                                "no es válida."
                            ),
                        },
                        status=400,
                    )


                if (
                    fecha_debito_validada <=
                    fecha_vencimiento_validada
                ):

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "El débito supera el total del registro, "
                                "pero no ocurrió después del vencimiento."
                            ),
                        },
                        status=400,
                    )


                if not confirmar_intereses_mora:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "La diferencia del débito debe "
                                "confirmarse como interés por mora "
                                "antes de guardar."
                            ),
                        },
                        status=400,
                    )


                importe_aplicado_debito = (
                    total
                )

                intereses_mora = (
                    importe_debitado -
                    total
                )


            total_aplicado += (
                importe_aplicado_debito
            )


            debito_automatico_validado = {

                "fecha":
                    fecha_debito_validada,

                "importe_debitado":
                    importe_debitado,

                "importe_aplicado":
                    importe_aplicado_debito,

                "intereses_mora":
                    intereses_mora,

            }


        # =========================================
        # CONTROL DE SOBREAPLICACIÓN
        # =========================================
        #
        # En una Carga Simple nueva el saldo
        # disponible para aplicar coincide con el
        # total documental del Movimiento.
        #
        # La validación pertenece al servicio
        # financiero común para que la misma regla
        # pueda reutilizarse luego en edición,
        # Carga Planificada y otros circuitos.
        # =========================================

        try:

            validar_importe_aplicable(
                saldo_pendiente=total,
                importe_aplicar=total_aplicado,
            )

        except ValueError as error:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": str(error),
                },
                status=400,
            )


        # =========================================
        # ESTADO DEL MOVIMIENTO
        # =========================================

        if total_aplicado == Decimal(
            "0.00"
        ):

            estado_movimiento = (
                "Pendiente"
            )


        elif total_aplicado < total:

            estado_movimiento = (
                "Parcial"
            )


        else:

            estado_movimiento = (
                "Pagado"
            )


        # =========================================
        # ARCHIVO DEL MOVIMIENTO
        # =========================================

        archivo = request.FILES.get(
            "archivo"
        )


        # =========================================
        # TRANSACCIÓN ATÓMICA
        # =========================================

        with transaction.atomic():

            # =====================================
            # MOVIMIENTO
            # =====================================

            movimiento = Movimiento.objects.create(

                empresa=
                    empresa,

                ejercicio=
                    ejercicio,

                tipo_gasto=
                    tipo_gasto,

                proveedor=
                    proveedor,

                centro_operativo=
                    centro_operativo,

                recurso_operativo=
                    recurso_operativo,

                descripcion="",

                fecha_registro=
                    fecha_registro,

                fecha_vencimiento=(
                    fecha_vencimiento
                    or None
                ),

                modalidad_pago=
                    modalidad_pago,

                cuenta_debito=
                    cuenta_debito,

                tipo_comprobante=
                    tipo_comprobante,

                numero_comprobante=
                    numero_comprobante,

                moneda=
                    "ARS",

                neto_gravado=
                    neto_gravado,

                no_gravado_exento=
                    no_gravado_exento,

                iva_21=
                    iva_21,

                iva_27=
                    iva_27,

                iva_105=
                    iva_105,

                recargos_intereses=
                    recargos_intereses,

                ajuste_redondeo=
                    ajuste_redondeo,

                percepcion_iibb=
                    percepcion_iibb,

                percepcion_iva=
                    percepcion_iva,

                percepcion_ganancias=
                    percepcion_ganancias,

                percepcion_tasas_municipales=(
                    percepcion_tasas_municipales
                ),

                total=
                    total,

                # Compatibilidad temporal.
                importe=
                    total,

                estado=
                    estado_movimiento,

                archivo=
                    archivo,
            )


            # =====================================
            # PAGOS
            # =====================================

            pagos_creados = []

            operaciones_creadas = []

            tarjetas_creadas = []

            cheques_creados = []

            retenciones_creadas = []

            debitos_automaticos_creados = []


            for pago_datos in pagos_validados:

                resultado_pago = (
                    crear_pago_validado_movimiento(
                        empresa=empresa,
                        movimiento=movimiento,
                        pago_datos=pago_datos,
                    )
                )


                pagos_creados.append(
                    resultado_pago[
                        "pago_id"
                    ]
                )


                operaciones_creadas.extend(
                    resultado_pago[
                        "operaciones_bancarias_ids"
                    ]
                )


                tarjetas_creadas.extend(
                    resultado_pago[
                        "tarjetas_ids"
                    ]
                )


                cheques_creados.extend(
                    resultado_pago[
                        "cheques_ids"
                    ]
                )


                retenciones_creadas.extend(
                    resultado_pago[
                        "retenciones_ids"
                    ]
                )

            # =====================================
            # DÉBITO AUTOMÁTICO REAL
            # =====================================

            debitos_automaticos_creados = []


            if debito_automatico_validado:

                pago_debito = Pago.objects.create(

                    empresa=
                        empresa,

                    fecha=
                        debito_automatico_validado[
                            "fecha"
                        ],

                    importe_efectivo=
                        Decimal("0.00"),

                )


                debito_creado = (
                    DebitoAutomaticoPago.objects.create(

                        pago=
                            pago_debito,

                        cuenta_bancaria=
                            cuenta_debito,

                        importe=
                            debito_automatico_validado[
                                "importe_debitado"
                            ],

                        intereses_mora=
                            debito_automatico_validado[
                                "intereses_mora"
                            ],

                        fecha_debito=
                            debito_automatico_validado[
                                "fecha"
                            ],

                    )
                )


                AplicacionPago.objects.create(

                    pago=
                        pago_debito,

                    movimiento=
                        movimiento,

                    importe=
                        debito_automatico_validado[
                            "importe_aplicado"
                        ],

                )


                pagos_creados.append(
                    pago_debito.id
                )


                debitos_automaticos_creados.append(
                    debito_creado.id
                )

        # =========================================
        # RESPUESTA
        # =========================================

        return JsonResponse(
            {
                "ok": True,

                "mensaje": (
                    "Registro guardado correctamente."
                ),

                "movimiento_id":
                    movimiento.id,

                "pagos_ids":
                    pagos_creados,

                "operaciones_bancarias_ids":
                    operaciones_creadas,

                "tarjetas_ids":
                    tarjetas_creadas,

                "cheques_ids":
                    cheques_creados,

                "retenciones_ids":
                    retenciones_creadas,

                "total_aplicado":
                    str(
                        total_aplicado
                    ),

                "estado":
                    estado_movimiento,
            }
        )


    except Exception as error:

        print(
            "Error guardando Movimiento:",
            error,
        )


        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Ocurrió un error al guardar el registro."
                ),
            },
            status=500,
        )

@login_required
def actualizar_movimiento(request):
    """
    Actualiza un Movimiento existente y puede registrar nuevos Pagos.

    Si el Movimiento todavía no tiene AplicacionPago histórica,
    sus datos pueden modificarse normalmente.

    Una vez aplicado al menos un Pago, los datos estructurales del
    Movimiento quedan bloqueados. Sólo pueden modificarse la forma
    prevista de pago y su cuenta de débito asociada, adjuntarse una
    factura y registrarse nuevos Pagos.

    Para modificar otros datos de un Movimiento con Pagos aplicados,
    primero deben eliminarse o revertirse esos Pagos.

    La actualización y los nuevos Pagos se procesan dentro de una
    única transacción.
    """

    import json
    import logging

    from decimal import Decimal, InvalidOperation

    from usuarios.services.financiero import (
        crear_pago_validado_movimiento,
        total_aplicado_movimiento,
        validar_importe_aplicable,
        validar_pago_movimiento,
    )

    from usuarios.services.seguridad import (
        obtener_empresa_autorizada,
    )


    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido.",
            },
            status=405,
        )


    empresa_id = (
        request.POST.get("empresa")
        or ""
    ).strip()

    movimiento_id = (
        request.POST.get("movimiento")
        or ""
    ).strip()

    pagos_raw = (
        request.POST.get("pagos")
        or ""
    ).strip()


    pagos = []


    if pagos_raw:

        try:

            pagos = json.loads(
                pagos_raw
            )

        except json.JSONDecodeError:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Los datos de los Pagos no son válidos."
                    ),
                },
                status=400,
            )


        if not isinstance(
            pagos,
            list
        ):

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El formato de los Pagos no es válido."
                    ),
                },
                status=400,
            )

    if not empresa_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Seleccione una empresa.",
            },
            status=400,
        )


    if not movimiento_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "No se indicó el Movimiento a modificar.",
            },
            status=400,
        )


    empresa = obtener_empresa_autorizada(
        request.user,
        empresa_id,
    )


    tipo_gasto_id = (
        request.POST.get("tipo_gasto")
        or ""
    ).strip()

    proveedor_id = (
        request.POST.get("proveedor")
        or ""
    ).strip()

    centro_operativo_id = (
        request.POST.get("centro_operativo")
        or ""
    ).strip()

    recurso_operativo_id = (
        request.POST.get("recurso_operativo")
        or ""
    ).strip()

    fecha_registro = (
        request.POST.get("fecha_registro")
        or ""
    ).strip()

    fecha_vencimiento = (
        request.POST.get("fecha_vencimiento")
        or ""
    ).strip()

    modalidad_pago = (
        request.POST.get("modalidad_pago")
        or "Manual"
    ).strip()

    cuenta_debito_id = (
        request.POST.get("cuenta_debito")
        or ""
    ).strip()

    tipo_comprobante = (
        request.POST.get("tipo_comprobante")
        or ""
    ).strip()

    numero_comprobante = (
        request.POST.get("numero_comprobante")
        or ""
    ).strip()


    if not tipo_gasto_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Seleccione un tipo de gasto.",
            },
            status=400,
        )


    if not proveedor_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Seleccione un proveedor.",
            },
            status=400,
        )


    if not fecha_registro:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Ingrese la fecha del registro.",
            },
            status=400,
        )


    tipo_gasto = (
        TipoGasto.objects.filter(
            id=tipo_gasto_id,
            empresa=empresa,
            activo=True,
        ).first()
    )


    if not tipo_gasto:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "El tipo de gasto no es válido.",
            },
            status=400,
        )


    proveedor = (
        Proveedor.objects.filter(
            id=proveedor_id,
            empresa=empresa,
            activo=True,
        ).first()
    )


    if not proveedor:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "El proveedor no es válido.",
            },
            status=400,
        )


    tipos_comprobante_validos = {
        "A",
        "B",
        "C",
        "X",
    }


    if tipo_comprobante not in tipos_comprobante_validos:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Seleccione un tipo de comprobante válido."
                ),
            },
            status=400,
        )


    centro_operativo = None


    if centro_operativo_id:

        centro_operativo = (
            CentroOperativo.objects.filter(
                id=centro_operativo_id,
                empresa=empresa,
                activo=True,
            ).first()
        )


        if not centro_operativo:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El Centro Operativo no es válido."
                    ),
                },
                status=400,
            )


    recurso_operativo = None


    if recurso_operativo_id:

        recurso_operativo = (
            RecursoOperativo.objects.filter(
                id=recurso_operativo_id,
                empresa=empresa,
                activo=True,
            ).first()
        )


        if not recurso_operativo:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El Recurso Operativo no es válido."
                    ),
                },
                status=400,
            )


        if (
            centro_operativo and
            hasattr(
                recurso_operativo,
                "centro_operativo"
            ) and
            recurso_operativo.centro_operativo_id !=
            centro_operativo.id
        ):

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El Recurso Operativo no pertenece "
                        "al Centro Operativo seleccionado."
                    ),
                },
                status=400,
            )


    modalidades_validas = {
        valor
        for valor, etiqueta
        in Movimiento.MODALIDADES_PAGO
    }


    if modalidad_pago not in modalidades_validas:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "La forma prevista de pago no es válida."
                ),
            },
            status=400,
        )


    cuenta_debito = None


    if modalidad_pago == "DebitoAutomatico":

        if not cuenta_debito_id:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Seleccione la cuenta prevista "
                        "para el débito automático."
                    ),
                },
                status=400,
            )


        cuenta_debito = (
            CuentaBancaria.objects.filter(
                id=cuenta_debito_id,
                empresa=empresa,
                activo=True,
                moneda="ARS",
            ).first()
        )


        if not cuenta_debito:

            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "La cuenta seleccionada para "
                        "el débito automático no es válida."
                    ),
                },
                status=400,
            )


    elif cuenta_debito_id:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Un Pago manual no debe tener "
                    "una cuenta prevista para débito."
                ),
            },
            status=400,
        )


    def decimal_post(nombre):
        """
        Convierte un importe recibido mediante POST
        en Decimal para persistencia.
        """

        valor = (
            request.POST.get(nombre)
            or "0"
        )


        try:

            return Decimal(
                str(valor)
            )


        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):

            return Decimal("0")


    neto_gravado = decimal_post(
        "neto_gravado"
    )

    no_gravado_exento = decimal_post(
        "no_gravado_exento"
    )

    iva_21 = decimal_post(
        "iva_21"
    )

    iva_27 = decimal_post(
        "iva_27"
    )

    iva_105 = decimal_post(
        "iva_105"
    )

    recargos_intereses = decimal_post(
        "recargos_intereses"
    )

    ajuste_redondeo = decimal_post(
        "ajuste_redondeo"
    )

    percepcion_iibb = decimal_post(
        "percepcion_iibb"
    )

    percepcion_iva = decimal_post(
        "percepcion_iva"
    )

    percepcion_ganancias = decimal_post(
        "percepcion_ganancias"
    )

    percepcion_tasas_municipales = (
        decimal_post(
            "percepcion_tasas_municipales"
        )
    )

    total = decimal_post(
        "total"
    )


    if total <= Decimal("0.00"):

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "El total del registro debe ser mayor a cero."
                ),
            },
            status=400,
        )


    archivo = request.FILES.get(
        "archivo"
    )


    try:

        with transaction.atomic():

            movimiento = (
                Movimiento.objects
                .select_for_update()
                .filter(
                    id=movimiento_id,
                    empresa=empresa,
                )
                .first()
            )


            if not movimiento:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El Movimiento no existe "
                            "o no pertenece a la empresa."
                        ),
                    },
                    status=404,
                )


            if movimiento.estado == "Cancelado":

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Un Movimiento cancelado "
                            "no puede modificarse."
                        ),
                    },
                    status=400,
                )


            comprobante_original = (
                movimiento.numero_comprobante
                or ""
            ).strip()


            comprobante_original_normalizado = bool(
                re.fullmatch(
                    r"\d{4}-\d{8}",
                    comprobante_original,
                )
            )


            conserva_comprobante_legado = (
                not comprobante_original_normalizado
                and
                tipo_comprobante ==
                (movimiento.tipo_comprobante or "")
                and
                numero_comprobante ==
                comprobante_original
            )


            if (
                not conserva_comprobante_legado
                and
                not re.fullmatch(
                    r"\d{4}-\d{8}",
                    numero_comprobante,
                )
            ):

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El número de comprobante no tiene "
                            "un formato válido."
                        ),
                    },
                    status=400,
                )


            comprobante_duplicado = (
                Movimiento.objects.filter(
                    empresa=empresa,
                    proveedor=proveedor,
                    tipo_comprobante=
                        tipo_comprobante,
                    numero_comprobante=
                        numero_comprobante,
                )
                .exclude(
                    id=movimiento.id,
                )
                .exists()
            )


            if comprobante_duplicado:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "Ese comprobante ya fue registrado "
                            "para este proveedor."
                        ),
                    },
                    status=400,
                )


            total_aplicado_existente = (
                total_aplicado_movimiento(
                    movimiento
                )
            )

            # =========================================
            # PROTECCIÓN DEL MOVIMIENTO CON PAGOS
            # =========================================
            #
            # Una vez que existe al menos una
            # AplicacionPago histórica, el hecho
            # económico/documental queda cerrado.
            #
            # Sólo pueden modificarse:
            #
            # - la forma prevista de pago;
            # - la cuenta prevista de débito asociada;
            # - el archivo de factura;
            # - y pueden incorporarse nuevos Pagos.
            #
            # Para modificar cualquier otro dato,
            # primero deben eliminarse/revertirse
            # todos los Pagos aplicados.
            #
            if (
                total_aplicado_existente >
                Decimal("0.00")
            ):

                fecha_registro_actual = (
                    str(
                        movimiento.fecha_registro
                    )
                    if movimiento.fecha_registro
                    else ""
                )

                fecha_vencimiento_actual = (
                    str(
                        movimiento.fecha_vencimiento
                    )
                    if movimiento.fecha_vencimiento
                    else ""
                )


                estructura_modificada = any(
                    [
                        str(
                            movimiento.tipo_gasto_id
                            or ""
                        ) != tipo_gasto_id,

                        str(
                            movimiento.proveedor_id
                            or ""
                        ) != proveedor_id,

                        str(
                            movimiento.centro_operativo_id
                            or ""
                        ) != centro_operativo_id,

                        str(
                            movimiento.recurso_operativo_id
                            or ""
                        ) != recurso_operativo_id,

                        fecha_registro_actual !=
                            fecha_registro,

                        fecha_vencimiento_actual !=
                            fecha_vencimiento,

                        (
                            movimiento.tipo_comprobante
                            or ""
                        ) != tipo_comprobante,

                        (
                            movimiento.numero_comprobante
                            or ""
                        ) != numero_comprobante,

                        movimiento.neto_gravado !=
                            neto_gravado,

                        movimiento.no_gravado_exento !=
                            no_gravado_exento,

                        movimiento.iva_21 !=
                            iva_21,

                        movimiento.iva_27 !=
                            iva_27,

                        movimiento.iva_105 !=
                            iva_105,

                        movimiento.recargos_intereses !=
                            recargos_intereses,

                        movimiento.ajuste_redondeo !=
                            ajuste_redondeo,

                        movimiento.percepcion_iibb !=
                            percepcion_iibb,

                        movimiento.percepcion_iva !=
                            percepcion_iva,

                        movimiento.percepcion_ganancias !=
                            percepcion_ganancias,

                        movimiento.percepcion_tasas_municipales !=
                            percepcion_tasas_municipales,

                        movimiento.total !=
                            total,
                    ]
                )


                if estructura_modificada:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "El Movimiento ya tiene Pagos "
                                "aplicados. Para modificar sus "
                                "datos primero debe eliminar "
                                "los Pagos realizados."
                            ),
                        },
                        status=400,
                    )

            try:

                validar_importe_aplicable(
                    saldo_pendiente=total,
                    importe_aplicar=
                        total_aplicado_existente,
                )


            except ValueError:

                return JsonResponse(
                    {
                        "ok": False,
                        "mensaje": (
                            "El total del registro no puede "
                            "ser menor al importe que ya fue "
                            "aplicado mediante Pagos."
                        ),
                    },
                    status=400,
                )


            saldo_disponible_pagos = (
                total -
                total_aplicado_existente
            )


            pagos_validados = []

            importe_total_nuevo = Decimal(
                "0.00"
            )


            if pagos:

                if modalidad_pago != "Manual":

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": (
                                "Los Pagos manuales sólo pueden "
                                "registrarse cuando la forma prevista "
                                "de pago es Manual."
                            ),
                        },
                        status=400,
                    )


                for pago_datos in pagos:

                    try:

                        pago_validado = (
                            validar_pago_movimiento(
                                empresa=empresa,
                                pago_datos=pago_datos,
                                archivos=request.FILES,
                            )
                        )

                    except ValueError as error:

                        return JsonResponse(
                            {
                                "ok": False,
                                "mensaje": str(error),
                            },
                            status=400,
                        )


                    pagos_validados.append(
                        pago_validado
                    )

                    importe_total_nuevo += (
                        pago_validado[
                            "importe_pago"
                        ]
                    )


                try:

                    validar_importe_aplicable(
                        saldo_pendiente=
                            saldo_disponible_pagos,
                        importe_aplicar=
                            importe_total_nuevo,
                    )

                except ValueError as error:

                    return JsonResponse(
                        {
                            "ok": False,
                            "mensaje": str(error),
                        },
                        status=400,
                    )


            total_aplicado_nuevo = (
                total_aplicado_existente +
                importe_total_nuevo
            )


            saldo_nuevo = (
                total -
                total_aplicado_nuevo
            )

            if (
                total_aplicado_nuevo <=
                Decimal("0.00")
            ):

                estado_movimiento = (
                    "Pendiente"
                )


            elif saldo_nuevo > Decimal("0.00"):

                estado_movimiento = (
                    "Parcial"
                )


            else:

                estado_movimiento = (
                    "Pagado"
                )


            movimiento.tipo_gasto = (
                tipo_gasto
            )

            movimiento.proveedor = (
                proveedor
            )

            movimiento.centro_operativo = (
                centro_operativo
            )

            movimiento.recurso_operativo = (
                recurso_operativo
            )

            movimiento.fecha_registro = (
                fecha_registro
            )

            movimiento.fecha_vencimiento = (
                fecha_vencimiento
                or None
            )

            movimiento.modalidad_pago = (
                modalidad_pago
            )

            movimiento.cuenta_debito = (
                cuenta_debito
            )

            movimiento.tipo_comprobante = (
                tipo_comprobante
            )

            movimiento.numero_comprobante = (
                numero_comprobante
            )

            movimiento.neto_gravado = (
                neto_gravado
            )

            movimiento.no_gravado_exento = (
                no_gravado_exento
            )

            movimiento.iva_21 = (
                iva_21
            )

            movimiento.iva_27 = (
                iva_27
            )

            movimiento.iva_105 = (
                iva_105
            )

            movimiento.recargos_intereses = (
                recargos_intereses
            )

            movimiento.ajuste_redondeo = (
                ajuste_redondeo
            )

            movimiento.percepcion_iibb = (
                percepcion_iibb
            )

            movimiento.percepcion_iva = (
                percepcion_iva
            )

            movimiento.percepcion_ganancias = (
                percepcion_ganancias
            )

            movimiento.percepcion_tasas_municipales = (
                percepcion_tasas_municipales
            )

            movimiento.total = (
                total
            )

            # Compatibilidad temporal con el campo
            # histórico importe.
            movimiento.importe = (
                total
            )

            movimiento.estado = (
                estado_movimiento
            )


            if archivo:

                movimiento.archivo = (
                    archivo
                )


            campos_actualizados = [
                "tipo_gasto",
                "proveedor",
                "centro_operativo",
                "recurso_operativo",
                "fecha_registro",
                "fecha_vencimiento",
                "modalidad_pago",
                "cuenta_debito",
                "tipo_comprobante",
                "numero_comprobante",
                "neto_gravado",
                "no_gravado_exento",
                "iva_21",
                "iva_27",
                "iva_105",
                "recargos_intereses",
                "ajuste_redondeo",
                "percepcion_iibb",
                "percepcion_iva",
                "percepcion_ganancias",
                "percepcion_tasas_municipales",
                "total",
                "importe",
                "estado",
            ]


            if archivo:

                campos_actualizados.append(
                    "archivo"
                )


            movimiento.save(
                update_fields=
                    campos_actualizados
            )

            resultados_pagos = []


            for pago_validado in pagos_validados:

                resultado_pago = (
                    crear_pago_validado_movimiento(
                        empresa=empresa,
                        movimiento=movimiento,
                        pago_datos=pago_validado,
                    )
                )

                resultados_pagos.append(
                    resultado_pago
                )

        return JsonResponse(
            {
                "ok": True,
                "mensaje": (
                    "Movimiento actualizado correctamente."
                ),
                "movimiento_id":
                    movimiento.id,
                "total":
                    str(total),
                "total_aplicado":
                    str(
                        total_aplicado_nuevo
                    ),
                "pagos_ids": [
                    resultado["pago_id"]
                    for resultado
                    in resultados_pagos
                ],
                "saldo_pendiente":
                    str(saldo_nuevo),
                "estado":
                    estado_movimiento,
            }
        )


    except Exception as error:

        print(
            "Error actualizando Movimiento:",
            error,
        )


        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "Ocurrió un error al actualizar "
                    "el Movimiento."
                ),
            },
            status=500,
        )
