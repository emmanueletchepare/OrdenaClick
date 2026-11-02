# Campos de vencimiento societario y habilitaciones por Centro.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0056_gestor_alertas_b2')]

    operations = [
        migrations.AddField(model_name='empresa', name='acta_directorio',
            field=models.FileField(blank=True, null=True, upload_to='documentos/')),
        migrations.AddField(model_name='empresa', name='fecha_acta_directorio',
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='empresa', name='vencimiento_acta_directorio',
            field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='empresa', name='vencimiento_acta',
            field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='empresa', name='vencimiento_designacion',
            field=models.DateField(blank=True, null=True)),
        migrations.CreateModel(name='HabilitacionCentro', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('descripcion', models.CharField(max_length=160)),
            ('organismo', models.CharField(blank=True, max_length=160)),
            ('numero', models.CharField(blank=True, max_length=100)),
            ('vencimiento', models.DateField(blank=True, null=True)),
            ('archivo', models.FileField(blank=True, null=True, upload_to='documentos/habilitaciones/')),
            ('activo', models.BooleanField(default=True)),
            ('creado_por', models.CharField(blank=True, max_length=150)),
            ('actualizado_por', models.CharField(blank=True, max_length=150)),
            ('creado', models.DateTimeField(auto_now_add=True)),
            ('modificado', models.DateTimeField(auto_now=True)),
            ('centro', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                        related_name='habilitaciones', to='usuarios.centrooperativo')),
        ], options={'ordering': ('centro_id', '-activo', '-creado', '-pk')}),
    ]
