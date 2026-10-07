import re

from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from usuarios.models import CentroOperativo, Ejercicio, Empresa, Movimiento


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
