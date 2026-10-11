"""Configuración EXCLUSIVA para pruebas B9c; nunca usar para servir la app."""
import os
from .settings import *  # noqa: F401,F403


def required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise RuntimeError(f'B9c requiere variable explícita: {name}')
    return value

# Un nombre reservado a pruebas impide apuntar por accidente a la base operativa.
name = required('B9C_PG_DATABASE')
if not name.startswith('test_b9c_'):
    raise RuntimeError('B9C_PG_DATABASE debe comenzar con test_b9c_')

DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': name,
    'USER': required('B9C_PG_USER'),
    'PASSWORD': required('B9C_PG_PASSWORD'),
    'HOST': required('B9C_PG_HOST'),
    'PORT': os.environ.get('B9C_PG_PORT', '5432'),
    'CONN_MAX_AGE': 0,
    'TEST': {'NAME': 'test_' + name},
}}
# No hacer alteraciones de autenticación ni comportamiento de la aplicación.
