"""Permisos operativos por Empresa y acción. El vínculo estructural no equivale a permiso."""
from django.conf import settings
from django.db import models


class PermisoAccesoColaborador(models.Model):
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.PROTECT, related_name='permisos_colaborador')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='permisos_modulos_empresa')
    codigo = models.CharField(max_length=64)
    activo = models.BooleanField(default=True)
    otorgado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='permisos_colaborador_otorgados')
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('empresa', 'usuario', 'codigo'), name='uniq_permiso_colab_emp_cod')]


class EventoPermisoAccesoColaborador(models.Model):
    empresa = models.ForeignKey('usuarios.Empresa', on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='historial_permisos_recibidos')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='historial_permisos_otorgados')
    codigo = models.CharField(max_length=64)
    activo = models.BooleanField()
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-creado', '-pk')
