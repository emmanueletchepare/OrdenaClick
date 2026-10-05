from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    CentroOperativo,
    RolFuncionalUsuarioEmpresa,
    SolicitudRelacionEmpresa,
)
from usuarios.services.identidades import obtener_identidad_usuario_empresa
from usuarios.services.seguridad import obtener_empresa_administrable


User = get_user_model()

ROLES_JERARQUICOS = {
    SolicitudRelacionEmpresa.ROL_ADMIN_GENERAL,
    SolicitudRelacionEmpresa.ROL_ADMIN_CENTRO,
    SolicitudRelacionEmpresa.ROL_COLABORADOR,
}

ROLES_FUNCIONALES = {
    SolicitudRelacionEmpresa.ROL_CONTABLE,
    SolicitudRelacionEmpresa.ROL_LEGAL,
}

ROLES_VALIDOS = ROLES_JERARQUICOS | ROLES_FUNCIONALES


def _buscar_usuario_existente(identificador):
    valor = (identificador or "").strip()
    if not valor:
        raise ValidationError("Indicá el usuario o correo electrónico de la persona.")

    usuario = (
        User.objects
        .filter(is_active=True)
        .filter(Q(username__iexact=valor) | Q(email__iexact=valor))
        .order_by("id")
        .first()
    )
    if not usuario:
        raise ValidationError(
            "No existe un usuario activo de OrdenaClick con ese usuario o correo electrónico."
        )
    return usuario


def crear_solicitud_relacion(
    *,
    solicitante,
    empresa_id,
    identificador_usuario,
    rol,
    centro_id=None,
    mensaje="",
):
    """Crea una solicitud pendiente sin conceder permisos automáticamente."""
    empresa = obtener_empresa_administrable(solicitante, empresa_id)

    if rol not in ROLES_VALIDOS:
        raise ValidationError("El rol solicitado no es válido.")

    destinatario = _buscar_usuario_existente(identificador_usuario)

    centro = None
    if rol == SolicitudRelacionEmpresa.ROL_ADMIN_CENTRO:
        try:
            centro = empresa.centros.get(pk=centro_id, activo=True)
        except (TypeError, ValueError, CentroOperativo.DoesNotExist) as error:
            raise ValidationError("Seleccioná un Centro Operativo válido para el Administrador.") from error
    elif centro_id:
        raise ValidationError("El rol seleccionado no utiliza Centro Operativo.")

    if destinatario.pk == empresa.propietario_id and rol in ROLES_JERARQUICOS:
        raise ValidationError(
            "El fundador ya administra la Empresa por propiedad y no necesita una asignación jerárquica."
        )

    if rol in ROLES_FUNCIONALES:
        rol_existente = RolFuncionalUsuarioEmpresa.objects.filter(
            empresa=empresa,
            usuario=destinatario,
            rol=rol,
            activo=True,
        ).exists()
        if rol_existente:
            raise ValidationError("Ese usuario ya tiene este rol activo en la Empresa.")
    else:
        asignacion = AsignacionUsuarioEmpresa.objects.filter(
            empresa=empresa,
            usuario=destinatario,
            activo=True,
        ).first()
        if asignacion:
            mismo_centro = (
                rol != SolicitudRelacionEmpresa.ROL_ADMIN_CENTRO
                or asignacion.centro_operativo_id == getattr(centro, "id", None)
            )
            if asignacion.jerarquia == rol and mismo_centro:
                raise ValidationError("Ese usuario ya tiene activa esa relación con la Empresa.")

    duplicada = SolicitudRelacionEmpresa.objects.filter(
        empresa=empresa,
        usuario_destino=destinatario,
        rol=rol,
        centro_operativo=centro,
        estado=SolicitudRelacionEmpresa.ESTADO_PENDIENTE,
    ).exists()
    if duplicada:
        raise ValidationError("Ya existe una solicitud pendiente equivalente para ese usuario.")

    try:
        with transaction.atomic():
            solicitud = SolicitudRelacionEmpresa(
                empresa=empresa,
                usuario_destino=destinatario,
                solicitada_por=solicitante,
                rol=rol,
                centro_operativo=centro,
                mensaje=(mensaje or "").strip(),
            )
            solicitud.full_clean()
            solicitud.save()
    except IntegrityError as error:
        raise ValidationError("Ya existe una solicitud pendiente equivalente.") from error

    return solicitud


def resolver_solicitud_relacion(*, usuario, solicitud_id, accion):
    """Acepta o rechaza una solicitud recibida por el usuario autenticado."""
    if accion not in {"aceptar", "rechazar"}:
        raise ValidationError("La acción solicitada no es válida.")

    with transaction.atomic():
        try:
            solicitud = (
                SolicitudRelacionEmpresa.objects
                .select_for_update()
                .select_related("empresa", "centro_operativo", "usuario_destino")
                .get(pk=solicitud_id)
            )
        except SolicitudRelacionEmpresa.DoesNotExist as error:
            raise PermissionDenied("La solicitud no existe o no está disponible.") from error

        if solicitud.usuario_destino_id != usuario.id:
            raise PermissionDenied("No puede resolver una solicitud dirigida a otro usuario.")

        if solicitud.estado != SolicitudRelacionEmpresa.ESTADO_PENDIENTE:
            raise ValidationError("La solicitud ya fue resuelta.")

        if accion == "rechazar":
            solicitud.estado = SolicitudRelacionEmpresa.ESTADO_RECHAZADA
            solicitud.resuelta = timezone.now()
            solicitud.save(update_fields=["estado", "resuelta", "actualizada"])
            return solicitud

        empresa = solicitud.empresa
        rol = solicitud.rol

        if rol in ROLES_JERARQUICOS:
            if usuario.pk == empresa.propietario_id:
                raise ValidationError(
                    "El fundador no se duplica como asignación jerárquica."
                )

            defaults = {
                "jerarquia": rol,
                "activo": True,
                "centro_operativo": (
                    solicitud.centro_operativo
                    if rol == SolicitudRelacionEmpresa.ROL_ADMIN_CENTRO
                    else None
                ),
            }
            asignacion, _ = AsignacionUsuarioEmpresa.objects.update_or_create(
                empresa=empresa,
                usuario=usuario,
                defaults=defaults,
            )
            asignacion.full_clean()
            asignacion.save()
        else:
            rol_funcional, _ = RolFuncionalUsuarioEmpresa.objects.get_or_create(
                empresa=empresa,
                usuario=usuario,
                rol=rol,
                defaults={"activo": True},
            )
            if not rol_funcional.activo:
                rol_funcional.activo = True
                rol_funcional.save(update_fields=["activo", "actualizado"])

        obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)

        solicitud.estado = SolicitudRelacionEmpresa.ESTADO_ACEPTADA
        solicitud.resuelta = timezone.now()
        solicitud.save(update_fields=["estado", "resuelta", "actualizada"])
        return solicitud
