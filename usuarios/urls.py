from django.urls import path



from .http.administrador import panel_admin
from .http.empresa_legado import (
    exportar_empresa,
    eliminar_empresa,
    importar_empresa,
    confirmar_reemplazo,
)

from .http.auth import (
    login_view,
    registro_view,
    logout_view,
)

from .http.cuenta import (
    home,
    seleccionar_perfil,
    modificar_usuario,
    baja_usuario,
)

from .http.perfiles_basicos import (
    panel_colaborador,
    panel_contable,
    panel_legal,
)

from .http.desarrollador import (
    panel_desarrollador,
    reemplazar_secret_key_desarrollador,
    guardar_configuracion_arca_desarrollador,
)


from .http.relaciones import (
    gestionar_relaciones_empresa,
    panel_relaciones,
    resolver_solicitud,
)

from .http.caja import (
    panel_caja,
    nueva_cobranza,
)

from .http.empresa_claves import (
    listar_gestion_claves,
    guardar_gestion_clave,
    ver_gestion_clave,
    modificar_gestion_clave,
    eliminar_gestion_clave,
    reactivar_gestion_clave,
)

from .http.tipos_gasto import (
    listar_tipos_gasto,
    guardar_tipo_gasto,
    modificar_tipo_gasto,
    eliminar_tipo_gasto,
    reactivar_tipo_gasto,
)

from .http.clientes import (
    listar_clientes,
    autocompletar_cliente_arca,
    guardar_cliente,
    modificar_cliente,
    eliminar_cliente,
    reactivar_cliente,
)

from .http.proveedores import (
    listar_proveedores,
    guardar_proveedor,
    modificar_proveedor,
    eliminar_proveedor,
    reactivar_proveedor,
)

from .http.bancos import (
    guardar_banco,
    listar_bancos,
    modificar_banco,
    eliminar_banco,
)

from .http.cuentas_bancarias import (
    listar_cuentas_bancarias,
    guardar_cuenta_bancaria,
    modificar_cuenta_bancaria,
    eliminar_cuenta_bancaria,
    reactivar_cuenta_bancaria,
)

from .http.tarjetas import (
    listar_tarjetas,
    guardar_tarjeta,
    modificar_tarjeta,
    eliminar_tarjeta,
    reactivar_tarjeta,
)

from .http.retenciones import (
    listar_retenciones,
    guardar_retencion,
    modificar_retencion,
    eliminar_retencion,
    reactivar_retencion,
)

from .http.centros_operativos import (
    listar_centros_operativos,
    guardar_centro_operativo,
    modificar_centro_operativo,
    eliminar_centro_operativo,
)

from .http.recursos_operativos import (
    listar_recursos_operativos,
    guardar_recurso_operativo,
    modificar_recurso_operativo,
    eliminar_recurso_operativo,
    reactivar_recurso_operativo,
)

from .http.vencimientos_alertas import (
    estado_llamador_alertas,
    listar_proximos_vencimientos,
)

from .http.movimientos_consultas import (
    verificar_comprobante_duplicado,
    obtener_movimiento_edicion,
)

from .http.movimientos_pagos import (
    eliminar_pago_movimiento,
    registrar_pago_manual_movimiento,
    registrar_debito_automatico_movimiento,
)

from .http.movimientos import (
    guardar_movimiento,
    actualizar_movimiento,
)
from .http.empresa_backup import (
    cancelar_importacion_empresa,
    exportar_empresa_v1,
    importar_empresa_v1,
    importar_empresa_wizard,
)

from .http.documentos_privados import descargar_documento_empresa

urlpatterns = [
    path(
        "empresa/<int:empresa_id>/documentos/<str:campo>/",
        descargar_documento_empresa,
        name="descargar_documento_empresa",
    ),

    # =========================================
    # ACCESO / PERFILES
    # =========================================

    path(
        '',
        login_view,
        name='login'
    ),

    path(
        'registro/',
        registro_view,
        name='registro'
    ),

    path(
        'logout/',
        logout_view,
        name='logout'
    ),

    path(
        'home/',
        home,
        name='home'
    ),

    path(
        'perfil/<str:perfil>/',
        seleccionar_perfil,
        name='seleccionar_perfil'
    ),

    path(
        'relaciones/',
        panel_relaciones,
        name='panel_relaciones'
    ),

    path(
        'relaciones/solicitud/<int:solicitud_id>/<str:accion>/',
        resolver_solicitud,
        name='resolver_solicitud_relacion'
    ),

    path(
        'empresa/<int:empresa_id>/relaciones/',
        gestionar_relaciones_empresa,
        name='gestionar_relaciones_empresa'
    ),

    path(
        'usuario/modificar/',
        modificar_usuario,
        name='modificar_usuario'
    ),

    path(
        'usuario/baja/',
        baja_usuario,
        name='baja_usuario'
    ),

    path(
        'panel-admin/',
        panel_admin,
        name='panel_admin'
    ),

    path(
        'panel-colaborador/',
        panel_colaborador,
        name='panel_colaborador'
    ),

    path(
        'panel-contable/',
        panel_contable,
        name='panel_contable'
    ),

    path(
        'panel-legal/',
        panel_legal,
        name='panel_legal'
    ),

    path(
        'panel-desarrollador/',
        panel_desarrollador,
        name='panel_desarrollador'
    ),

    path(
        'panel-desarrollador/seguridad/reemplazar-secret-key/',
        reemplazar_secret_key_desarrollador,
        name='reemplazar_secret_key_desarrollador'
    ),

    path(
        "panel-desarrollador/arca/guardar/",
        guardar_configuracion_arca_desarrollador,
        name="guardar_configuracion_arca_desarrollador",
    ),

    path(
        'exportar-empresa/<int:empresa_id>/',
        exportar_empresa_v1,
        name='exportar_empresa'
    ),

    path(
        'eliminar-empresa/<int:empresa_id>/',
        eliminar_empresa,
        name='eliminar_empresa'
    ),

    path(
        'importar-empresa/',
        importar_empresa_v1,
        name='importar_empresa'
    ),

    path(
        'importar-empresa/wizard/<str:paso>/',
        importar_empresa_wizard,
        name='importar_empresa_wizard'
    ),

    path(
        'importar-empresa/cancelar/',
        cancelar_importacion_empresa,
        name='cancelar_importacion_empresa'
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

    # =========================================
    # CUENTAS BANCARIAS
    # =========================================

    path(
        "cuentas-bancarias/",
        listar_cuentas_bancarias,
        name="listar_cuentas_bancarias"
    ),

    path(
        "cuentas-bancarias/guardar/",
        guardar_cuenta_bancaria,
        name="guardar_cuenta_bancaria"
    ),

    path(
        "cuentas-bancarias/modificar/",
        modificar_cuenta_bancaria,
        name="modificar_cuenta_bancaria"
    ),

    path(
        "cuentas-bancarias/eliminar/",
        eliminar_cuenta_bancaria,
        name="eliminar_cuenta_bancaria"
    ),

    path(
        "cuentas-bancarias/reactivar/",
        reactivar_cuenta_bancaria,
        name="reactivar_cuenta_bancaria"
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

    # =========================================
    # TARJETAS
    # =========================================

    path(
        "tarjetas/",
        listar_tarjetas,
        name="listar_tarjetas"
    ),

    path(
        "tarjetas/guardar/",
        guardar_tarjeta,
        name="guardar_tarjeta"
    ),

    path(
        "tarjetas/modificar/",
        modificar_tarjeta,
        name="modificar_tarjeta"
    ),

    path(
        "tarjetas/eliminar/",
        eliminar_tarjeta,
        name="eliminar_tarjeta"
    ),

    path(
        "tarjetas/reactivar/",
        reactivar_tarjeta,
        name="reactivar_tarjeta"
    ),

    # =========================================
    # RETENCIONES
    # =========================================

    path(
        "retenciones/",
        listar_retenciones,
        name="listar_retenciones"
    ),

    path(
        "retenciones/guardar/",
        guardar_retencion,
        name="guardar_retencion"
    ),

    path(
        "retenciones/modificar/",
        modificar_retencion,
        name="modificar_retencion"
    ),

    path(
        "retenciones/eliminar/",
        eliminar_retencion,
        name="eliminar_retencion"
    ),

    path(
        "retenciones/reactivar/",
        reactivar_retencion,
        name="reactivar_retencion"
    ),

    # =========================================
    # RECURSOS OPERATIVOS
    # =========================================

    path(
        "recursos-operativos/",
        listar_recursos_operativos,
        name="listar_recursos_operativos"
    ),

    path(
        "recursos-operativos/guardar/",
        guardar_recurso_operativo,
        name="guardar_recurso_operativo"
    ),

    path(
        "recursos-operativos/modificar/",
        modificar_recurso_operativo,
        name="modificar_recurso_operativo"
    ),

    path(
        "recursos-operativos/eliminar/",
        eliminar_recurso_operativo,
        name="eliminar_recurso_operativo"
    ),

    path(
        "recursos-operativos/reactivar/",
        reactivar_recurso_operativo,
        name="reactivar_recurso_operativo"
    ),

    # =========================================
    # PROVEEDORES
    # =========================================

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
    # CLIENTES
    # =========================================

    path(
        "clientes/",
        listar_clientes,
        name="listar_clientes"
    ),

    path(
        "clientes/guardar/",
        guardar_cliente,
        name="guardar_cliente"
    ),

    path(
        "clientes/autocompletar-arca/",
        autocompletar_cliente_arca,
        name="autocompletar_cliente_arca"
    ),

    path(
        "clientes/modificar/",
        modificar_cliente,
        name="modificar_cliente"
    ),

    path(
        "clientes/eliminar/",
        eliminar_cliente,
        name="eliminar_cliente"
    ),

    path(
        "clientes/reactivar/",
        reactivar_cliente,
        name="reactivar_cliente"
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

    # =========================================
    # GESTIÓN DE CLAVES
    # =========================================

    path(
        "gestion-claves/",
        listar_gestion_claves,
        name="listar_gestion_claves"
    ),

    path(
        "gestion-claves/guardar/",
        guardar_gestion_clave,
        name="guardar_gestion_clave"
    ),

    path(
        "gestion-claves/ver/",
        ver_gestion_clave,
        name="ver_gestion_clave"
    ),

    path(
        "gestion-claves/modificar/",
        modificar_gestion_clave,
        name="modificar_gestion_clave"
    ),

    path(
        "gestion-claves/eliminar/",
        eliminar_gestion_clave,
        name="eliminar_gestion_clave"
    ),

    path(
        "gestion-claves/reactivar/",
        reactivar_gestion_clave,
        name="reactivar_gestion_clave"
    ),

    # =========================================
    # PRÓXIMOS VENCIMIENTOS / ALERTAS
    # =========================================

    path(
        "proximos-vencimientos/",
        listar_proximos_vencimientos,
        name="listar_proximos_vencimientos",
    ),

    path(
        "movimientos/edicion/",
        obtener_movimiento_edicion,
        name="obtener_movimiento_edicion",
    ),

    path(
        "movimientos/actualizar/",
        actualizar_movimiento,
        name="actualizar_movimiento",
    ),

    path(
        "movimientos/registrar-pago/",
        registrar_pago_manual_movimiento,
        name="registrar_pago_manual_movimiento",
    ),

    path(
        "movimientos/eliminar-pago/",
        eliminar_pago_movimiento,
        name="eliminar_pago_movimiento",
    ),

    path(
        "movimientos/registrar-debito-automatico/",
        registrar_debito_automatico_movimiento,
        name="registrar_debito_automatico_movimiento",
    ),

    path(
        "alertas/llamador/",
        estado_llamador_alertas,
        name="estado_llamador_alertas",
    ),


    # =========================================
    # CAJA / COBRANZAS
    # =========================================

    path(
        "caja/",
        panel_caja,
        name="panel_caja",
    ),

    path(
        "caja/cobranzas/nueva/",
        nueva_cobranza,
        name="nueva_cobranza",
    ),

    # =========================================
    # MOVIMIENTOS
    # =========================================

    path(
        "movimientos/verificar-comprobante/",
        verificar_comprobante_duplicado,
        name="verificar_comprobante_duplicado"
    ),

    path(
        "movimientos/guardar/",
        guardar_movimiento,
        name="guardar_movimiento"
    ),

]