"""Pendientes globales DE LA EMPRESA ACTIVA, sin selector interempresas."""
import json
from decimal import Decimal, InvalidOperation
import uuid
from urllib.parse import urlencode
from datetime import timedelta

from django.db.models import Q, CharField
from django.db.models.functions import Cast

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import (AsignacionUsuarioEmpresa, Banco, Cliente, CentroOperativo, CuentaBancaria, Proveedor,
    PendienteBancario, PermisoPendienteBancarioCentro, RevisionPendienteBancario)
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.permisos_bancarios_accion import permitido as permiso_bancario, exigir as exigir_bancario
from usuarios.services.pendientes_bancarios import (
    alcance_pendientes, cambiar_permiso, registrar_lote, resolver_pendiente, ErrorFilaPendiente,
)


def _empresa_activa(request):
    pk = request.session.get('gestion_bancaria_empresa')
    if not pk:
        raise PermissionDenied('Entre desde el menú de una Empresa autorizada.')
    return alcance_pendientes(request.user, pk)


def _volver(request):
    origen = request.session.get('gestion_bancaria_origen')
    if origen == 'admin':
        pk = request.session.get('gestion_bancaria_empresa')
        return reverse('panel_admin') + '?' + urlencode({'empresa': pk})
    return reverse('panel_colaborador')


@login_required
@never_cache
@require_POST
def entrar_gestion_bancaria(request):
    """Entrada explícita desde la Empresa elegida fuera del módulo."""
    try:
        empresa, _ = alcance_pendientes(request.user, request.POST.get('empresa'))
        exigir_bancario(request.user,empresa.pk,'pendientes.ver')
    except (PermissionDenied, TypeError, ValueError):
        return HttpResponseForbidden('No tiene permiso para ingresar a esta Empresa.')
    origen = request.POST.get('origen')
    if origen not in ('admin', 'colaborador'):
        return HttpResponseForbidden('Entrada de navegación inválida.')
    destino = request.POST.get('destino', 'pendientes')
    if destino not in ('pendientes', 'permisos'):
        return HttpResponseForbidden('Destino inválido.')
    request.session['gestion_bancaria_empresa'] = empresa.pk
    request.session['gestion_bancaria_origen'] = origen
    if destino == 'permisos':
        return redirect('configurar_permisos_bancarios')
    return redirect('gestion_bancaria')


@login_required
@never_cache
@require_GET
@xframe_options_sameorigin
def gestion_bancaria(request):
    try:
        empresa, centros_habilitados = _empresa_activa(request)
    except (PermissionDenied, ValueError, TypeError):
        return HttpResponseForbidden('No tiene una Empresa activa autorizada.')
    exigir_bancario(request.user,empresa.pk,'pendientes.ver')
    puede_cargar=permiso_bancario(request.user,empresa.pk,'pendientes.crear')
    puede_salidas=permiso_bancario(request.user,empresa.pk,'pendientes.salidas')
    puede_editar=permiso_bancario(request.user,empresa.pk,'pendientes.editar')
    puede_resolver=permiso_bancario(request.user,empresa.pk,'pendientes.resolver')
    puede_estado=permiso_bancario(request.user,empresa.pk,'pendientes.estado')
    estado = request.GET.get('estado', 'Pendiente')
    if estado not in ('Pendiente', 'Resuelto'):
        return HttpResponseForbidden('Filtro inválido.')
    # TODOS los pendientes son globales dentro de la Empresa.
    pendientes = PendienteBancario.objects.filter(empresa=empresa, estado=estado)
    centros = CentroOperativo.objects.filter(empresa=empresa, activo=True).order_by('nombre')
    if centros_habilitados is not None:
        centros = centros.filter(pk__in=centros_habilitados)
        if estado == 'Resuelto':
            pendientes = pendientes.filter(centro_operativo_id__in=centros_habilitados)
    centro_filtro = request.GET.get('centro', '') if estado == 'Resuelto' else ''
    if centro_filtro:
        try:
            centro_pk = int(centro_filtro)
        except (ValueError, TypeError):
            return HttpResponseForbidden('Centro inválido.')
        if not centros.filter(pk=centro_pk).exists():
            return HttpResponseForbidden('Centro no autorizado.')
        pendientes = pendientes.filter(centro_operativo_id=centro_pk)
    buscar = (request.GET.get('buscar') or '').strip()[:80]
    if buscar:
        # Se filtra en SQL antes de paginar, sin limitarse a la página visible.
        pendientes = pendientes.annotate(importe_busqueda=Cast('importe', CharField()))
        condiciones = (Q(identificacion__icontains=buscar)
            | Q(referencia__icontains=buscar)
            | Q(echeq_numero__icontains=buscar)
            | Q(echeq_titular__icontains=buscar))
        numero = buscar.replace(' ', '').replace('$', '')
        if ',' in numero:
            numero = numero.replace('.', '').replace(',', '.')
        elif numero.count('.') > 1 or (numero.count('.') == 1 and len(numero.split('.')[-1]) == 3):
            numero = numero.replace('.', '')
        if numero and all(c in '0123456789.' for c in numero):
            condiciones |= Q(importe_busqueda__icontains=numero)
            try:
                valor = Decimal(numero)
                if valor.is_finite() and valor >= 0:
                    condiciones |= Q(importe=valor)
            except (InvalidOperation, ValueError):
                pass
        pendientes = pendientes.filter(condiciones)
    pendientes = pendientes.select_related('resuelto_por', 'creado_por', 'centro_operativo').order_by('-fecha', '-creado', '-pk')
    pagina = Paginator(pendientes, 25).get_page(request.GET.get('pagina', 1))
    es_general = centros_habilitados is None
    cuentas = CuentaBancaria.objects.filter(empresa=empresa, activo=True).select_related('banco').order_by('nombre') if (puede_cargar or puede_salidas) else []
    bancos_emisores = Banco.objects.filter(empresa=empresa, activo=True).order_by('nombre') if (puede_cargar or puede_salidas) else []
    proveedores_salida = Proveedor.objects.filter(empresa=empresa, activo=True).order_by('razon_social') if puede_salidas else []
    clientes_titulares = Cliente.objects.filter(empresa=empresa, activo=True).order_by('razon_social') if puede_cargar else []
    return render(request, 'usuarios/caja/gestion_bancaria.html', {
        'empresa': empresa, 'pagina': pagina, 'estado': estado,
        'centro_filtro': centro_filtro, 'centros': centros, 'cuentas': cuentas,
        'bancos_emisores': bancos_emisores, 'clientes_titulares': clientes_titulares,
        'proveedores_salida': proveedores_salida,
        'es_general': es_general,
        'puede_cargar':puede_cargar,'puede_salidas':puede_salidas,
        'puede_editar':puede_editar,'puede_resolver':puede_resolver,
        'puede_estado':puede_estado,'fecha_hoy': timezone.localdate(),
        'volver': _volver(request), 'usuario_id': request.user.pk,
        'buscar': buscar, 'fecha_minima_echeq': timezone.localdate() - timedelta(days=30),
    })


@login_required
@never_cache
@require_GET
@xframe_options_sameorigin
def abm_contextual_echeq(request, tipo):
    """ABM real desde e-Cheq, limitado a la Empresa activa y capacidad general.

    Reusa los mismos fragmentos Bancos/Clientes que el panel Administrador.
    La navegación al ABM y su retorno no conceden Caja ni crean un e-Cheq.
    """
    if tipo not in ('bancos', 'clientes', 'proveedores'):
        return HttpResponseForbidden('ABM no permitido.')
    try:
        empresa, alcance = _empresa_activa(request)
        if alcance is not None:
            raise PermissionDenied('Sólo administración general puede usar este ABM.')
    except (PermissionDenied, TypeError, ValueError):
        return HttpResponseForbidden('ABM de Empresa no autorizado.')
    if tipo == 'bancos':
        datos = {'empresa': empresa, 'bancos': Banco.objects.filter(empresa=empresa, activo=True).order_by('nombre')}
        contenido = render_to_string('usuarios/maestros/bancos.html', datos, request=request)
    elif tipo == 'proveedores':
        datos = {'empresa':empresa, 'proveedores':Proveedor.objects.filter(empresa=empresa).order_by('razon_social')}
        contenido = render_to_string('usuarios/maestros/proveedores.html', datos, request=request)
    else:
        datos = {
            'empresa': empresa,
            'clientes': Cliente.objects.filter(empresa=empresa, activo=True).select_related('centro_operativo').order_by('centro_operativo__nombre', 'numero_cliente'),
            'centros_operativos': CentroOperativo.objects.filter(empresa=empresa, activo=True).order_by('nombre'),
        }
        contenido = render_to_string('usuarios/maestros/clientes.html', datos, request=request)
    return render(request, 'usuarios/caja/abm_contextual_echeq.html', {
        'empresa': empresa, 'tipo': tipo, 'contenido_abm': contenido,
        'volver': reverse('gestion_bancaria'), 'usuario_id': request.user.pk,
    })


@login_required
@never_cache
@require_POST
def registrar_lote_bancario_http(request):
    if len(request.body) > 70000:
        return JsonResponse({'ok': False, 'mensaje': 'La carga es demasiado extensa.'}, status=400)
    try:
        empresa, _ = _empresa_activa(request)
        datos = json.loads(request.body.decode('utf-8'))
        if not isinstance(datos, dict):
            raise ValueError('La carga debe ser un objeto.')
        ids = registrar_lote(usuario=request.user, empresa_id=empresa.pk,
            cuenta_id=datos.get('cuenta'), clase=datos.get('clase'), filas=datos.get('filas'))
    except PermissionDenied:
        return JsonResponse({'ok': False, 'mensaje': 'No tiene autorización.'}, status=403)
    except ErrorFilaPendiente as error:
        return JsonResponse({'ok': False, 'mensaje': str(error),
                             'fila': error.fila, 'campo': error.campo}, status=400)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
        return JsonResponse({'ok': False, 'mensaje': str(error)}, status=400)
    return JsonResponse({'ok': True, 'ids': ids})


@login_required
@never_cache
@require_POST
def registrar_pendiente_bancario_http(request):
    # Endpoint legado: no permite cambiar Empresa por POST ni crear e-Cheq incompleto.
    from usuarios.services.pendientes_bancarios import registrar_pendiente
    try:
        empresa, _ = _empresa_activa(request)
        registrar_pendiente(usuario=request.user, empresa_id=empresa.pk, datos=request.POST)
    except PermissionDenied:
        return HttpResponseForbidden('No tiene autorización.')
    except (ValueError, TypeError) as error:
        return render(request, 'usuarios/caja/gestion_error.html', {'mensaje': str(error), 'volver': reverse('gestion_bancaria')}, status=400)
    return redirect('gestion_bancaria')


@login_required
@never_cache
@require_POST
def resolver_pendiente_bancario_http(request, pendiente_id):
    try:
        empresa, _ = _empresa_activa(request)
        resolver_pendiente(usuario=request.user, empresa_id=empresa.pk, pendiente_id=pendiente_id,
            centro_id=request.POST.get('centro'), identificacion=request.POST.get('identificacion', ''),
            tipo_resolucion=request.POST.get('tipo_resolucion', ''),
            referencia=request.POST.get('referencia_resolucion', ''))
    except PermissionDenied:
        return HttpResponseForbidden('No tiene autorización para resolver este pendiente.')
    except ValueError as error:
        return render(request, 'usuarios/caja/gestion_error.html', {'mensaje': str(error), 'volver': reverse('gestion_bancaria')}, status=409 if 'ya fue resuelto' in str(error) else 400)
    return redirect('gestion_bancaria')


@login_required
@never_cache
@require_GET
def configurar_permisos_bancarios(request):
    try:
        empresa, _ = _empresa_activa(request)
        contexto = obtener_contexto_capacidades_empresa(request.user, empresa.pk)
        if not (contexto.es_propietario or contexto.es_superusuario or contexto.jerarquia == 'admin_general'):
            raise PermissionDenied()
    except PermissionDenied:
        return HttpResponseForbidden('Solo administradores generales pueden configurar permisos.')
    colaboradores = get_user_model().objects.filter(
        asignaciones_empresas__empresa=empresa, asignaciones_empresas__activo=True,
        asignaciones_empresas__jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR,
        is_active=True).distinct().order_by('username')
    permisos = PermisoPendienteBancarioCentro.objects.filter(empresa=empresa,
        activo=True).select_related('usuario', 'centro_operativo').order_by('usuario__username')
    return render(request, 'usuarios/caja/gestion_permisos.html', {
        'empresa': empresa, 'colaboradores': colaboradores,
        'centros': CentroOperativo.objects.filter(empresa=empresa, activo=True).order_by('nombre'),
        'permisos': permisos,
        'incidencias': RevisionPendienteBancario.objects.filter(
            pendiente__empresa=empresa, tipo='Incidencia', estado='Abierto'
        ).select_related('pendiente','actor').order_by('-creado')[:100],
        'volver': _volver(request),
    })


@login_required
@never_cache
@require_POST
def asignar_centro_gestion_bancaria_http(request):
    try:
        empresa, _ = _empresa_activa(request)
        cambiar_permiso(admin=request.user, empresa_id=empresa.pk,
            usuario_id=request.POST.get('usuario'), centro_id=request.POST.get('centro'),
            activo=request.POST.get('activo'))
    except PermissionDenied:
        return HttpResponseForbidden('No tiene autorización para modificar permisos.')
    except ValueError as error:
        return render(request, 'usuarios/caja/gestion_error.html', {'mensaje': str(error), 'volver': reverse('configurar_permisos_bancarios')}, status=400)
    return redirect('configurar_permisos_bancarios')


@login_required
@never_cache
@require_POST
def clasificar_pendiente_bancario_http(request, pendiente_id):
    # Compatibilidad de ruta: ya no se clasifica antes de resolver.
    return JsonResponse({'ok': False, 'mensaje': 'El Centro se indica al confirmar la resolución.'}, status=409)
