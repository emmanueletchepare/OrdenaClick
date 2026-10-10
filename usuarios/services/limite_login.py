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
from django.utils import timezone

from usuarios.modelo_intentos_login import IntentoLoginOrigen


MAX_FALLOS = 25
VENTANA = timedelta(minutes=10)


def _origen(request):
    remoto = ipaddress.ip_address(request.META.get('REMOTE_ADDR', '')).compressed
    confiables = getattr(settings, 'ORDENACLICK_LOGIN_PROXIES_CONFIABLES', ())
    if remoto in confiables:
        cabecera = request.META.get('HTTP_X_FORWARDED_FOR', '')
        # Se toma el último valor: proxy directo debe agregar/sobrescribir
        # la cabecera (se requiere sobrescritura en despliegue).
        candidato = cabecera.split(',')[-1].strip() if cabecera else ''
        if candidato:
            remoto = ipaddress.ip_address(candidato).compressed
    return hmac.new(settings.SECRET_KEY.encode(), remoto.encode(), hashlib.sha256).hexdigest()


def bloqueado(request):
    origen = _origen(request)
    item = IntentoLoginOrigen.objects.filter(origen=origen).first()
    return bool(item and item.inicio_ventana > timezone.now() - VENTANA and item.fallos >= MAX_FALLOS)


def registrar_fallo(request):
    origen = _origen(request)
    ahora = timezone.now()
    with transaction.atomic():
        item, _ = IntentoLoginOrigen.objects.get_or_create(
            origen=origen,
            defaults={'inicio_ventana': ahora, 'fallos': 0},
        )
        # PostgreSQL bloquea la fila para serializar contadores concurrentes.
        item = IntentoLoginOrigen.objects.select_for_update().get(pk=item.pk)
        if item.inicio_ventana <= ahora - VENTANA:
            item.inicio_ventana = ahora
            item.fallos = 0
        item.fallos = min(item.fallos + 1, MAX_FALLOS)
        item.save(update_fields=['inicio_ventana', 'fallos'])


def limpiar_exito(request):
    IntentoLoginOrigen.objects.filter(origen=_origen(request)).delete()
