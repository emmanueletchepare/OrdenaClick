# ARQUITECTURA.md --- Cómo está construido OrdenaClick

## 1. Principio rector

OrdenaClick usa una arquitectura común y escalable. Las diferencias
entre planes, perfiles o complejidad operativa se resuelven mediante
permisos, capacidades, configuración y visibilidad; no mediante bases
incompatibles.

## 2. Separación de responsabilidades

La aplicación debe evolucionar evitando archivos monolíticos: - Las
vistas coordinan HTTP, permisos, formularios y respuestas. - Las reglas
de negocio reutilizables viven en servicios. - La lógica financiera
central no se duplica entre pantallas. - JavaScript nuevo debe ir a
archivos estáticos. - CSS nuevo debe ir a archivos estáticos. -
Templates deben concentrarse en estructura/presentación y no convertirse
en depósitos de reglas de negocio.

Al tocar código viejo, se debe aprovechar para extraer progresivamente
JS/CSS inline y responsabilidades excesivas, sin iniciar refactors
masivos que desvíen la Beta.

### Navegación contextual como infraestructura común

Los saltos realizados mediante `[+]` deben utilizar una pila común de
contextos de navegación. Cada entrada guarda el estado necesario para
reconstruir el nivel llamador, incluida su posición visual, y cada
retorno desapila un solo nivel.

El mecanismo admite encadenamientos
`formulario → [+] → ABM → [+] → ABM ...` sin pérdida de datos. La
pantalla destino no necesita conocer quién la llamó. Los retornos
especiales heredados se migran gradualmente y se eliminan únicamente
cuando sus flujos estén cubiertos por la infraestructura común y sus
pruebas.

Para la salida Beta, el JavaScript inline heredado deja de considerarse
solamente una limpieza oportunista: debe eliminarse de los flujos
publicados de la Beta.

## 3. Núcleo financiero

Estructura conceptual:

``` text
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

Movimiento = hecho económico/documental.\
Pago = hecho financiero.\
AplicaciónPago = cuánto de un Pago cancela un Movimiento o una Cuota.\
Vencimiento = obligación/compromiso financiero abierto.\
Alerta = aviso asociado; nunca reemplaza al Vencimiento como fuente de
verdad.

## 4. Saldo

La fuente común debe calcular el saldo sobre aplicaciones efectivas:

``` text
saldo_pendiente = Movimiento.total - SUM(AplicacionPago.importe)
```

Los costos financieros (intereses de tarjeta, mora, punitorios u otros)
se conservan diferenciados y no incrementan artificialmente el importe
aplicado al Movimiento.

### Regla de aplicación máxima

El importe aplicado directamente a un Movimiento nunca puede superar su
saldo pendiente actual.

``` text
0 <= nueva_aplicacion <= saldo_pendiente
```

Por lo tanto:

-   aplicación `0`: el Movimiento conserva su saldo;
-   aplicación menor al saldo: Pago parcial;
-   aplicación igual al saldo: cancelación total;
-   aplicación mayor al saldo: no permitida dentro de Comprobantes,
    Carga Planificada ni edición directa del Movimiento.

Cuando el Movimiento ya posee Pagos históricos, la validación se realiza
contra el saldo pendiente actual, no contra el total original del
documento. Los Pagos históricos no se reescriben silenciosamente durante
una edición.

Un Pago como hecho financiero sí puede ser mayor que el saldo de un
Movimiento determinado. Ese caso pertenece al circuito **Registrar
Pago**, que deberá permitir distribuir un mismo Pago entre varios
Movimientos y, cuando corresponda, conservar un remanente a cuenta.

La excepción definida es el Débito automático con intereses/costos por
mora confirmados: el importe real debitado puede superar el saldo, pero
el importe aplicado al Movimiento no. La diferencia se registra
separadamente como costo financiero.

La validación definitiva pertenece al backend y debe centralizarse en
servicios reutilizables. El frontend puede anticipar el error para
mejorar UX, pero no es autoridad.

## 5. Movimiento y Pago son independientes

Un Movimiento puede existir sin pago, con pago parcial, total, múltiples
pagos o convertirse en Plan después de pagos previos. Un Pago puede
combinar medios de cancelación.

Medios previstos: efectivo, transferencias/depósitos, tarjetas,
cheques/e-Cheqs, retenciones y otros futuros.

## 6. Comprobantes y Obligaciones

No todos los Movimientos económicos se originan en una factura.

La interfaz separa conceptualmente dos circuitos de registración:

``` text
REGISTROS
├── Comprobantes
└── Obligaciones
```

### Comprobantes

Corresponde al circuito actualmente implementado como Carga Simple.

Está destinado a facturas y otros comprobantes para los cuales tienen
sentido datos como:

-   Proveedor.
-   Tipo de comprobante.
-   Punto de venta.
-   Número de comprobante.
-   Tipo de gasto.
-   Centro Operativo.
-   Recurso Operativo, cuando corresponda.
-   Importe.
-   Vencimiento.
-   Forma de pago.

### Obligaciones / Liquidaciones

Está destinado a compromisos económicos que no deben forzarse dentro de
la estructura documental de una factura.

Casos iniciales previstos:

-   Sueldos.
-   Aportes y contribuciones.
-   VEP / impuestos.
-   Tasas y otros.

Datos conceptuales iniciales:

-   Concepto.
-   Organismo / beneficiario.
-   Período.
-   Referencia.
-   Centro Operativo, cuando corresponda.
-   Importe.
-   Vencimiento.
-   Forma de pago.

La existencia de circuitos de carga distintos no implica crear núcleos
financieros paralelos.

Comprobantes y Obligaciones deben utilizar, cuando corresponda, la
arquitectura común de Movimiento, Pago, AplicaciónPago, Vencimiento y
Alerta.

La estructura definitiva de datos de Obligaciones debe definirse antes
de implementarla.

## 7. Vencimientos y Alertas

Todo evento económicamente relevante con fecha futura debe evaluarse
como fuente de Vencimiento. Movimiento impago, cuotas, cheques propios,
débito automático y futuras obligaciones alimentan una fuente común.

El paso del tiempo no borra una obligación: pasa de próxima a vencer a
vence hoy o vencida y sigue visible mientras exista saldo pendiente.

La campanita, Próximos Vencimientos, futuras notificaciones móviles y
otros llamadores deben consumir la misma fuente de verdad.

## 8. Planes de Pago

Convertir a Plan trabaja sobre el saldo restante. El Movimiento original
conserva su historia. La obligación previa reemplazada deja de estar
abierta y las cuotas del Plan generan nuevas obligaciones
independientes.

## 9. Histórico

Centro Operativo y Recurso Operativo utilizados en un Movimiento se
conservan históricamente. Si el recurso cambia de centro después, el
Movimiento no cambia retroactivamente.

## 10. Moneda

La Beta opera en ARS. El modelo debe quedar preparado para identificar
moneda. Cuentas incompatibles (por ejemplo USD para un Movimiento ARS)
no deben habilitarse como medio de pago durante la Beta. Multimoneda,
conversión y tipo de cambio son posteriores.

## 11. Reportes y contabilidad futura

Se persisten componentes fiscales y financieros discriminados, no
solamente totales. Esto debe permitir filtros por Empresa, Ejercicio,
Proveedor, Tipo de Gasto, Centro, Recurso, fechas, estado, componentes
fiscales, pagos y dimensiones futuras.

## 12. Exportar / Importar Empresa

La exportación debe ser una copia completa y portable del entorno
Empresa. Si un dato se perdería al eliminar y reimportar, debe formar
parte del backup salvo exclusión explícita documentada.

Debe incluir versión de formato y reconstruir relaciones mediante mapas
de identificadores, sin asumir que los IDs originales se conservan.

Incluye, según existan: Empresa, configuración, documentación
societaria, ejercicios, centros, recursos, bancos, cuentas bancarias,
proveedores, tipos de gasto y relaciones, movimientos, archivos, pagos,
aplicaciones, tarjetas, cheques/e-Cheqs, retenciones, planes, cuotas,
vencimientos, alertas y futuras órdenes de pago.

Nunca exportar SECRET_KEY, claves maestras, variables de entorno,
credenciales de infraestructura ni contraseñas en texto plano. La clave
de cifrado no viaja dentro del backup.

El primer formato estable será **Backup Empresa v1**. Antes de Beta no se
mantendrá compatibilidad con los ZIP legacy generados durante desarrollo:
pueden descartarse porque no existen todavía clientes ni backups productivos
que deban preservarse.

Importar Empresa no es una restauración ciega. El ZIP es entrada no confiable
y describe el estado de origen, pero no decide por sí solo el estado operativo
o los privilegios actuales. El flujo debe ser guiado: inspeccionar y validar
completamente el backup, permitir que un usuario autorizado confirme o ajuste
los datos que pueden haber cambiado (por ejemplo categoría fiscal,
documentación, usuarios activos/inactivos y jerarquías), mostrar un resumen y
recién entonces ejecutar la restauración.

Los usuarios vinculados a historia no se eliminan físicamente por una
importación. Debe preservarse la trazabilidad de quién generó o modificó
operaciones, separando identidad histórica de autorización actual. Una
jerarquía contenida en el backup no concede privilegios automáticamente en el
destino.

Si el CUIT ya existe, nunca se elimina primero la Empresa válida para luego
intentar recrearla. La restauración debe planificarse y validarse antes de
modificar estado persistente, y ejecutarse con atomicidad/rollback suficiente
para no dejar una Empresa borrada o parcialmente restaurada ante una falla.

La futura precarga de catálogos o datos iniciales (por ejemplo bancos comunes)
es infraestructura distinta del backup empresarial y no debe mezclarse con
Exportar/Importar Empresa.

## 13. Seguridad de arquitectura

Cada endpoint debe validar usuario, empresa activa, rol/permisos y
pertenencia de los objetos manipulados. No confiar en IDs enviados por
frontend. Operaciones compuestas deben usar transacciones cuando
corresponda. La información sensible debe protegerse en tránsito, reposo
y backup según su naturaleza.

### Seguridad global de la instalación

OrdenaClick distingue la configuración sensible global de la instalación
de los datos pertenecientes a una Empresa.

El Perfil Desarrollador es una función técnica de instalación:

-   sólo puede ser accedido por superusuarios;
-   no pertenece a una Empresa;
-   centraliza configuración técnica sensible;
-   nunca muestra secretos ya almacenados;
-   las operaciones sensibles siguen siendo autorizadas por backend;
-   los secretos no se almacenan en `static/`, `media/`, el repositorio,
    backups de Empresa ni JavaScript.

La configuración privada de instalación se almacena fuera del
repositorio y de los directorios públicos de la aplicación. En
desarrollo puede utilizar un directorio privado del usuario; en
producción deberá ubicarse en almacenamiento protegido para la cuenta
del servicio y con permisos del sistema operativo adecuados.

Para `SECRET_KEY`, el orden de resolución es:

``` text
ORDENACLICK_SECRET_KEY del entorno
        ↓ si no existe
configuración privada de instalación
        ↓ si no existe
error de arranque
```

No existe una clave insegura de fallback incorporada al código.

Si `ORDENACLICK_SECRET_KEY` está definida en el entorno, la aplicación
la considera administrada externamente y no permite reemplazarla desde
el Perfil Desarrollador.

La rotación desde OrdenaClick genera la nueva clave exclusivamente en el
servidor y la persiste sin devolverla al navegador. La clave efectiva
del proceso no cambia hasta reiniciar Django.

Mientras la clave privada persistida sea distinta de
`settings.SECRET_KEY`, el sistema considera que existe un reinicio
pendiente y bloquea una segunda rotación.

Una rotación de `SECRET_KEY` puede invalidar sesiones y otros datos
firmados con la clave anterior. El Perfil Desarrollador debe advertirlo
antes de preparar el reemplazo.

Las operaciones sensibles del Perfil Desarrollador requieren, según
corresponda:

-   autenticación;
-   condición de superusuario validada en backend;
-   `POST`;
-   CSRF;
-   errores controlados sin exposición de secretos;
-   estado explícito cuando una modificación requiere reiniciar el
    servidor.

Las rutas protegidas utilizan el login propio de OrdenaClick como
`LOGIN_URL`; una sesión ausente o inválida no debe redirigir al login
predeterminado `/accounts/login/`.

Las futuras credenciales globales de integraciones, incluida ARCA,
siguen esta misma frontera arquitectónica: pertenecen a la instalación y
no a una Empresa.

## 14. Auditoría

Las operaciones relevantes deben quedar preparadas para trazabilidad:
usuario, empresa, fecha/hora, creación/modificación, reversión y cambios
sensibles.

## 15. Deuda técnica y crecimiento

Dirección acordada:

``` text
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

------------------------------------------------------------------------

## Motor común de Vencimientos y Alertas

Vencimiento y Alerta son conceptos separados.

-   Vencimiento representa el compromiso económico real.
-   Alerta representa cuándo ese compromiso debe llamar la atención del
    usuario.
-   El Llamador de OrdenaClick es solamente un componente de interfaz.
-   Ni la Alerta ni el Llamador crean, cancelan ni modifican
    obligaciones económicas.

La determinación de qué registros deben producir una Alerta pertenece al
backend, dentro de una capa reutilizable de servicios.

El frontend no debe implementar reglas como:

-   "fecha \<= hoy + 3 días";
-   ventanas de presentación de cheques;
-   vencimientos por tipo de instrumento;
-   estados financieros.

El frontend debe solicitar las Alertas vigentes y limitarse a
presentarlas.

### Políticas de alerta

No existe una única regla temporal universal para todas las Alertas.

#### Obligaciones económicas comunes

Para Movimientos, cuotas y otras obligaciones con fecha de vencimiento:

-   anticipación inicial: 3 días corridos;
-   se muestran desde tres días antes de su vencimiento;
-   si llega el vencimiento y continúa existiendo saldo pendiente,
    siguen requiriendo atención;
-   pagar totalmente la obligación elimina su condición de pendiente,
    pero no su histórico.

Conceptualmente:

Vencimiento → Alerta desde 3 días antes → Vencimiento → continúa visible
mientras siga pendiente

#### Cheques y e-Cheqs de terceros en cartera

La futura Cartera de Cheques y e-Cheqs utilizará el mismo motor de
Vencimientos y Alertas.

Para un valor disponible para depósito/cobro:

-   la fecha de acreditación habilita el comienzo de la ventana de
    atención;
-   desde esa fecha debe alimentar Alertas;
-   la ventana será de 30 días corridos;
-   una vez agotada esa ventana sin haberse depositado/cobrado, el valor
    pasa conceptualmente a vencido;
-   alcanzar una fecha no significa automáticamente que el cheque haya
    sido depositado, cobrado o acreditado financieramente.

La definición técnica exacta de los límites de esos 30 días deberá
quedar centralizada y respaldada por tests de frontera para evitar
errores de un día.

#### Caja y disponibilidad de valores

Caja separará visualmente `Cheques de terceros` y `e-Cheqs de terceros`.
El ingreso registra el valor recibido, no la venta/cobranza externa que
le dio origen. Cada valor de tercero se relacionará con un Cliente; el
Cliente pertenece a un Centro Operativo.

La disponibilidad para Pago no equivale simplemente a estar en Cartera:

-   Cheque a la orden: seleccionable para Pago o depósito.
-   Cheque no a la orden: sólo depósito en cuenta propia.
-   e-Cheq a la orden: Pago por endoso o depósito.
-   e-Cheq no a la orden: Pago por cesión o depósito.

Endoso/cesión se deriva de la condición del instrumento; no debe pedirse
al usuario una decisión que el sistema ya puede determinar.

La salida de Cartera puede producirse por Pago/Orden de Pago o por
depósito en una Cuenta Bancaria propia. Debe conservarse la trazabilidad
del destino.

Los instrumentos propios siguen otro circuito: no salen de Cartera, sino
que se emiten para el Pago. La Orden de Pago podrá combinar efectivo,
retenciones, valores de terceros disponibles y cheques/e-Cheqs propios
emitidos.

### Extensibilidad

Cada tipo de compromiso podrá poseer su propia política de alerta.

El servicio común debe poder incorporar nuevas fuentes sin obligar a
modificar la interfaz de Próximos Vencimientos.

Ejemplos futuros:

-   Movimientos.
-   Cuotas.
-   Cheques propios.
-   Cheques/e-Cheqs de terceros en cartera.
-   Débitos automáticos.
-   Otros compromisos económicos.

------------------------------------------------------------------------

## Edición, Pagos históricos y eliminación de Movimientos

### Frontera histórica

La existencia de una `AplicacionPago` histórica determina si un
Movimiento sigue siendo estructuralmente editable.

-   Sin aplicaciones históricas al iniciar la transacción: el Movimiento
    puede modificarse normalmente y puede recibir uno o varios Pagos
    nuevos en el mismo `Guardar cambios`. Si cambia el total, esos Pagos
    se validan contra el nuevo total ya validado por backend.
-   Con al menos una aplicación histórica: quedan congelados total,
    proveedor, fechas, Tipo de Gasto, Centro/Recurso, comprobante,
    componentes monetarios, vencimiento y demás estructura.
-   Con historia sólo pueden modificarse factura/archivo, forma prevista
    de pago y cuenta prevista válida; además pueden agregarse nuevos
    Pagos contra saldo.
-   Los Pagos nuevos de la misma petición no congelan retroactivamente
    una edición que comenzó sin aplicaciones históricas.
-   Backend es autoridad; el bloqueo visual sólo mejora UX.

### Gestión de Pagos históricos

Los Pagos anteriores deben mostrarse en la edición del Movimiento con
una acción de gestión/detalle. Una corrección no reescribe
silenciosamente un Pago aplicado: se elimina/revierte de forma
controlada y, si corresponde, se registra uno nuevo.

Eliminar/revertir un Pago debe mantener coherentes `Pago`,
`AplicacionPago`, componentes financieros, saldo y estado del
Movimiento, Vencimiento y Alertas. Si el Pago ya produjo consecuencias
financieras posteriores que no sea seguro borrar, la operación debe
rechazarse o utilizar una reversión histórica.

### Baja física por error de carga

`Error de carga != hecho histórico`.

Un Movimiento sin ninguna `AplicacionPago` puede eliminarse físicamente.
Un Movimiento con una o más aplicaciones no puede eliminarse: primero
deben eliminarse/revertirse todos sus Pagos.

Esta regla es general y no depende del medio de pago. Al desaparecer la
última aplicación, el Movimiento vuelve a quedar estructuralmente
editable y puede eliminarse si corresponde.

La baja física requiere autorización por Empresa, `POST`, CSRF,
`transaction.atomic()`, bloqueos necesarios y eliminación explícita de
dependencias derivadas; `PROTECT` no se reemplaza por `CASCADE`.

### Concurrencia

Las operaciones financieras/destructivas se diseñan para servidor
público: autorizar Empresa, reconsultar objetos dentro de ese contexto,
abrir transacción, usar `select_for_update()` cuando exista competencia,
recalcular saldo/estado dentro del bloqueo y validar nuevamente antes de
persistir.
