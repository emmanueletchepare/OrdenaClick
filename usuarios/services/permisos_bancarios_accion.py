"""Permisos por acción sin perder la bandeja global ni el alcance de Centro.

La asignación bancaria legada por Centro sigue siendo una concesión explícita
válida para consulta, confirmación y corrección del propio movimiento. Cuando
Gestión de Accesos guarda una decisión moderna, esta prevalece incluso al revocar.
"""
from django.core.exceptions import PermissionDenied
from usuarios.models import (AsignacionUsuarioEmpresa, PermisoAccesoColaborador,
    PermisoPendienteBancarioCentro, CentroOperativo)
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.alcances_centros import centros_activos_de_usuario

CODIGOS=frozenset({'pendientes.ver','pendientes.crear','pendientes.editar',
                    'pendientes.resolver','pendientes.estado','pendientes.salidas'})

def permitido(usuario,empresa_id,codigo):
    if codigo not in CODIGOS: return False
    try: c=obtener_contexto_capacidades_empresa(usuario,empresa_id)
    except (PermissionDenied,TypeError,ValueError): return False
    if c.es_superusuario or c.es_propietario or c.jerarquia=='admin_general': return True
    if c.jerarquia not in ('colaborador','admin_centro'): return False
    if c.jerarquia=='admin_centro' and not centros_activos_de_usuario(usuario,c.empresa): return False
    permiso=PermisoAccesoColaborador.objects.filter(empresa=c.empresa,usuario=usuario,codigo=codigo).first()
    if permiso is not None: return permiso.activo
    # Compatibilidad exclusivamente con permisos bancarios POR CENTRO que ya
    # habían sido concedidos antes de existir las casillas de acción.
    if codigo not in ('pendientes.ver','pendientes.editar','pendientes.resolver'):
        return False
    if c.jerarquia=='admin_centro':
        return bool(centros_activos_de_usuario(usuario,c.empresa))
    return PermisoPendienteBancarioCentro.objects.filter(
        empresa=c.empresa,usuario=usuario,activo=True,
        centro_operativo__empresa=c.empresa,centro_operativo__activo=True).exists()

def exigir(usuario,empresa_id,codigo):
    if not permitido(usuario,empresa_id,codigo):
        raise PermissionDenied('Acción bancaria no concedida por Administración general.')
    return obtener_contexto_capacidades_empresa(usuario,empresa_id).empresa
