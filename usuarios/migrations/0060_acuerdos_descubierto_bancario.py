# Campos no destructivos, las cuentas existentes quedan sin acuerdo.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0059_saldo_informado_cuentas_bancarias')]
    operations = [
        migrations.AddField('cuentabancaria', 'descubierto_importe',
            models.DecimalField(blank=True, null=True, max_digits=14, decimal_places=2)),
        migrations.AddField('cuentabancaria', 'descubierto_vencimiento',
            models.DateField(blank=True, null=True)),
        migrations.AddField('cuentabancaria', 'descubierto_alerta_dias',
            models.PositiveSmallIntegerField(default=3)),
        migrations.AddField('cuentabancaria', 'descubierto_alerta_habilitada',
            models.BooleanField(default=False)),
        migrations.CreateModel('EventoAcuerdoDescubierto', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('antes', models.JSONField(default=dict)),
            ('despues', models.JSONField(default=dict)),
            ('creado', models.DateTimeField(auto_now_add=True)),
            ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                to='usuarios.identidadusuarioempresa')),
            ('cuenta_bancaria', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                related_name='eventos_descubierto', to='usuarios.cuentabancaria')),
            ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                to='usuarios.empresa')),
        ], options={'ordering': ['-creado', '-pk']}),
    ]
