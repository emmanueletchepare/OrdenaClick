"""Configuración aislada para despliegue; no cambia el desarrollo local.

Activación explícita: DJANGO_SETTINGS_MODULE=ordenaclick.settings_production.
No desplegar hasta cerrar uploads privados, backups y pruebas de producción.
"""
import os
from pathlib import Path

from .settings import *  # noqa: F403,F401 - hereda únicamente la configuración existente


def _required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise RuntimeError(f'Falta variable obligatoria de producción: {name}')
    return value


def _csv(name):
    result = [s.strip() for s in _required(name).split(',') if s.strip()]
    if not result:
        raise RuntimeError(f'{name} no puede estar vacío')
    return result


DEBUG = False
ALLOWED_HOSTS = _csv('ORDENACLICK_ALLOWED_HOSTS')
if '*' in ALLOWED_HOSTS:
    raise RuntimeError('No se admite ALLOWED_HOSTS=* en producción')
CSRF_TRUSTED_ORIGINS = _csv('ORDENACLICK_CSRF_TRUSTED_ORIGINS')
if any(not origin.startswith('https://') or '*' in origin for origin in CSRF_TRUSTED_ORIGINS):
    raise RuntimeError('CSRF_TRUSTED_ORIGINS debe contener orígenes HTTPS explícitos')

# Sólo se activa mediante HTTPS real y un proxy configurado por infraestructura.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_SSL_REDIRECT = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
# HSTS se activa al validar HTTPS, subdominios y reverso; no imponemos riesgo DNS ahora.
SECURE_HSTS_SECONDS = 0

if os.environ.get('ORDENACLICK_TRUST_PROXY_HTTPS') == '1':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': _required('ORDENACLICK_DB_NAME'),
        'USER': _required('ORDENACLICK_DB_USER'),
        'PASSWORD': _required('ORDENACLICK_DB_PASSWORD'),
        'HOST': _required('ORDENACLICK_DB_HOST'),
        'PORT': os.environ.get('ORDENACLICK_DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }
}

# Dejar media aislado del árbol de código y fuera de cualquier raíz pública.
_media = Path(_required('ORDENACLICK_PRIVATE_MEDIA_ROOT')).expanduser().resolve()
if _media == BASE_DIR or BASE_DIR in _media.parents:
    raise RuntimeError('Los archivos privados no pueden almacenarse dentro del proyecto')
MEDIA_ROOT = _media

# El proxy/servidor no debe servir MEDIA_ROOT directamente: usar vistas autorizadas.
