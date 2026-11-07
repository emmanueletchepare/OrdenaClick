"""Alertas de vencimiento del acuerdo de descubierto, sólo lectura.

La casilla de la Cuenta Bancaria habilita la fuente; el gestor existente
controla destinatarios. Nunca altera el acuerdo ni importes de Caja.
"""
from datetime import timedelta

from django.utils import timezone

from usuarios.models import CuentaBancaria
from usuarios.services.accesos_colaborador import puede
from usuarios.services.caja_bancos_informados import puede_ver_bancos

CODIGO = 'FIN-05'


def fuentes_bancos(empresa, hoy=None):
    """Devuelve acuerdos alertables por Empresa, incluidos ya vencidos."""
    hoy = hoy or timezone.localdate()
    cuentas = CuentaBancaria.objects.filter(
        empresa=empresa, activo=True, descubierto_alerta_habilitada=True,
        descubierto_importe__gt=0, descubierto_vencimiento__isnull=False,
    ).select_related('banco').order_by('pk')
    avisos = []
    for cuenta in cuentas:
        fecha = cuenta.descubierto_vencimiento
        if hoy < fecha - timedelta(days=cuenta.descubierto_alerta_dias):
            continue
        avisos.append({
            'codigo': CODIGO, 'grupo': 'descubierto_bancario', 'id': cuenta.pk,
            'nombre': cuenta.banco.nombre + ' · ' + cuenta.nombre,
            'fecha_vencimiento': fecha.isoformat(),
            'estado_alerta': 'Vencido' if fecha < hoy else 'Hoy' if fecha == hoy else 'Proximo',
        })
    return avisos


def aviso_bancario_autorizado(usuario, empresa, aviso):
    """No expone ni siquiera nombres bancarios a perfiles sin permiso Bancos."""
    return (aviso.get('codigo') == CODIGO
            and puede(usuario, empresa.pk, 'alertas.ver')
            and puede_ver_bancos(usuario, empresa.pk))


def avisos_bancos_visibles(usuario, empresa, hoy=None):
    """Aplica autorizaciones en cada lectura, también al llamador."""
    if not (puede(usuario, empresa.pk, 'alertas.ver')
            and puede_ver_bancos(usuario, empresa.pk)):
        return []
    return [a for a in fuentes_bancos(empresa, hoy)
            if aviso_bancario_autorizado(usuario, empresa, a)]


def avisos_bancos_publicos(usuario, empresa, hoy=None):
    """Contenido mínimo para la pantalla, sin importes ni IDs ajenos."""
    return [{k: a[k] for k in ('codigo','grupo','nombre','fecha_vencimiento','estado_alerta')}
            for a in avisos_bancos_visibles(usuario, empresa, hoy)]
