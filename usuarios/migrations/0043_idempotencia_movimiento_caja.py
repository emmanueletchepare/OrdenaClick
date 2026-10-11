from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0042_idempotencia_pago_manual'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IdempotenciaMovimientoCaja',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.UUIDField(unique=True)),
                ('huella', models.CharField(max_length=64)),
                ('respuesta', models.JSONField()),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('caja', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarios.caja')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarios.empresa')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
