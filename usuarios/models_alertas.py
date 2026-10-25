"""Configuración de avisos por Empresa/usuario, separada de permisos de acceso."""
from django.conf import settings
from django.db import models


class DestinatarioAlerta(models.Model):
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    codigo = models.CharField(max_length=12)
    activo = models.BooleanField(default=False)
    configurado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                                       related_name='destinatarios_alertas_configurados')
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['empresa', 'usuario', 'codigo'],
                                               name='uniq_alerta_destino_empresa_usuario_tipo')]


class PreferenciaSonidoAlerta(models.Model):
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    habilitado = models.BooleanField(default=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['empresa', 'usuario'],
                                               name='uniq_alerta_sonido_empresa_usuario')]


class EventoConfiguracionAlerta(models.Model):
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                               related_name='alertas_configuracion_recibida')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                             related_name='alertas_configuracion_realizada')
    codigo = models.CharField(max_length=12)  # FIN-01 / NOM-01 / SONIDO
    activo = models.BooleanField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-creado', '-pk')
