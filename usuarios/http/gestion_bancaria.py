"""Bandeja de aplicación de operaciones vistas en el banco (sin contabilizar)."""
import logging
import uuid
from urllib.parse import urlencode
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import (AsignacionUsuarioEmpresa, CentroOperativo, CuentaBancaria,
    Empresa, PendienteBancario, PermisoPendienteBancarioCentro)
from usuarios.services.pendientes_bancarios import (
    alcance_pendientes, cambiar_permiso, exigir_centro,
    registrar_pendiente, resolver_pendiente, clasificar_pendiente)


def _empresas_posibles(usuario):
    if usuario.is_superuser:
        return Empresa.objects.all().order_by('razon_social')
    return Empresa.objects.filter(Q(propietario=usuario) | Q(
        asignaciones_usuarios__usuario=usuario, asignaciones_usuarios__activo=True,
        asignaciones_usuarios__jerarquia__in=['admin_general', 'admin_centro']) | Q(
        permisos_pendientes_bancarios__usuario=usuario,
        permisos_pendientes_bancarios__activo=True,
        permisos_pendientes_bancarios__centro_operativo__activo=True)).distinct().order_by('razon_social')


def _url(empresa_id):
    return reverse('gestion_bancaria') + '?' + urlencode({'empresa': empresa_id})


@login_required
@never_cache
@require_GET
def gestion_bancaria(request):
    empresas = _empresas_posibles(request.user)
    empresa_id = request.GET.get('empresa')
    if not empresa_id:
        return render(request, 'usuarios/caja/gestion_bancaria.html', {
            'empresas': empresas, 'empresa': None,
        })
    try:
        empresa, permitidos = alcance_pendientes(request.user, empresa_id)
    except (PermissionDenied, ValueError, TypeError):
        return HttpResponseForbidden('No tiene autorización para consultar pendientes de esta Empresa.')
    centros = CentroOperativo.objects.filter(empresa=empresa, activo=True).order_by('nombre')
    if permitidos is not None:
        centros = centros.filter(pk__in=permitidos)
    cuenta = CuentaBancaria.objects.filter(empresa=empresa, activo=True).select_related('banco').order_by('nombre')
    estado = request.GET.get('estado', 'Pendiente')
    if estado not in ('Pendiente', 'Resuelto'):
        return HttpResponseForbidden('Filtro de estado inválido.')
    pendientes = PendienteBancario.objects.filter(empresa=empresa, estado=estado)
    if permitidos is not None:
        pendientes = pendientes.filter(centro_operativo_id__in=permitidos)
    centro_filtro = request.GET.get('centro', '')
    if centro_filtro:
        try:
            centro_pk = exigir_centro(centro_filtro, permitidos)
        except PermissionDenied:
            return HttpResponseForbidden('Centro fuera de alcance.')
        if not centros.filter(pk=centro_pk).exists():
            return HttpResponseForbidden('Centro fuera de alcance.')
        pendientes = pendientes.filter(centro_operativo_id=centro_pk)
    pendientes = pendientes.select_related('cuenta_bancaria__banco', 'centro_operativo',
        'creado_por', 'resuelto_por').order_by('-fecha', '-creado', '-pk')
    pagina = Paginator(pendientes, 25).get_page(request.GET.get('pagina', 1))
    es_general = permitidos is None
    es_administrador = es_general  # Quien consulta bancos, no quien sólo resuelve tareas.
    colaboradores = get_user_model().objects.filter(asignaciones_empresas__empresa=empresa,
        asignaciones_empresas__activo=True, asignaciones_empresas__jerarquia='colaborador',
        is_active=True).order_by('username') if es_general else []
    permisos = PermisoPendienteBancarioCentro.objects.filter(empresa=empresa,
        activo=True).select_related('usuario', 'centro_operativo').order_by('usuario__username') if es_general else []
    return render(request, 'usuarios/caja/gestion_bancaria.html', {
        'empresas': empresas, 'empresa': empresa, 'centros': centros, 'cuentas': cuenta,
        'estado': estado, 'centro_filtro': centro_filtro, 'pagina': pagina,
        'es_general': es_general, 'es_administrador': es_administrador,
        'colaboradores': colaboradores, 'permisos': permisos,
        'fecha_hoy': timezone.localdate(), 'clave': uuid.uuid4(),
        'aviso': request.GET.get('aviso', ''),
    })


def _error(request, mensaje, empresa_id, status=400):
    # Los valores no secretos del POST se conservan para que el usuario
    # pueda corregirlos; contraseñas, tokens y claves nunca se repueblan.
    return render(request, 'usuarios/caja/gestion_error.html', {
        'mensaje': mensaje, 'empresa_id': empresa_id,
        'datos': {k: v for k, v in request.POST.items() if k not in ('csrfmiddlewaretoken', 'clave')},
        'clave_nueva': uuid.uuid4(),
    }, status=status)


@login_required
@never_cache
@require_POST
def registrar_pendiente_bancario_http(request):
    empresa_id = request.POST.get('empresa')
    try:
        registrar_pendiente(usuario=request.user, empresa_id=empresa_id, datos=request.POST)
    except PermissionDenied:
        return HttpResponseForbidden('No tiene autorización para registrar este pendiente.')
    except (ValueError, TypeError) as exc:
        return _error(request, str(exc), empresa_id)
    return redirect(_url(empresa_id))


@login_required
@never_cache
@require_POST
def resolver_pendiente_bancario_http(request, pendiente_id):
    empresa_id = request.POST.get('empresa')
    try:
        resolver_pendiente(usuario=request.user, empresa_id=empresa_id, pendiente_id=pendiente_id,
            tipo_resolucion=request.POST.get('tipo_resolucion'), referencia=request.POST.get('referencia_resolucion', ''))
    except PermissionDenied:
        return HttpResponseForbidden('No tiene autorización para resolver este pendiente.')
    except (ValueError, TypeError) as exc:
        return _error(request, str(exc), empresa_id, status=409 if 'ya fue resuelto' in str(exc) else 400)
    return redirect(_url(empresa_id))


@login_required
@never_cache
@require_POST
def asignar_centro_gestion_bancaria_http(request):
    empresa_id = request.POST.get('empresa')
    try:
        cambiar_permiso(admin=request.user, empresa_id=empresa_id,
            usuario_id=request.POST.get('usuario'), centro_id=request.POST.get('centro'),
            activo=request.POST.get('activo'))
    except PermissionDenied:
        return HttpResponseForbidden('No tiene autorización para administrar permisos.')
    except (ValueError, TypeError) as exc:
        return _error(request, str(exc), empresa_id)
    return redirect(_url(empresa_id))


@login_required
@never_cache
@require_POST
def clasificar_pendiente_bancario_http(request, pendiente_id):
    empresa_id = request.POST.get('empresa')
    try:
        clasificar_pendiente(admin=request.user, empresa_id=empresa_id,
            pendiente_id=pendiente_id, centro_id=request.POST.get('centro'))
    except PermissionDenied:
        return HttpResponseForbidden('No tiene autorización para clasificar este pendiente.')
    except (ValueError, TypeError) as exc:
        return _error(request, str(exc), empresa_id)
    return redirect(_url(empresa_id))
