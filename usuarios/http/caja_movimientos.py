"""Vistas operativas de efectivo de Caja; no reutilizar como traslado ni Pago."""
import json
import uuid

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from datetime import date, timedelta
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import MovimientoCaja
from usuarios.services.seguridad import obtener_caja_autorizada, cajas_autorizadas
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
    html = render_to_string('usuarios/caja/movimientos.html', {
        'empresa': empresa, 'caja': caja,
        'fecha_hoy': timezone.localdate(), 'clave': uuid.uuid4(),
    }, request=request)
    return JsonResponse({'ok': True, 'html': html})


@login_required
@never_cache
@require_GET
def historial_movimientos_caja_http(request):
    """Historial de movimientos limitado a Cajas autorizadas por servidor.

    'todas' reune solamente las Cajas de alcance real del usuario.
    Las fechas son de los movimientos, no su momento de creacion.
    """
    try:
        empresa, cajas = cajas_autorizadas(request.user, request.GET.get('empresa'))
    except (PermissionDenied, ValueError, TypeError):
        return JsonResponse({'ok': False, 'mensaje': 'No tiene acceso al historial solicitado.'}, status=403)

    caja_param = request.GET.get('caja', '')
    if caja_param == 'todas':
        mostrar_caja = True
    elif caja_param:
        try:
            caja_elegida = cajas.get(pk=caja_param)
        except (TypeError, ValueError, cajas.model.DoesNotExist):
            return JsonResponse({'ok': False, 'mensaje': 'No tiene acceso a esa Caja.'}, status=403)
        cajas = cajas.filter(pk=caja_elegida.pk)
        mostrar_caja = False
    else:
        return JsonResponse({'ok': False, 'mensaje': 'Seleccione una Caja autorizada.'}, status=400)

    modo = request.GET.get('modo', 'hoy')
    if modo == 'hoy':
        desde = hasta = timezone.localdate()
    elif modo == 'rango':
        inicio = request.GET.get('desde', '')
        fin = request.GET.get('hasta', '')
        if not (len(inicio) == len(fin) == 10):
            return JsonResponse({'ok': False, 'mensaje': 'Seleccione fechas validas.'}, status=400)
        try:
            desde, hasta = date.fromisoformat(inicio), date.fromisoformat(fin)
        except ValueError:
            return JsonResponse({'ok': False, 'mensaje': 'Seleccione fechas validas.'}, status=400)
        if desde.isoformat() != inicio or hasta.isoformat() != fin or desde > hasta:
            return JsonResponse({'ok': False, 'mensaje': 'El rango de fechas no es valido.'}, status=400)
        if hasta - desde > timedelta(days=366):
            return JsonResponse({'ok': False, 'mensaje': 'El rango maximo es de 367 dias.'}, status=400)
    else:
        return JsonResponse({'ok': False, 'mensaje': 'Filtro de fechas no valido.'}, status=400)

    historial = (MovimientoCaja.objects.filter(
        empresa=empresa, caja__in=cajas, fecha__gte=desde, fecha__lte=hasta)
        .select_related('creado_por', 'caja__centro_operativo')
        .order_by('-fecha', '-creado', '-pk'))
    pagina = Paginator(historial, 25).get_page(request.GET.get('pagina', 1))
    html = render_to_string('usuarios/caja/historial.html', {
        'pagina': pagina, 'mostrar_caja': mostrar_caja,
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
