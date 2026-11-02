# Marca societaria optativa, sin modificar documentos ni fechas existentes.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0057_alertas_documentales')]

    operations = [
        migrations.AddField(
            model_name='empresa', name='acta_incluye_designacion',
            field=models.BooleanField(default=False),
        ),
    ]
