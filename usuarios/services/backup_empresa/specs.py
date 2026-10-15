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
    ModelSpec("correcciones_movimientos_caja", models.CorreccionMovimientoCaja, "original__empresa"),
    ModelSpec("pendientes_bancarios", models.PendienteBancario, "empresa"),
    ModelSpec("eventos_pendientes_bancarios", models.EventoPendienteBancario, "pendiente__empresa"),
    ModelSpec("revisiones_pendientes_bancarios", models.RevisionPendienteBancario, "pendiente__empresa"),
    ModelSpec("estados_cartera_echeq", models.EventoEstadoECheq, "pendiente__empresa"),
    ModelSpec("cheques", models.Cheque, "empresa"),
    ModelSpec("vencimientos", models.Vencimiento, "empresa"),
    ModelSpec("alertas", models.Alerta, "vencimiento__empresa"),
    ModelSpec("empleados", models.Empleado, "empresa"),
    ModelSpec("eventos_empleados", models.EventoEmpleado, "empleado__empresa"),
    ModelSpec("alertas_licencia_empleados", models.AlertaLicenciaEmpleado, "empleado__empresa"),
    ModelSpec("casos_empleados", models.CasoEmpleado, "empleado__empresa"),
    ModelSpec("actuaciones_casos_empleados", models.ActuacionCasoEmpleado, "caso__empleado__empresa"),
    ModelSpec("documentos_empleados", models.DocumentoEmpleado, "empleado__empresa"),
)

SPEC_BY_KEY = {spec.key: spec for spec in MODEL_SPECS}
MODEL_TO_SPEC = {spec.model: spec for spec in MODEL_SPECS}

FORMAT_ID = "ordenaclick_empresa"
FORMAT_VERSION = 1

# Componentes adicionales de Caja 2: opcionales al leer un Backup v1 anterior.
OPTIONAL_NEW_KEYS = frozenset({"correcciones_movimientos_caja", "pendientes_bancarios", "eventos_pendientes_bancarios", "revisiones_pendientes_bancarios", "estados_cartera_echeq", "empleados", "eventos_empleados", "alertas_licencia_empleados", "casos_empleados", "actuaciones_casos_empleados", "documentos_empleados"})
