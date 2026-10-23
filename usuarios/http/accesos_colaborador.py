"""Gestión de accesos: propietario/general, GET consultivo, POST + CSRF + auditoría."""
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.db import transaction
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.clickjacking import xframe_options_sameorigin
from usuarios.models import AsignacionUsuarioEmpresa, PermisoAccesoColaborador, RolFuncionalUsuarioEmpresa, PermisoNominaCentro, CentroOperativo
from usuarios.services.accesos_colaborador import ARBOL, CODIGOS_HABILITABLES, exigir_administrar_permisos, colaborador_activo, guardar_accesos


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
@xframe_options_sameorigin
def gestion_accesos(request, empresa_id):
    try: empresa=exigir_administrar_permisos(request.user, empresa_id)
    except (PermissionDenied, TypeError, ValueError):return HttpResponseForbidden('No autorizado.')
    asignaciones=AsignacionUsuarioEmpresa.objects.filter(empresa=empresa,activo=True,jerarquia__in=('colaborador','admin_centro')).select_related('usuario').order_by('usuario__username')
    usuarios={a.usuario_id:a.usuario for a in asignaciones}
    # Roles funcionales independientes, sin necesidad de convertirlos en Colaboradores.
    funcionales = RolFuncionalUsuarioEmpresa.objects.filter(
        empresa=empresa, activo=True, rol__in=('contable','legal','rrhh')).select_related('usuario')
    for rol in funcionales:
        usuarios.setdefault(rol.usuario_id, rol.usuario)
    jerarquias = {a.usuario_id:a.jerarquia for a in asignaciones}
    try: seleccionado=int(request.POST.get('usuario') or request.GET.get('usuario') or 0)
    except (ValueError, TypeError):return HttpResponseForbidden('Usuario inválido.')
    if not seleccionado and usuarios:seleccionado=next(iter(usuarios))
    if seleccionado and seleccionado not in usuarios:return HttpResponseForbidden('Usuario ajeno.')
    if request.method=='POST':
        if not seleccionado:return HttpResponseForbidden('No hay un miembro configurable válido.')
        codigos=request.POST.getlist('capacidad')
        from usuarios.services.gestionar_nomina_accesos import guardar_permisos_operativos
        try:
            guardar_permisos_operativos(administrador=request.user,empresa_id=empresa.pk,
                usuario_id=seleccionado,codigos=codigos,centros_nomina=request.POST.getlist('nomina_centro'))
        except (PermissionDenied,ValueError,TypeError):
            return HttpResponseForbidden('No se pudieron guardar permisos.')
        return redirect(reverse('gestion_accesos_colaborador',args=[empresa.pk])+'?usuario='+str(seleccionado)+'&guardado=1')
    habilitados=set(PermisoAccesoColaborador.objects.filter(empresa=empresa,usuario_id=seleccionado,activo=True).values_list('codigo',flat=True)) if seleccionado else set()
    rol_actual = jerarquias.get(seleccionado)
    permitidos = CODIGOS_HABILITABLES if rol_actual in ('colaborador','admin_centro') else {'nomina.total'}
    if rol_actual != 'admin_centro': permitidos = set(permitidos)-{'caja.total'}
    arbol=[{'titulo':titulo,'codigo':str(i),'hijos':[{'nombre':nombre,'codigo':codigo,
        'activo':codigo in habilitados,
        'habilitable':codigo in permitidos} for nombre,codigo in hojas]}
        for i,(titulo,hojas) in enumerate(ARBOL)]
    # Sin casillas deshabilitadas o preseleccionadas por jerarquía. Sólo los
    # permisos ya guardados de forma explícita aparecen tildados.
    for seccion in arbol:
        seccion['tiene_habilitables'] = any(hijo['habilitable'] for hijo in seccion['hijos'])
        for hijo in seccion['hijos']:
            codigo = hijo['codigo']
            if codigo.startswith('pendientes.'):
                hijo['ayuda'] = 'Se gestiona desde permisos bancarios por Centro'
            elif codigo == 'caja.total' and rol_actual != 'admin_centro':
                hijo['ayuda'] = 'No disponible para este perfil'
            elif codigo.startswith('config.'):
                hijo['ayuda'] = 'Reservado a administración general'
            else:
                hijo['ayuda'] = 'Pendiente de integración con el servidor'
    centros = list(CentroOperativo.objects.filter(empresa=empresa,activo=True).order_by('nombre','pk'))
    centros_nomina = set(PermisoNominaCentro.objects.filter(empresa=empresa,usuario_id=seleccionado,activo=True)
                         .values_list('centro_operativo_id',flat=True))
    return render(request,'usuarios/empresa/gestion_accesos_colaborador.html',{
        'empresa':empresa,'colaboradores':usuarios.values(),'usuario_seleccionado':seleccionado,
        'arbol':arbol,'guardado':request.GET.get('guardado')=='1',
        'centros_nomina':centros,'centros_nomina_ids':centros_nomina,
        'es_admin_centro':rol_actual == 'admin_centro',
        'mostrar_centros_nomina':rol_actual != 'admin_centro',
    })
