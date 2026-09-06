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
