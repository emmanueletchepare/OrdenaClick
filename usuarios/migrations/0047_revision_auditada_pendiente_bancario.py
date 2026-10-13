"""Registro inmutable de ediciones de pendientes e incidencias sobre resueltos."""
import uuid
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('usuarios','0046_echeq_sin_cuenta_receptora')]
    operations = [migrations.CreateModel(
        name='RevisionPendienteBancario', fields=[
            ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
            ('clave',models.UUIDField(unique=True)),
            ('tipo',models.CharField(max_length=24,choices=[('Editado','Edición auditada'),('Incidencia','Error informado')])),
            ('estado',models.CharField(max_length=16,default='Aplicado')),
            ('motivo',models.CharField(max_length=300)),
            ('anterior',models.JSONField(default=dict)),
            ('nuevo',models.JSONField(default=dict)),
            ('contenido',models.JSONField(default=dict)),
            ('creado',models.DateTimeField(auto_now_add=True)),
            ('actor',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='usuarios.identidadusuarioempresa')),
            ('pendiente',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name='revisiones',to='usuarios.pendientebancario')),
        ], options={'ordering':['-creado','-pk']},
    )]
