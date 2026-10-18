from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('usuarios','0052_permisos_accesos_colaborador'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.AddField(model_name='gestionclave',name='creado_por',
            field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.PROTECT,
                related_name='claves_creadas',to=settings.AUTH_USER_MODEL)),
    ]
