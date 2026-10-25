# Generada desde el esquema B2, sin migrar BD automáticamente.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0055_permisos_nomina_centros'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='DestinatarioAlerta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=12)),
                ('activo', models.BooleanField(default=False)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('configurado_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='destinatarios_alertas_configurados', to=settings.AUTH_USER_MODEL)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.empresa')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={'constraints': [models.UniqueConstraint(fields=('empresa','usuario','codigo'), name='uniq_alerta_destino_empresa_usuario_tipo')]},
        ),
        migrations.CreateModel(
            name='PreferenciaSonidoAlerta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('habilitado', models.BooleanField(default=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.empresa')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={'constraints': [models.UniqueConstraint(fields=('empresa','usuario'), name='uniq_alerta_sonido_empresa_usuario')]},
        ),
        migrations.CreateModel(
            name='EventoConfiguracionAlerta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=12)),
                ('activo', models.BooleanField()),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='alertas_configuracion_realizada', to=settings.AUTH_USER_MODEL)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.empresa')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='alertas_configuracion_recibida', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ('-creado', '-pk')},
        ),
    ]
