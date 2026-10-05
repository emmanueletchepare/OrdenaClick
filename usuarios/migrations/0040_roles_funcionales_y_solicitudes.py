from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0039_identidad_usuario_empresa"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RolFuncionalUsuarioEmpresa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rol", models.CharField(choices=[("contable", "Contable"), ("legal", "Legal")], max_length=20)),
                ("activo", models.BooleanField(default=True)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="roles_funcionales_usuarios", to="usuarios.empresa")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="roles_funcionales_empresas", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["usuario__username", "rol"]},
        ),
        migrations.AddConstraint(
            model_name="rolfuncionalusuarioempresa",
            constraint=models.UniqueConstraint(fields=("empresa", "usuario", "rol"), name="uniq_rol_funcional_usuario_empresa"),
        ),
        migrations.CreateModel(
            name="SolicitudRelacionEmpresa",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rol", models.CharField(choices=[("admin_general", "Administrador general"), ("admin_centro", "Administrador"), ("colaborador", "Colaborador"), ("contable", "Contable"), ("legal", "Legal")], max_length=20)),
                ("estado", models.CharField(choices=[("pendiente", "Pendiente"), ("aceptada", "Aceptada"), ("rechazada", "Rechazada"), ("cancelada", "Cancelada")], default="pendiente", max_length=20)),
                ("mensaje", models.CharField(blank=True, max_length=500)),
                ("creada", models.DateTimeField(auto_now_add=True)),
                ("actualizada", models.DateTimeField(auto_now=True)),
                ("resuelta", models.DateTimeField(blank=True, null=True)),
                ("centro_operativo", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="solicitudes_relaciones", to="usuarios.centrooperativo")),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="solicitudes_relaciones", to="usuarios.empresa")),
                ("solicitada_por", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="solicitudes_relaciones_enviadas", to=settings.AUTH_USER_MODEL)),
                ("usuario_destino", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="solicitudes_relaciones_recibidas", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-creada"]},
        ),
        migrations.AddConstraint(
            model_name="solicitudrelacionempresa",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("centro_operativo__isnull", False), ("rol", "admin_centro")), models.Q(("centro_operativo__isnull", True), ("rol__in", ["admin_general", "colaborador", "contable", "legal"])), _connector="OR"), name="solicitud_rol_centro_coherente"),
        ),
        migrations.AddConstraint(
            model_name="solicitudrelacionempresa",
            constraint=models.UniqueConstraint(condition=models.Q(("centro_operativo__isnull", True), ("estado", "pendiente")), fields=("empresa", "usuario_destino", "rol"), name="uniq_solicitud_pendiente_sin_centro"),
        ),
        migrations.AddConstraint(
            model_name="solicitudrelacionempresa",
            constraint=models.UniqueConstraint(condition=models.Q(("centro_operativo__isnull", False), ("estado", "pendiente")), fields=("empresa", "usuario_destino", "rol", "centro_operativo"), name="uniq_solicitud_pendiente_con_centro"),
        ),
    ]
