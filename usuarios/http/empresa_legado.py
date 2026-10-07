import json
import os
import uuid
import zipfile

from io import BytesIO

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    CuentaBancaria,
    Empresa,
    RecursoOperativo,
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
