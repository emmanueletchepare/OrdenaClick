from django.urls import path

from .views import (
    listar_bancos,
    listar_centros_operativos,
    panel_admin,
    exportar_empresa,
    eliminar_empresa,
    importar_empresa,
    confirmar_reemplazo,
    guardar_banco,
    guardar_centro_operativo,
    modificar_banco,
    eliminar_banco,
    modificar_centro_operativo,
    eliminar_centro_operativo,
    listar_proveedores,
    guardar_proveedor,
    modificar_proveedor,
    eliminar_proveedor,
    reactivar_proveedor,
    listar_tipos_gasto,
    guardar_tipo_gasto,
    modificar_tipo_gasto,
    eliminar_tipo_gasto,
    reactivar_tipo_gasto
    
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

    path(
        "modificar-banco/",
        modificar_banco,
        name="modificar_banco"
        ),

    path(
        "eliminar-banco/",
        eliminar_banco,
        name="eliminar_banco"
    ),

    path(
        "guardar-centro-operativo/",
        guardar_centro_operativo,
        name="guardar_centro_operativo"
    ),

    path(
        "listar-centros-operativos/",
        listar_centros_operativos,
        name="listar_centros_operativos"
    ),

    path(
        "modificar-centro-operativo/",
        modificar_centro_operativo,
        name="modificar_centro_operativo"
    ),

    path(
        "eliminar-centro-operativo/",
        eliminar_centro_operativo,
        name="eliminar_centro_operativo"
    ),

        path(
        "listar-proveedores/",
        listar_proveedores,
        name="listar_proveedores"
    ),

    path(
        "guardar-proveedor/",
        guardar_proveedor,
        name="guardar_proveedor"
    ),

    path(
        "modificar-proveedor/",
        modificar_proveedor,
        name="modificar_proveedor"
    ),

    path(
        "eliminar-proveedor/",
        eliminar_proveedor,
        name="eliminar_proveedor"
    ),

    path(
        "reactivar-proveedor/",
        reactivar_proveedor,
        name="reactivar_proveedor"
    ),

    # =========================================
    # TIPOS DE GASTO
    # =========================================

    path(
        "tipos-gasto/",
        listar_tipos_gasto,
        name="listar_tipos_gasto"
    ),

    path(
     "tipos-gasto/guardar/",
     guardar_tipo_gasto,
     name="guardar_tipo_gasto"
    ),

    path(
     "tipos-gasto/modificar/",
     modificar_tipo_gasto,
     name="modificar_tipo_gasto"
    ),

    path(
     "tipos-gasto/eliminar/",
        eliminar_tipo_gasto,
        name="eliminar_tipo_gasto"
    ),

    path(
     "tipos-gasto/reactivar/",
     reactivar_tipo_gasto,
     name="reactivar_tipo_gasto"
    ),

]