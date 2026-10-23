from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0054_admin_centros_adicionales_y_auditoria'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='PermisoNominaCentro',
            fields=[
                ('id', models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
                ('activo', models.BooleanField(default=True)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='permisos_nomina_centros',to='usuarios.empresa')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='permisos_nomina_centros',to=settings.AUTH_USER_MODEL)),
                ('centro_operativo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='permisos_nomina',to='usuarios.centrooperativo')),
                ('otorgado_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='permisos_nomina_concedidos',to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(model_name='permisonominacentro',
            constraint=models.UniqueConstraint(fields=('empresa','usuario','centro_operativo'),
                name='uniq_permiso_nomina_por_centro')),
    ]
