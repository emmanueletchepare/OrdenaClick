from django.urls import path

from .views import (
    listar_bancos,
    panel_admin,
    exportar_empresa,
    eliminar_empresa,
    importar_empresa,
    confirmar_reemplazo,
    guardar_banco
  
)

urlpatterns = [

    path(
        '',
        panel_admin,
        name='panel_admin'
    ),

    path(
        'exportar-empresa/<int:empresa_id>/',
        exportar_empresa,
        name='exportar_empresa'
    ),

    path(
        'eliminar-empresa/<int:empresa_id>/',
        eliminar_empresa,
        name='eliminar_empresa'
    ),

    path(
        'importar-empresa/',
        importar_empresa,
        name='importar_empresa'
    ),

    path(
        "confirmar-reemplazo/",
        confirmar_reemplazo,
        name="confirmar_reemplazo"
    ),

    path(
        "guardar-banco/",
        guardar_banco,
        name="guardar_banco"
    ),

    path(
        "listar-bancos/",
        listar_bancos,
        name="listar_bancos"
    ),

]