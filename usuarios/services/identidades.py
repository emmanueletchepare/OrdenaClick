from django.db import IntegrityError, transaction

from usuarios.models import IdentidadUsuarioEmpresa


def _datos_historicos_usuario(usuario):
    """Devuelve una fotografía legible y no privilegiada del usuario."""
    nombre_completo = usuario.get_full_name().strip()

    return {
        "username_historico": usuario.get_username(),
        "nombre_historico": nombre_completo,
        "email_historico": usuario.email or "",
    }


def obtener_identidad_usuario_empresa(*, empresa, usuario):
    """
    Obtiene o crea la identidad histórica del usuario dentro de la Empresa.

    La identidad no concede acceso ni jerarquía. Su única responsabilidad es
    conservar trazabilidad portable para operaciones históricas.
    """
    if not usuario or not usuario.is_authenticated:
        raise ValueError(
            "Se requiere un usuario autenticado para registrar identidad histórica."
        )

    datos = _datos_historicos_usuario(usuario)

    try:
        with transaction.atomic():
            identidad, creada = IdentidadUsuarioEmpresa.objects.get_or_create(
                empresa=empresa,
                usuario=usuario,
                defaults=datos,
            )
    except IntegrityError:
        identidad = IdentidadUsuarioEmpresa.objects.get(
            empresa=empresa,
            usuario=usuario,
        )
        creada = False

    if not creada:
        campos_actualizados = []
        for campo, valor in datos.items():
            if getattr(identidad, campo) != valor:
                setattr(identidad, campo, valor)
                campos_actualizados.append(campo)

        if campos_actualizados:
            identidad.save(update_fields=[*campos_actualizados, "actualizado"])

    return identidad
