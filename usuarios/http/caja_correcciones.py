"""Edición/anulación contable explícita; rechaza GET y exige CSRF."""
import json
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from usuarios.services.caja_correcciones import corregir_movimiento


@login_required
@never_cache
@require_POST
def corregir_movimiento_caja_http(request, movimiento_id):
    if len(request.body) > 8192:
        return JsonResponse({'ok': False, 'mensaje': 'Solicitud demasiado extensa.'}, status=400)
    try:
        datos = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({'ok': False, 'mensaje': 'Formato inválido.'}, status=400)
    if not isinstance(datos, dict):
        return JsonResponse({'ok': False, 'mensaje': 'Formato inválido.'}, status=400)
    try:
        correccion, creada = corregir_movimiento(
            usuario=request.user, empresa_id=datos.get('empresa_id'),
            caja_id=datos.get('caja_id'), movimiento_id=movimiento_id, datos=datos)
    except PermissionDenied:
        return JsonResponse({'ok': False, 'mensaje': 'Movimiento no autorizado para corrección.'}, status=403)
    except (ValueError, TypeError) as error:
        return JsonResponse({'ok': False, 'mensaje': str(error)}, status=409 if 'Identificador utilizado' in str(error) else 400)
    return JsonResponse({'ok': True, 'correccion_id': correccion.pk,
                         'mensaje': 'Corrección registrada sin borrar el historial.'}, status=201 if creada else 200)
