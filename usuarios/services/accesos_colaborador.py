"""Catálogo único sidebar -> funciones, y comprobación real por Empresa y acción."""
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.contrib.auth import get_user_model
from usuarios.models import AsignacionUsuarioEmpresa, Empresa, EventoPermisoAccesoColaborador, PermisoAccesoColaborador, RolFuncionalUsuarioEmpresa
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.alcances_centros import centros_activos_de_usuario

# Catálogo alineado al menú lateral. Funciones sin endpoint real permanecen informativas.
ARBOL = (
    ('Registros', (('Comprobantes · consultar', 'registros.ver'),
                   ('Comprobantes · registrar', 'registros.crear'),
                   ('Comprobantes · modificar', 'registros.editar'),
                   ('Obligaciones', 'registros.obligaciones'))),
    ('Pendientes bancarios', (('Consultar', 'pendientes.ver'), ('Cargar', 'pendientes.crear'),
                   ('Editar / auditoría', 'pendientes.editar'), ('Confirmar', 'pendientes.resolver'),
                   ('Estado e historial', 'pendientes.estado'), ('Salidas e-Cheq', 'pendientes.salidas'))),
    ('Caja', (('Caja · centros autorizados', 'caja.total'),)),
    ('Dashboard', (('Dashboard', 'dashboard.ver'),)),
    ('Alertas', (('Consultar alertas', 'alertas.ver'),)),
    ('Próximos vencimientos', (('Hoy, Esta semana y Rango de fechas', 'vencimientos.ver'),)),
    ('Reportes', (('Reportes', 'reportes.ver'),)),
    ('Estado de Resultados', (('Estado de Resultados', 'resultados.ver'),)),
    ('Balance', (('Balance', 'balance.ver'),)),
    ('Herramientas', (('Gestión de claves propias', 'claves.propias'),
                     ('Nómina de Empleados · acceso completo', 'nomina.total'))),
    ('ABMs · Estructura Operativa', (('Centros Operativos','abm.centros'),
                     ('Recursos Operativos','abm.recursos'), ('Proveedores','abm.proveedores'),
                     ('Tipos de gastos','abm.tipos'), ('Clientes','abm.clientes'))),
    ('ABMs · Finanzas y medios de pago', (('Bancos','abm.bancos'),
                     ('Cuentas Bancarias','abm.cuentas'), ('Tarjetas','abm.tarjetas'),
                     ('Retenciones','abm.retenciones'))),
    ('Configuración', (('Modificar Empresa','config.empresa'),
                     ('Designar perfiles','config.perfiles'),
                     ('Gestión de accesos','config.accesos'))),
)
CODIGOS = frozenset(codigo for _,hojas in ARBOL for _,codigo in hojas)
# Sólo las capacidades con comprobación real del backend son concedibles.
# La lista visible es más amplia para mostrar TODOS los apartados del sidebar.
CODIGOS_HABILITABLES = frozenset({'claves.propias','nomina.total','vencimientos.ver','alertas.ver','caja.total',
                                   'registros.ver','registros.crear','registros.editar','registros.obligaciones',
                                   'pendientes.ver','pendientes.crear','pendientes.editar','pendientes.resolver',
                                   'pendientes.estado','pendientes.salidas',
                                   *(c for c in CODIGOS if c.startswith('abm.'))})
ROLES_NOMINA_FUNCIONALES = frozenset({'contable','legal','rrhh'})  # RRHH futuro; no se crea rol.


def contexto_empresa(usuario, empresa_id):
    return obtener_contexto_capacidades_empresa(usuario, empresa_id)


def puede(usuario, empresa_id, codigo):
    if codigo not in CODIGOS: return False
    try: c=contexto_empresa(usuario, empresa_id)
    except (PermissionDenied, ValueError, TypeError): return False
    if c.es_superusuario or c.es_propietario or c.jerarquia=='admin_general': return True
    if codigo == 'caja.total':
        # Caja no se concede por rol: requiere autorización explícita, activa y
        # dentro de los Centros operativos que ya autoriza la jerarquía.
        return (c.jerarquia == 'admin_centro'
            and bool(centros_activos_de_usuario(usuario, c.empresa))
            and PermisoAccesoColaborador.objects.filter(
                empresa=c.empresa, usuario=usuario, codigo='caja.total', activo=True).exists())
    if c.jerarquia == 'admin_centro':
        if not centros_activos_de_usuario(usuario, c.empresa): return False
    elif c.jerarquia != 'colaborador':
        if not (codigo == 'nomina.total' and c.roles_funcionales.intersection(ROLES_NOMINA_FUNCIONALES)):
            return False
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
    """La configuración alcanza a colaboradores y administradores de centro activos."""
    return (AsignacionUsuarioEmpresa.objects.filter(
        empresa=empresa,usuario_id=usuario_id,jerarquia__in=('colaborador','admin_centro'),activo=True).exists()
        or RolFuncionalUsuarioEmpresa.objects.filter(
            empresa=empresa,usuario_id=usuario_id,rol__in=ROLES_NOMINA_FUNCIONALES,activo=True).exists())


@transaction.atomic
def guardar_accesos(*, administrador, empresa_id, colaborador_id, codigos):
    empresa=exigir_administrar_permisos(administrador,empresa_id)
    if not isinstance(codigos,(list,set,tuple)) or len(codigos)>len(CODIGOS) or any(c not in CODIGOS_HABILITABLES for c in codigos):
        raise ValueError('Selección de permisos inválida.')
    nuevo=set(codigos)
    Empresa.objects.select_for_update().get(pk=empresa.pk)
    if not colaborador_activo(empresa,colaborador_id):
        raise PermissionDenied('No es un miembro configurable activo de esta Empresa.')
    contexto_destino = contexto_empresa(get_user_model().objects.get(pk=colaborador_id), empresa.pk)
    if 'caja.total' in nuevo and contexto_destino.jerarquia != 'admin_centro':
        raise PermissionDenied('Sólo Administrador de Centro puede recibir Caja.')
    if (contexto_destino.jerarquia not in ('colaborador','admin_centro')
            and (nuevo - {'nomina.total'})):
        raise PermissionDenied('Un rol funcional solo puede recibir Nómina.')
    anteriores={p.codigo:p for p in PermisoAccesoColaborador.objects.select_for_update().filter(empresa=empresa,usuario_id=colaborador_id)}
    # Una vez guardado Gestión de Accesos, los permisos bancarios ausentes
    # también quedan expresamente revocados. Se evita revivir autorizaciones
    # legadas por Centro cuando la casilla está desmarcada.
    from usuarios.services.permisos_bancarios_accion import permitido as permiso_bancario
    usuario_destino = get_user_model().objects.get(pk=colaborador_id)
    for codigo in sorted(c for c in CODIGOS if c.startswith('pendientes.')):
        if codigo not in anteriores and codigo not in nuevo:
            antes_legado = permiso_bancario(usuario_destino,empresa.pk,codigo)
            anteriores[codigo] = PermisoAccesoColaborador.objects.create(
                empresa=empresa,usuario_id=colaborador_id,codigo=codigo,
                activo=False,otorgado_por=administrador)
            if antes_legado:
                EventoPermisoAccesoColaborador.objects.create(
                    empresa=empresa,usuario_id=colaborador_id,actor=administrador,
                    codigo=codigo,activo=False)
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
    if contexto.jerarquia in ('colaborador', 'admin_centro') and puede(usuario, empresa_id, 'claves.propias'):
        return contexto.empresa, True
    raise PermissionDenied('Gestión de claves no autorizada.')
