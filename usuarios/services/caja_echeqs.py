"""Lectura consolidada de cartera e-Cheqs sin modificar sus estados."""
from decimal import Decimal

from django.db.models import Count, DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from usuarios.models import PendienteBancario


def resumen_echeqs_en_cartera(empresa):
    """Suma todos los e-Cheqs EnCartera de la Empresa sin mutar estados.

    Pendiente/Resuelto es gestión administrativa independiente; no se filtra.
    Este valor representa cartera, no acreditación bancaria garantizada.
    """
    return (PendienteBancario.objects
        .filter(empresa=empresa, tipo='ECheq', estado_cartera='EnCartera')
        .aggregate(cantidad=Count('pk'), total=Coalesce(
            Sum('importe'), Value(Decimal('0.00')),
            output_field=DecimalField(max_digits=18, decimal_places=2))))
