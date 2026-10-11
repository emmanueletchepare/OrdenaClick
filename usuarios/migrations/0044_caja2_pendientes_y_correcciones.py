from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0043_idempotencia_movimiento_caja'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='CorreccionMovimientoCaja', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('clave', models.UUIDField(unique=True)),
            ('accion', models.CharField(choices=[('Editar', 'Editar'), ('Anular', 'Anular')], max_length=10)),
            ('motivo', models.CharField(max_length=300)),
            ('huella', models.CharField(max_length=64)),
            ('creado', models.DateTimeField(auto_now_add=True)),
            ('original', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='correccion_operativa', to='usuarios.movimientocaja')),
            ('contraasiento', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='contraasiento_de', to='usuarios.movimientocaja')),
            ('reemplazo', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='reemplazo_de', to='usuarios.movimientocaja')),
            ('creado_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.identidadusuarioempresa')),
        ]),
        migrations.CreateModel(name='PermisoPendienteBancarioCentro', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('activo', models.BooleanField(default=True)),
            ('actualizado', models.DateTimeField(auto_now=True)),
            ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permisos_pendientes_bancarios', to='usuarios.empresa')),
            ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permisos_pendientes_bancarios', to=settings.AUTH_USER_MODEL)),
            ('centro_operativo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permisos_pendientes_bancarios', to='usuarios.centrooperativo')),
            ('otorgado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='usuarios.identidadusuarioempresa')),
        ], options={'constraints': [models.UniqueConstraint(fields=('empresa', 'usuario', 'centro_operativo'), name='uniq_permiso_pendiente_centro')]}),
        migrations.CreateModel(name='EventoPermisoBancario', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('concedido', models.BooleanField()),
            ('creado', models.DateTimeField(auto_now_add=True)),
            ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarios.empresa')),
            ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ('centro_operativo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='usuarios.centrooperativo')),
            ('actor', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, to='usuarios.identidadusuarioempresa')),
        ]),
        migrations.CreateModel(name='PendienteBancario', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('clave', models.UUIDField(unique=True)),
            ('fecha', models.DateField()),
            ('tipo', models.CharField(choices=[('Transferencia', 'Transferencia recibida'), ('Deposito', 'Depósito recibido'), ('ECheq', 'e-Cheq detectado')], max_length=20)),
            ('importe', models.DecimalField(decimal_places=2, max_digits=14)),
            ('referencia', models.CharField(max_length=200)),
            ('observaciones', models.CharField(blank=True, max_length=300)),
            ('estado', models.CharField(choices=[('Pendiente', 'Pendiente'), ('Resuelto', 'Resuelto')], default='Pendiente', max_length=12)),
            ('resuelto_en', models.DateTimeField(blank=True, null=True)),
            ('tipo_resolucion', models.CharField(blank=True, max_length=20)),
            ('referencia_resolucion', models.CharField(blank=True, max_length=200)),
            ('creado', models.DateTimeField(auto_now_add=True)),
            ('modificado', models.DateTimeField(auto_now=True)),
            ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pendientes_bancarios', to='usuarios.empresa')),
            ('cuenta_bancaria', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pendientes_aplicacion', to='usuarios.cuentabancaria')),
            ('centro_operativo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pendientes_bancarios', to='usuarios.centrooperativo')),
            ('creado_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='pendientes_creados', to='usuarios.identidadusuarioempresa')),
            ('resuelto_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='pendientes_resueltos', to='usuarios.identidadusuarioempresa')),
        ], options={'ordering': ['-fecha', '-creado', '-pk'], 'constraints': [models.CheckConstraint(condition=models.Q(importe__gt=0), name='pendiente_bancario_importe_positivo')]}),
        migrations.CreateModel(name='EventoPendienteBancario', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('accion', models.CharField(max_length=30)),
            ('detalle', models.CharField(blank=True, max_length=300)),
            ('creado', models.DateTimeField(auto_now_add=True)),
            ('pendiente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='eventos', to='usuarios.pendientebancario')),
            ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='usuarios.identidadusuarioempresa')),
        ]),
    ]
