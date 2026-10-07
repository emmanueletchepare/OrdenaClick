from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def panel_colaborador(request):
    """Muestra la entrada al perfil Colaborador."""
    return render(
        request,
        "usuarios/perfiles/colaborador/panel.html"
    )


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
