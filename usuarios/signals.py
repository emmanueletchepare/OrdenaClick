from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    CentroOperativo,
    RecursoOperativo,
    RecursoOperativoCentro,
)


@receiver(
    post_save,
    sender=CentroOperativo
)
def crear_recurso_general_casa_central(
    sender,
    instance,
    created,
    **kwargs
):
    """
    Crea el Recurso Operativo GENERAL para una Casa Central
    y asegura su relación con el Centro Operativo creado.
    """

    if not created:
        return

    if instance.tipo != "Casa Central":
        return

    recurso_general, _ = (
        RecursoOperativo.objects.get_or_create(
            empresa=instance.empresa,
            nombre="GENERAL",
            defaults={
                "tipo_recurso": "Inmueble",
                "descripcion": (
                    "Recurso operativo general "
                    "creado automáticamente."
                ),
                "activo": True,
            },
        )
    )

    RecursoOperativoCentro.objects.get_or_create(
        recurso_operativo=recurso_general,
        centro_operativo=instance,
    )