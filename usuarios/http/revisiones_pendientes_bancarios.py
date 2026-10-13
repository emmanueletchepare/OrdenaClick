"""Revisiones POST + CSRF por Empresa activa y permisos de backend."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from usuarios.http.gestion_bancaria import _empresa_activa
from usuarios.services.revisiones_pendientes_bancarios import revisar_pendiente

@login_required
@never_cache
@require_POST
def revisar_pendiente_http(request, pendiente_id):
    if len(request.body) > 8192:
        return JsonResponse({'ok': False, 'mensaje':'Solicitud de revisión demasiado extensa.'},status=400)
    asincrono = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    try:
        empresa, _ = _empresa_activa(request)
        revision, _ = revisar_pendiente(
            usuario=request.user, empresa_id=empresa.pk, pendiente_id=pendiente_id,
            clave=request.POST.get('clave'), motivo=request.POST.get('motivo',''),
            datos=request.POST)
    except PermissionDenied:
        if asincrono: return JsonResponse({'ok':False,'mensaje':'No está autorizado para revisar ese movimiento.'},status=403)
        return HttpResponseForbidden('No está autorizado para revisar ese movimiento.')
    except (ValueError, TypeError) as exc:
        if asincrono: return JsonResponse({'ok':False,'mensaje':str(exc)},status=400)
        return render(request,'usuarios/caja/gestion_error.html',{
            'mensaje':str(exc),'volver':reverse('gestion_bancaria')}, status=400)
    ruta = reverse('gestion_bancaria') + ('?estado=Resuelto' if revision.tipo == 'Incidencia' else '')
    if asincrono: return JsonResponse({'ok':True,'destino':ruta,'tipo':revision.tipo})
    return redirect(ruta)
