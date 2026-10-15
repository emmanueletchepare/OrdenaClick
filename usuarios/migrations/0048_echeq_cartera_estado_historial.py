"""Estado operativo separado de la aplicación y hechos inmutables de e-Cheqs."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0047_revision_auditada_pendiente_bancario')]
    operations = [
        migrations.AddField(
            model_name='pendientebancario', name='estado_cartera',
            field=models.CharField(max_length=16, default='EnCartera', choices=[
                ('EnCartera', 'En cartera'), ('Rechazado', 'Rechazado'),
                ('Devuelto', 'Devuelto'), ('Vencido', 'Vencido'),
            ])),
        migrations.CreateModel(
            name='EventoEstadoECheq',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.UUIDField(unique=True)),
                ('estado_anterior', models.CharField(max_length=16)),
                ('estado_nuevo', models.CharField(max_length=16)),
                ('fecha', models.DateField()),
                ('observaciones', models.CharField(blank=True, max_length=300)),
                ('creado', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.identidadusuarioempresa')),
                ('pendiente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                    related_name='estados_cartera', to='usuarios.pendientebancario')),
            ], options={'ordering': ['creado', 'pk']},
        ),
    ]
