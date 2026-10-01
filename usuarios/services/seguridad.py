from django.core.exceptions import PermissionDenied

from usuarios.models import Empresa


def obtener_empresa_autorizada(
    usuario,
    empresa_id,
):
    """
    Devuelve una Empresa únicamente si el usuario tiene autorización
    para operar sobre ella.

    Reglas actuales:
    - Un superusuario puede acceder a cualquier Empresa.
    - Un Administrador sólo puede acceder a Empresas de las que es propietario.
    - Los perfiles Colaborador, Contable y Legal se incorporarán mediante
      relaciones explícitas de asignación cuando se implementen.
    """

    if not usuario.is_authenticated:
        raise PermissionDenied(
            "El usuario no está autenticado."
        )

    empresa = Empresa.objects.filter(
        id=empresa_id,
    ).first()

    if not empresa:
        raise PermissionDenied(
            "La Empresa solicitada no existe."
        )

    if usuario.is_superuser:
        return empresa

    if empresa.propietario_id == usuario.id:
        return empresa

    raise PermissionDenied(
        "No tiene permisos para operar sobre esta Empresa."
    )

def obtener_caja_autorizada(
    usuario,
    empresa_id,
    caja_id,
):
    """
    Devuelve una Caja operativa únicamente cuando el usuario puede operar
    sobre su Empresa y la Caja pertenece a esa misma Empresa.

    La autorización de usuario se resuelve primero mediante
    obtener_empresa_autorizada(). Además, la Caja debe estar activa,
    pertenecer a un Centro Operativo activo y dicho Centro debe ser una
    Casa Casa Central, Sucursal o Mostrador.

    Esta función constituye el punto común de autorización para las
    operaciones financieras sobre Caja. Los futuros alcances explícitos
    por Centro Operativo o Caja deberán incorporarse aquí, sin delegar
    esa decisión al navegador.
    """
    from usuarios.models import Caja

    empresa = obtener_empresa_autorizada(
        usuario,
        empresa_id,
    )

    try:
        caja = (
            Caja.objects
            .select_related(
                "centro_operativo",
            )
            .get(
                id=caja_id,
                empresa=empresa,
                activo=True,
                centro_operativo__activo=True,
                centro_operativo__tipo__in=[
                    "Casa Central",
                    "Sucursal",
                    "Mostrador",
                ],
            )
        )
    except (
        Caja.DoesNotExist,
        TypeError,
        ValueError,
    ) as error:
        raise PermissionDenied(
            "No tiene autorización para operar sobre esta Caja."
        ) from error

    return empresa, caja

def empresas_autorizadas(usuario):
    """
    Devuelve las Empresas que el usuario puede consultar.

    Reglas actuales:
    - Un superusuario puede consultar todas las Empresas.
    - Un Administrador normal consulta únicamente sus Empresas.
    """

    if not usuario.is_authenticated:
        return Empresa.objects.none()

    if usuario.is_superuser:
        return Empresa.objects.all()

    return Empresa.objects.filter(
        propietario=usuario,
    )