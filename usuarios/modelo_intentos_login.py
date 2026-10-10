from django.db import models


class IntentoLoginOrigen(models.Model):
    """Contador temporal por origen; almacena un digest, nunca la IP en claro."""

    origen = models.CharField(max_length=64, unique=True)
    inicio_ventana = models.DateTimeField()
    fallos = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Intentos de acceso por origen'
