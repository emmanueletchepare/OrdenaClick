"""Gestión conjunta de accesos y destinatarios: autorización separada, un solo UX.

La pantalla presenta ambos contratos; los servicios originales siguen siendo
fuente de verdad. POST unificado es atómico y no concede accesos por avisos.
"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_http_methods

from usuarios.models import (AsignacionUsuarioEmpresa, CentroOperativo,
    DestinatarioAlerta, PermisoAccesoColaborador, PermisoNominaCentro,
    RolFuncionalUsuarioEmpresa)
from usuarios.services.accesos_colaborador import (
    ARBOL, CODIGOS_HABILITABLES, exigir_administrar_permisos, puede)
from usuarios.services.catalogo_alertas import TIPOS_POR_CODIGO
from usuarios.services.destinatarios_alertas import (
    alcance_fuente, alertas_sin_destinatarios, guardar_destinatarios_usuario,
    miembros_empresa)
from usuarios.services.permisos_bancarios_accion import permitido as permiso_bancario

# Sólo se muestran alertas operativas; los tipos futuros no adquieren permisos.
# Columna de aviso ubicada junto al módulo de origen, no en otro gestor.
ALERTAS_POR_CAPACIDAD = {
    'pendientes.ver': 'FIN-03',
    'caja.total': 'FIN-02',
    'vencimientos.ver': 'FIN-01',
    'nomina.total': 'NOM-01',
}


def _seleccionar_usuario(request, usuarios):
    """Valida pertenencia activa antes de consultar o guardar cualquier dato."""
    texto = (request.POST.get('usuario') if request.method == 'POST'
             else request.GET.get('usuario'))
    if not texto:
        if request.method == 'POST':
            raise ValueError('Debe seleccionar un usuario.')
        return next(iter(usuarios), None)
    if not texto.isascii() or not texto.isdecimal():
        raise ValueError('Usuario inválido.')
    elegido = int(texto)
    if elegido not in usuarios:
        raise PermissionDenied('Usuario ajeno o inactivo.')
    return elegido


@login_required
@never_cache
@require_http_methods(['GET', 'POST'])
@xframe_options_sameorigin
def gestion_accesos(request, empresa_id):
    """Editar en un solo formulario sin cambiar los servicios financieros."""
    try:
        empresa = exigir_administrar_permisos(request.user, empresa_id)
    except (PermissionDenied, TypeError, ValueError):
        return HttpResponseForbidden('No autorizado.')

    # Mismo universo de miembros del gestor B2, incluido propietario/general.
    usuarios = {u.pk: u for u in miembros_empresa(empresa)}
    asignaciones = {
        a.usuario_id: a.jerarquia for a in AsignacionUsuarioEmpresa.objects.filter(
            empresa=empresa, activo=True).select_related('usuario')
    }
    funcionales = set(RolFuncionalUsuarioEmpresa.objects.filter(
        empresa=empresa, activo=True, rol__in=('contable', 'legal', 'rrhh')
    ).values_list('usuario_id', flat=True))
    try:
        elegido = _seleccionar_usuario(request, usuarios)
    except (PermissionDenied, TypeError, ValueError):
        return HttpResponseForbidden('Usuario no autorizado.')

    rol = asignaciones.get(elegido)
    # La jerarquía de administración prevalece sobre cualquier rol funcional.
    privilegiado = (elegido == empresa.propietario_id or rol == 'admin_general'
                   or (elegido is not None and usuarios[elegido].is_superuser))
    editable = not privilegiado and (rol in ('colaborador', 'admin_centro')
                                    or elegido in funcionales)
    if request.method == 'POST':
        if elegido is None:
            return HttpResponseForbidden('No hay un miembro configurable válido.')
        unificado = request.POST.get('formulario') == 'accesos-alertas'
        if request.POST.get('formulario') not in (None, '', 'accesos-alertas'):
            return HttpResponseForbidden('Formulario inválido.')
        # Sigue aceptando POST antiguo sólo para accesos (tests/rutas existentes).
        # Nunca borra alertas por omitirlas en un formulario anterior.
        if not editable and not unificado:
            return HttpResponseForbidden('La jerarquía no permite editar accesos.')
        if not editable and request.POST.getlist('capacidad'):
            return HttpResponseForbidden('Los accesos de esta jerarquía son inherentes.')
        from usuarios.services.gestionar_nomina_accesos import guardar_permisos_operativos
        try:
            with transaction.atomic():
                # Al actualizar permisos primero, el servicio de B2 comprueba la
                # autorización NUEVA antes de asociar un aviso; rollback completo.
                if editable:
                    guardar_permisos_operativos(
                        administrador=request.user, empresa_id=empresa.pk,
                        usuario_id=elegido, codigos=request.POST.getlist('capacidad'),
                        centros_nomina=request.POST.getlist('nomina_centro'))
                if unificado:
                    guardar_destinatarios_usuario(
                        administrador=request.user, empresa_id=empresa.pk,
                        usuario_id=elegido, codigos=request.POST.getlist('alerta'))
        except (PermissionDenied, ValueError, TypeError):
            return HttpResponseForbidden(
                'No se pudo guardar: revisá los accesos necesarios para cada alerta. '
                'No se modificó ninguna configuración.')
        return redirect(reverse('gestion_accesos_colaborador', args=[empresa.pk]) +
                        f'?usuario={elegido}&guardado=1')

    asignados = set(DestinatarioAlerta.objects.filter(
        empresa=empresa, usuario_id=elegido, activo=True
    ).values_list('codigo', flat=True)) if elegido is not None else set()
    habilitados = set(PermisoAccesoColaborador.objects.filter(
        empresa=empresa, usuario_id=elegido, activo=True
    ).values_list('codigo', flat=True)) if elegido is not None else set()
    # Un usuario con rol funcional sólo recibe permisos de Nómina; jerarquías
    # generales no necesitan casillas para acceder a módulos propios.
    permitidos = (set(CODIGOS_HABILITABLES) if rol in ('colaborador', 'admin_centro')
                  else {'nomina.total'} if editable else set())
    if rol != 'admin_centro':
        permitidos.discard('caja.total')
    arbol = []
    for indice, (titulo, hojas) in enumerate(ARBOL):
        hijos = []
        for nombre, codigo in hojas:
            alerta_codigo = ALERTAS_POR_CAPACIDAD.get(codigo)
            tipo = TIPOS_POR_CODIGO.get(alerta_codigo)
            # Sin migraciones ni duplicar alertas: se conserva la configuración B2.
            alerta = None
            if tipo is not None and tipo.operativa and elegido is not None:
                alerta = {
                    'codigo': tipo.codigo, 'nombre': tipo.nombre,
                    'activo': tipo.codigo in asignados,
                    'efectivo': alcance_fuente(usuarios[elegido], empresa, tipo.codigo)[0],
                }
            hijos.append({
                'nombre': nombre, 'codigo': codigo,
                # Permisos bancarios legados autorizados se muestran tildados,
                # evitando revocarlos inadvertidamente al guardar otra casilla.
                'activo': (codigo in habilitados or
                           (editable and codigo.startswith('pendientes.') and
                            permiso_bancario(usuarios[elegido],empresa.pk,codigo))),
                'habilitable': codigo in permitidos,
                'heredado': not editable and elegido is not None and
                             puede(usuarios[elegido], empresa.pk, codigo),
                'ayuda': ('Reservado a administración general' if codigo.startswith('config.')
                          else 'Acceso definido por jerarquía' if not editable
                          else 'No disponible para este perfil' if codigo == 'caja.total'
                          else 'Disponible al integrar este módulo' ),
                'alerta': alerta,
            })
        arbol.append({'titulo': titulo, 'codigo': str(indice), 'hijos': hijos,
            'tiene_habilitables': any(h['habilitable'] for h in hijos)})
    centros = list(CentroOperativo.objects.filter(
        empresa=empresa, activo=True).order_by('nombre', 'pk'))
    centros_nomina = set(PermisoNominaCentro.objects.filter(
        empresa=empresa, usuario_id=elegido, activo=True
    ).values_list('centro_operativo_id', flat=True)) if elegido else set()
    pendientes = alertas_sin_destinatarios(empresa)
    return render(request, 'usuarios/empresa/gestion_accesos_colaborador.html', {
        'empresa': empresa, 'colaboradores': list(usuarios.values()),
        'usuario_seleccionado': elegido, 'arbol': arbol,
        'guardado': request.GET.get('guardado') == '1',
        'centros_nomina': centros, 'centros_nomina_ids': centros_nomina,
        'es_admin_centro': rol == 'admin_centro',
        'mostrar_centros_nomina': editable and rol != 'admin_centro',
        'puede_editar_accesos': editable, 'sin_destinatarios': pendientes,
        'permisos_inherentes': not editable,
        'lectura_bancaria': bool(elegido and permiso_bancario(usuarios[elegido], empresa.pk, 'pendientes.ver')),
    })
