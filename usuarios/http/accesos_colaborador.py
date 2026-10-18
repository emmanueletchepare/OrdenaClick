"""Gestión de accesos: propietario/general, GET consultivo, POST + CSRF + auditoría."""
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.clickjacking import xframe_options_sameorigin
from usuarios.models import AsignacionUsuarioEmpresa, PermisoAccesoColaborador
from usuarios.services.accesos_colaborador import ARBOL, CODIGOS_HABILITABLES, exigir_administrar_permisos, colaborador_activo, guardar_accesos


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
@xframe_options_sameorigin
def gestion_accesos(request, empresa_id):
    try: empresa=exigir_administrar_permisos(request.user, empresa_id)
    except (PermissionDenied, TypeError, ValueError):return HttpResponseForbidden('No autorizado.')
    asignaciones=AsignacionUsuarioEmpresa.objects.filter(empresa=empresa,activo=True,jerarquia='colaborador').select_related('usuario').order_by('usuario__username')
    usuarios={a.usuario_id:a.usuario for a in asignaciones}
    try: seleccionado=int(request.POST.get('usuario') or request.GET.get('usuario') or 0)
    except (ValueError, TypeError):return HttpResponseForbidden('Usuario inválido.')
    if not seleccionado and usuarios:seleccionado=next(iter(usuarios))
    if seleccionado and seleccionado not in usuarios:return HttpResponseForbidden('Usuario ajeno.')
    if request.method=='POST':
        if not seleccionado:return HttpResponseForbidden('No hay Colaborador válido.')
        codigos=request.POST.getlist('capacidad')
        try:guardar_accesos(administrador=request.user,empresa_id=empresa.pk,colaborador_id=seleccionado,codigos=codigos)
        except (PermissionDenied,ValueError):return HttpResponseForbidden('No se pudieron guardar permisos.')
        return redirect(reverse('gestion_accesos_colaborador',args=[empresa.pk])+'?usuario='+str(seleccionado)+'&guardado=1')
    habilitados=set(PermisoAccesoColaborador.objects.filter(empresa=empresa,usuario_id=seleccionado,activo=True).values_list('codigo',flat=True)) if seleccionado else set()
    arbol=[{'titulo':titulo,'codigo':str(i),'hijos':[{'nombre':nombre,'codigo':codigo,'activo':codigo in habilitados, 'habilitable':codigo in CODIGOS_HABILITABLES} for nombre,codigo in hojas]} for i,(titulo,hojas) in enumerate(ARBOL)]
    return render(request,'usuarios/empresa/gestion_accesos_colaborador.html',{
        'empresa':empresa,'colaboradores':usuarios.values(),'usuario_seleccionado':seleccionado,
        'arbol':arbol,'guardado':request.GET.get('guardado')=='1',
    })
