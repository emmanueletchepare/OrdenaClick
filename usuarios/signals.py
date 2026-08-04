from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    CentroOperativo,
    RecursoOperativo
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

    if not created:

        return

    if instance.tipo != "Casa Central":

        return

    RecursoOperativo.objects.get_or_create(

        empresa=instance.empresa,

        nombre="GENERAL",

        defaults={
            "tipo_recurso": "Inmueble",
            "centro_operativo": instance,
            "descripcion": (
                "Recurso operativo general "
                "creado automáticamente."
            ),
            "activo": True
        }

    )