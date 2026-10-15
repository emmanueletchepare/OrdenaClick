"""API privada de la cartera virtual de e-Cheqs."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from usuarios.services.estados_echeq import consultar_estado, registrar_estado
from usuarios.services.pendientes_bancarios import alcance_pendientes


def _empresa(request):
    pk = request.session.get('gestion_bancaria_empresa')
    if not pk:
        raise PermissionDenied('Ingrese desde el menú de una Empresa.')
    return alcance_pendientes(request.user, pk)[0]


@login_required
@never_cache
@require_GET
def estado_echeq_detalle(request, pendiente_id):
    try:
        empresa = _empresa(request)
        datos = consultar_estado(usuario=request.user, empresa_id=empresa.pk,
                                 pendiente_id=pendiente_id)
    except (PermissionDenied, TypeError, ValueError):
        return JsonResponse({'ok': False, 'mensaje': 'Instrumento no autorizado.'}, status=403)
    return JsonResponse({'ok': True, **datos})


@login_required
@never_cache
@require_POST
def estado_echeq_registrar(request, pendiente_id):
    try:
        empresa = _empresa(request)
        _, creada = registrar_estado(
            usuario=request.user, empresa_id=empresa.pk, pendiente_id=pendiente_id,
            clave=request.POST.get('clave'), nuevo_estado=request.POST.get('estado'),
            fecha=request.POST.get('fecha'), observaciones=request.POST.get('observaciones', ''))
    except (PermissionDenied, TypeError):
        return JsonResponse({'ok': False, 'mensaje': 'No está autorizado.'}, status=403)
    except ValueError as exc:
        return JsonResponse({'ok': False, 'mensaje': str(exc)}, status=400)
    return JsonResponse({'ok': True, 'creada': creada})
