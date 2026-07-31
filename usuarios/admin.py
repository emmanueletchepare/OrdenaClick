from django.contrib import admin

from .models import (
    Empresa,
    Ejercicio,
    TipoGasto,
    TipoGastoProveedor,
    Movimiento,
    CentroOperativo,
    Banco,
    Proveedor,
)


admin.site.register(Empresa)
admin.site.register(Ejercicio)
admin.site.register(TipoGasto)
admin.site.register(TipoGastoProveedor)
admin.site.register(Movimiento)
admin.site.register(CentroOperativo)
admin.site.register(Banco)
admin.site.register(Proveedor)