from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    RolFuncionalUsuarioEmpresa,
    SolicitudRelacionEmpresa,
)
from usuarios.services.relaciones import (
    crear_solicitud_relacion,
    resolver_solicitud_relacion,
)
from usuarios.services.seguridad import obtener_empresa_administrable


@login_required
def panel_relaciones(request):
    """Muestra solicitudes pendientes y vínculos actuales del usuario."""
    pendientes = (
        SolicitudRelacionEmpresa.objects
        .filter(
            usuario_destino=request.user,
            estado=SolicitudRelacionEmpresa.ESTADO_PENDIENTE,
        )
        .select_related("empresa", "solicitada_por", "centro_operativo")
        .order_by("-creada")
    )

    jerarquias = (
        AsignacionUsuarioEmpresa.objects
        .filter(usuario=request.user, activo=True)
        .select_related("empresa", "centro_operativo")
        .order_by("empresa__nombre_fantasia", "empresa__razon_social")
    )

    roles_funcionales = (
        RolFuncionalUsuarioEmpresa.objects
        .filter(usuario=request.user, activo=True)
        .select_related("empresa")
        .order_by("empresa__nombre_fantasia", "empresa__razon_social", "rol")
    )

    empresas_fundadas = (
        request.user.empresas_propias
        .all()
        .order_by("nombre_fantasia", "razon_social")
    )

    return render(
        request,
        "usuarios/relaciones/panel_relaciones.html",
        {
            "pendientes": pendientes,
            "jerarquias": jerarquias,
            "roles_funcionales": roles_funcionales,
            "empresas_fundadas": empresas_fundadas,
        },
    )


@login_required
def gestionar_relaciones_empresa(request, empresa_id):
    """Permite gestionar solicitudes sin sacar al usuario del panel de Empresa."""
    empresa = obtener_empresa_administrable(request.user, empresa_id)
    es_fragmento = (
        request.GET.get("fragment") == "1"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )

    if request.method == "POST":
        try:
            solicitud = crear_solicitud_relacion(
                solicitante=request.user,
                empresa_id=empresa.id,
                identificador_usuario=request.POST.get("usuario"),
                rol=request.POST.get("rol"),
                centro_id=request.POST.get("centro_operativo") or None,
                mensaje=request.POST.get("mensaje") or "",
            )
        except ValidationError as error:
            messages.error(request, " ".join(error.messages))
        else:
            messages.success(
                request,
                f"Solicitud enviada a {solicitud.usuario_destino.username}.",
            )
            if not es_fragmento:
                return redirect("gestionar_relaciones_empresa", empresa_id=empresa.id)

    pendientes = (
        SolicitudRelacionEmpresa.objects
        .filter(empresa=empresa, estado=SolicitudRelacionEmpresa.ESTADO_PENDIENTE)
        .select_related("usuario_destino", "solicitada_por", "centro_operativo")
        .order_by("-creada")
    )
    jerarquias = (
        AsignacionUsuarioEmpresa.objects
        .filter(empresa=empresa)
        .select_related("usuario", "centro_operativo")
        .order_by("usuario__username")
    )
    roles_funcionales = (
        RolFuncionalUsuarioEmpresa.objects
        .filter(empresa=empresa)
        .select_related("usuario")
        .order_by("usuario__username", "rol")
    )
    centros = empresa.centros.filter(activo=True).order_by("nombre")
    contexto = {
        "empresa": empresa,
        "pendientes": pendientes,
        "jerarquias": jerarquias,
        "roles_funcionales": roles_funcionales,
        "centros": centros,
        "roles": SolicitudRelacionEmpresa.ROLES,
    }
    template = (
        "usuarios/empresa/designar_relaciones_fragment.html"
        if es_fragmento
        else "usuarios/empresa/designar_relaciones.html"
    )
    return render(request, template, contexto)


@login_required
@require_POST
def resolver_solicitud(request, solicitud_id, accion):
    """Resuelve una solicitud recibida sin permitir IDOR entre usuarios."""
    try:
        solicitud = resolver_solicitud_relacion(
            usuario=request.user,
            solicitud_id=solicitud_id,
            accion=accion,
        )
    except (ValidationError, PermissionDenied) as error:
        messages.error(request, str(error))
    else:
        verbo = "aceptada" if accion == "aceptar" else "rechazada"
        messages.success(
            request,
            f"Solicitud de {solicitud.get_rol_display()} {verbo}.",
        )

    return redirect("panel_relaciones")
