# ARQUITECTURA.md — Cómo está construido OrdenaClick

## 1. Principio rector
OrdenaClick usa una arquitectura común y escalable. Las diferencias entre planes, perfiles o complejidad operativa se resuelven mediante permisos, capacidades, configuración y visibilidad; no mediante bases incompatibles.

## 2. Separación de responsabilidades
La aplicación debe evolucionar evitando archivos monolíticos:
- Las vistas coordinan HTTP, permisos, formularios y respuestas.
- Las reglas de negocio reutilizables viven en servicios.
- La lógica financiera central no se duplica entre pantallas.
- JavaScript nuevo debe ir a archivos estáticos.
- CSS nuevo debe ir a archivos estáticos.
- Templates deben concentrarse en estructura/presentación y no convertirse en depósitos de reglas de negocio.

Al tocar código viejo, se debe aprovechar para extraer progresivamente JS/CSS inline y responsabilidades excesivas, sin iniciar refactors masivos que desvíen la Beta.

## 3. Núcleo financiero
Estructura conceptual:

```text
EMPRESA
└── EJERCICIO
    └── MOVIMIENTO
        ├── PAGOS
        │   └── APLICACIONES DE PAGO
        ├── PLAN DE PAGOS
        │   └── CUOTAS
        └── VENCIMIENTOS
            └── ALERTAS
```

Movimiento = hecho económico/documental.  
Pago = hecho financiero.  
AplicaciónPago = cuánto de un Pago cancela un Movimiento o una Cuota.  
Vencimiento = obligación/compromiso financiero abierto.  
Alerta = aviso asociado; nunca reemplaza al Vencimiento como fuente de verdad.

## 4. Saldo
La fuente común debe calcular el saldo sobre aplicaciones efectivas:

```text
saldo_pendiente = Movimiento.total - SUM(AplicacionPago.importe)
```

Los costos financieros (intereses de tarjeta, mora, punitorios u otros) se conservan diferenciados y no incrementan artificialmente el importe aplicado al Movimiento.

### Regla de aplicación máxima

El importe aplicado directamente a un Movimiento nunca puede superar su saldo pendiente actual.

```text
0 <= nueva_aplicacion <= saldo_pendiente
```

Por lo tanto:

- aplicación `0`: el Movimiento conserva su saldo;
- aplicación menor al saldo: Pago parcial;
- aplicación igual al saldo: cancelación total;
- aplicación mayor al saldo: no permitida dentro de Comprobantes, Carga Planificada ni edición directa del Movimiento.

Cuando el Movimiento ya posee Pagos históricos, la validación se realiza contra el saldo pendiente actual, no contra el total original del documento. Los Pagos históricos no se reescriben silenciosamente durante una edición.

Un Pago como hecho financiero sí puede ser mayor que el saldo de un Movimiento determinado. Ese caso pertenece al circuito **Registrar Pago**, que deberá permitir distribuir un mismo Pago entre varios Movimientos y, cuando corresponda, conservar un remanente a cuenta.

La excepción definida es el Débito automático con intereses/costos por mora confirmados: el importe real debitado puede superar el saldo, pero el importe aplicado al Movimiento no. La diferencia se registra separadamente como costo financiero.

La validación definitiva pertenece al backend y debe centralizarse en servicios reutilizables. El frontend puede anticipar el error para mejorar UX, pero no es autoridad.

## 5. Movimiento y Pago son independientes
Un Movimiento puede existir sin pago, con pago parcial, total, múltiples pagos o convertirse en Plan después de pagos previos. Un Pago puede combinar medios de cancelación.

Medios previstos: efectivo, transferencias/depósitos, tarjetas, cheques/e-Cheqs, retenciones y otros futuros.

## 6. Comprobantes y Obligaciones

No todos los Movimientos económicos se originan en una factura.

La interfaz separa conceptualmente dos circuitos de registración:

```text
REGISTROS
├── Comprobantes
└── Obligaciones
```

### Comprobantes

Corresponde al circuito actualmente implementado como Carga Simple.

Está destinado a facturas y otros comprobantes para los cuales tienen sentido datos como:

- Proveedor.
- Tipo de comprobante.
- Punto de venta.
- Número de comprobante.
- Tipo de gasto.
- Centro Operativo.
- Recurso Operativo, cuando corresponda.
- Importe.
- Vencimiento.
- Forma de pago.

### Obligaciones / Liquidaciones

Está destinado a compromisos económicos que no deben forzarse dentro de la estructura documental de una factura.

Casos iniciales previstos:

- Sueldos.
- Aportes y contribuciones.
- VEP / impuestos.
- Tasas y otros.

Datos conceptuales iniciales:

- Concepto.
- Organismo / beneficiario.
- Período.
- Referencia.
- Centro Operativo, cuando corresponda.
- Importe.
- Vencimiento.
- Forma de pago.

La existencia de circuitos de carga distintos no implica crear núcleos financieros paralelos.

Comprobantes y Obligaciones deben utilizar, cuando corresponda, la arquitectura común de Movimiento, Pago, AplicaciónPago, Vencimiento y Alerta.

La estructura definitiva de datos de Obligaciones debe definirse antes de implementarla.

## 7. Vencimientos y Alertas
Todo evento económicamente relevante con fecha futura debe evaluarse como fuente de Vencimiento. Movimiento impago, cuotas, cheques propios, débito automático y futuras obligaciones alimentan una fuente común.

El paso del tiempo no borra una obligación: pasa de próxima a vencer a vence hoy o vencida y sigue visible mientras exista saldo pendiente.

La campanita, Próximos Vencimientos, futuras notificaciones móviles y otros llamadores deben consumir la misma fuente de verdad.

## 8. Planes de Pago
Convertir a Plan trabaja sobre el saldo restante. El Movimiento original conserva su historia. La obligación previa reemplazada deja de estar abierta y las cuotas del Plan generan nuevas obligaciones independientes.

## 9. Histórico
Centro Operativo y Recurso Operativo utilizados en un Movimiento se conservan históricamente. Si el recurso cambia de centro después, el Movimiento no cambia retroactivamente.

## 10. Moneda
La Beta opera en ARS. El modelo debe quedar preparado para identificar moneda. Cuentas incompatibles (por ejemplo USD para un Movimiento ARS) no deben habilitarse como medio de pago durante la Beta. Multimoneda, conversión y tipo de cambio son posteriores.

## 11. Reportes y contabilidad futura
Se persisten componentes fiscales y financieros discriminados, no solamente totales. Esto debe permitir filtros por Empresa, Ejercicio, Proveedor, Tipo de Gasto, Centro, Recurso, fechas, estado, componentes fiscales, pagos y dimensiones futuras.

## 12. Exportar / Importar Empresa
La exportación debe ser una copia completa y portable del entorno Empresa. Si un dato se perdería al eliminar y reimportar, debe formar parte del backup salvo exclusión explícita documentada.

Debe incluir versión de formato y reconstruir relaciones mediante mapas de identificadores, sin asumir que los IDs originales se conservan.

Incluye, según existan: Empresa, configuración, documentación societaria, ejercicios, centros, recursos, bancos, cuentas bancarias, proveedores, tipos de gasto y relaciones, movimientos, archivos, pagos, aplicaciones, tarjetas, cheques/e-Cheqs, retenciones, planes, cuotas, vencimientos, alertas y futuras órdenes de pago.

Nunca exportar SECRET_KEY, claves maestras, variables de entorno, credenciales de infraestructura ni contraseñas en texto plano. La clave de cifrado no viaja dentro del backup.

## 13. Seguridad de arquitectura
Cada endpoint debe validar usuario, empresa activa, rol/permisos y pertenencia de los objetos manipulados. No confiar en IDs enviados por frontend. Operaciones compuestas deben usar transacciones cuando corresponda. La información sensible debe protegerse en tránsito, reposo y backup según su naturaleza.

## 14. Auditoría
Las operaciones relevantes deben quedar preparadas para trazabilidad: usuario, empresa, fecha/hora, creación/modificación, reversión y cambios sensibles.

## 15. Deuda técnica y crecimiento
Dirección acordada:
```text
templates grandes
    ↓ extraer JS/CSS al tocarlos
static/js/
static/css/

views.py monolítico
    ↓ separación progresiva
views/
services/
```
No se duplica una regla financiera para resolver rápido una pantalla.

---

## Motor común de Vencimientos y Alertas

Vencimiento y Alerta son conceptos separados.

- Vencimiento representa el compromiso económico real.
- Alerta representa cuándo ese compromiso debe llamar la atención del usuario.
- El Llamador de OrdenaClick es solamente un componente de interfaz.
- Ni la Alerta ni el Llamador crean, cancelan ni modifican obligaciones económicas.

La determinación de qué registros deben producir una Alerta pertenece al backend,
dentro de una capa reutilizable de servicios.

El frontend no debe implementar reglas como:

- "fecha <= hoy + 3 días";
- ventanas de presentación de cheques;
- vencimientos por tipo de instrumento;
- estados financieros.

El frontend debe solicitar las Alertas vigentes y limitarse a presentarlas.

### Políticas de alerta

No existe una única regla temporal universal para todas las Alertas.

#### Obligaciones económicas comunes

Para Movimientos, cuotas y otras obligaciones con fecha de vencimiento:

- anticipación inicial: 3 días corridos;
- se muestran desde tres días antes de su vencimiento;
- si llega el vencimiento y continúa existiendo saldo pendiente, siguen requiriendo atención;
- pagar totalmente la obligación elimina su condición de pendiente, pero no su histórico.

Conceptualmente:

Vencimiento
→ Alerta desde 3 días antes
→ Vencimiento
→ continúa visible mientras siga pendiente

#### Cheques y e-Cheqs de terceros en cartera

La futura Cartera de Cheques y e-Cheqs utilizará el mismo motor de
Vencimientos y Alertas.

Para un valor disponible para depósito/cobro:

- la fecha de acreditación habilita el comienzo de la ventana de atención;
- desde esa fecha debe alimentar Alertas;
- la ventana será de 30 días corridos;
- una vez agotada esa ventana sin haberse depositado/cobrado, el valor pasa
  conceptualmente a vencido;
- alcanzar una fecha no significa automáticamente que el cheque haya sido
  depositado, cobrado o acreditado financieramente.

La definición técnica exacta de los límites de esos 30 días deberá quedar
centralizada y respaldada por tests de frontera para evitar errores de un día.

### Extensibilidad

Cada tipo de compromiso podrá poseer su propia política de alerta.

El servicio común debe poder incorporar nuevas fuentes sin obligar a modificar
la interfaz de Próximos Vencimientos.

Ejemplos futuros:

- Movimientos.
- Cuotas.
- Cheques propios.
- Cheques/e-Cheqs de terceros en cartera.
- Débitos automáticos.
- Otros compromisos económicos.