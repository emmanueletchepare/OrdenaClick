from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0040_roles_funcionales_y_solicitudes')]

    operations = [
        migrations.CreateModel(
            name='IntentoLoginOrigen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('origen', models.CharField(max_length=64, unique=True)),
                ('inicio_ventana', models.DateTimeField()),
                ('fallos', models.PositiveIntegerField(default=0)),
            ],
            options={'verbose_name': 'Intentos de acceso por origen'},
        ),
    ]
