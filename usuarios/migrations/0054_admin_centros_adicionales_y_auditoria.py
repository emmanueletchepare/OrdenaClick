from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0053_gestion_clave_creador'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='CentroAdicionalAdministrador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('asignacion', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='centros_adicionales', to='usuarios.asignacionusuarioempresa')),
                ('centro_operativo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='asignaciones_adicionales', to='usuarios.centrooperativo')),
            ],
        ),
        migrations.AddConstraint(model_name='centroadicionaladministrador',
            constraint=models.UniqueConstraint(fields=('asignacion','centro_operativo'),
                name='uniq_centro_adicional_admin')),
        migrations.CreateModel(
            name='EventoGestionAsignacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(max_length=48)),
                ('detalle', models.JSONField(default=dict)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='eventos_asignacion_realizados', to=settings.AUTH_USER_MODEL)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='eventos_asignacion_recibidos', to=settings.AUTH_USER_MODEL)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    to='usuarios.empresa')),
            ],
        ),
    ]
