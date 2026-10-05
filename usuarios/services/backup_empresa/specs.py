from dataclasses import dataclass

from usuarios import models


@dataclass(frozen=True)
class ModelSpec:
    key: str
    model: type
    company_lookup: str
    restore: bool = True
    exclude_fields: tuple[str, ...] = ()


# El orden también es el orden de restauración. Las dependencias deben existir antes.
MODEL_SPECS = (
    ModelSpec("ejercicios", models.Ejercicio, "empresa"),
    ModelSpec("tipos_gasto", models.TipoGasto, "empresa"),
    ModelSpec("proveedores", models.Proveedor, "empresa"),
    ModelSpec("tipos_gasto_proveedores", models.TipoGastoProveedor, "tipo_gasto__empresa"),
    ModelSpec("centros_operativos", models.CentroOperativo, "empresa"),
    ModelSpec("recursos_operativos", models.RecursoOperativo, "empresa"),
    ModelSpec("recursos_centros", models.RecursoOperativoCentro, "recurso_operativo__empresa"),
    ModelSpec("clientes", models.Cliente, "empresa"),
    ModelSpec("bancos", models.Banco, "empresa"),
    ModelSpec("cuentas_bancarias", models.CuentaBancaria, "empresa"),
    ModelSpec("tarjetas", models.Tarjeta, "empresa"),
    ModelSpec("retenciones", models.Retencion, "empresa"),
    ModelSpec("cajas", models.Caja, "empresa"),
    ModelSpec(
        "identidades_usuarios",
        models.IdentidadUsuarioEmpresa,
        "empresa",
        exclude_fields=("usuario",),
    ),
    ModelSpec(
        "gestion_claves",
        models.GestionClave,
        "empresa",
        exclude_fields=("contrasena_cifrada",),
    ),
    ModelSpec("movimientos", models.Movimiento, "empresa"),
    ModelSpec("pagos", models.Pago, "empresa"),
    ModelSpec("planes_pago", models.PlanPago, "movimiento__empresa"),
    ModelSpec("cuotas_plan", models.CuotaPlan, "plan__movimiento__empresa"),
    ModelSpec("aplicaciones_pago", models.AplicacionPago, "pago__empresa"),
    ModelSpec("operaciones_bancarias_pago", models.OperacionBancariaPago, "pago__empresa"),
    ModelSpec("debitos_automaticos_pago", models.DebitoAutomaticoPago, "pago__empresa"),
    ModelSpec("tarjetas_pago", models.TarjetaPago, "pago__empresa"),
    ModelSpec("retenciones_pago", models.RetencionPago, "pago__empresa"),
    ModelSpec("cobranzas", models.Cobranza, "empresa"),
    ModelSpec("movimientos_caja", models.MovimientoCaja, "empresa"),
    ModelSpec("cheques", models.Cheque, "empresa"),
    ModelSpec("vencimientos", models.Vencimiento, "empresa"),
    ModelSpec("alertas", models.Alerta, "vencimiento__empresa"),
)

SPEC_BY_KEY = {spec.key: spec for spec in MODEL_SPECS}
MODEL_TO_SPEC = {spec.model: spec for spec in MODEL_SPECS}

FORMAT_ID = "ordenaclick_empresa"
FORMAT_VERSION = 1
