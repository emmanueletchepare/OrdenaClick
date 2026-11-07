from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0058_acta_asamblea_designacion')]

    operations = [
        migrations.CreateModel(
            name='SaldoInformadoCuentaBancaria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('importe', models.DecimalField(decimal_places=2, max_digits=14)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('clave', models.UUIDField()),
                ('cuenta_bancaria', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='posiciones_informadas', to='usuarios.cuentabancaria')),
                ('creado_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='posiciones_bancarias_informadas', to='usuarios.identidadusuarioempresa')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='saldos_bancarios_informados', to='usuarios.empresa')),
            ],
            options={'ordering': ['-creado', '-pk']},
        ),
        migrations.AddConstraint(
            model_name='saldoinformadocuentabancaria',
            constraint=models.UniqueConstraint(fields=('empresa', 'cuenta_bancaria', 'clave'), name='uniq_posicion_banco_cuenta_clave'),
        ),
    ]
