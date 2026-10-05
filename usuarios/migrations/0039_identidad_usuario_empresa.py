import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def crear_identidades_historicas(apps, schema_editor):
    Identidad = apps.get_model("usuarios", "IdentidadUsuarioEmpresa")
    Cobranza = apps.get_model("usuarios", "Cobranza")
    MovimientoCaja = apps.get_model("usuarios", "MovimientoCaja")
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    Usuario = apps.get_model(app_label, model_name)

    pares = set(
        Cobranza.objects.values_list("empresa_id", "creado_por_id")
    )
    pares.update(
        MovimientoCaja.objects.values_list("empresa_id", "creado_por_id")
    )

    mapa = {}

    for empresa_id, usuario_id in pares:
        if not empresa_id or not usuario_id:
            continue

        usuario = Usuario.objects.get(pk=usuario_id)
        nombre_completo = " ".join(
            parte
            for parte in [
                getattr(usuario, "first_name", ""),
                getattr(usuario, "last_name", ""),
            ]
            if parte
        ).strip()

        identidad, _ = Identidad.objects.get_or_create(
            empresa_id=empresa_id,
            usuario_id=usuario_id,
            defaults={
                "username_historico": getattr(usuario, "username", str(usuario_id)),
                "nombre_historico": nombre_completo,
                "email_historico": getattr(usuario, "email", "") or "",
            },
        )
        mapa[(empresa_id, usuario_id)] = identidad.id

    for cobranza in Cobranza.objects.all().iterator():
        cobranza.creado_por_identidad_id = mapa[
            (cobranza.empresa_id, cobranza.creado_por_id)
        ]
        cobranza.save(update_fields=["creado_por_identidad"])

    for movimiento in MovimientoCaja.objects.all().iterator():
        movimiento.creado_por_identidad_id = mapa[
            (movimiento.empresa_id, movimiento.creado_por_id)
        ]
        movimiento.save(update_fields=["creado_por_identidad"])


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0038_asignacionusuarioempresa_centro_operativo_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IdentidadUsuarioEmpresa",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                    ),
                ),
                ("username_historico", models.CharField(max_length=150)),
                ("nombre_historico", models.CharField(blank=True, max_length=300)),
                ("email_historico", models.EmailField(blank=True, max_length=254)),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="identidades_usuarios",
                        to="usuarios.empresa",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="identidades_empresas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["username_historico"],
            },
        ),
        migrations.AddConstraint(
            model_name="identidadusuarioempresa",
            constraint=models.UniqueConstraint(
                condition=models.Q(usuario__isnull=False),
                fields=("empresa", "usuario"),
                name="uniq_identidad_usuario_empresa_vinculado",
            ),
        ),
        migrations.AddField(
            model_name="cobranza",
            name="creado_por_identidad",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cobranzas_creadas",
                to="usuarios.identidadusuarioempresa",
            ),
        ),
        migrations.AddField(
            model_name="movimientocaja",
            name="creado_por_identidad",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="movimientos_caja_creados",
                to="usuarios.identidadusuarioempresa",
            ),
        ),
        migrations.RunPython(
            crear_identidades_historicas,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="cobranza",
            name="creado_por",
        ),
        migrations.RemoveField(
            model_name="movimientocaja",
            name="creado_por",
        ),
        migrations.RenameField(
            model_name="cobranza",
            old_name="creado_por_identidad",
            new_name="creado_por",
        ),
        migrations.RenameField(
            model_name="movimientocaja",
            old_name="creado_por_identidad",
            new_name="creado_por",
        ),
        migrations.AlterField(
            model_name="cobranza",
            name="creado_por",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cobranzas_creadas",
                to="usuarios.identidadusuarioempresa",
            ),
        ),
        migrations.AlterField(
            model_name="movimientocaja",
            name="creado_por",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="movimientos_caja_creados",
                to="usuarios.identidadusuarioempresa",
            ),
        ),
    ]
