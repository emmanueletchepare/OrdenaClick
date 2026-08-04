from django.db import migrations


def crear_recursos_generales(
    apps,
    schema_editor
):

    Empresa = apps.get_model(
        "usuarios",
        "Empresa"
    )

    CentroOperativo = apps.get_model(
        "usuarios",
        "CentroOperativo"
    )

    RecursoOperativo = apps.get_model(
        "usuarios",
        "RecursoOperativo"
    )


    for empresa in Empresa.objects.all():

        centro = (
            CentroOperativo.objects
            .filter(
                empresa=empresa,
                tipo="Casa Central"
            )
            .order_by(
                "id"
            )
            .first()
        )


        if not centro:

            centro = CentroOperativo.objects.create(

                empresa=empresa,

                nombre="CASA CENTRAL",

                tipo="Casa Central",

                direccion=(
                    empresa.direccion_real or ""
                ),

                activo=True

            )


        RecursoOperativo.objects.get_or_create(

            empresa=empresa,

            nombre="GENERAL",

            defaults={

                "tipo_recurso":
                    "Inmueble",

                "centro_operativo":
                    centro,

                "descripcion": (
                    "Recurso operativo general "
                    "creado automáticamente."
                ),

                "activo":
                    True

            }

        )


def revertir_recursos_generales(
    apps,
    schema_editor
):

    pass


class Migration(migrations.Migration):

    dependencies = [
        (
            "usuarios",
            "0014_recursooperativo"
        ),
    ]

    operations = [

        migrations.RunPython(
            crear_recursos_generales,
            revertir_recursos_generales
        ),

    ]