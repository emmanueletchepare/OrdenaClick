"""Nómina por Empresa: legajos, documentos privados, actuaciones y licencia."""
from django.db import migrations, models
import django.db.models.deletion
import usuarios.models


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0048_echeq_cartera_estado_historial')]
    operations = [
        migrations.CreateModel(name='Empleado', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('cuil', models.CharField(max_length=11)),
            ('nombre_apellido', models.CharField(max_length=200)),
            ('fecha_nacimiento', models.DateField(blank=True, null=True)),
            ('legajo', models.CharField(max_length=30)),
            ('direccion', models.CharField(blank=True, max_length=250)),
            ('telefono_personal', models.CharField(blank=True, max_length=60)),
            ('mail_personal', models.EmailField(blank=True, max_length=254)),
            ('mail_laboral', models.EmailField(blank=True, max_length=254)),
            ('fecha_vencimiento_licencia', models.DateField(blank=True, null=True)),
            ('emergencia_nombre', models.CharField(blank=True, max_length=150)),
            ('emergencia_telefono', models.CharField(blank=True, max_length=60)),
            ('fecha_ingreso', models.DateField()),
            ('cbu', models.CharField(blank=True, max_length=22)),
            ('tipo_contratacion', models.CharField(choices=[('Completa','Jornada completa'),('Media','Media jornada')], default='Completa', max_length=10)),
            ('activo', models.BooleanField(default=True)),
            ('fecha_desvinculacion', models.DateField(blank=True, null=True)),
            ('motivo_desvinculacion', models.CharField(blank=True, max_length=300)),
            ('creado', models.DateTimeField(auto_now_add=True)),
            ('modificado', models.DateTimeField(auto_now=True)),
            ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='empleados', to='usuarios.empresa')),
            ('centro_operativo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='empleados', to='usuarios.centrooperativo')),
            ('vehiculo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='empleados_asignados', to='usuarios.recursooperativo')),
            ('banco', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='empleados', to='usuarios.banco')),
        ], options={'ordering':['nombre_apellido','pk'], 'constraints':[
            models.UniqueConstraint(fields=('empresa','cuil'),name='nomina_cuil_empresa_unico'),
            models.UniqueConstraint(fields=('empresa','legajo'),name='nomina_legajo_empresa_unico'),
        ]}),
        migrations.CreateModel(name='EventoEmpleado', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('accion', models.CharField(max_length=40)),
            ('detalle', models.CharField(blank=True, max_length=300)),
            ('creado', models.DateTimeField(auto_now_add=True)),
            ('actor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='usuarios.identidadusuarioempresa')),
            ('empleado', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='eventos',to='usuarios.empleado')),
        ], options={'ordering':['creado','pk']}),
        migrations.CreateModel(name='AlertaLicenciaEmpleado', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('fecha_vencimiento', models.DateField()),
            ('fecha_aviso', models.DateField()),
            ('reconocida_en', models.DateTimeField(blank=True, null=True)),
            ('cancelada_en', models.DateTimeField(blank=True, null=True)),
            ('creado', models.DateTimeField(auto_now_add=True)),
            ('modificado', models.DateTimeField(auto_now=True)),
            ('empleado',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,related_name='alerta_licencia',to='usuarios.empleado')),
        ]),
        migrations.CreateModel(name='CasoEmpleado', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('categoria', models.CharField(choices=[('Apercibimiento','Apercibimiento'),('Despido','Despido'),('BajaARCA','Baja ARCA'),('Aportes','Constancia de aportes'),('Juicio','Juicio / reclamo laboral'),('Otro','Otro')],max_length=25)),
            ('fecha',models.DateField()),('descripcion',models.TextField(max_length=3000)),
            ('estado',models.CharField(choices=[('Abierto','Abierto'),('Cerrado','Cerrado')],default='Abierto',max_length=10)),
            ('creado',models.DateTimeField(auto_now_add=True)),
            ('actor',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='usuarios.identidadusuarioempresa')),
            ('empleado',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='casos',to='usuarios.empleado')),
        ], options={'ordering':['-fecha','-pk']}),
        migrations.CreateModel(name='ActuacionCasoEmpleado',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('fecha',models.DateField()),('detalle',models.TextField(max_length=3000)),
            ('creado',models.DateTimeField(auto_now_add=True)),
            ('actor',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='usuarios.identidadusuarioempresa')),
            ('caso',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='actuaciones',to='usuarios.casoempleado')),
        ],options={'ordering':['fecha','creado','pk']}),
        migrations.CreateModel(name='DocumentoEmpleado',fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('tipo',models.CharField(choices=[('DNIFrente','DNI frente'),('DNIDorso','DNI dorso'),('Licencia','Licencia de conducir'),('CAT','Clave de Alta Temprana - CAT'),('Preocupacional','Preocupacional'),('Caso','Documento de caso')],max_length=20)),
            ('archivo',models.FileField(upload_to=usuarios.models.ruta_documento_nomina)),
            ('nombre_original',models.CharField(max_length=150)),('sha256',models.CharField(max_length=64)),
            ('creado',models.DateTimeField(auto_now_add=True)),
            ('actor',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='usuarios.identidadusuarioempresa')),
            ('caso',models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,related_name='documentos',to='usuarios.casoempleado')),
            ('empleado',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='documentos',to='usuarios.empleado')),
        ],options={'ordering':['-creado','-pk']}),
    ]
