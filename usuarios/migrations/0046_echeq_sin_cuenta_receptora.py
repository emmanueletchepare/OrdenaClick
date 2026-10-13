"""e-Cheqs detectados no pertenecen a ninguna cuenta hasta depósito posterior.

Migración aditiva: preserva todos los registros y cuentas legadas. Depósitos y
transferencias continúan obligados a tener cuenta tanto por servicio como SQL.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0045_pendientes_globales_y_echeq')]
    operations = [
        migrations.AlterField(
            model_name='pendientebancario', name='cuenta_bancaria',
            field=models.ForeignKey(
                'usuarios.cuentabancaria', on_delete=django.db.models.deletion.PROTECT,
                null=True, blank=True, related_name='pendientes_aplicacion'),
        ),
        migrations.AddConstraint(
            model_name='pendientebancario',
            constraint=models.CheckConstraint(
                condition=models.Q(tipo='ECheq') | models.Q(cuenta_bancaria__isnull=False),
                name='pendiente_banco_cuenta_requerida',
            ),
        ),
    ]
