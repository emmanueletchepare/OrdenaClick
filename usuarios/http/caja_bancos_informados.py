"""Actualización manual de bancos desde Caja: no realiza operaciones financieras."""
import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from usuarios.services.caja_bancos_informados import guardar_posiciones


@login_required
@require_POST
def actualizar_disponibles_bancarios(request):
    """Guarda exclusivamente importes informados con permiso bancario explícito."""
    try:
        datos = json.loads(request.body)
        if not isinstance(datos, dict):
            raise ValueError('Solicitud inválida.')
        creado = guardar_posiciones(usuario=request.user, empresa_id=datos.get('empresa'),
            clave=datos.get('clave'), filas=datos.get('filas'))
    except PermissionDenied as exc:
        return JsonResponse({'ok': False, 'mensaje': str(exc)}, status=403)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return JsonResponse({'ok': False, 'mensaje': str(exc)}, status=400)
    return JsonResponse({'ok': True, 'actualizado': creado})
