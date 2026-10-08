from django.test import TestCase
from django.urls import reverse


class RutasPrivadasAnonimoTests(TestCase):
    """
    Inventario ejecutable de rutas privadas activas.

    Un usuario anónimo debe ser interceptado por autenticación antes de que
    cualquier endpoint llegue a lógica de Empresa, objetos hijos, secretos,
    archivos o mutaciones.
    """

    def test_todas_las_rutas_privadas_activas_requieren_login(self):
        casos = (
            ("GET", "logout", (), {}),
            ("GET", "home", (), {}),
            ("GET", "seleccionar_perfil", ("administrador",), {}),
            ("GET", "panel_relaciones", (), {}),
            ("POST", "resolver_solicitud_relacion", (1, "aceptar"), {}),
            ("GET", "gestionar_relaciones_empresa", (1,), {}),
            ("GET", "modificar_usuario", (), {}),
            ("POST", "baja_usuario", (), {}),
            ("GET", "panel_admin", (), {}),
            ("GET", "panel_colaborador", (), {}),
            ("GET", "panel_contable", (), {}),
            ("GET", "panel_legal", (), {}),
            ("GET", "panel_desarrollador", (), {}),
            ("POST", "reemplazar_secret_key_desarrollador", (), {}),
            ("POST", "guardar_configuracion_arca_desarrollador", (), {}),
            ("GET", "exportar_empresa", (1,), {}),
            ("POST", "eliminar_empresa", (1,), {}),
            ("POST", "importar_empresa", (), {}),
            ("GET", "importar_empresa_wizard", ("empresa",), {}),
            ("POST", "cancelar_importacion_empresa", (), {}),
            ("POST", "guardar_banco", (), {}),
            ("GET", "listar_bancos", (), {}),
            ("POST", "modificar_banco", (), {}),
            ("POST", "eliminar_banco", (), {}),
            ("GET", "listar_cuentas_bancarias", (), {}),
            ("POST", "guardar_cuenta_bancaria", (), {}),
            ("POST", "modificar_cuenta_bancaria", (), {}),
            ("POST", "eliminar_cuenta_bancaria", (), {}),
            ("POST", "reactivar_cuenta_bancaria", (), {}),
            ("POST", "guardar_centro_operativo", (), {}),
            ("GET", "listar_centros_operativos", (), {}),
            ("POST", "modificar_centro_operativo", (), {}),
            ("POST", "eliminar_centro_operativo", (), {}),
            ("GET", "listar_tarjetas", (), {}),
            ("POST", "guardar_tarjeta", (), {}),
            ("POST", "modificar_tarjeta", (), {}),
            ("POST", "eliminar_tarjeta", (), {}),
            ("POST", "reactivar_tarjeta", (), {}),
            ("GET", "listar_retenciones", (), {}),
            ("POST", "guardar_retencion", (), {}),
            ("POST", "modificar_retencion", (), {}),
            ("POST", "eliminar_retencion", (), {}),
            ("POST", "reactivar_retencion", (), {}),
            ("GET", "listar_recursos_operativos", (), {}),
            ("POST", "guardar_recurso_operativo", (), {}),
            ("POST", "modificar_recurso_operativo", (), {}),
            ("POST", "eliminar_recurso_operativo", (), {}),
            ("POST", "reactivar_recurso_operativo", (), {}),
            ("GET", "listar_proveedores", (), {}),
            ("POST", "guardar_proveedor", (), {}),
            ("POST", "modificar_proveedor", (), {}),
            ("POST", "eliminar_proveedor", (), {}),
            ("POST", "reactivar_proveedor", (), {}),
            ("GET", "listar_clientes", (), {}),
            ("POST", "guardar_cliente", (), {}),
            ("GET", "autocompletar_cliente_arca", (), {}),
            ("POST", "modificar_cliente", (), {}),
            ("POST", "eliminar_cliente", (), {}),
            ("POST", "reactivar_cliente", (), {}),
            ("GET", "listar_tipos_gasto", (), {}),
            ("POST", "guardar_tipo_gasto", (), {}),
            ("POST", "modificar_tipo_gasto", (), {}),
            ("POST", "eliminar_tipo_gasto", (), {}),
            ("POST", "reactivar_tipo_gasto", (), {}),
            ("GET", "listar_gestion_claves", (), {}),
            ("POST", "guardar_gestion_clave", (), {}),
            ("GET", "ver_gestion_clave", (), {}),
            ("POST", "modificar_gestion_clave", (), {}),
            ("POST", "eliminar_gestion_clave", (), {}),
            ("POST", "reactivar_gestion_clave", (), {}),
            ("GET", "listar_proximos_vencimientos", (), {}),
            ("GET", "obtener_movimiento_edicion", (), {}),
            ("POST", "actualizar_movimiento", (), {}),
            ("POST", "registrar_pago_manual_movimiento", (), {}),
            ("POST", "eliminar_pago_movimiento", (), {}),
            ("POST", "registrar_debito_automatico_movimiento", (), {}),
            ("GET", "estado_llamador_alertas", (), {}),
            ("GET", "panel_caja", (), {}),
            ("POST", "nueva_cobranza", (), {}),
            ("GET", "verificar_comprobante_duplicado", (), {}),
            ("POST", "guardar_movimiento", (), {}),
        )

        for metodo, nombre_url, args, data in casos:
            with self.subTest(metodo=metodo, url=nombre_url):
                url = reverse(nombre_url, args=args)

                if metodo == "POST":
                    respuesta = self.client.post(url, data)
                else:
                    respuesta = self.client.get(url, data)

                self.assertEqual(
                    respuesta.status_code,
                    302,
                    msg=(
                        f"{nombre_url} no interceptó al usuario anónimo "
                        f"antes de ejecutar la ruta privada."
                    ),
                )
                self.assertIn(
                    reverse("login"),
                    respuesta["Location"],
                )
