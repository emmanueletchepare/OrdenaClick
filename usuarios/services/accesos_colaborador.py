"""Catálogo único sidebar -> funciones, y comprobación real por Empresa y acción."""
from django.core.exceptions import PermissionDenied
from django.db import transaction
from usuarios.models import AsignacionUsuarioEmpresa, Empresa, EventoPermisoAccesoColaborador, PermisoAccesoColaborador
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa

# Orden exactamente correspondiente a las secciones del sidebar.
ARBOL = (
    ('Registros', (('Consultar', 'registros.ver'), ('Registrar', 'registros.crear'), ('Editar', 'registros.editar'))),
    ('Pendientes bancarios', (('Consultar', 'pendientes.ver'), ('Cargar', 'pendientes.crear'), ('Editar / auditoría', 'pendientes.editar'), ('Confirmar', 'pendientes.resolver'), ('Estado e historial', 'pendientes.estado'), ('Salidas e-Cheq', 'pendientes.salidas'))),
    ('Herramientas', (('Gestión de claves propias', 'claves.propias'),)),
    ('ABMs · Estructura Operativa', (('Centros Operativos', 'abm.centros'), ('Recursos Operativos', 'abm.recursos'), ('Proveedores', 'abm.proveedores'), ('Tipos de gastos', 'abm.tipos'), ('Clientes', 'abm.clientes'))),
    ('ABMs · Finanzas y estado de pagos', (('Bancos', 'abm.bancos'), ('Cuentas Bancarias', 'abm.cuentas'), ('Tarjetas', 'abm.tarjetas'), ('Retenciones', 'abm.retenciones'))),
)
CODIGOS = frozenset(codigo for _,hojas in ARBOL for _,codigo in hojas)
# Solo capacidades cuyos endpoints tienen integración prevista en el bloque 3.
CODIGOS_HABILITABLES = frozenset({'claves.propias', *(c for c in CODIGOS if c.startswith('abm.'))})


def contexto_empresa(usuario, empresa_id):
    return obtener_contexto_capacidades_empresa(usuario, empresa_id)


def puede(usuario, empresa_id, codigo):
    if codigo not in CODIGOS: return False
    try: c=contexto_empresa(usuario, empresa_id)
    except (PermissionDenied, ValueError, TypeError): return False
    if c.es_superusuario or c.es_propietario or c.jerarquia=='admin_general': return True
    if c.jerarquia != 'colaborador': return False
    return PermisoAccesoColaborador.objects.filter(empresa=c.empresa, usuario=usuario, codigo=codigo, activo=True).exists()


def exigir(usuario, empresa_id, codigo):
    if not puede(usuario,empresa_id,codigo): raise PermissionDenied('No tiene autorizado este módulo o acción.')
    return contexto_empresa(usuario, empresa_id).empresa


def exigir_administrar_permisos(usuario, empresa_id):
    c=contexto_empresa(usuario, empresa_id)
    if not (c.es_superusuario or c.es_propietario or c.jerarquia=='admin_general'):
        raise PermissionDenied('Solo administración general puede modificar accesos.')
    return c.empresa


def colaborador_activo(empresa, usuario_id):
    return AsignacionUsuarioEmpresa.objects.filter(empresa=empresa,usuario_id=usuario_id,jerarquia='colaborador',activo=True).exists()


@transaction.atomic
def guardar_accesos(*, administrador, empresa_id, colaborador_id, codigos):
    empresa=exigir_administrar_permisos(administrador,empresa_id)
    if not isinstance(codigos,(list,set,tuple)) or len(codigos)>len(CODIGOS) or any(c not in CODIGOS_HABILITABLES for c in codigos):
        raise ValueError('Selección de permisos inválida.')
    nuevo=set(codigos)
    Empresa.objects.select_for_update().get(pk=empresa.pk)
    if not colaborador_activo(empresa,colaborador_id):raise PermissionDenied('No es Colaborador activo de esta Empresa.')
    anteriores={p.codigo:p for p in PermisoAccesoColaborador.objects.select_for_update().filter(empresa=empresa,usuario_id=colaborador_id)}
    for codigo in sorted(CODIGOS):
        obj=anteriores.get(codigo)
        antes=bool(obj and obj.activo)
        despues=codigo in nuevo
        if antes==despues:continue
        if obj:
            obj.activo=despues;obj.otorgado_por=administrador;obj.save(update_fields=('activo','otorgado_por','modificado'))
        else:
            PermisoAccesoColaborador.objects.create(empresa=empresa,usuario_id=colaborador_id,codigo=codigo,activo=True,otorgado_por=administrador)
        EventoPermisoAccesoColaborador.objects.create(empresa=empresa,usuario_id=colaborador_id,actor=administrador,codigo=codigo,activo=despues)
    return nuevo


def exigir_abm(usuario, empresa_id, codigo):
    if not codigo.startswith('abm.') or codigo not in CODIGOS:
        raise PermissionDenied('ABM no reconocido.')
    exigir(usuario, empresa_id, codigo)
    return contexto_empresa(usuario, empresa_id)


def permiso_claves(usuario, empresa_id):
    contexto=contexto_empresa(usuario, empresa_id)
    if contexto.es_superusuario or contexto.es_propietario or contexto.jerarquia=='admin_general':
        return contexto.empresa, False
    if contexto.jerarquia=='colaborador' and puede(usuario, empresa_id, 'claves.propias'):
        return contexto.empresa, True
    raise PermissionDenied('Gestión de claves no autorizada.')
