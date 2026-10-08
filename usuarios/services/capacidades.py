from dataclasses import dataclass

from django.core.exceptions import PermissionDenied

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    Empresa,
    RolFuncionalUsuarioEmpresa,
)


CAPACIDAD_EMPRESA_ADMINISTRAR = "empresa.administrar"
CAPACIDAD_EMPRESA_BACKUP = "empresa.backup"
CAPACIDAD_EMPRESA_RESTAURAR = "empresa.restaurar"
CAPACIDAD_CAJA_VER = "caja.ver"
CAPACIDAD_CAJA_OPERAR = "caja.operar"


CAPACIDADES_EMPRESA_COMPLETA = frozenset(
    {
        CAPACIDAD_EMPRESA_ADMINISTRAR,
        CAPACIDAD_EMPRESA_BACKUP,
        CAPACIDAD_EMPRESA_RESTAURAR,
        CAPACIDAD_CAJA_VER,
        CAPACIDAD_CAJA_OPERAR,
    }
)

CAPACIDADES_ADMIN_GENERAL = CAPACIDADES_EMPRESA_COMPLETA

CAPACIDADES_ADMIN_CENTRO = frozenset(
    {
        CAPACIDAD_CAJA_VER,
        CAPACIDAD_CAJA_OPERAR,
    }
)

CAPACIDADES_COLABORADOR = frozenset()


@dataclass(frozen=True)
class ContextoCapacidadesEmpresa:
    """
    Resume la autorización estructural vigente de un usuario en una Empresa.

    Esta capa no reemplaza todavía los helpers existentes de seguridad.
    Centraliza el significado de capacidades ya cerradas sin modificar el
    comportamiento de las views actuales.

    ``centro_operativo_id`` limita las capacidades de Administrador de Centro.
    Propietario y superusuario conservan alcance completo por decisión vigente.
    Los roles funcionales Contable/Legal no conceden capacidades administrativas
    ni de Caja por sí solos.
    """

    empresa: Empresa
    capacidades: frozenset[str]
    centro_operativo_id: int | None
    roles_funcionales: frozenset[str]
    es_superusuario: bool
    es_propietario: bool
    jerarquia: str | None

    def tiene(self, capacidad):
        """Indica si el contexto incluye una capacidad concreta."""
        return capacidad in self.capacidades


def obtener_contexto_capacidades_empresa(usuario, empresa_id):
    """
    Resuelve capacidades estructurales ya definidas para una Empresa.

    Reglas preservadas:
    - superusuario: alcance completo;
    - propietario: alcance completo;
    - admin_general activo: alcance completo actual;
    - admin_centro activo: capacidades de Caja limitadas a su Centro;
    - colaborador: sin capacidades administrativas/Caja implícitas;
    - Contable/Legal: roles funcionales independientes, sin elevación implícita.

    Esta función niega acceso si el usuario no está autenticado, la Empresa no
    existe o el usuario no posee ninguna relación estructural/funcional con ella.
    """

    if not getattr(usuario, "is_authenticated", False):
        raise PermissionDenied("El usuario no está autenticado.")

    empresa = Empresa.objects.filter(pk=empresa_id).first()

    if empresa is None:
        raise PermissionDenied("La Empresa solicitada no existe.")

    roles_funcionales = frozenset(
        RolFuncionalUsuarioEmpresa.objects.filter(
            empresa=empresa,
            usuario=usuario,
            activo=True,
        ).values_list("rol", flat=True)
    )

    if usuario.is_superuser:
        return ContextoCapacidadesEmpresa(
            empresa=empresa,
            capacidades=CAPACIDADES_EMPRESA_COMPLETA,
            centro_operativo_id=None,
            roles_funcionales=roles_funcionales,
            es_superusuario=True,
            es_propietario=empresa.propietario_id == usuario.id,
            jerarquia=None,
        )

    if empresa.propietario_id == usuario.id:
        return ContextoCapacidadesEmpresa(
            empresa=empresa,
            capacidades=CAPACIDADES_EMPRESA_COMPLETA,
            centro_operativo_id=None,
            roles_funcionales=roles_funcionales,
            es_superusuario=False,
            es_propietario=True,
            jerarquia=None,
        )

    asignacion = (
        AsignacionUsuarioEmpresa.objects
        .filter(
            empresa=empresa,
            usuario=usuario,
            activo=True,
        )
        .first()
    )

    if asignacion is not None:
        if (
            asignacion.jerarquia
            == AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL
        ):
            capacidades = CAPACIDADES_ADMIN_GENERAL
            centro_operativo_id = None
        elif (
            asignacion.jerarquia
            == AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO
        ):
            capacidades = CAPACIDADES_ADMIN_CENTRO
            centro_operativo_id = asignacion.centro_operativo_id
        else:
            capacidades = CAPACIDADES_COLABORADOR
            centro_operativo_id = None

        return ContextoCapacidadesEmpresa(
            empresa=empresa,
            capacidades=capacidades,
            centro_operativo_id=centro_operativo_id,
            roles_funcionales=roles_funcionales,
            es_superusuario=False,
            es_propietario=False,
            jerarquia=asignacion.jerarquia,
        )

    if roles_funcionales:
        return ContextoCapacidadesEmpresa(
            empresa=empresa,
            capacidades=frozenset(),
            centro_operativo_id=None,
            roles_funcionales=roles_funcionales,
            es_superusuario=False,
            es_propietario=False,
            jerarquia=None,
        )

    raise PermissionDenied(
        "No tiene una relación activa con esta Empresa."
    )


def exigir_capacidad_empresa(usuario, empresa_id, capacidad):
    """
    Devuelve el contexto cuando el usuario posee la capacidad solicitada.

    No decide todavía permisos de objetos hijos. Las views que migren a esta
    capa deberán seguir acotando Centro/Caja/objeto dentro del alcance devuelto.
    """

    contexto = obtener_contexto_capacidades_empresa(
        usuario,
        empresa_id,
    )

    if not contexto.tiene(capacidad):
        raise PermissionDenied(
            "No tiene la capacidad requerida para operar sobre esta Empresa."
        )

    return contexto
