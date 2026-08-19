from django.shortcuts import (
    render,
    redirect
)

from django.contrib.auth import (
    authenticate,
    login,
    logout
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from django.http import HttpResponse

from django.conf import settings

from django.utils import timezone

from datetime import (
    datetime,
    timedelta
)

from io import BytesIO

from django.core.exceptions import ValidationError
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
    CentroOperativo,
    Banco,
    CuentaBancaria,
    Tarjeta,
    GestionClave,
    RecursoOperativo,
    RecursoOperativoCentro,
    Proveedor,
    PerfilUsuario
)

from .seguridad_claves import (
    cifrar_clave,
    descifrar_clave
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
        "usuarios/login.html",
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
        "usuarios/register.html",
        {"error": error}
    )


@login_required
def logout_view(request):
    """Cierra la sesión actual y vuelve al login."""
    logout(request)
    return redirect("login")


@login_required
def home(request):
    """Muestra los cuatro perfiles desde los que puede operar el usuario."""
    return render(
        request,
        "usuarios/home.html"
    )


@login_required
def seleccionar_perfil(request, perfil):
    """Dirige al panel correspondiente al perfil elegido."""
    destinos = {
        "administrador": "panel_admin",
        "colaborador": "panel_colaborador",
        "contable": "panel_contable",
        "legal": "panel_legal",
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
        "usuarios/modificar_usuario.html",
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
        "usuarios/panel_colaborador.html"
    )


@login_required
def panel_contable(request):
    """Muestra la entrada al perfil Contable."""
    return render(
        request,
        "usuarios/panel_contable.html"
    )


@login_required
def panel_legal(request):
    """Muestra la entrada al perfil Legal."""
    return render(
        request,
        "usuarios/panel_legal.html"
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
            empresa_actual = Empresa.objects.get(id=empresa_id)

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

    empresa_existente = request.session.get(
        "empresa_existente"
    )

    request.session.pop(
        "empresa_existente",
        None
    )

    empresas = Empresa.objects.all().order_by(
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

    'usuarios/panel_admin.html',

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

def guardar_banco(request):

    if request.method != "POST":
        return JsonResponse(
            {"ok": False}
        )

    empresa = Empresa.objects.get(
        id=request.POST.get("empresa")
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre."
        })

    if Banco.objects.filter(
        empresa=empresa,
        nombre=nombre,
        activo=True
    ).exists():

        return JsonResponse({
            "ok": False,
            "mensaje": "Ese banco ya existe."
        })

    banco = Banco.objects.create(

        empresa=empresa,

        nombre=nombre
    )

    return JsonResponse({

        "ok": True,

        "banco": {
            "id": banco.id,
            "nombre": banco.nombre
        }

    })


def listar_bancos(request):

    empresa_id = request.GET.get("empresa")

    empresa = Empresa.objects.get(
        id=empresa_id
    )

    bancos = Banco.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by("nombre")

    html = render_to_string(

        "usuarios/bancos.html",

        {

            "empresa": empresa,
            "bancos": bancos

        },

        request=request

    )

    return JsonResponse({

    "html": html,

    "bancos": [

        {
            "id": banco.id,
            "nombre": banco.nombre
        }

        for banco in bancos

    ]

    })

def modificar_banco(request):

    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    banco_id = request.POST.get("banco")
    empresa_id = request.POST.get("empresa")

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    if not nombre:
        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese el nombre del banco."
        })

    try:
        banco = Banco.objects.get(
            id=banco_id,
            empresa_id=empresa_id,
            activo=True
        )

    except Banco.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "mensaje": "El banco no existe."
        }, status=404)

    if Banco.objects.filter(
        empresa_id=empresa_id,
        nombre=nombre,
        activo=True
    ).exclude(id=banco.id).exists():

        return JsonResponse({
            "ok": False,
            "mensaje": "Ya existe otro banco con ese nombre."
        })

    banco.nombre = nombre
    banco.save(update_fields=["nombre"])

    return JsonResponse({
        "ok": True
    })


def eliminar_banco(request):

    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    banco_id = request.POST.get("banco")
    empresa_id = request.POST.get("empresa")

    try:
        banco = Banco.objects.get(
            id=banco_id,
            empresa_id=empresa_id,
            activo=True
        )

    except Banco.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "mensaje": "El banco no existe."
        }, status=404)

    banco.activo = False
    banco.save(update_fields=["activo"])

    return JsonResponse({
        "ok": True
    })

# =========================================
# CUENTAS BANCARIAS
# =========================================

def listar_cuentas_bancarias(request):
    """
    Devuelve el ABM de cuentas bancarias correspondiente
    a la empresa activa.
    """

    empresa_id = request.GET.get(
        "empresa"
    )

    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La empresa no existe."
            },
            status=404
        )

    cuentas = CuentaBancaria.objects.filter(
        empresa=empresa,
        activo=True
    ).select_related(
        "banco"
    ).order_by(
        "banco__nombre",
        "nombre"
    )

    bancos = Banco.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by(
        "nombre"
    )

    html = render_to_string(
        "usuarios/cuentas_bancarias.html",
        {
            "empresa": empresa,
            "cuentas": cuentas,
            "bancos": bancos,
            "tipos_cuenta": CuentaBancaria.TIPOS_CUENTA,
            "monedas": CuentaBancaria.MONEDAS,
        },
        request=request
    )

    return JsonResponse({
        "ok": True,
        "html": html,
        "cuentas": [
            {
                "id": cuenta.id,
                "nombre": cuenta.nombre,
                "banco_id": cuenta.banco_id,
                "banco": cuenta.banco.nombre,
                "tipo_cuenta": cuenta.tipo_cuenta,
                "moneda": cuenta.moneda,
                "numero_cuenta": cuenta.numero_cuenta,
                "cbu": cuenta.cbu,
                "alias": cuenta.alias,
            }
            for cuenta in cuentas
        ]
    })


def guardar_cuenta_bancaria(request):
    """
    Crea una cuenta bancaria para la empresa activa.
    Si existe una cuenta equivalente inactiva,
    la reactiva en lugar de crear un duplicado.
    """

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )

    empresa_id = request.POST.get(
        "empresa"
    )

    banco_id = request.POST.get(
        "banco"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_cuenta = (
        request.POST.get("tipo_cuenta") or ""
    ).strip()

    moneda = (
        request.POST.get("moneda") or ""
    ).strip()

    numero_cuenta = (
        request.POST.get("numero_cuenta") or ""
    ).strip()

    cbu = (
        request.POST.get("cbu") or ""
    ).strip()

    alias = (
        request.POST.get("alias") or ""
    ).strip().upper()

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre para la cuenta."
        })

    tipos_validos = {
        valor
        for valor, etiqueta
        in CuentaBancaria.TIPOS_CUENTA
    }

    if tipo_cuenta not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo de cuenta válido."
        })

    monedas_validas = {
        valor
        for valor, etiqueta
        in CuentaBancaria.MONEDAS
    }

    if moneda not in monedas_validas:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione una moneda válida."
        })

    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La empresa no existe."
            },
            status=404
        )

    try:

        banco = Banco.objects.get(
            id=banco_id,
            empresa=empresa,
            activo=True
        )

    except Banco.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un banco válido."
        })

    cuenta_existente = CuentaBancaria.objects.filter(
        empresa=empresa,
        banco=banco,
        nombre=nombre
    ).first()

    if cuenta_existente:

        if cuenta_existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe una cuenta bancaria "
                    "con ese nombre para ese banco."
                )
            })

        return JsonResponse({
            "ok": False,
            "inactiva": True,
            "cuenta": {
                "id": cuenta_existente.id,
                "nombre": cuenta_existente.nombre,
                "banco_id": cuenta_existente.banco_id,
                "tipo_cuenta": cuenta_existente.tipo_cuenta,
                "moneda": cuenta_existente.moneda,
                "numero_cuenta": cuenta_existente.numero_cuenta,
                "cbu": cuenta_existente.cbu,
                "alias": cuenta_existente.alias,
            },
            "mensaje": (
                "La cuenta bancaria ya existe pero está inactiva. "
                "Puede reactivarla."
            )
        })

    cuenta = CuentaBancaria.objects.create(
        empresa=empresa,
        banco=banco,
        nombre=nombre,
        tipo_cuenta=tipo_cuenta,
        moneda=moneda,
        numero_cuenta=numero_cuenta,
        cbu=cbu,
        alias=alias
    )

    return JsonResponse({
        "ok": True,
        "cuenta": {
            "id": cuenta.id,
            "nombre": cuenta.nombre
        }
    })


def modificar_cuenta_bancaria(request):
    """
    Modifica una cuenta bancaria activa perteneciente
    a la empresa indicada.
    """

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )

    empresa_id = request.POST.get(
        "empresa"
    )

    cuenta_id = request.POST.get(
        "cuenta"
    )

    banco_id = request.POST.get(
        "banco"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_cuenta = (
        request.POST.get("tipo_cuenta") or ""
    ).strip()

    moneda = (
        request.POST.get("moneda") or ""
    ).strip()

    numero_cuenta = (
        request.POST.get("numero_cuenta") or ""
    ).strip()

    cbu = (
        request.POST.get("cbu") or ""
    ).strip()

    alias = (
        request.POST.get("alias") or ""
    ).strip().upper()

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre para la cuenta."
        })

    tipos_validos = {
        valor
        for valor, etiqueta
        in CuentaBancaria.TIPOS_CUENTA
    }

    if tipo_cuenta not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo de cuenta válido."
        })

    monedas_validas = {
        valor
        for valor, etiqueta
        in CuentaBancaria.MONEDAS
    }

    if moneda not in monedas_validas:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione una moneda válida."
        })

    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa_id=empresa_id,
            activo=True
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La cuenta bancaria no existe."
            },
            status=404
        )

    try:

        banco = Banco.objects.get(
            id=banco_id,
            empresa_id=empresa_id,
            activo=True
        )

    except Banco.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un banco válido."
        })

    duplicada = CuentaBancaria.objects.filter(
        empresa_id=empresa_id,
        banco=banco,
        nombre=nombre,
        activo=True
    ).exclude(
        id=cuenta.id
    ).exists()

    if duplicada:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra cuenta bancaria "
                "con ese nombre para ese banco."
            )
        })

    cuenta.banco = banco
    cuenta.nombre = nombre
    cuenta.tipo_cuenta = tipo_cuenta
    cuenta.moneda = moneda
    cuenta.numero_cuenta = numero_cuenta
    cuenta.cbu = cbu
    cuenta.alias = alias

    cuenta.save(
        update_fields=[
            "banco",
            "nombre",
            "tipo_cuenta",
            "moneda",
            "numero_cuenta",
            "cbu",
            "alias",
        ]
    )

    return JsonResponse({
        "ok": True
    })


def eliminar_cuenta_bancaria(request):
    """
    Realiza la baja lógica de una cuenta bancaria.
    No elimina físicamente el registro.
    """

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )

    empresa_id = request.POST.get(
        "empresa"
    )

    cuenta_id = request.POST.get(
        "cuenta"
    )

    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa_id=empresa_id,
            activo=True
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La cuenta bancaria no existe."
            },
            status=404
        )

    cuenta.activo = False

    cuenta.save(
        update_fields=[
            "activo"
        ]
    )

    return JsonResponse({
        "ok": True
    })


def reactivar_cuenta_bancaria(request):
    """
    Reactiva una cuenta bancaria inactiva y permite
    actualizar sus datos antes de volver a utilizarla.
    """

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )

    empresa_id = request.POST.get(
        "empresa"
    )

    cuenta_id = request.POST.get(
        "cuenta"
    )

    banco_id = request.POST.get(
        "banco"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_cuenta = (
        request.POST.get("tipo_cuenta") or ""
    ).strip()

    moneda = (
        request.POST.get("moneda") or ""
    ).strip()

    numero_cuenta = (
        request.POST.get("numero_cuenta") or ""
    ).strip()

    cbu = (
        request.POST.get("cbu") or ""
    ).strip()

    alias = (
        request.POST.get("alias") or ""
    ).strip().upper()

    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa_id=empresa_id,
            activo=False
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": (
                    "La cuenta bancaria inactiva "
                    "no existe."
                )
            },
            status=404
        )

    try:

        banco = Banco.objects.get(
            id=banco_id,
            empresa_id=empresa_id,
            activo=True
        )

    except Banco.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un banco válido."
        })

    duplicada = CuentaBancaria.objects.filter(
        empresa_id=empresa_id,
        banco=banco,
        nombre=nombre,
        activo=True
    ).exclude(
        id=cuenta.id
    ).exists()

    if duplicada:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra cuenta bancaria activa "
                "con ese nombre para ese banco."
            )
        })

    cuenta.banco = banco
    cuenta.nombre = nombre
    cuenta.tipo_cuenta = tipo_cuenta
    cuenta.moneda = moneda
    cuenta.numero_cuenta = numero_cuenta
    cuenta.cbu = cbu
    cuenta.alias = alias
    cuenta.activo = True

    cuenta.save(
        update_fields=[
            "banco",
            "nombre",
            "tipo_cuenta",
            "moneda",
            "numero_cuenta",
            "cbu",
            "alias",
            "activo",
        ]
    )

    return JsonResponse({
        "ok": True
    })

# =========================================
# TARJETAS
# =========================================

def listar_tarjetas(request):

    empresa_id = request.GET.get(
        "empresa"
    )


    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La empresa no existe."
            },
            status=404
        )


    tarjetas = (
        Tarjeta.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .select_related(
            "cuenta_bancaria",
            "cuenta_bancaria__banco"
        )
        .order_by(
            "nombre"
        )
    )


    cuentas = (
        CuentaBancaria.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .select_related(
            "banco"
        )
        .order_by(
            "banco__nombre",
            "nombre"
        )
    )


    html = render_to_string(
        "usuarios/tarjetas.html",
        {
            "empresa":
                empresa,

            "tarjetas":
                tarjetas,

            "cuentas":
                cuentas,

            "tipos_tarjeta":
                Tarjeta.TIPOS_TARJETA,
        },
        request=request
    )


    return JsonResponse({
        "ok": True,

        "html":
            html,

        "tarjetas": [

            {
                "id":
                    tarjeta.id,

                "nombre":
                    tarjeta.nombre,

                "tipo_tarjeta":
                    tarjeta.tipo_tarjeta,

                "tipo_tarjeta_label":
                    tarjeta.get_tipo_tarjeta_display(),

                "cuenta_bancaria_id":
                    tarjeta.cuenta_bancaria_id,

                "cuenta_bancaria":
                    tarjeta.cuenta_bancaria.nombre,

                "banco":
                    tarjeta.cuenta_bancaria.banco.nombre,
            }

            for tarjeta in tarjetas
        ]
    })


def guardar_tarjeta(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )


    empresa_id = request.POST.get(
        "empresa"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_tarjeta = (
        request.POST.get("tipo_tarjeta") or ""
    ).strip()

    cuenta_id = request.POST.get(
        "cuenta_bancaria"
    )


    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre para la tarjeta."
        })


    tipos_validos = {
        valor
        for valor, etiqueta
        in Tarjeta.TIPOS_TARJETA
    }


    if tipo_tarjeta not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo de tarjeta válido."
        })


    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La empresa no existe."
            },
            status=404
        )


    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa=empresa,
            activo=True
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione una cuenta bancaria válida."
        })


    existente = (
        Tarjeta.objects
        .filter(
            empresa=empresa,
            nombre__iexact=nombre
        )
        .first()
    )


    if existente:

        if existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe una tarjeta activa "
                    "con ese nombre."
                )
            })


        return JsonResponse({
            "ok": False,

            "requiere_reactivacion": True,

            "mensaje": (
                "La tarjeta ya existe pero está inactiva. "
                "Puede reactivarla."
            ),

            "tarjeta": {
                "id":
                    existente.id,

                "nombre":
                    existente.nombre,

                "tipo_tarjeta":
                    existente.tipo_tarjeta,

                "cuenta_bancaria_id":
                    existente.cuenta_bancaria_id,
            }
        })


    tarjeta = Tarjeta.objects.create(

        empresa=
            empresa,

        nombre=
            nombre,

        tipo_tarjeta=
            tipo_tarjeta,

        cuenta_bancaria=
            cuenta

    )


    return JsonResponse({
        "ok": True,

        "tarjeta": {
            "id":
                tarjeta.id,

            "nombre":
                tarjeta.nombre,
        }
    })


def modificar_tarjeta(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )


    empresa_id = request.POST.get(
        "empresa"
    )

    tarjeta_id = request.POST.get(
        "tarjeta"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_tarjeta = (
        request.POST.get("tipo_tarjeta") or ""
    ).strip()

    cuenta_id = request.POST.get(
        "cuenta_bancaria"
    )


    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre para la tarjeta."
        })


    tipos_validos = {
        valor
        for valor, etiqueta
        in Tarjeta.TIPOS_TARJETA
    }


    if tipo_tarjeta not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo de tarjeta válido."
        })


    try:

        tarjeta = Tarjeta.objects.get(
            id=tarjeta_id,
            empresa_id=empresa_id,
            activo=True
        )

    except Tarjeta.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La tarjeta no existe."
            },
            status=404
        )


    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa_id=empresa_id,
            activo=True
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione una cuenta bancaria válida."
        })


    duplicada = (
        Tarjeta.objects
        .filter(
            empresa_id=empresa_id,
            nombre__iexact=nombre,
            activo=True
        )
        .exclude(
            id=tarjeta.id
        )
        .exists()
    )


    if duplicada:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra tarjeta activa "
                "con ese nombre."
            )
        })


    tarjeta.nombre = nombre

    tarjeta.tipo_tarjeta = tipo_tarjeta

    tarjeta.cuenta_bancaria = cuenta


    tarjeta.save(
        update_fields=[
            "nombre",
            "tipo_tarjeta",
            "cuenta_bancaria",
        ]
    )


    return JsonResponse({
        "ok": True
    })


def eliminar_tarjeta(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )


    empresa_id = request.POST.get(
        "empresa"
    )

    tarjeta_id = request.POST.get(
        "tarjeta"
    )


    try:

        tarjeta = Tarjeta.objects.get(
            id=tarjeta_id,
            empresa_id=empresa_id,
            activo=True
        )

    except Tarjeta.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La tarjeta no existe."
            },
            status=404
        )


    tarjeta.activo = False


    tarjeta.save(
        update_fields=[
            "activo"
        ]
    )


    return JsonResponse({
        "ok": True
    })


def reactivar_tarjeta(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "Método no permitido."
            },
            status=405
        )


    empresa_id = request.POST.get(
        "empresa"
    )

    tarjeta_id = request.POST.get(
        "tarjeta"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo_tarjeta = (
        request.POST.get("tipo_tarjeta") or ""
    ).strip()

    cuenta_id = request.POST.get(
        "cuenta_bancaria"
    )


    try:

        tarjeta = Tarjeta.objects.get(
            id=tarjeta_id,
            empresa_id=empresa_id,
            activo=False
        )

    except Tarjeta.DoesNotExist:

        return JsonResponse(
            {
                "ok": False,
                "mensaje": "La tarjeta inactiva no existe."
            },
            status=404
        )


    tipos_validos = {
        valor
        for valor, etiqueta
        in Tarjeta.TIPOS_TARJETA
    }


    if tipo_tarjeta not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo de tarjeta válido."
        })


    try:

        cuenta = CuentaBancaria.objects.get(
            id=cuenta_id,
            empresa_id=empresa_id,
            activo=True
        )

    except CuentaBancaria.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione una cuenta bancaria válida."
        })


    duplicada = (
        Tarjeta.objects
        .filter(
            empresa_id=empresa_id,
            nombre__iexact=nombre,
            activo=True
        )
        .exclude(
            id=tarjeta.id
        )
        .exists()
    )


    if duplicada:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra tarjeta activa "
                "con ese nombre."
            )
        })


    tarjeta.nombre = nombre

    tarjeta.tipo_tarjeta = tipo_tarjeta

    tarjeta.cuenta_bancaria = cuenta

    tarjeta.activo = True


    tarjeta.save(
        update_fields=[
            "nombre",
            "tipo_tarjeta",
            "cuenta_bancaria",
            "activo",
        ]
    )


    return JsonResponse({
        "ok": True
    })

def listar_centros_operativos(request):

    empresa_id = request.GET.get("empresa")

    empresa = Empresa.objects.get(
        id=empresa_id
    )

    centros = CentroOperativo.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by("nombre")

    html = render_to_string(
        "usuarios/centros_operativos.html",
        {
            "empresa": empresa,
            "centros": centros
        },
        request=request
    )

    return JsonResponse({
        "html": html,
        "centros": [
            {
                "id": centro.id,
                "nombre": centro.nombre,
                "tipo": centro.tipo,
                "direccion": centro.direccion
            }
            for centro in centros
        ]
    })

def guardar_centro_operativo(request):

    if request.method != "POST":
        return JsonResponse(
            {"ok": False}
        )

    empresa = Empresa.objects.get(
        id=request.POST.get("empresa")
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo = (
        request.POST.get("tipo") or ""
    ).strip()

    direccion = (
        request.POST.get("direccion") or ""
    ).strip().upper()

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese un nombre."
        })

    if not tipo:

        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione un tipo."
        })

    if CentroOperativo.objects.filter(
        empresa=empresa,
        nombre=nombre,
        activo=True
    ).exists():

        return JsonResponse({
            "ok": False,
            "mensaje": "Ese centro operativo ya existe."
        })

    centro = CentroOperativo.objects.create(
        empresa=empresa,
        nombre=nombre,
        tipo=tipo,
        direccion=direccion
    )

    return JsonResponse({
        "ok": True,
        "centro": {
            "id": centro.id,
            "nombre": centro.nombre,
        }
    })

def modificar_centro_operativo(request):

    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    centro_id = request.POST.get("centro")
    empresa_id = request.POST.get("empresa")

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    tipo = (
        request.POST.get("tipo") or ""
    ).strip()

    direccion = (
        request.POST.get("direccion") or ""
    ).strip().upper()

    if not nombre:
        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese el nombre del centro operativo."
        })

    if not tipo:
        return JsonResponse({
            "ok": False,
            "mensaje": "Seleccione el tipo."
        })

    tipos_validos = {
        "Casa Central",
        "Sucursal",
        "Deposito",
        "Mostrador"
    }

    if tipo not in tipos_validos:
        return JsonResponse({
            "ok": False,
            "mensaje": "El tipo seleccionado no es válido."
        })

    try:
        centro = CentroOperativo.objects.get(
            id=centro_id,
            empresa_id=empresa_id,
            activo=True
        )

    except CentroOperativo.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "mensaje": "El centro operativo no existe."
        }, status=404)

    if CentroOperativo.objects.filter(
        empresa_id=empresa_id,
        nombre=nombre,
        activo=True
    ).exclude(id=centro.id).exists():

        return JsonResponse({
            "ok": False,
            "mensaje": "Ya existe otro centro operativo con ese nombre."
        })

    centro.nombre = nombre
    centro.tipo = tipo
    centro.direccion = direccion

    centro.save(
        update_fields=[
            "nombre",
            "tipo",
            "direccion"
        ]
    )

    return JsonResponse({
        "ok": True
    })


def eliminar_centro_operativo(request):

    if request.method != "POST":
        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    centro_id = request.POST.get("centro")
    empresa_id = request.POST.get("empresa")

    try:
        centro = CentroOperativo.objects.get(
            id=centro_id,
            empresa_id=empresa_id,
            activo=True
        )

    except CentroOperativo.DoesNotExist:
        return JsonResponse({
            "ok": False,
            "mensaje": "El centro operativo no existe."
        }, status=404)

    cantidad_centros_activos = (
        CentroOperativo.objects
        .filter(
            empresa_id=empresa_id,
            activo=True
        )
        .count()
    )

    if cantidad_centros_activos <= 1:
        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No se puede eliminar el único centro operativo "
                "de la empresa. Cree otro centro operativo antes "
                "de eliminar este."
            )
        })

    centro.activo = False
    centro.save(update_fields=["activo"])

    return JsonResponse({
        "ok": True
    })

# =========================================
# RECURSOS OPERATIVOS
# =========================================

def obtener_centros_recurso_request(
    request,
    empresa_id
):

    centros_ids = request.POST.getlist(
        "centros_operativos"
    )


    # Evitamos IDs repetidos conservando el orden.
    centros_ids = list(
        dict.fromkeys(
            centro_id
            for centro_id in centros_ids
            if centro_id
        )
    )


    if not centros_ids:

        return (
            None,
            "Seleccione al menos un Centro Operativo."
        )


    centros = list(
        CentroOperativo.objects
        .filter(
            id__in=centros_ids,
            empresa_id=empresa_id,
            activo=True
        )
    )


    if len(centros) != len(centros_ids):

        return (
            None,
            (
                "Uno o más Centros Operativos "
                "no existen o están inactivos."
            )
        )


    centros_por_id = {
        str(centro.id): centro
        for centro in centros
    }


    centros_ordenados = [

        centros_por_id[
            str(centro_id)
        ]

        for centro_id in centros_ids

    ]


    return (
        centros_ordenados,
        None
    )

def listar_recursos_operativos(request):

    empresa_id = request.GET.get(
        "empresa"
    )


    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )


    except Empresa.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La empresa no existe."
        }, status=404)


    recursos = (
        RecursoOperativo.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .prefetch_related(
            "relaciones_centros__centro_operativo"
        )
        .order_by(
            "tipo_recurso",
            "nombre"
        )
    )


    centros = (
        CentroOperativo.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .order_by(
            "nombre"
        )
    )


    html = render_to_string(
        "usuarios/recursos_operativos.html",
        {
            "empresa": empresa,
            "recursos": recursos,
            "centros": centros
        },
        request=request
    )


    recursos_json = []


    for recurso in recursos:

        relaciones = list(
            recurso.relaciones_centros.all()
        )


        centros_recurso = [

            relacion.centro_operativo

            for relacion in relaciones

        ]


        recursos_json.append({

            "id":
                recurso.id,

            "nombre":
                recurso.nombre,

            "tipo_recurso":
                recurso.tipo_recurso,

            "tipo_recurso_label":
                recurso.get_tipo_recurso_display(),



            # =====================================
            # NUEVO SISTEMA MULTICENTRO
            # =====================================

            "centros_operativos_ids": [

                str(centro.id)

                for centro in centros_recurso

            ],

            "centros_operativos": [

                {
                    "id":
                        centro.id,

                    "nombre":
                        centro.nombre
                }

                for centro in centros_recurso

            ],

            "descripcion":
                recurso.descripcion

        })


    return JsonResponse({
        "ok": True,
        "html": html,
        "recursos": recursos_json
    })


def guardar_recurso_operativo(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)


    empresa_id = request.POST.get(
        "empresa"
    )


    nombre = (
        request.POST.get(
            "nombre"
        ) or ""
    ).strip().upper()


    tipo_recurso = (
        request.POST.get(
            "tipo_recurso"
        ) or ""
    ).strip()


    descripcion = (
        request.POST.get(
            "descripcion"
        ) or ""
    ).strip()


    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "Ingrese el nombre del recurso operativo."
        })


    tipos_validos = {
        "Persona",
        "Vehiculo",
        "Inmueble",
        "Equipo",
        "Otro"
    }


    if tipo_recurso not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "Seleccione un tipo de recurso válido."
        })


    centros, error_centros = (
        obtener_centros_recurso_request(
            request,
            empresa_id
        )
    )


    if error_centros:

        return JsonResponse({
            "ok": False,
            "mensaje": error_centros
        })


    existente = (
        RecursoOperativo.objects
        .filter(
            empresa_id=empresa_id,
            nombre__iexact=nombre
        )
        .first()
    )


    if existente:

        if existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe un recurso operativo "
                    "activo con ese nombre."
                )
            })


        return JsonResponse({
            "ok": False,
            "requiere_reactivacion": True,
            "mensaje": (
                "Ya existe un recurso operativo "
                "inactivo con ese nombre."
            ),
            "recurso": {
                "id":
                    existente.id,

                "nombre":
                    existente.nombre
            }
        })


    with transaction.atomic():

        recurso = RecursoOperativo.objects.create(

            empresa_id=
                empresa_id,

            nombre=
                nombre,

            tipo_recurso=
                tipo_recurso,

            descripcion=
                descripcion

        )


        RecursoOperativoCentro.objects.bulk_create([

            RecursoOperativoCentro(
                recurso_operativo=recurso,
                centro_operativo=centro
            )

            for centro in centros

        ])


    return JsonResponse({
        "ok": True,
        "recurso": {
            "id":
                recurso.id,

            "nombre":
                recurso.nombre,

            "centros_operativos_ids": [
                str(centro.id)
                for centro in centros
            ]
        }
    })


def modificar_recurso_operativo(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)


    recurso_id = request.POST.get(
        "recurso"
    )


    empresa_id = request.POST.get(
        "empresa"
    )


    nombre = (
        request.POST.get(
            "nombre"
        ) or ""
    ).strip().upper()


    tipo_recurso = (
        request.POST.get(
            "tipo_recurso"
        ) or ""
    ).strip()


    descripcion = (
        request.POST.get(
            "descripcion"
        ) or ""
    ).strip()


    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "Ingrese el nombre del recurso operativo."
        })


    tipos_validos = {
        "Persona",
        "Vehiculo",
        "Inmueble",
        "Equipo",
        "Otro"
    }


    if tipo_recurso not in tipos_validos:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "Seleccione un tipo de recurso válido."
        })


    try:

        recurso = RecursoOperativo.objects.get(
            id=recurso_id,
            empresa_id=empresa_id,
            activo=True
        )


    except RecursoOperativo.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "El recurso operativo no existe."
        }, status=404)


    centros, error_centros = (
        obtener_centros_recurso_request(
            request,
            empresa_id
        )
    )


    if error_centros:

        return JsonResponse({
            "ok": False,
            "mensaje": error_centros
        })


    duplicado = (
        RecursoOperativo.objects
        .filter(
            empresa_id=empresa_id,
            nombre__iexact=nombre,
            activo=True
        )
        .exclude(
            id=recurso.id
        )
        .exists()
    )


    if duplicado:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otro recurso operativo "
                "activo con ese nombre."
            )
        })


    with transaction.atomic():

        recurso.nombre = nombre

        recurso.tipo_recurso = tipo_recurso

        recurso.descripcion = descripcion

        recurso.save(
            update_fields=[
                "nombre",
                "tipo_recurso",
                "descripcion"
            ]
        )


        recurso.relaciones_centros.all().delete()


        RecursoOperativoCentro.objects.bulk_create([

            RecursoOperativoCentro(
                recurso_operativo=recurso,
                centro_operativo=centro
            )

            for centro in centros

        ])


    return JsonResponse({
        "ok": True,
        "centros_operativos_ids": [
            str(centro.id)
            for centro in centros
        ]
    })


def eliminar_recurso_operativo(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    recurso_id = request.POST.get(
        "recurso"
    )

    empresa_id = request.POST.get(
        "empresa"
    )

    try:

        recurso = RecursoOperativo.objects.get(
            id=recurso_id,
            empresa_id=empresa_id,
            activo=True
        )

    except RecursoOperativo.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje":
                "El recurso operativo no existe."
        }, status=404)


    cantidad_activos = (
        RecursoOperativo.objects
        .filter(
            empresa_id=empresa_id,
            activo=True
        )
        .count()
    )


    if cantidad_activos <= 1:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "La empresa debe conservar al menos "
                "un recurso operativo activo."
            )
        })


    recurso.activo = False

    recurso.save(
        update_fields=[
            "activo"
        ]
    )


    return JsonResponse({
        "ok": True
    })


def reactivar_recurso_operativo(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)


    recurso_id = request.POST.get(
        "recurso"
    )


    empresa_id = request.POST.get(
        "empresa"
    )


    try:

        recurso = (
            RecursoOperativo.objects
            .prefetch_related(
                "relaciones_centros__centro_operativo"
            )
            .get(
                id=recurso_id,
                empresa_id=empresa_id,
                activo=False
            )
        )


    except RecursoOperativo.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "El recurso operativo inactivo "
                "no existe o ya fue activado."
            )
        }, status=404)


    relaciones_activas = [

        relacion

        for relacion
        in recurso.relaciones_centros.all()

        if relacion.centro_operativo.activo

    ]


    if not relaciones_activas:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No se puede reactivar el recurso porque "
                "no tiene ningún Centro Operativo activo relacionado."
            )
        })


    duplicado = (
        RecursoOperativo.objects
        .filter(
            empresa_id=empresa_id,
            nombre__iexact=recurso.nombre,
            activo=True
        )
        .exclude(
            id=recurso.id
        )
        .exists()
    )


    if duplicado:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe un recurso operativo "
                "activo con ese nombre."
            )
        })


        recurso.activo = True


        recurso.save(
            update_fields=[
                "activo"
            ]
        )


    return JsonResponse({
        "ok": True,
        "recurso": {

            "id":
                recurso.id,

            "nombre":
                recurso.nombre,

            "centros_operativos_ids": [

                str(
                    relacion.centro_operativo_id
                )

                for relacion
                in recurso.relaciones_centros.all()

            ]

        }
    })

# =========================================
# PROVEEDORES
# =========================================

def validar_email_proveedor(valor, nombre_campo):

    if not valor:
        return None

    try:

        validate_email(valor)

    except ValidationError:

        return f"El e-mail de {nombre_campo} no es válido."

    return None


def datos_proveedor_request(request):

    return {

        "razon_social": (
            request.POST.get("razon_social") or ""
        ).strip().upper(),

        "cuit": (
            request.POST.get("cuit") or ""
        ).strip(),

        "direccion": (
            request.POST.get("direccion") or ""
        ).strip().upper(),

        "localidad": (
            request.POST.get("localidad") or ""
        ).strip().upper(),

        "contacto1_nombre": (
            request.POST.get("contacto1_nombre") or ""
        ).strip().upper(),

        "contacto1_telefono": (
            request.POST.get("contacto1_telefono") or ""
        ).strip(),

        "contacto1_email": (
            request.POST.get("contacto1_email") or ""
        ).strip().lower(),

        "contacto2_nombre": (
            request.POST.get("contacto2_nombre") or ""
        ).strip().upper(),

        "contacto2_telefono": (
            request.POST.get("contacto2_telefono") or ""
        ).strip(),

        "contacto2_email": (
            request.POST.get("contacto2_email") or ""
        ).strip().lower(),

        "email": (
            request.POST.get("email") or ""
        ).strip().lower(),

        "observaciones": (
            request.POST.get("observaciones") or ""
        ).strip(),

    }


def validar_datos_proveedor(datos):

    if not datos["razon_social"]:

        return "Ingrese la razón social del proveedor."

    if not re.match(
        r"^\d{2}-\d{8}-\d{1}$",
        datos["cuit"]
    ):

        return (
            "El CUIT debe tener el formato "
            "00-00000000-0."
        )

    validaciones_email = [

        (
            datos["contacto1_email"],
            "contacto 1"
        ),

        (
            datos["contacto2_email"],
            "contacto 2"
        ),

        (
            datos["email"],
            "proveedor"
        ),

    ]

    for email, nombre_campo in validaciones_email:

        error = validar_email_proveedor(
            email,
            nombre_campo
        )

        if error:

            return error

    return None


def listar_proveedores(request):

    empresa_id = request.GET.get(
        "empresa"
    )

    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La empresa no existe."
        }, status=404)

    proveedores = Proveedor.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by(
        "razon_social"
    )

    html = render_to_string(
        "usuarios/proveedores.html",
        {
            "empresa": empresa,
            "proveedores": proveedores
        },
        request=request
    )

    return JsonResponse({

        "ok": True,

        "html": html,

        "proveedores": [

            {
                "id": proveedor.id,
                "razon_social": proveedor.razon_social,
                "cuit": proveedor.cuit
            }

            for proveedor in proveedores

        ]

    })


def guardar_proveedor(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La empresa no existe."
        }, status=404)

    datos = datos_proveedor_request(
        request
    )

    error = validar_datos_proveedor(
        datos
    )

    if error:

        return JsonResponse({
            "ok": False,
            "mensaje": error
        })

    proveedor_existente = (
        Proveedor.objects
        .filter(
            empresa=empresa,
            cuit=datos["cuit"]
        )
        .first()
    )

    if proveedor_existente:

        if proveedor_existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe un proveedor activo "
                    "con ese CUIT."
                )
            })

        return JsonResponse({
            "ok": False,
            "requiere_reactivacion": True,

            "mensaje": (
                "Este CUIT pertenece a un proveedor "
                "inactivo. Puede reactivarlo."
            ),

            "proveedor": {
                "id": proveedor_existente.id,
                "razon_social": proveedor_existente.razon_social,
                "cuit": proveedor_existente.cuit,
                "direccion": proveedor_existente.direccion,
                "localidad": proveedor_existente.localidad,

                "contacto1_nombre":
                    proveedor_existente.contacto1_nombre,

                "contacto1_telefono":
                    proveedor_existente.contacto1_telefono,

                "contacto1_email":
                    proveedor_existente.contacto1_email,

                "contacto2_nombre":
                    proveedor_existente.contacto2_nombre,

                "contacto2_telefono":
                    proveedor_existente.contacto2_telefono,

                "contacto2_email":
                    proveedor_existente.contacto2_email,

                "email": proveedor_existente.email,
                "observaciones": proveedor_existente.observaciones,
            }
        })

    proveedor = Proveedor.objects.create(
        empresa=empresa,
        **datos
    )

    return JsonResponse({

        "ok": True,

        "proveedor": {
            "id": proveedor.id,
            "razon_social": proveedor.razon_social,
            "cuit": proveedor.cuit
        }

    })


def modificar_proveedor(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    proveedor_id = request.POST.get(
        "proveedor"
    )

    try:

        proveedor = Proveedor.objects.get(
            id=proveedor_id,
            empresa_id=empresa_id,
            activo=True
        )

    except Proveedor.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "El proveedor no existe."
        }, status=404)

    datos = datos_proveedor_request(
        request
    )

    error = validar_datos_proveedor(
        datos
    )

    if error:

        return JsonResponse({
            "ok": False,
            "mensaje": error
        })

    cuit_duplicado = (
        Proveedor.objects
        .filter(
            empresa_id=empresa_id,
            cuit=datos["cuit"]
        )
        .exclude(
            id=proveedor.id
        )
        .exists()
    )

    if cuit_duplicado:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otro proveedor, activo "
                "o inactivo, con ese CUIT."
            )
        })

    for campo, valor in datos.items():

        setattr(
            proveedor,
            campo,
            valor
        )

    proveedor.save(
        update_fields=list(
            datos.keys()
        )
    )

    return JsonResponse({
        "ok": True
    })


def eliminar_proveedor(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    proveedor_id = request.POST.get(
        "proveedor"
    )

    try:

        proveedor = Proveedor.objects.get(
            id=proveedor_id,
            empresa_id=empresa_id,
            activo=True
        )

    except Proveedor.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "El proveedor no existe."
        }, status=404)

    proveedor.activo = False

    proveedor.save(
        update_fields=[
            "activo"
        ]
    )

    return JsonResponse({
        "ok": True
    })

def reactivar_proveedor(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    proveedor_id = request.POST.get(
        "proveedor"
    )

    try:

        proveedor = Proveedor.objects.get(
            id=proveedor_id,
            empresa_id=empresa_id,
            activo=False
        )

    except Proveedor.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "El proveedor inactivo no existe "
                "o ya fue reactivado."
            )
        }, status=404)

    proveedor.activo = True

    proveedor.save(
        update_fields=[
            "activo"
        ]
    )

    return JsonResponse({
        "ok": True,

        "proveedor": {
            "id": proveedor.id,
            "razon_social": proveedor.razon_social,
            "cuit": proveedor.cuit
        }
    })

# =========================================
# GESTIÓN DE CLAVES
# =========================================


def datos_gestion_clave_request(request):

    return {

        "nombre": (
            request.POST.get(
                "nombre"
            ) or ""
        ).strip(),

        "sitio": (
            request.POST.get(
                "sitio"
            ) or ""
        ).strip(),

        "usuario": (
            request.POST.get(
                "usuario"
            ) or ""
        ).strip(),

        "correo": (
            request.POST.get(
                "correo"
            ) or ""
        ).strip().lower(),

        "contrasena": (
            request.POST.get(
                "contrasena"
            ) or ""
        ),

        "referencia_recuperacion_1": (
            request.POST.get(
                "referencia_recuperacion_1"
            ) or ""
        ).strip(),

        "referencia_recuperacion_2": (
            request.POST.get(
                "referencia_recuperacion_2"
            ) or ""
        ).strip(),

        "observaciones": (
            request.POST.get(
                "observaciones"
            ) or ""
        ).strip(),

    }


def validar_datos_gestion_clave(
    datos,
    requiere_contrasena=True
):

    if not datos["nombre"]:

        return (
            "Ingrese el nombre "
            "de la credencial."
        )

    if (
        requiere_contrasena and
        not datos["contrasena"]
    ):

        return (
            "Ingrese una contraseña."
        )

    if datos["correo"]:

        try:

            validate_email(
                datos["correo"]
            )

        except ValidationError:

            return (
                "El correo ingresado "
                "no es válido."
            )

    return None


def listar_gestion_claves(request):

    empresa_id = request.GET.get(
        "empresa"
    )

    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La empresa no existe."
        }, status=404)

    claves = GestionClave.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by(
        "nombre"
    )

    html = render_to_string(
        "usuarios/gestion_claves.html",
        {
            "empresa": empresa,
            "claves": claves
        },
        request=request
    )

    return JsonResponse({
        "ok": True,
        "html": html
    })

def guardar_gestion_clave(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La empresa no existe."
        }, status=404)

    datos = datos_gestion_clave_request(
        request
    )

    error = validar_datos_gestion_clave(
        datos,
        requiere_contrasena=True
    )

    if error:

        return JsonResponse({
            "ok": False,
            "mensaje": error
        })

    existente = (
        GestionClave.objects
        .filter(
            empresa=empresa,
            nombre__iexact=datos["nombre"]
        )
        .first()
    )

    if existente:

        if existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe una credencial "
                    "activa con ese nombre."
                )
            })

        return JsonResponse({

            "ok": False,

            "requiere_reactivacion": True,

            "mensaje": (
                "Ya existe una credencial "
                "inactiva con ese nombre."
            ),

            "clave": {
                "id": existente.id,
                "nombre": existente.nombre
            }

        })

    try:

        contrasena_cifrada = cifrar_clave(
            datos["contrasena"]
        )

    except Exception as error:

        print(
            "Error cifrando contraseña:",
            error
        )

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No fue posible cifrar "
                "la contraseña."
            )
        }, status=500)

    clave = GestionClave.objects.create(

        empresa=empresa,

        nombre=datos["nombre"],

        sitio=datos["sitio"],

        usuario=datos["usuario"],

        correo=datos["correo"],

        contrasena_cifrada=
            contrasena_cifrada,

        referencia_recuperacion_1=
            datos[
                "referencia_recuperacion_1"
            ],

        referencia_recuperacion_2=
            datos[
                "referencia_recuperacion_2"
            ],

        observaciones=
            datos["observaciones"]

    )

    return JsonResponse({

        "ok": True,

        "clave": {
            "id": clave.id,
            "nombre": clave.nombre
        }

    })

def ver_gestion_clave(request):

    empresa_id = request.GET.get(
        "empresa"
    )

    clave_id = request.GET.get(
        "clave"
    )

    try:

        clave = GestionClave.objects.get(
            id=clave_id,
            empresa_id=empresa_id,
            activo=True
        )

    except GestionClave.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La credencial no existe."
        }, status=404)

    try:

        contrasena = descifrar_clave(
            clave.contrasena_cifrada
        )

    except ValueError:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "No fue posible recuperar "
                "la contraseña."
            )
        }, status=500)

    return JsonResponse({

        "ok": True,

        "clave": {

            "id":
                clave.id,

            "nombre":
                clave.nombre,

            "sitio":
                clave.sitio,

            "usuario":
                clave.usuario,

            "correo":
                clave.correo,

            "contrasena":
                contrasena,

            "referencia_recuperacion_1":
                clave.referencia_recuperacion_1,

            "referencia_recuperacion_2":
                clave.referencia_recuperacion_2,

            "observaciones":
                clave.observaciones,

        }

    })

def modificar_gestion_clave(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    clave_id = request.POST.get(
        "clave"
    )

    try:

        clave = GestionClave.objects.get(
            id=clave_id,
            empresa_id=empresa_id,
            activo=True
        )

    except GestionClave.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La credencial no existe."
        }, status=404)

    datos = datos_gestion_clave_request(
        request
    )

    error = validar_datos_gestion_clave(
        datos,
        requiere_contrasena=False
    )

    if error:

        return JsonResponse({
            "ok": False,
            "mensaje": error
        })

    duplicado = (
        GestionClave.objects
        .filter(
            empresa_id=empresa_id,
            nombre__iexact=datos["nombre"],
            activo=True
        )
        .exclude(
            id=clave.id
        )
        .exists()
    )

    if duplicado:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otra credencial "
                "activa con ese nombre."
            )
        })

    clave.nombre = (
        datos["nombre"]
    )

    clave.sitio = (
        datos["sitio"]
    )

    clave.usuario = (
        datos["usuario"]
    )

    clave.correo = (
        datos["correo"]
    )

    clave.referencia_recuperacion_1 = (
        datos[
            "referencia_recuperacion_1"
        ]
    )

    clave.referencia_recuperacion_2 = (
        datos[
            "referencia_recuperacion_2"
        ]
    )

    clave.observaciones = (
        datos["observaciones"]
    )

    campos_actualizados = [
        "nombre",
        "sitio",
        "usuario",
        "correo",
        "referencia_recuperacion_1",
        "referencia_recuperacion_2",
        "observaciones",
        "modificado"
    ]

    if datos["contrasena"]:

        try:

            clave.contrasena_cifrada = (
                cifrar_clave(
                    datos["contrasena"]
                )
            )

        except Exception as error:

            print(
                "Error cifrando contraseña:",
                error
            )

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "No fue posible cifrar "
                    "la contraseña."
                )
            }, status=500)

        campos_actualizados.append(
            "contrasena_cifrada"
        )

    clave.save(
        update_fields=campos_actualizados
    )

    return JsonResponse({
        "ok": True
    })

def eliminar_gestion_clave(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    clave_id = request.POST.get(
        "clave"
    )

    try:

        clave = GestionClave.objects.get(
            id=clave_id,
            empresa_id=empresa_id,
            activo=True
        )

    except GestionClave.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La credencial no existe."
        }, status=404)

    clave.activo = False

    clave.save(
        update_fields=[
            "activo",
            "modificado"
        ]
    )

    return JsonResponse({
        "ok": True
    })


def reactivar_gestion_clave(request):

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    clave_id = request.POST.get(
        "clave"
    )

    try:

        clave = GestionClave.objects.get(
            id=clave_id,
            empresa_id=empresa_id,
            activo=False
        )

    except GestionClave.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "La credencial inactiva "
                "no existe o ya fue activada."
            )
        }, status=404)

    duplicado_activo = (
        GestionClave.objects
        .filter(
            empresa_id=empresa_id,
            nombre__iexact=clave.nombre,
            activo=True
        )
        .exclude(
            id=clave.id
        )
        .exists()
    )

    if duplicado_activo:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe una credencial "
                "activa con ese nombre."
            )
        })

    clave.activo = True

    clave.save(
        update_fields=[
            "activo",
            "modificado"
        ]
    )

    return JsonResponse({

        "ok": True,

        "clave": {
            "id": clave.id,
            "nombre": clave.nombre
        }

    })

# =========================================
# TIPOS DE GASTO
# =========================================

def obtener_proveedores_tipo_gasto(request, empresa_id):
    """
    Obtiene y valida los proveedores enviados para un tipo de gasto.

    Sólo admite proveedores activos pertenecientes a la empresa indicada.
    """

    proveedores_ids = request.POST.getlist(
        "proveedores"
    )

    proveedores_ids = [
        proveedor_id
        for proveedor_id in proveedores_ids
        if proveedor_id
    ]

    proveedores = Proveedor.objects.filter(
        id__in=proveedores_ids,
        empresa_id=empresa_id,
        activo=True
    )

    if proveedores.count() != len(set(proveedores_ids)):

        return None

    return proveedores


def listar_tipos_gasto(request):
    """
    Devuelve el ABM de tipos de gasto correspondiente a la empresa activa.
    """

    empresa_id = request.GET.get(
        "empresa"
    )

    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La empresa no existe."
        }, status=404)

    tipos_gasto = (
        TipoGasto.objects
        .filter(
            empresa=empresa,
            activo=True
        )
        .prefetch_related(
            "relaciones_proveedores__proveedor"
        )
        .order_by(
            "nombre"
        )
    )

    proveedores = Proveedor.objects.filter(
        empresa=empresa,
        activo=True
    ).order_by(
        "razon_social"
    )

    html = render_to_string(
        "usuarios/tipos_gasto.html",
        {
            "empresa": empresa,
            "tipos_gasto": tipos_gasto,
            "proveedores": proveedores
        },
        request=request
    )

    return JsonResponse({
        "ok": True,
        "html": html,
        "tipos_gasto": [
            {
                "id": tipo_gasto.id,
                "nombre": tipo_gasto.nombre,
                "descripcion": tipo_gasto.descripcion,
                "proveedores": [
                    relacion.proveedor_id
                    for relacion
                    in tipo_gasto.relaciones_proveedores.all()
                ]
            }
            for tipo_gasto in tipos_gasto
        ]
    })


@transaction.atomic
def guardar_tipo_gasto(request):
    """
    Crea un tipo de gasto y registra sus proveedores relacionados.
    """

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    descripcion = (
        request.POST.get("descripcion") or ""
    ).strip()

    try:

        empresa = Empresa.objects.get(
            id=empresa_id
        )

    except Empresa.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "La empresa no existe."
        }, status=404)

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese el nombre del tipo de gasto."
        })

    tipo_gasto_existente = (
        TipoGasto.objects
        .filter(
            empresa=empresa,
            nombre=nombre
        )
        .first()
    )

    if tipo_gasto_existente:

        if tipo_gasto_existente.activo:

            return JsonResponse({
                "ok": False,
                "mensaje": (
                    "Ya existe un tipo de gasto activo "
                    "con ese nombre."
                )
            })

        return JsonResponse({
            "ok": False,
            "requiere_reactivacion": True,
            "mensaje": (
                "Ese tipo de gasto se encuentra inactivo. "
                "Puede reactivarlo."
            ),
            "tipo_gasto": {
                "id": tipo_gasto_existente.id,
                "nombre": tipo_gasto_existente.nombre,
                "descripcion": tipo_gasto_existente.descripcion,
                "proveedores": [
                    relacion.proveedor_id
                    for relacion
                    in tipo_gasto_existente
                    .relaciones_proveedores
                    .all()
                ]
            }
        })

    proveedores = obtener_proveedores_tipo_gasto(
        request,
        empresa.id
    )

    if proveedores is None:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Uno o más proveedores seleccionados "
                "no son válidos."
            )
        })

    tipo_gasto = TipoGasto.objects.create(
        empresa=empresa,
        nombre=nombre,
        descripcion=descripcion
    )

    TipoGastoProveedor.objects.bulk_create([
        TipoGastoProveedor(
            tipo_gasto=tipo_gasto,
            proveedor=proveedor
        )
        for proveedor in proveedores
    ])

    return JsonResponse({
        "ok": True,
        "tipo_gasto": {
            "id": tipo_gasto.id,
            "nombre": tipo_gasto.nombre
        }
    })


@transaction.atomic
def modificar_tipo_gasto(request):
    """
    Modifica un tipo de gasto y reemplaza sus proveedores relacionados.
    """

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    tipo_gasto_id = request.POST.get(
        "tipo_gasto"
    )

    nombre = (
        request.POST.get("nombre") or ""
    ).strip().upper()

    descripcion = (
        request.POST.get("descripcion") or ""
    ).strip()

    if not nombre:

        return JsonResponse({
            "ok": False,
            "mensaje": "Ingrese el nombre del tipo de gasto."
        })

    try:

        tipo_gasto = TipoGasto.objects.get(
            id=tipo_gasto_id,
            empresa_id=empresa_id,
            activo=True
        )

    except TipoGasto.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "El tipo de gasto no existe."
        }, status=404)

    nombre_duplicado = (
        TipoGasto.objects
        .filter(
            empresa_id=empresa_id,
            nombre=nombre
        )
        .exclude(
            id=tipo_gasto.id
        )
        .exists()
    )

    if nombre_duplicado:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Ya existe otro tipo de gasto, activo "
                "o inactivo, con ese nombre."
            )
        })

    proveedores = obtener_proveedores_tipo_gasto(
        request,
        empresa_id
    )

    if proveedores is None:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "Uno o más proveedores seleccionados "
                "no son válidos."
            )
        })

    tipo_gasto.nombre = nombre
    tipo_gasto.descripcion = descripcion

    tipo_gasto.save(
        update_fields=[
            "nombre",
            "descripcion"
        ]
    )

    tipo_gasto.relaciones_proveedores.all().delete()

    TipoGastoProveedor.objects.bulk_create([
        TipoGastoProveedor(
            tipo_gasto=tipo_gasto,
            proveedor=proveedor
        )
        for proveedor in proveedores
    ])

    return JsonResponse({
        "ok": True
    })


def eliminar_tipo_gasto(request):
    """
    Da de baja lógica un tipo de gasto activo.
    """

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    tipo_gasto_id = request.POST.get(
        "tipo_gasto"
    )

    try:

        tipo_gasto = TipoGasto.objects.get(
            id=tipo_gasto_id,
            empresa_id=empresa_id,
            activo=True
        )

    except TipoGasto.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": "El tipo de gasto no existe."
        }, status=404)

    tipo_gasto.activo = False

    tipo_gasto.save(
        update_fields=[
            "activo"
        ]
    )

    return JsonResponse({
        "ok": True
    })


def reactivar_tipo_gasto(request):
    """
    Reactiva un tipo de gasto previamente dado de baja.
    """

    if request.method != "POST":

        return JsonResponse({
            "ok": False,
            "mensaje": "Método no permitido."
        }, status=405)

    empresa_id = request.POST.get(
        "empresa"
    )

    tipo_gasto_id = request.POST.get(
        "tipo_gasto"
    )

    try:

        tipo_gasto = TipoGasto.objects.get(
            id=tipo_gasto_id,
            empresa_id=empresa_id,
            activo=False
        )

    except TipoGasto.DoesNotExist:

        return JsonResponse({
            "ok": False,
            "mensaje": (
                "El tipo de gasto inactivo no existe "
                "o ya fue reactivado."
            )
        }, status=404)

    tipo_gasto.activo = True

    tipo_gasto.save(
        update_fields=[
            "activo"
        ]
    )

    return JsonResponse({
        "ok": True,
        "tipo_gasto": {
            "id": tipo_gasto.id,
            "nombre": tipo_gasto.nombre
        }
    })