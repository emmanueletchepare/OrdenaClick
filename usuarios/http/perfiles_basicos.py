from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse


@login_required
def panel_colaborador(request):
    """Ruta histórica: Colaborador usa ahora el acceso único Administrar."""
    empresa_id = request.session.get('gestion_bancaria_empresa') if (
        request.session.get('gestion_bancaria_origen') == 'colaborador'
    ) else None
    if empresa_id:
        return redirect(reverse('panel_administrar') + '?empresa=' + str(empresa_id))
    return redirect('panel_administrar')


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
