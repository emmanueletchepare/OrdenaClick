"""Alcance de Registros: concesión por acción; Centro limitado para admin_centro.

No convierte permisos de Registros en permisos de Caja ni en ABMs editables.
"""
from django.core.exceptions import PermissionDenied
from usuarios.models import Movimiento, CentroOperativo
from usuarios.services.accesos_colaborador import exigir, puede
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.alcances_centros import centros_activos_de_usuario

ACCIONES=('registros.ver','registros.crear','registros.editar','registros.obligaciones')

def empresa_registros(usuario,empresa_id,codigo):
    contexto = obtener_contexto_capacidades_empresa(usuario,empresa_id)
    # La jerarquía general administra accesos; no implica permiso automático
    # para crear/editar Movimientos, antes reservado al propietario.
    if (contexto.jerarquia == 'admin_general'
            and not (contexto.es_propietario or contexto.es_superusuario)
            and codigo in ('registros.crear','registros.editar')):
        raise PermissionDenied('La jerarquía Administrador general no autoriza escribir Movimientos.')
    if isinstance(codigo,(tuple,list,set)):
        for posible in codigo:
            if posible not in ACCIONES: raise PermissionDenied('Acción no admitida.')
            if puede(usuario,empresa_id,posible):
                return obtener_contexto_capacidades_empresa(usuario,empresa_id).empresa
        raise PermissionDenied('Registros no autorizados.')
    if codigo not in ACCIONES: raise PermissionDenied('Acción no admitida.')
    return exigir(usuario,empresa_id,codigo)

def comprobar_centro(usuario,empresa,centro_id):
    c=obtener_contexto_capacidades_empresa(usuario,empresa.pk)
    if c.jerarquia!='admin_centro':return
    ids=centros_activos_de_usuario(usuario,empresa)
    try: centro_id=int(centro_id)
    except (TypeError,ValueError) as exc:raise PermissionDenied('Seleccione un Centro autorizado.') from exc
    if centro_id not in ids:
        raise PermissionDenied('Centro operativo fuera del alcance de Registros.')

def comprobar_movimiento(usuario,empresa,movimiento_id):
    movimiento=Movimiento.objects.filter(empresa=empresa,pk=movimiento_id).only('centro_operativo_id').first()
    if movimiento is None: raise PermissionDenied('Movimiento no disponible en esta Empresa.')
    comprobar_centro(usuario,empresa,movimiento.centro_operativo_id)
    return movimiento

def impedir_pagos_delegados(usuario,empresa,datos):
    c=obtener_contexto_capacidades_empresa(usuario,empresa.pk)
    if c.es_superusuario or c.es_propietario or c.jerarquia=='admin_general':return
    pagos=(datos.get('pagos') or '').strip()
    debito=(datos.get('debito_automatico') or '').strip()
    modalidad=(datos.get('modalidad_pago') or 'Manual').strip()
    if pagos not in ('','[]') or debito not in ('','null','{}') or modalidad=='DebitoAutomatico':
        raise PermissionDenied('Los Pagos se autorizan por su circuito propio, no por Registros.')
