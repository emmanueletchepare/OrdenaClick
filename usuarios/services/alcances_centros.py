"""Alcance explícito de centros de un Administrador de Centro (sin permisos implícitos)."""
from usuarios.models import AsignacionUsuarioEmpresa, CentroAdicionalAdministrador, CentroOperativo


def centros_activos_de_asignacion(asignacion):
    """Devuelve IDs autorizados, de la Empresa y activos, incluido centro primario."""
    if not asignacion or not asignacion.activo or asignacion.jerarquia != 'admin_centro':
        return frozenset()
    posibles = {asignacion.centro_operativo_id}
    posibles.update(CentroAdicionalAdministrador.objects.filter(
        asignacion=asignacion,
    ).values_list('centro_operativo_id', flat=True))
    return frozenset(CentroOperativo.objects.filter(
        pk__in=posibles, empresa_id=asignacion.empresa_id, activo=True,
    ).values_list('pk', flat=True))


def centros_activos_de_usuario(usuario, empresa):
    """Resuelve cada petición en base a asignación vigente, no a caché/sesión."""
    asignacion = AsignacionUsuarioEmpresa.objects.filter(
        empresa=empresa, usuario=usuario, activo=True, jerarquia='admin_centro',
    ).first()
    return centros_activos_de_asignacion(asignacion)
