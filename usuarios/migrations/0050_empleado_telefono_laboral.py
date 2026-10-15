"""Teléfono laboral opcional en Nómina; los empleados existentes se conservan."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0049_nomina_empleados')]
    operations = [
        migrations.AddField(
            model_name='empleado',
            name='telefono_laboral',
            field=models.CharField(max_length=60, blank=True),
        ),
    ]
