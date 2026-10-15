"""Reglas de personal: permisos, seguimiento de licencias y documentos privados."""
import calendar
import hashlib
import uuid
from datetime import date
from pathlib import Path

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from usuarios.models import AlertaLicenciaEmpleado, EventoEmpleado
from usuarios.services.identidades import obtener_identidad_usuario_empresa
from usuarios.services.seguridad import obtener_empresa_administrable

DOCUMENTOS = {"DNIFrente", "DNIDorso", "Licencia", "CAT", "Preocupacional", "Caso"}
MAX_DOCUMENTO = 20 * 1024 * 1024


def acceso_nomina(usuario, empresa_id):
    """Acceso transitorio de mínimo privilegio, hasta la matriz granular aprobada."""
    return obtener_empresa_administrable(usuario, empresa_id)


def mes_anterior(fecha):
    mes = fecha.month - 1 or 12
    anio = fecha.year - (1 if fecha.month == 1 else 0)
    return date(anio, mes, min(fecha.day, calendar.monthrange(anio, mes)[1]))


def sincronizar_alerta(empleado):
    """Persistir recordatorio; desvincular cancela sin borrar el rastro."""
    alerta = AlertaLicenciaEmpleado.objects.select_for_update().filter(empleado=empleado).first()
    if not empleado.fecha_vencimiento_licencia:
        if alerta and alerta.cancelada_en is None:
            alerta.cancelada_en = timezone.now()
            alerta.save(update_fields=["cancelada_en", "modificado"])
        return
    if not alerta:
        AlertaLicenciaEmpleado.objects.create(
            empleado=empleado, fecha_vencimiento=empleado.fecha_vencimiento_licencia,
            fecha_aviso=mes_anterior(empleado.fecha_vencimiento_licencia),
            cancelada_en=None if empleado.activo else timezone.now(),
        )
        return
    if alerta.fecha_vencimiento != empleado.fecha_vencimiento_licencia:
        alerta.fecha_vencimiento = empleado.fecha_vencimiento_licencia
        alerta.fecha_aviso = mes_anterior(empleado.fecha_vencimiento_licencia)
        alerta.reconocida_en = None
        alerta.cancelada_en = None if empleado.activo else timezone.now()
        alerta.save()
    elif empleado.activo and alerta.cancelada_en is not None:
        alerta.cancelada_en = None
        alerta.reconocida_en = None
        alerta.save(update_fields=['cancelada_en', 'reconocida_en', 'modificado'])
    elif empleado.activo and alerta.cancelada_en is not None:
        alerta.cancelada_en = None
        alerta.reconocida_en = None
        alerta.save(update_fields=['cancelada_en', 'reconocida_en', 'modificado'])
    elif empleado.activo and alerta.cancelada_en is not None:
        alerta.cancelada_en = None
        alerta.reconocida_en = None
        alerta.save(update_fields=['cancelada_en', 'reconocida_en', 'modificado'])
    elif empleado.activo and alerta.cancelada_en is not None:
        alerta.cancelada_en = None
        alerta.reconocida_en = None
        alerta.save(update_fields=['cancelada_en', 'reconocida_en', 'modificado'])
    elif not empleado.activo and alerta.cancelada_en is None:
        alerta.cancelada_en = timezone.now()
        alerta.save(update_fields=["cancelada_en", "modificado"])


def alertas_pendientes(empresa, hoy=None):
    return AlertaLicenciaEmpleado.objects.filter(
        empleado__empresa=empresa, empleado__activo=True,
        cancelada_en__isnull=True, reconocida_en__isnull=True,
        fecha_aviso__lte=hoy or timezone.localdate(),
    ).select_related('empleado').order_by('fecha_vencimiento', 'pk')


def evento(empleado, usuario, accion, detalle=""):
    identidad = obtener_identidad_usuario_empresa(empresa=empleado.empresa, usuario=usuario)
    return EventoEmpleado.objects.create(empleado=empleado, actor=identidad,
                                         accion=accion, detalle=str(detalle)[:300])


def archivo_validado(archivo):
    """Comprobar contenido y tamaño real, no extensión o MIME declarados."""
    if not archivo or archivo.size > MAX_DOCUMENTO or archivo.size <= 0:
        raise ValidationError('El documento debe tener entre 1 byte y 20 MiB.')
    posicion = archivo.tell()
    try:
        inicio = archivo.read(16)
        if inicio.startswith(b'%PDF-'):
            extension = '.pdf'
        elif inicio.startswith(b'\xff\xd8\xff'):
            extension = '.jpg'
        elif inicio.startswith(b'\x89PNG\r\n\x1a\n'):
            extension = '.png'
        else:
            raise ValidationError('Se permiten PDF, JPG y PNG con contenido válido.')
        archivo.seek(0)
        digest = hashlib.sha256()
        total = 0
        for bloque in archivo.chunks():
            total += len(bloque)
            if total > MAX_DOCUMENTO:
                raise ValidationError('El documento supera 20 MiB.')
            digest.update(bloque)
        return extension, digest.hexdigest()
    finally:
        archivo.seek(posicion)


def ruta_documento(instance, nombre):
    """Nombre opaco, nunca CUIL, DNI, nombres, ni ruta suministrada por navegador."""
    ext = getattr(instance, '_extension_verificada', None)
    if ext not in ('.pdf', '.jpg', '.png'):
        raise ValidationError('Documento no validado.')
    return f'nomina/empresa_{instance.empleado.empresa_id}/empleado_{instance.empleado_id}/{uuid.uuid4().hex}{ext}'
