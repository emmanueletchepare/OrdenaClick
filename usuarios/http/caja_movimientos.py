"""Vistas operativas de efectivo de Caja; no reutilizar como traslado ni Pago."""
import json
import uuid

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import MovimientoCaja
from usuarios.services.seguridad import obtener_caja_autorizada
from usuarios.services.caja_movimientos import (
    ConflictoIdempotenciaCaja, registrar_movimiento_caja,
)


@login_required
@never_cache
@require_GET
def vista_movimientos_caja(request):
    try:
        empresa, caja = obtener_caja_autorizada(
            request.user, request.GET.get('empresa'), request.GET.get('caja'))
    except PermissionDenied:
        return JsonResponse({'ok': False, 'mensaje': 'No tiene autorizacion para esa Caja.'}, status=403)
    historial = (MovimientoCaja.objects.filter(empresa=empresa, caja=caja)
                 .select_related('creado_por')
                 .order_by('-fecha', '-creado', '-pk'))
    pagina = Paginator(historial, 25).get_page(request.GET.get('pagina', 1))
    html = render_to_string('usuarios/caja/movimientos.html', {
        'empresa': empresa, 'caja': caja, 'pagina': pagina,
        'fecha_hoy': timezone.localdate(), 'clave': uuid.uuid4(),
    }, request=request)
    return JsonResponse({'ok': True, 'html': html})


@login_required
@never_cache
@require_POST
def registrar_movimiento_caja_http(request):
    if len(request.body) > 8192:
        return JsonResponse({'ok': False, 'mensaje': 'El movimiento enviado es demasiado extenso.'}, status=400)
    try:
        datos = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({'ok': False, 'mensaje': 'Formato de movimiento invalido.'}, status=400)
    if not isinstance(datos, dict):
        return JsonResponse({'ok': False, 'mensaje': 'Formato de movimiento invalido.'}, status=400)
    try:
        empresa, caja = obtener_caja_autorizada(
            request.user, datos.get('empresa_id'), datos.get('caja_id'))
    except PermissionDenied:
        return JsonResponse({'ok': False, 'mensaje': 'No tiene autorizacion para esa Caja.'}, status=403)
    try:
        respuesta, creado = registrar_movimiento_caja(
            empresa=empresa, caja=caja, usuario=request.user, datos=datos.get('movimiento'))
    except PermissionDenied:
        return JsonResponse({'ok': False, 'mensaje': 'No tiene autorizacion para esa Caja.'}, status=403)
    except ConflictoIdempotenciaCaja as error:
        return JsonResponse({'ok': False, 'mensaje': str(error)}, status=409)
    except ValueError as error:
        return JsonResponse({'ok': False, 'mensaje': str(error)}, status=400)
    return JsonResponse(respuesta, status=201 if creado else 200)
