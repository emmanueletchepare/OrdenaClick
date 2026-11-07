"""Crea una Caja inicial si un Centro operativo todavía no posee ninguna.

Nunca crea Cajas en Depósitos. No se usa como señal global: la restauración
Backup Empresa v1 y los fixtures preservan su propio historial y sus Cajas.
"""
from django.db import transaction
from usuarios.models import Caja, CentroOperativo

TIPOS_CON_CAJA = frozenset(('Casa Central', 'Sucursal', 'Mostrador'))


def asegurar_caja_inicial(centro):
    """Devuelve (Caja o None, creada) sin duplicar ni reactivar Cajas previas.

    Bloquea el Centro en PostgreSQL para serializar el alta y protege el caso
    en que ya exista cualquier Caja, incluso inactiva o con otro nombre.
    Se invoca desde las altas autorizadas y desde regularización explícita.
    """
    if centro is None or centro.pk is None:
        raise ValueError('Se requiere un Centro Operativo persistido.')
    with transaction.atomic():
        actual = CentroOperativo.objects.select_for_update().get(pk=centro.pk)
        if not actual.activo or actual.tipo not in TIPOS_CON_CAJA:
            return None, False
        anterior = (Caja.objects.filter(
            empresa_id=actual.empresa_id,
            centro_operativo_id=actual.pk,
        ).order_by('pk').first())
        if anterior is not None:
            return anterior, False
        caja, creada = Caja.objects.get_or_create(
            empresa_id=actual.empresa_id,
            centro_operativo_id=actual.pk,
            nombre='CAJA PRINCIPAL',
            defaults={'activo': True},
        )
        return caja, creada
