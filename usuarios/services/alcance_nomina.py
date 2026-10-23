"""Permiso de Nómina: funciones completas, alcance estricto por Centro."""
from django.core.exceptions import PermissionDenied
from usuarios.models import CentroOperativo, PermisoNominaCentro
from usuarios.services.alcances_centros import centros_activos_de_usuario
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa


def alcance_nomina(usuario, empresa_id):
    """(empresa, None=toda empresa | frozenset de centros activos)."""
    contexto = obtener_contexto_capacidades_empresa(usuario, empresa_id)
    empresa = contexto.empresa
    if contexto.es_superusuario or contexto.es_propietario or contexto.jerarquia == 'admin_general':
        return empresa, None
    from usuarios.services.accesos_colaborador import puede
    if not puede(usuario, empresa.pk, 'nomina.total'):
        raise PermissionDenied('No tiene permiso para Nómina.')
    if contexto.jerarquia == 'admin_centro':
        ids = centros_activos_de_usuario(usuario, empresa)
    else:
        ids = frozenset(PermisoNominaCentro.objects.filter(
            empresa=empresa, usuario=usuario, activo=True,
            centro_operativo__empresa=empresa, centro_operativo__activo=True,
        ).values_list('centro_operativo_id', flat=True))
    if not ids:
        raise PermissionDenied('No hay centros de Nómina autorizados.')
    return empresa, ids


def restringir_nomina(queryset, usuario, empresa_id, campo='centro_operativo_id'):
    """El filtro siempre se ejecuta en la consulta SQL, no en el navegador."""
    _, ids = alcance_nomina(usuario, empresa_id)
    return queryset if ids is None else queryset.filter(**{campo+'__in': ids})


def comprobar_centro_nomina(usuario, empresa_id, centro_id):
    empresa, ids = alcance_nomina(usuario, empresa_id)
    try:
        centro = CentroOperativo.objects.get(pk=centro_id, empresa=empresa, activo=True)
    except (CentroOperativo.DoesNotExist, TypeError, ValueError) as error:
        raise PermissionDenied('Centro de Nómina no autorizado.') from error
    if ids is not None and centro.pk not in ids:
        raise PermissionDenied('Centro de Nómina no autorizado.')
    return centro
