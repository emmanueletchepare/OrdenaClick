from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0041_intentos_login_origen')]

    operations = [
        migrations.CreateModel(
            name='IdempotenciaPagoManual',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.UUIDField(unique=True)),
                ('huella', models.CharField(max_length=64)),
                ('respuesta', models.JSONField()),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.empresa')),
                ('movimiento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.movimiento')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
