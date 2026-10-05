from django.core.exceptions import PermissionDenied

from usuarios.models import AsignacionUsuarioEmpresa, Empresa


JERARQUIAS_ADMINISTRACION_EMPRESA = {
    AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
}

JERARQUIAS_CAJA = {
    AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
    AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO,
}


def _validar_usuario_autenticado(usuario):
    if not usuario.is_authenticated:
        raise PermissionDenied(
            "El usuario no está autenticado."
        )


def _obtener_empresa(empresa_id):
    empresa = Empresa.objects.filter(
        id=empresa_id,
    ).first()

    if not empresa:
        raise PermissionDenied(
            "La Empresa solicitada no existe."
        )

    return empresa


def _obtener_asignacion_activa(usuario, empresa):
    return (
        AsignacionUsuarioEmpresa.objects
        .select_related(
            "centro_operativo",
        )
        .filter(
            empresa=empresa,
            usuario=usuario,
            activo=True,
        )
        .first()
    )


def obtener_empresa_autorizada(
    usuario,
    empresa_id,
):
    """
    Devuelve una Empresa únicamente si el usuario tiene autorización
    estructural de propietario sobre ella.

    Esta función conserva deliberadamente un alcance restrictivo porque
    todavía existen views administrativas históricas que la utilizan como
    barrera general. Las jerarquías asignadas deben habilitarse mediante
    funciones explícitas de capacidad para evitar ampliar privilegios por
    efecto colateral.

    Reglas:
    - Un superusuario puede acceder a cualquier Empresa.
    - El propietario puede acceder a su Empresa.
    - Las asignaciones NO se habilitan implícitamente desde esta función.
    """

    _validar_usuario_autenticado(usuario)
    empresa = _obtener_empresa(empresa_id)

    if usuario.is_superuser:
        return empresa

    if empresa.propietario_id == usuario.id:
        return empresa

    raise PermissionDenied(
        "No tiene permisos para operar sobre esta Empresa."
    )


def obtener_empresa_administrable(
    usuario,
    empresa_id,
):
    """
    Devuelve una Empresa cuando el usuario puede administrarla de forma
    global.

    Se utiliza para capacidades sensibles de alcance Empresa completo,
    como Backup/Restore. No habilita a Administradores de Centro ni a
    Colaboradores.
    """

    _validar_usuario_autenticado(usuario)
    empresa = _obtener_empresa(empresa_id)

    if usuario.is_superuser or empresa.propietario_id == usuario.id:
        return empresa

    asignacion = _obtener_asignacion_activa(
        usuario,
        empresa,
    )

    if (
        asignacion
        and asignacion.jerarquia
        == AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL
    ):
        return empresa

    raise PermissionDenied(
        "No tiene permisos de administración general sobre esta Empresa."
    )


def obtener_centro_autorizado(
    usuario,
    empresa_id,
    centro_id,
):
    """
    Devuelve un Centro Operativo activo dentro del alcance del usuario.

    - Propietario, superusuario y Administrador general: cualquier Centro
      activo de la Empresa.
    - Administrador: únicamente su Centro activo asignado.
    - Colaborador: sin alcance de administración por Centro en esta etapa.
    """
    from usuarios.models import CentroOperativo

    _validar_usuario_autenticado(usuario)
    empresa = _obtener_empresa(empresa_id)

    try:
        centro = CentroOperativo.objects.get(
            id=centro_id,
            empresa=empresa,
            activo=True,
        )
    except (
        CentroOperativo.DoesNotExist,
        TypeError,
        ValueError,
    ) as error:
        raise PermissionDenied(
            "No tiene autorización para operar sobre este Centro Operativo."
        ) from error

    if usuario.is_superuser or empresa.propietario_id == usuario.id:
        return empresa, centro

    asignacion = _obtener_asignacion_activa(
        usuario,
        empresa,
    )

    if not asignacion:
        raise PermissionDenied(
            "No tiene autorización para operar sobre este Centro Operativo."
        )

    if (
        asignacion.jerarquia
        == AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL
    ):
        return empresa, centro

    if (
        asignacion.jerarquia
        == AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO
        and asignacion.centro_operativo_id == centro.id
    ):
        return empresa, centro

    raise PermissionDenied(
        "No tiene autorización para operar sobre este Centro Operativo."
    )


def cajas_autorizadas(
    usuario,
    empresa_id,
):
    """
    Devuelve la Empresa y el queryset de Cajas operativas dentro del
    alcance real del usuario.

    Colaborador no posee acceso a Caja. Un Administrador sólo ve las
    Cajas de su Centro. Propietario, superusuario y Administrador general
    ven todas las Cajas operativas de la Empresa.
    """
    from usuarios.models import Caja

    _validar_usuario_autenticado(usuario)
    empresa = _obtener_empresa(empresa_id)

    cajas = (
        Caja.objects
        .filter(
            empresa=empresa,
            activo=True,
            centro_operativo__activo=True,
            centro_operativo__tipo__in=[
                "Casa Central",
                "Sucursal",
                "Mostrador",
            ],
        )
        .select_related(
            "centro_operativo",
        )
        .order_by(
            "centro_operativo__nombre",
            "nombre",
        )
    )

    if usuario.is_superuser or empresa.propietario_id == usuario.id:
        return empresa, cajas

    asignacion = _obtener_asignacion_activa(
        usuario,
        empresa,
    )

    if not asignacion:
        raise PermissionDenied(
            "No tiene autorización para operar sobre Caja."
        )

    if (
        asignacion.jerarquia
        == AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL
    ):
        return empresa, cajas

    if (
        asignacion.jerarquia
        == AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO
        and asignacion.centro_operativo_id
    ):
        return (
            empresa,
            cajas.filter(
                centro_operativo_id=asignacion.centro_operativo_id,
            ),
        )

    raise PermissionDenied(
        "No tiene autorización para operar sobre Caja."
    )


def obtener_caja_autorizada(
    usuario,
    empresa_id,
    caja_id,
):
    """
    Devuelve una Caja concreta únicamente cuando pertenece a la Empresa,
    está operativa y queda dentro del alcance real del usuario.

    La autorización se resuelve completamente en backend; el ID recibido
    desde el navegador nunca define el alcance.
    """

    from usuarios.models import Caja

    empresa, cajas = cajas_autorizadas(
        usuario,
        empresa_id,
    )

    try:
        caja = cajas.get(
            id=caja_id,
        )
    except (
        TypeError,
        ValueError,
        Caja.DoesNotExist,
    ) as error:
        raise PermissionDenied(
            "No tiene autorización para operar sobre esta Caja."
        ) from error

    return empresa, caja


def empresas_autorizadas(usuario):
    """
    Devuelve las Empresas que el usuario puede consultar desde el panel
    administrativo histórico.

    Deliberadamente conserva el alcance propietario/superusuario mientras
    las pantallas administrativas se habilitan módulo por módulo según
    capacidad. Evita que una asignación operativa abra todo el panel por
    accidente.
    """

    if not usuario.is_authenticated:
        return Empresa.objects.none()

    if usuario.is_superuser:
        return Empresa.objects.all()

    return Empresa.objects.filter(
        propietario=usuario,
    )
