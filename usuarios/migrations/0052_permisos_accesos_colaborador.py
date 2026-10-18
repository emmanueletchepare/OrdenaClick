"""Autorizaciones operativas granulares y eventos de cambios."""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios', '0051_salida_echeq_auditada'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='PermisoAccesoColaborador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=64)),
                ('activo', models.BooleanField(default=True)),
                ('modificado', models.DateTimeField(auto_now=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='permisos_colaborador', to='usuarios.empresa')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='permisos_modulos_empresa', to=settings.AUTH_USER_MODEL)),
                ('otorgado_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='permisos_colaborador_otorgados', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(model_name='permisoaccesocolaborador', constraint=models.UniqueConstraint(fields=('empresa', 'usuario', 'codigo'), name='uniq_permiso_colab_emp_cod')),
        migrations.CreateModel(
            name='EventoPermisoAccesoColaborador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=64)),
                ('activo', models.BooleanField()),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.empresa')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='historial_permisos_recibidos', to=settings.AUTH_USER_MODEL)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='historial_permisos_otorgados', to=settings.AUTH_USER_MODEL)),
            ], options={'ordering': ('-creado', '-pk')},
        ),
    ]
