from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from usuarios.models import Empresa
from usuarios.services.pendientes_bancarios import alcance_pendientes


@login_required
def panel_colaborador(request):
    """Muestra la entrada al perfil Colaborador."""
    posibles = Empresa.objects.filter(
        Q(propietario=request.user) |
        Q(asignaciones_usuarios__usuario=request.user, asignaciones_usuarios__activo=True) |
        Q(permisos_pendientes_bancarios__usuario=request.user, permisos_pendientes_bancarios__activo=True)
    ).distinct().order_by('razon_social')
    empresas = []
    for empresa in posibles:
        try:
            alcance_pendientes(request.user, empresa.pk)
        except PermissionDenied:
            continue
        empresas.append(empresa)
    return render(request, 'usuarios/perfiles/colaborador/panel.html', {
        'empresas_pendientes': empresas,
    })


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
