from django.shortcuts import (
    render,
    redirect
)

from django.http import HttpResponse

from django.conf import settings

from django.utils import timezone

from datetime import (
    datetime,
    timedelta
)

from io import BytesIO

import os
import re
import json
import uuid
import zipfile

from .models import (
    Empresa,
    Ejercicio,
    Rubro,
    Subrubro,
    Movimiento,
    CentroOperativo,
    Banco

)


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
                return redirect('/')

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
                f'/?empresa={nueva_empresa.id}'
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
               f'/?empresa={empresa_actual.id}'
            )   
    
        # ================================
        # NUEVO MOVIMIENTO
        # ================================

        if request.POST.get('guardar_movimiento'):

            ejercicio = empresa_actual.ejercicios.filter(
                estado="Abierto"
            ).first()

            if not ejercicio:
                return redirect(f"/?empresa={empresa_actual.id}")

            Movimiento.objects.create(

                ejercicio=ejercicio,

                rubro_id=request.POST.get("rubro"),

                subrubro_id=request.POST.get("subrubro") or None,

                descripcion=request.POST.get("descripcion"),

                importe=request.POST.get("importe"),

                fecha_pago=request.POST.get("fecha_pago"),

                fecha_vencimiento=request.POST.get("fecha_vencimiento") or None,

                estado=request.POST.get("estado"),

                observaciones=request.POST.get("observaciones"),

                archivo=request.FILES.get("archivo")
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

    rubros = Rubro.objects.all().order_by(
        'nombre'
    )

    subrubros = Subrubro.objects.all().order_by(
        'nombre'
    )

    movimientos = []

    if empresa_actual:

        ejercicio_abierto = empresa_actual.ejercicios.filter(
            estado='Abierto'
        ).first()

        if ejercicio_abierto:

            movimientos = Movimiento.objects.filter(
                ejercicio=ejercicio_abierto
            ).order_by('-fecha_pago')

    return render(

    request,

    'usuarios/panel_admin.html',

    {

        'empresas': empresas,
        'empresa_actual': empresa_actual,
        'empresa_importada': empresa_importada,

        'rubros': rubros,
        'subrubros': subrubros,
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

    return redirect('/')

def importar_empresa(request):

    if request.method != "POST":
        return redirect("/")

    archivo_zip = request.FILES.get(
        "archivo_zip"
    )

    if not archivo_zip:
        return redirect("/")

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

        return redirect("/")

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

    return redirect("/")

def confirmar_reemplazo(request):

    request.session[
        "confirmar_reemplazo"
    ] = True

    return redirect("/")    

# =====================================
# GUARDAR BANCO
# =====================================

from django.http import JsonResponse
from django.template.loader import render_to_string

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

    Banco.objects.create(

        empresa=empresa,

        nombre=nombre

    )

    return JsonResponse({

        "ok": True

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