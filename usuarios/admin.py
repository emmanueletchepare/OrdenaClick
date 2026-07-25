from django.contrib import admin

from .models import (
    Empresa,
    Ejercicio,
    Rubro,
    Subrubro,
    Movimiento,
    CentroOperativo,
    Banco,
    Proveedor,
)

admin.site.register(Empresa)
admin.site.register(Ejercicio)
admin.site.register(Rubro)
admin.site.register(Subrubro)
admin.site.register(Movimiento)
admin.site.register(CentroOperativo)
admin.site.register(Banco)
admin.site.register(Proveedor)