"""Edición previa a resolución y reporte posterior inmutable, por Empresa."""
import logging
from datetime import timedelta
from uuid import UUID
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from usuarios.models import Banco, Empresa, EventoPendienteBancario, PendienteBancario, RevisionPendienteBancario
from usuarios.services.identidades import obtener_identidad_usuario_empresa
from usuarios.services.cheques import normalizar_numero_cheque
from usuarios.services.pendientes_bancarios import alcance_pendientes, importe_positivo, _fecha, _texto

LOG = logging.getLogger('ordenaclick.audit')

def _snapshot(p):
    return {
        'fecha': p.fecha.isoformat(), 'tipo': p.tipo, 'importe': str(p.importe),
        'identificacion': p.identificacion, 'referencia': p.referencia,
        'cuenta_bancaria_id': p.cuenta_bancaria_id,
        'echeq_numero': p.echeq_numero, 'echeq_titular': p.echeq_titular,
        'echeq_banco_nombre': p.echeq_banco_nombre,
        'echeq_fecha_acreditacion': p.echeq_fecha_acreditacion.isoformat() if p.echeq_fecha_acreditacion else None,
        'centro_operativo_id': p.centro_operativo_id,
        'estado': p.estado, 'resuelto_en': p.resuelto_en.isoformat() if p.resuelto_en else None,
    }

def revisar_pendiente(*, usuario, empresa_id, pendiente_id, clave, motivo, datos):
    empresa, alcance = alcance_pendientes(usuario, empresa_id)
    motivo = _texto(motivo, 'Motivo de revisión', 300, obligatorio=True)
    if len(motivo) < 8:
        raise ValueError('Explicá el motivo de la corrección (mínimo 8 caracteres).')
    try:
        clave = UUID(str(clave))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError('Identificador de revisión inválido.') from exc
    contenido = {c: str(datos.get(c, '')) for c in ('fecha','identificacion','importe','numero','titular','banco')}
    with transaction.atomic():
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        previa = RevisionPendienteBancario.objects.select_related('pendiente','actor').filter(clave=clave).first()
        if previa:
            if previa.pendiente_id != int(pendiente_id) or previa.actor.usuario_id != usuario.pk or previa.motivo != motivo or previa.contenido != contenido:
                raise ValueError('Identificador de revisión reutilizado con otros datos.')
            return previa, False
        p = PendienteBancario.objects.select_for_update().select_related('creado_por','resuelto_por').filter(
            empresa=empresa, pk=pendiente_id).first()
        if not p:
            raise PermissionDenied('El movimiento no pertenece a esta Empresa.')
        # Revisión de un resuelto tampoco permite consultar/corregir un Centro ajeno.
        if p.estado == 'Resuelto' and alcance is not None and p.centro_operativo_id not in alcance:
            raise PermissionDenied('El Centro resuelto no está autorizado.')
        general = alcance is None
        autor = p.creado_por.usuario_id == usuario.pk
        resolvedor = p.resuelto_por_id and p.resuelto_por.usuario_id == usuario.pk
        if p.estado == 'Pendiente':
            if not (general or autor):
                raise PermissionDenied('Sólo el creador o administración general puede editar.')
        elif not (general or autor or resolvedor):
            raise PermissionDenied('No puede abrir una auditoría de este movimiento.')
        actor = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        antes = _snapshot(p)
        if p.estado == 'Pendiente':
            fecha = _fecha(datos.get('fecha'))
            importe = importe_positivo(datos.get('importe'))
            identificacion = _texto(datos.get('identificacion', ''), 'Titular / Cliente', 200)
            p.fecha, p.importe, p.identificacion = fecha, importe, identificacion
            campos = ['fecha','importe','identificacion','modificado']
            if p.tipo == 'ECheq':
                if fecha < timezone.localdate() - timedelta(days=30):
                    raise ValueError('La fecha del e-Cheq no puede ser anterior a 30 días.')
                p.echeq_fecha_acreditacion = fecha
                p.echeq_numero = normalizar_numero_cheque(datos.get('numero', ''))
                p.referencia = p.echeq_numero
                p.echeq_titular = _texto(datos.get('titular', ''), 'Titular / Cliente', 200, obligatorio=True)
                banco = _texto(datos.get('banco',''), 'Banco emisor', 120, obligatorio=True)
                emisor = Banco.objects.filter(empresa=empresa, nombre__iexact=banco, activo=True).first()
                if emisor is None:
                    raise ValueError('Seleccione un banco emisor registrado en esta Empresa.')
                p.echeq_banco_nombre = emisor.nombre
                campos += ['echeq_fecha_acreditacion','echeq_numero','echeq_titular','echeq_banco_nombre','referencia']
            else:
                p.referencia = identificacion or 'Sin identificar'
                campos.append('referencia')
            despues = _snapshot(p)
            if antes == despues:
                raise ValueError('No hay cambios que registrar.')
            p.save(update_fields=campos)
            tipo, estado = 'Editado', 'Aplicado'
        else:
            # Evitar mutar el movimiento ya conciliado o imputado externamente.
            despues = antes
            tipo, estado = 'Incidencia', 'Abierto'
        revision = RevisionPendienteBancario.objects.create(
            pendiente=p, actor=actor, clave=clave, tipo=tipo, estado=estado,
            motivo=motivo, anterior=antes, nuevo=despues, contenido=contenido)
        EventoPendienteBancario.objects.create(pendiente=p, actor=actor,
            accion='Editado' if tipo == 'Editado' else 'RevisionSolicitada', detalle=motivo[:300])
    LOG.info('banco.revision_pendiente empresa_id=%s pendiente_id=%s revision_id=%s tipo=%s',empresa.pk,p.pk,revision.pk,tipo)
    return revision, True
