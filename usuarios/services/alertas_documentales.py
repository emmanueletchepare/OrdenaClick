"""DOC-01 a DOC-04: avisos derivados, sin alterar documentos ni estados.

La anticipación inicial es 30 días; un vencido sigue visible. Un Centro activo
sin habilitación activa emite DOC-03 aun sin fecha. No presume validez legal.
"""
from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.utils import timezone
from usuarios.models import CentroOperativo, HabilitacionCentro
from usuarios.services.accesos_colaborador import puede
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.alcances_centros import centros_activos_de_usuario

CODIGOS = ('DOC-01', 'DOC-03', 'DOC-04')
ANTICIPACION_DIAS = 30


def alcance_documental(usuario, empresa, codigo):
    """(habilitado, Centros o None). Solo administradores, nunca por alerta."""
    if codigo not in CODIGOS or not puede(usuario, empresa.pk, 'alertas.ver'):
        return False, frozenset()
    try:
        c = obtener_contexto_capacidades_empresa(usuario, empresa.pk)
    except (TypeError, ValueError, PermissionDenied):
        return False, frozenset()
    if c.es_superusuario or c.es_propietario or c.jerarquia == 'admin_general':
        return True, None
    if codigo == 'DOC-03' and c.jerarquia == 'admin_centro':
        centros = frozenset(centros_activos_de_usuario(usuario, empresa))
        return bool(centros), centros
    return False, frozenset()


def predeterminado_documental(usuario, empresa, codigo):
    return alcance_documental(usuario, empresa, codigo)[0]


def fuentes_documentales(empresa, hoy=None):
    """Ocurrencias existentes, sin filtrar destinatarios; no exponen adjuntos."""
    hoy = hoy or timezone.localdate()
    futuro = hoy + timedelta(days=ANTICIPACION_DIAS)
    avisos = []
    for codigo, campo, titulo in (
        ('DOC-01', 'vencimiento_acta_directorio', 'Acta de directorio'),
        ('DOC-04', 'vencimiento_designacion', 'Acta de designación de autoridades (Asamblea)'),
    ):
        # Los campos de Asamblea son históricos. Si una Empresa declaró que
        # el acta acreditaba autoridades y aún no asignó una fecha propia a
        # Designación, usar la anterior sin migrar ni alterar ningún registro.
        fecha = getattr(empresa, campo)
        if codigo == 'DOC-04' and fecha is None and empresa.acta_incluye_designacion:
            fecha = empresa.vencimiento_acta
        if fecha is not None and fecha <= futuro:
            avisos.append({'codigo': codigo, 'grupo': 'societaria',
                'nombre': titulo, 'fecha_vencimiento': fecha.isoformat(),
                'estado_alerta': ('Vencido' if fecha < hoy else 'Hoy' if fecha == hoy else 'Proximo'),
                'centro_id': None, 'id': empresa.pk})
    centros = CentroOperativo.objects.filter(empresa=empresa, activo=True).prefetch_related('habilitaciones')
    for centro in centros:
        habilitaciones = [h for h in centro.habilitaciones.all() if h.activo]
        if not habilitaciones:
            avisos.append({'codigo': 'DOC-03', 'grupo': 'habilitaciones',
                'nombre': 'Sin habilitación registrada · ' + centro.nombre,
                'fecha_vencimiento': None, 'estado_alerta': 'Sin habilitacion',
                'centro_id': centro.pk, 'id': centro.pk})
        for hab in habilitaciones:
            if hab.vencimiento is None or hab.vencimiento > futuro:
                continue
            fecha = hab.vencimiento
            avisos.append({'codigo': 'DOC-03', 'grupo': 'habilitaciones',
                'nombre': hab.descripcion + ' · ' + centro.nombre,
                'fecha_vencimiento': fecha.isoformat(),
                'estado_alerta': ('Vencido' if fecha < hoy else 'Hoy' if fecha == hoy else 'Proximo'),
                'centro_id': centro.pk, 'id': hab.pk})
    return avisos


def aviso_documental_autorizado(usuario, empresa, aviso):
    autorizado, centros = alcance_documental(usuario, empresa, aviso['codigo'])
    if not autorizado:
        return False
    return centros is None or aviso['centro_id'] in centros


def avisos_documentales_visibles(usuario, empresa, hoy=None):
    return [a for a in fuentes_documentales(empresa, hoy)
            if aviso_documental_autorizado(usuario, empresa, a)]


def avisos_documentales_publicos(usuario, empresa, hoy=None):
    """Campos mínimos; sin rutas, archivos ni información de otros Centros."""
    campos = ('codigo', 'grupo', 'nombre', 'fecha_vencimiento', 'estado_alerta')
    return [{k: a[k] for k in campos} for a in avisos_documentales_visibles(usuario, empresa, hoy)]
