from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0044_caja2_pendientes_y_correcciones')]
    operations = [
        migrations.AddField(model_name='pendientebancario', name='identificacion',
            field=models.CharField(max_length=200, blank=True)),
        migrations.AddField(model_name='pendientebancario', name='echeq_titular',
            field=models.CharField(max_length=200, blank=True)),
        migrations.AddField(model_name='pendientebancario', name='echeq_numero',
            field=models.CharField(max_length=80, blank=True)),
        migrations.AddField(model_name='pendientebancario', name='echeq_banco_nombre',
            field=models.CharField(max_length=150, blank=True)),
        migrations.AddField(model_name='pendientebancario', name='echeq_banco_codigo',
            field=models.CharField(max_length=12, blank=True)),
        migrations.AddField(model_name='pendientebancario', name='echeq_fecha_acreditacion',
            field=models.DateField(null=True, blank=True)),
        migrations.AddField(model_name='pendientebancario', name='echeq_condicion',
            field=models.CharField(max_length=8, choices=[('Orden', 'A la orden'), ('NoOrden', 'No a la orden')], default='Orden')),
    ]
