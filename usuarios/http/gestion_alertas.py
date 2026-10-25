"""Gestión por usuario, mismo patrón que Gestión de accesos; sonido personal."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_http_methods

from usuarios.models import DestinatarioAlerta
from usuarios.services.accesos_colaborador import exigir, exigir_administrar_permisos
from usuarios.services.catalogo_alertas import CATEGORIAS, TIPOS_ALERTA, tipos_operativos
from usuarios.services.destinatarios_alertas import (
    alertas_sin_destinatarios, alcance_fuente, guardar_destinatarios_usuario,
    guardar_sonido_propio, miembros_empresa, sonido_habilitado,
)


def _usuario_elegido(request, usuarios):
    """El identificador de la URL o POST debe estar dentro de esta Empresa."""
    texto = (request.POST.get('usuario') if request.method == 'POST'
             else request.GET.get('usuario'))
    if not texto:
        if request.method == 'POST':
            raise ValueError('Debe seleccionar un usuario.')
        return usuarios[0].pk if usuarios else None
    if not texto.isascii() or not texto.isdecimal():
        raise ValueError('Usuario inválido.')
    elegido = int(texto)
    if not any(u.pk == elegido for u in usuarios):
        raise PermissionDenied('Usuario ajeno o inactivo.')
    return elegido


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
@xframe_options_sameorigin
def gestion_alertas(request, empresa_id):
    try:
        empresa = exigir_administrar_permisos(request.user, empresa_id)
    except (PermissionDenied, ValueError, TypeError):
        return HttpResponseForbidden('No autorizado.')
    usuarios = miembros_empresa(empresa)
    try:
        elegido = _usuario_elegido(request, usuarios)
    except (PermissionDenied, TypeError, ValueError):
        return HttpResponseForbidden('Usuario no autorizado.')
    if request.method == 'POST':
        if request.POST.get('formulario') != 'destinatarios-usuario':
            return HttpResponseForbidden('Formulario no autorizado.')
        try:
            guardar_destinatarios_usuario(
                administrador=request.user, empresa_id=empresa.pk,
                usuario_id=elegido, codigos=request.POST.getlist('codigo'),
            )
        except (PermissionDenied, TypeError, ValueError):
            return HttpResponseForbidden('Alertas no autorizadas.')
        return redirect(reverse('gestion_alertas', args=[empresa.pk]) +
                        f'?usuario={elegido}&guardado=1')

    elegido_obj = next((u for u in usuarios if u.pk == elegido), None)
    activos = set(DestinatarioAlerta.objects.filter(
        empresa=empresa, usuario_id=elegido, activo=True).values_list('codigo', flat=True)
    ) if elegido is not None else set()
    secciones = []
    for categoria in CATEGORIAS:
        hijos = []
        for tipo in (t for t in TIPOS_ALERTA if t.categoria == categoria):
            elegible = (alcance_fuente(elegido_obj, empresa, tipo.codigo)[0]
                        if elegido_obj is not None and tipo.operativa else False)
            hijos.append({
                'tipo': tipo,
                'habilitable': elegible,
                'activo': elegible and tipo.codigo in activos,
                'ayuda': ('Todavía no operativa' if not tipo.operativa else
                          'Sin acceso vigente al módulo de origen' if not elegible else ''),
            })
        secciones.append({'titulo': categoria, 'codigo': categoria,
                          'hijos': hijos, 'tiene_habilitables': any(h['habilitable'] for h in hijos)})
    pendientes = {item['codigo']: item for item in alertas_sin_destinatarios(empresa)}
    sin_destinatarios = [dict(tipo=tipo, **pendientes[tipo.codigo])
                         for tipo in tipos_operativos() if tipo.codigo in pendientes]
    return render(request, 'usuarios/empresa/gestion_alertas.html', {
        'empresa': empresa, 'colaboradores': usuarios, 'usuario_seleccionado': elegido,
        'secciones': secciones, 'sin_destinatarios': sin_destinatarios,
        'guardado': request.GET.get('guardado') == '1',
    })


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
def sonido_alertas_usuario(request):
    """Preferencia estrictamente propia. POST protegido por CSRF de Django."""
    empresa_id = (request.GET.get('empresa') or request.POST.get('empresa') or '').strip()
    try:
        empresa = exigir(request.user, empresa_id, 'alertas.ver')
        if not any(u.pk == request.user.pk for u in miembros_empresa(empresa)):
            raise PermissionDenied('Sin vínculo vigente.')
    except (PermissionDenied, ValueError, TypeError):
        return HttpResponseForbidden('No autorizado.')
    if request.method == 'POST':
        valor = request.POST.get('habilitado')
        if valor not in ('0', '1'):
            return JsonResponse({'ok': False, 'mensaje': 'Valor inválido.'}, status=400)
        try:
            guardar_sonido_propio(usuario=request.user, empresa_id=empresa.pk,
                                 habilitado=valor == '1')
        except (PermissionDenied, TypeError, ValueError):
            return HttpResponseForbidden('No autorizado.')
    return JsonResponse({'ok': True, 'habilitado': sonido_habilitado(request.user, empresa)})
