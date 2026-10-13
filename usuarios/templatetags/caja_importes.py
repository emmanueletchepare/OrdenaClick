"""Formato de importes ARS/USD independiente del idioma de ejecución."""
from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()

@register.filter(name='importe_ar')
def importe_ar(valor):
    try:
        numero = Decimal(str(valor))
        if not numero.is_finite():
            return '—'
        americano = f'{numero:,.2f}'
        return americano.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (InvalidOperation, TypeError, ValueError):
        return '—'
