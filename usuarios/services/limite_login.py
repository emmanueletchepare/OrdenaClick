"""Protección básica de fuerza bruta compartida entre procesos Django.

No usa username: conocer la cuenta ajena no permite bloquearla globalmente.
En despliegue con proxy, configurar explícitamente los IP de proxies confiables
Y asegurar que el proxy SOBRESCRIBA X-Forwarded-For.
"""
import hashlib
import hmac
import ipaddress
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import Case, DateTimeField, F, PositiveIntegerField, Value, When
from django.db.models.functions import Least
from django.utils import timezone

from usuarios.modelo_intentos_login import IntentoLoginOrigen


MAX_FALLOS = 25
VENTANA = timedelta(minutes=10)


def _ip_o_none(value):
    try:
        return ipaddress.ip_address(value or '').compressed
    except (ValueError, TypeError):
        return None


def _origen(request):
    # Nunca aceptar una IP arbitraria del cliente por cabeceras reenviadas.
    remoto = _ip_o_none(request.META.get('REMOTE_ADDR'))
    confiables = getattr(settings, 'ORDENACLICK_LOGIN_PROXIES_CONFIABLES', ())
    if remoto and remoto in confiables:
        cabecera = request.META.get('HTTP_X_FORWARDED_FOR', '')
        # Usar sólo el último salto si el proxy directo está autorizado.
        candidato = cabecera.split(',')[-1].strip() if isinstance(cabecera, str) and cabecera else ''
        origen_proxy = _ip_o_none(candidato)
        if origen_proxy:
            remoto = origen_proxy
    # Una IP ausente o inválida comparte un bucket restrictivo, nunca libera el límite.
    remoto = remoto or 'origen-desconocido'
    return hmac.new(settings.SECRET_KEY.encode(), remoto.encode(), hashlib.sha256).hexdigest()


def bloqueado(request):
    origen = _origen(request)
    item = IntentoLoginOrigen.objects.filter(origen=origen).first()
    return bool(item and item.inicio_ventana > timezone.now() - VENTANA and item.fallos >= MAX_FALLOS)


def registrar_fallo(request):
    origen = _origen(request)
    ahora = timezone.now()
    # El índice unique sobre origen garantiza una única fila entre procesos.
    # get_or_create maneja el alta concurrente; el incremento se hace en SQL.
    with transaction.atomic():
        item, _ = IntentoLoginOrigen.objects.get_or_create(
            origen=origen,
            defaults={'inicio_ventana': ahora, 'fallos': 0},
        )
        # Un UPDATE atómico evita perder incrementos durante intentos simultáneos.
        IntentoLoginOrigen.objects.filter(pk=item.pk).update(
            inicio_ventana=Case(
                When(inicio_ventana__lte=ahora - VENTANA, then=Value(ahora)),
                default=F('inicio_ventana'),
                output_field=DateTimeField(),
            ),
            fallos=Case(
                When(inicio_ventana__lte=ahora - VENTANA, then=Value(1)),
                default=Least(F('fallos') + Value(1), Value(MAX_FALLOS)),
                output_field=PositiveIntegerField(),
            ),
        )


def limpiar_exito(request):
    IntentoLoginOrigen.objects.filter(origen=_origen(request)).delete()
