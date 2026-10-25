"""Bloque B: tipos documentados de Alertas. No otorga permisos ni genera eventos.

Un tipo sólo pasa a ``operativa=True`` después de implementar y probar su
fuente, reglas de origen y controles de Empresa/Centro. Nunca activar una idea
por agregarla al catálogo. El Gestor utilizará esta fuente inmutable de tipos.
"""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TipoAlerta:
    codigo: str
    categoria: str
    nombre: str
    origen: str
    alcance: str
    operativa: bool = False


TIPOS_ALERTA = (
    TipoAlerta('FIN-01', 'Financieras', 'Vencimiento de Movimientos con saldo pendiente',
               'Movimientos', 'Empresa/Centro según el Movimiento', True),
    TipoAlerta('FIN-02', 'Financieras', 'Vencimiento de cheques físicos',
               'Cartera física y cheques propios emitidos', 'Empresa/Caja/Centro y origen', True),
    TipoAlerta('FIN-03', 'Financieras', 'Vencimiento de e-Cheqs',
               'Cartera electrónica y e-Cheqs propios emitidos', 'Empresa/Centro y origen', True),
    TipoAlerta('FIN-04', 'Financieras', 'Vencimiento de cuotas de registros planificados',
               'Registro planificado', 'Empresa/Centro por definir'),
    TipoAlerta('ADM-01', 'Administrativas', 'Orden de Pago lista para imprimir o aplicar',
               'Orden de Pago', 'Empresa/Centro por definir'),
    TipoAlerta('NOM-01', 'Nómina', 'Vencimiento de licencia de conducir',
               'Nómina de Empleados', 'Empresa/Centro del empleado', True),
    TipoAlerta('NOM-02', 'Nómina', 'Vencimiento de plazos de documentación de cese laboral',
               'Documentación de cese laboral', 'Empresa/Centro por definir'),
    TipoAlerta('DOC-01', 'Documentales', 'Renovación o revisión de acta de directorio',
               'Documentación de Empresa', 'Empresa'),
    TipoAlerta('DOC-02', 'Documentales', 'Renovación o revisión de acta de asamblea',
               'Documentación de Empresa', 'Empresa'),
    TipoAlerta('DOC-03', 'Documentales', 'Vencimiento de habilitación municipal',
               'Habilitación del Centro Operativo (pendiente de diseñar)', 'Centro Operativo'),
)

TIPOS_POR_CODIGO = {tipo.codigo: tipo for tipo in TIPOS_ALERTA}
CODIGOS_OPERATIVOS = frozenset(tipo.codigo for tipo in TIPOS_ALERTA if tipo.operativa)
CATEGORIAS = ('Financieras', 'Administrativas', 'Nómina', 'Documentales')


def tipos_operativos():
    """Tipos cuya fuente existe, sin confundir catalogación con notificaciones."""
    return tuple(tipo for tipo in TIPOS_ALERTA if tipo.operativa)


def tipo_operativo(codigo):
    """Valida códigos para el futuro Gestor; falla cerrado para tipos futuros."""
    tipo = TIPOS_POR_CODIGO.get(codigo)
    if tipo is None or not tipo.operativa:
        raise ValueError('Tipo de alerta todavía no operativo o desconocido.')
    return tipo
