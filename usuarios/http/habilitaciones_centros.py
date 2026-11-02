"""Documentación de habilitación municipal; nunca es una operación de Caja."""
import mimetypes
import os
from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import FileResponse, Http404, JsonResponse
from django.utils.http import content_disposition_header
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import CentroOperativo, HabilitacionCentro
from usuarios.services.accesos_colaborador import exigir_abm
from usuarios.services.seguridad import obtener_centro_autorizado
from usuarios.services.documentos_empresa_b10a import validar_documentos_empresa


def _centro(usuario, empresa_id, centro_id):
    empresa = exigir_abm(usuario, empresa_id, 'abm.centros').empresa
    _, centro = obtener_centro_autorizado(usuario, empresa.pk, centro_id)
    return centro


@login_required
@require_POST
@never_cache
def agregar_habilitacion_centro(request):
    centro = _centro(request.user, request.POST.get('empresa'), request.POST.get('centro'))
    descripcion = (request.POST.get('descripcion') or '').strip()
    organismo = (request.POST.get('organismo') or '').strip()
    numero = (request.POST.get('numero') or '').strip()
    if not descripcion or len(descripcion) > 160 or len(organismo) > 160 or len(numero) > 100:
        return JsonResponse({'ok': False, 'mensaje': 'Completá una descripción válida (máximo 160 caracteres).'}, status=400)
    texto = (request.POST.get('vencimiento') or '').strip()
    try:
        vencimiento = date.fromisoformat(texto) if texto else None
    except ValueError:
        return JsonResponse({'ok': False, 'mensaje': 'La fecha de vencimiento no es válida.'}, status=400)
    try:
        validar_documentos_empresa(request.FILES, campos=('archivo',))
    except ValueError as exc:
        return JsonResponse({'ok': False, 'mensaje': str(exc)}, status=400)
    archivo = request.FILES.get('archivo')
    HabilitacionCentro.objects.create(
        centro=centro, descripcion=descripcion, organismo=organismo,
        numero=numero, vencimiento=vencimiento, archivo=archivo,
        creado_por=request.user.get_username()[:150],
    )
    return JsonResponse({'ok': True})


@login_required
@require_POST
@never_cache
@transaction.atomic
def archivar_habilitacion_centro(request):
    centro = _centro(request.user, request.POST.get('empresa'), request.POST.get('centro'))
    registro_id = request.POST.get('habilitacion') or ''
    if not registro_id.isascii() or not registro_id.isdecimal():
        raise Http404('Habilitación no encontrada.')
    registro = HabilitacionCentro.objects.select_for_update().filter(
        pk=int(registro_id), centro=centro).first()
    if registro is None:
        raise Http404('Habilitación no encontrada.')
    if registro.activo:
        registro.activo = False
        registro.actualizado_por = request.user.get_username()[:150]
        registro.save(update_fields=['activo', 'actualizado_por', 'modificado'])
    return JsonResponse({'ok': True})


@login_required
@require_GET
@never_cache
def descargar_habilitacion_centro(request, empresa_id, centro_id, habilitacion_id):
    centro = _centro(request.user, empresa_id, centro_id)
    registro = HabilitacionCentro.objects.filter(pk=habilitacion_id, centro=centro).first()
    if registro is None or not registro.archivo or not registro.archivo.name:
        raise Http404('Documento no disponible.')
    try:
        registro.archivo.open('rb')
    except (OSError, ValueError, FileNotFoundError):
        raise Http404('Documento no disponible.')
    nombre = os.path.basename(registro.archivo.name.replace('\\', '/'))
    tipo, _ = mimetypes.guess_type(nombre)
    admitidos = {'application/pdf', 'image/jpeg', 'image/png'}
    tipo = tipo if tipo in admitidos else 'application/octet-stream'
    respuesta = FileResponse(registro.archivo, content_type=tipo)
    respuesta['Content-Disposition'] = content_disposition_header(tipo == 'application/octet-stream', nombre)
    return respuesta
