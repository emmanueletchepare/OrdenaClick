"""Entrada única Administrar: pertenencia ≠ permiso. Sin elevar privilegios.

Se reutiliza la estructura del panel existente. Hasta autorizar los endpoints
restantes, el modo restringido solo ofrece Pendientes si su permiso existe.
"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from usuarios.models import AsignacionUsuarioEmpresa, Empresa, RolFuncionalUsuarioEmpresa
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.pendientes_bancarios import alcance_pendientes
from usuarios.services.accesos_colaborador import puede


ETIQUETAS = {
    'admin_general': 'Administrador general',
    'admin_centro': 'Administrador de Centro',
    'colaborador': 'Colaborador',
}


def empresas_para_administrar(usuario):
    """Pertenencia estructural activa; nunca permisos sueltos ni solicitudes pendientes."""
    if not usuario.is_authenticated:
        return Empresa.objects.none()
    if usuario.is_superuser:
        empresas = Empresa.objects.all().order_by('nombre_fantasia', 'razon_social')
    else:
        empresas = Empresa.objects.filter(
            Q(propietario=usuario) |
            Q(asignaciones_usuarios__usuario=usuario, asignaciones_usuarios__activo=True) |
            Q(roles_funcionales_usuarios__usuario=usuario, roles_funcionales_usuarios__activo=True)
        ).distinct().order_by('nombre_fantasia', 'razon_social')
    # Etiquetas solo de presentación; la autorización de entrada se recalcula.
    lista = list(empresas)
    asignaciones = {
        a.empresa_id: a.jerarquia for a in AsignacionUsuarioEmpresa.objects.filter(
            usuario=usuario, activo=True, empresa_id__in=[e.pk for e in lista]
        )
    }
    # No anunciar 'Administrar' al rol funcional hasta que tenga acceso real.
    lista = [e for e in lista if (usuario.is_superuser or e.propietario_id == usuario.pk
             or e.pk in asignaciones or puede(usuario,e.pk,'nomina.total'))]
    for empresa in lista:
        if usuario.is_superuser or empresa.propietario_id == usuario.pk:
            empresa.etiqueta_acceso = 'Administrador'
        else:
            empresa.etiqueta_acceso = ETIQUETAS.get(asignaciones.get(empresa.pk), 'Rol funcional')
    return lista


@login_required
@never_cache
@require_GET
def panel_administrar(request):
    """Vista compartida. Administración plena solo si es propietario/superusuario.

    Esta ruta NO procesa formularios administrativos. El panel histórico no
    cambia su barrera de propietario. Colaborador no recibe datos, formularios
    ni scripts administrativos desde el servidor.
    """
    empresas = empresas_para_administrar(request.user)
    empresa_id = request.GET.get('empresa')
    if empresa_id:
        try:
            contexto = obtener_contexto_capacidades_empresa(request.user, empresa_id)
        except (PermissionDenied, ValueError, TypeError):
            return HttpResponseForbidden('No tenés acceso a esta Empresa.')
        if contexto.es_superusuario or contexto.es_propietario:
            return redirect(reverse('panel_admin') + '?empresa=' + str(contexto.empresa.pk))
        solo_funcional = contexto.jerarquia is None and bool(contexto.roles_funcionales)
        if contexto.jerarquia not in ETIQUETAS and not (
            solo_funcional and puede(request.user,contexto.empresa.pk,'nomina.total')):
            return HttpResponseForbidden('Esta relación no habilita el área Administrar.')
        try:
            alcance_pendientes(request.user, contexto.empresa.pk)
            from usuarios.services.permisos_bancarios_accion import permitido
            pendientes = permitido(request.user, contexto.empresa.pk, 'pendientes.ver')
        except PermissionDenied:
            pendientes = False
        abms = (
            ('centros','Centros Operativos'),('recursos','Recursos Operativos'),
            ('proveedores','Proveedores'),('tipos','Tipos de gastos'),('clientes','Clientes'),
            ('bancos','Bancos'),('cuentas','Cuentas Bancarias'),('tarjetas','Tarjetas'),('retenciones','Retenciones'),
        )
        autorizados=[{'codigo':nombre,'nombre':etiqueta} for nombre,etiqueta in abms
                     if puede(request.user,contexto.empresa.pk,'abm.'+nombre)]
        claves=puede(request.user,contexto.empresa.pk,'claves.propias')
        nomina=puede(request.user,contexto.empresa.pk,'nomina.total')
        caja=puede(request.user,contexto.empresa.pk,'caja.total')
        vencimientos=puede(request.user,contexto.empresa.pk,'vencimientos.ver')
        registros={c:puede(request.user,contexto.empresa.pk,c) for c in (
            'registros.ver','registros.crear','registros.editar','registros.obligaciones')}
        puede_comprobantes=any(registros[c] for c in ('registros.ver','registros.crear','registros.editar'))
        return render(request, 'usuarios/perfiles/administrador/panel.html', {
            'empresa_actual': contexto.empresa,
            'empresas': empresas,
            'acceso_restringido': True,
            'puede_ver_pendientes': pendientes,
            'puede_gestion_claves':claves, 'puede_ver_nomina':nomina,
            'puede_ver_caja':caja, 'puede_ver_vencimientos':vencimientos,
            'puede_ver_registros':any(registros.values()),
            'puede_ver_comprobantes':puede_comprobantes,
            'puede_ver_obligaciones':registros['registros.obligaciones'],
            'puede_ver_abms': bool(autorizados),
            'abms_autorizados':autorizados,
            'abms_codigos':[a['codigo'] for a in autorizados],
            'abms_estructura':[a for a in autorizados if a['codigo'] in ('centros','recursos','proveedores','tipos','clientes')],
            'abms_finanzas':[a for a in autorizados if a['codigo'] in ('bancos','cuentas','tarjetas','retenciones')],
        })
    return render(request, 'usuarios/perfiles/administrador/panel.html', {
        'empresa_actual': None,
        'empresas': empresas,
        'acceso_restringido': True,
        'puede_ver_pendientes': False,
    })
