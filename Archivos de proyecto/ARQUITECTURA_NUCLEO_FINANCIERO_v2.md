# Arquitectura del Núcleo Financiero --- OrdenaClick

## 1. Propósito

Este documento registra las decisiones conceptuales tomadas para el
núcleo financiero de OrdenaClick antes de implementar el guardado
definitivo de movimientos.

Su objetivo es servir como referencia para futuras etapas de desarrollo,
otros colaboradores y nuevas conversaciones de trabajo, evitando
reconstruir decisiones importantes únicamente a partir del código.

Este documento describe arquitectura y reglas de negocio. No implica que
todas las funcionalidades aquí mencionadas estén implementadas en la
versión Beta.

------------------------------------------------------------------------

## 2. Objetivo funcional de OrdenaClick

OrdenaClick debe ayudar a una empresa en dos frentes principales:

1.  Registrar y conservar información completa de gastos, comprobantes y
    pagos para su posterior consulta y explotación mediante Reportes.
2.  Evitar que el empresario pierda de vista compromisos financieros
    pendientes o próximos a vencer.

Por este motivo, el sistema no debe tratar un gasto únicamente como una
factura almacenada. Debe poder representar también su estado financiero,
sus pagos y las obligaciones futuras que genere.

------------------------------------------------------------------------

## 3. Núcleo conceptual

La estructura conceptual definida es:

``` text
EMPRESA
   │
   └── EJERCICIO
          │
          └── MOVIMIENTO
                │
                ├── PAGOS / APLICACIONES DE PAGO
                │
                └── OBLIGACIONES
                       │
                       ├── Pendientes
                       ├── Próximas a vencer
                       └── Vencidas

MOVIMIENTO
   │
   └── puede convertirse en
       PLAN DE PAGOS
          │
          └── CUOTAS
                 │
                 └── OBLIGACIONES

CHEQUE PROPIO EMITIDO
   └── genera una obligación por su fecha correspondiente

DÉBITO AUTOMÁTICO
   └── genera una obligación por su fecha prevista

REGISTRO / RENDICIÓN DEL VENDEDOR
   │
   └── REGISTRO PENDIENTE
          │
          └── revisión y completado por Admin / Colaborador
                 │
                 └── MOVIMIENTO definitivo
```

------------------------------------------------------------------------

## 4. Empresa y Ejercicio

Cada empresa abre y cierra ejercicios contables.

Los movimientos deben quedar asociados a:

-   una Empresa;
-   un Ejercicio.

Conceptualmente:

``` text
Empresa
 ├── Ejercicio 2026
 │    ├── Movimiento
 │    ├── Movimiento
 │    └── Movimiento
 │
 └── Ejercicio 2027
      ├── Movimiento
      └── Movimiento
```

El cierre de un ejercicio no debe eliminar su información histórica.

Las reglas exactas sobre qué operaciones podrán realizarse sobre un
ejercicio cerrado quedan pendientes de definición.

------------------------------------------------------------------------

## 5. Movimiento

El Movimiento representa el hecho económico y documental.

Debe conservar la información necesaria para reconstruir históricamente
el gasto y permitir posteriormente filtros e informes.

Como mínimo se prevé conservar:

-   Empresa.
-   Ejercicio.
-   Tipo de gasto.
-   Proveedor.
-   Centro Operativo.
-   Recurso Operativo.
-   Fecha de registro.
-   Fecha de vencimiento.
-   Tipo de comprobante.
-   Número de comprobante.
-   Descripción.
-   Neto gravado.
-   No gravado / exento.
-   IVA 21%.
-   IVA 27%.
-   IVA 10,5%.
-   Recargos / intereses propios del comprobante.
-   Ajuste por redondeo.
-   Percepción de Ingresos Brutos.
-   Percepción de IVA.
-   Percepción de Ganancias.
-   Percepción de Tasas Municipales.
-   Total.
-   Factura / archivo adjunto.
-   Estado.
-   Observaciones.
-   Moneda.
-   Datos de auditoría que correspondan.

El Total debe conservarse, pero también deben persistirse sus
componentes fiscales. No debe almacenarse únicamente un importe final
que impida reconstruir posteriormente la composición del gasto.

------------------------------------------------------------------------

## 6. Moneda

### Beta

La primera versión Beta operará exclusivamente en pesos argentinos
(ARS).

Los medios de pago disponibles durante esta etapa deben impedir
introducir importes en monedas incompatibles.

En particular, las cuentas bancarias en USD pueden continuar existiendo
en su ABM, pero no deben utilizarse como medio de pago de movimientos
ARS durante la Beta.

### Preparación para multimoneda

El modelo debe quedar preparado para identificar la moneda del
Movimiento aunque inicialmente todos los movimientos sean ARS.

Cuando se implemente multimoneda:

``` text
Movimiento ARS
→ habilita medios de pago compatibles con ARS

Movimiento USD
→ habilita medios de pago compatibles con USD
```

No se implementan todavía:

-   conversiones cambiarias;
-   tipos de cambio;
-   pagos cruzados entre monedas;
-   reglas definitivas para resúmenes de tarjetas en escenarios
    multimoneda.

Estas cuestiones se resolverán como una funcionalidad específica
posterior.

------------------------------------------------------------------------

## 7. Pago

El Pago representa el hecho financiero.

Un Movimiento puede tener:

-   cero pagos;
-   un pago;
-   múltiples pagos.

Los medios actualmente contemplados incluyen:

-   Efectivo.
-   Transferencias / Depósitos.
-   Tarjetas.
-   Cheques.
-   Retenciones.

Las Retenciones forman parte del importe aplicado al Pago.

El Pago y sus aplicaciones deben permanecer conceptualmente separados
del Movimiento para permitir pagos parciales, múltiples pagos y futuras
relaciones más complejas.

------------------------------------------------------------------------

## 8. Saldo pendiente

El sistema debe poder determinar cuánto del Movimiento permanece
pendiente.

Ejemplo:

``` text
Movimiento:       $100.000
Pagos aplicados:   $30.000
Saldo pendiente:   $70.000
```

El saldo pendiente es el que puede originar obligaciones futuras y
alertas.

------------------------------------------------------------------------

## 9. Obligación

La Obligación representa un compromiso financiero que todavía debe ser
atendido.

No debe confundirse con el Movimiento ni con la alerta visual.

Ejemplo:

``` text
Movimiento:
Factura proveedor X
Total: $100.000

Pago:
$30.000

Obligación:
Saldo pendiente: $70.000
Vencimiento: 15/09
```

La obligación permanece abierta mientras el compromiso continúe
pendiente.

### Vencimiento

El paso de la fecha NO elimina una obligación.

Una obligación abierta puede clasificarse como:

``` text
Fecha futura cercana  → Próxima a vencer
Fecha actual           → Vence hoy
Fecha pasada           → Vencida
```

Si el usuario no ingresa a OrdenaClick durante varios días y una
obligación vence durante ese período, al volver a ingresar debe
mostrarse como VENCIDA y continuar visible mientras siga pendiente.

Una obligación deja de formar parte de los compromisos abiertos cuando
corresponda por una acción real de negocio, por ejemplo:

-   pago/cancelación;
-   reemplazo por nuevas obligaciones derivadas de una conversión a Plan
    de Pagos;
-   otra acción futura expresamente definida.

------------------------------------------------------------------------


### Correspondencia con los modelos Django actuales

En la implementación actual de OrdenaClick, la entidad conceptual **Obligación** se encuentra representada técnicamente por el modelo `Vencimiento`.

Por lo tanto:

```text
OBLIGACIÓN conceptual
        =
Vencimiento en models.py
```

`Vencimiento` es la fuente de verdad del compromiso financiero abierto: conserva origen, fecha de vencimiento, importe original, importe pendiente y estado.

**Alerta no es sinónimo de Obligación.**

El modelo `Alerta` representa el aviso asociado a un `Vencimiento`, por ejemplo la fecha desde la cual corresponde llamar la atención del usuario y sus datos de anticipación/atención.

Conceptualmente:

```text
Movimiento / Cuota / Cheque
          ↓
     Vencimiento
     (Obligación)
          ↓
       Alerta
       (Aviso)
```

Una obligación vencida no desaparece por el paso del tiempo. Mientras `Vencimiento.importe_pendiente` continúe abierto y su estado no sea Pagado o Cancelado, debe seguir formando parte de los compromisos de la Empresa aunque su fecha ya haya pasado.

La campanita y la futura sección [Próximos vencimientos] deben tomar como fuente principal los `Vencimiento` abiertos. Las `Alerta` pueden utilizarse para programación, anticipación, atención o reprogramación del aviso, pero no deben reemplazar al `Vencimiento` como fuente de verdad del compromiso.


## 10. Campanita y Próximos vencimientos

La campanita no es la fuente de verdad de los vencimientos.

La fuente de verdad son las obligaciones abiertas.

Cuando el usuario selecciona una Empresa, OrdenaClick debe consultar las
obligaciones abiertas correspondientes a esa Empresa.

La campanita podrá informar:

-   compromisos próximos;
-   compromisos que vencen hoy;
-   compromisos vencidos que continúan pendientes.

La campanita direccionará al usuario a la futura sección:

``` text
[Próximos vencimientos]
```

del sidebar.

La versión móvil prevista deberá poder utilizar esta misma información
para generar notificaciones.

La estrategia técnica definitiva para notificaciones móviles queda
pendiente de definición.

------------------------------------------------------------------------

## 11. Fuentes de obligaciones

Una obligación puede originarse desde diferentes partes del sistema.

Entre las fuentes previstas se encuentran:

### Movimiento parcialmente o totalmente impago

El saldo pendiente genera una obligación según su vencimiento.

### Cheque propio emitido

Un cheque propio representa un compromiso de disponer de fondos en la
fecha correspondiente.

Debe poder generar una obligación futura.

### Débito automático

Un débito automático próximo representa un compromiso financiero futuro.

Debe poder generar una obligación según su fecha prevista.

### Plan de Pagos

Cada cuota pendiente del plan constituye una obligación con su propio
vencimiento.

El sistema de alertas no debería necesitar conocer internamente todas
las particularidades de cada origen para determinar que existe un
compromiso pendiente.

------------------------------------------------------------------------

## 12. Plan de Pagos

Carga Simple podrá convertirse posteriormente en Plan de Pagos.

La conversión debe heredar los datos necesarios del Movimiento original
y trabajar sobre el saldo restante.

Ejemplo:

``` text
Movimiento original: $1.000.000
Pagado:                 $200.000
Saldo:                  $800.000
```

Si el saldo se convierte en un plan:

``` text
Plan de Pagos
 ├── Cuota 1 → importe + vencimiento
 ├── Cuota 2 → importe + vencimiento
 ├── Cuota 3 → importe + vencimiento
 └── Cuota 4 → importe + vencimiento
```

Las cuotas podrán incorporar los intereses correspondientes al plan.

Al producirse la conversión:

1.  el Movimiento original conserva su historia;
2.  la obligación pendiente que estaba siendo reemplazada deja de formar
    parte de los compromisos abiertos;
3.  el Plan genera nuevas obligaciones correspondientes a sus cuotas;
4.  cada cuota será alertada según su propio vencimiento.

No debe destruirse ni reescribirse el valor documental histórico del
Movimiento original para representar el Plan.

------------------------------------------------------------------------

## 13. Intereses por mora

Un registro vencido podrá generar intereses al momento del pago.

Los intereses generados posteriormente al comprobante no deberían
modificar retroactivamente el importe documental original.

Ejemplo:

``` text
Factura original: $100.000
Interés por mora:    $5.000
Pago realizado:    $105.000
```

Debe ser posible distinguir posteriormente:

-   importe original;
-   interés generado por mora;
-   importe efectivamente pagado.

Esto permitirá además futuros Reportes sobre costos financieros e
intereses.

La fórmula, configuración y reglas definitivas de cálculo de mora quedan
pendientes de definición.

------------------------------------------------------------------------

## 14. Reportes

La sección \[Reportes\] utilizará la información persistida en los
Movimientos y demás entidades relacionadas.

Por ese motivo debe conservarse la información discriminada y no
solamente totales.

Se prevé que los usuarios puedan filtrar datos por diferentes
dimensiones, entre ellas las que posteriormente se definan sobre:

-   Empresa.
-   Ejercicio.
-   Proveedor.
-   Tipo de gasto.
-   Centro Operativo.
-   Recurso Operativo.
-   Fechas.
-   Estado.
-   Componentes fiscales.
-   Pagos.
-   Otras dimensiones futuras.

------------------------------------------------------------------------

## 15. Registro / Rendición del Vendedor

El futuro módulo del Vendedor estará orientado principalmente a la
rendición de viáticos y gastos producidos durante sus giras.

El vendedor realizará una carga simplificada con poca información.

Inicialmente se prevé:

-   Proveedor.
-   Importe.
-   Factura adjunta.
-   Comprobante de pago, cuando corresponda.
-   Otros datos mínimos que se definan al diseñar el módulo.

Esta información tiene valor para evitar una segunda carga manual
completa.

Sin embargo:

> Un Registro del Vendedor no debe convertirse automáticamente en un
> Movimiento contable definitivo.

El flujo conceptual será:

``` text
Vendedor
   ↓
Rendición / Registro preliminar
   ↓
Registros pendientes
   ↓
Admin / Colaborador
   ↓
Carga Simple precargada con la información disponible
   ↓
Completar / validar información restante
   ↓
Movimiento definitivo
```

El módulo concreto del Vendedor se diseñará e implementará
posteriormente, pero el núcleo financiero debe evitar decisiones que
impidan esta integración futura.

------------------------------------------------------------------------

## 16. Estados del Movimiento

Se prevén conceptualmente los siguientes estados:

-   Pendiente.
-   Parcial.
-   Pagado.
-   Vencido.
-   Cancelado.

Las reglas exactas de transición deberán definirse al implementar el
registro efectivo y la lógica de pagos.

El estado visual del Movimiento no debe reemplazar la existencia de
Obligaciones como fuente de verdad para compromisos financieros
abiertos.

------------------------------------------------------------------------

## 17. Seguridad

OrdenaClick funcionará como aplicación web y deberá contemplar seguridad
desde el backend.

No debe confiarse únicamente en restricciones de interfaz o JavaScript.

La autorización conceptual debe considerar:

``` text
Usuario
   ↓
permiso sobre Empresa
   ↓
Ejercicio
   ↓
Movimiento / Pago / Obligación / demás entidades
```

Cada operación sensible deberá validar del lado servidor que:

-   el usuario está autenticado;
-   tiene autorización sobre la Empresa;
-   el objeto pertenece a esa Empresa;
-   el Ejercicio corresponde;
-   su rol permite la operación;
-   las demás reglas de negocio aplicables se cumplen.

Los identificadores enviados por el navegador no deben considerarse
prueba suficiente de autorización.

La implementación debe mantener un equilibrio: seguridad correcta desde
el diseño sin agregar complejidad innecesaria antes de que sea
requerida.

------------------------------------------------------------------------

## 18. Planes, proveedor de pagos y webhooks

OrdenaClick tendrá planes de servicio.

En una etapa posterior se integrará un proveedor de pagos que permitirá
verificar el estado del plan contratado.

Se prevé el uso de webhooks.

Deben mantenerse separados dos conceptos:

``` text
1. ¿El usuario tiene permiso para operar sobre esta Empresa?

2. ¿El plan/suscripción de esa Empresa habilita esta funcionalidad?
```

La interfaz podrá ocultar o deshabilitar funcionalidades según el plan,
pero esa restricción visual no reemplaza la validación del backend.

El estado válido de la suscripción no debe depender exclusivamente de
información enviada por el navegador.

La integración concreta con el proveedor, validación de webhooks,
almacenamiento del estado de suscripción y políticas ante fallos se
diseñarán cuando se implemente el sistema comercial.

------------------------------------------------------------------------

## 19. Auditoría y trazabilidad

Por tratarse de información financiera y una aplicación web
multiusuario, los modelos principales deberían quedar preparados para
conservar trazabilidad suficiente.

Como mínimo debe evaluarse durante la implementación la necesidad de
registrar:

-   fecha de creación;
-   fecha de última modificación;
-   usuario creador;
-   usuario que realizó modificaciones relevantes;
-   estados y cambios que requieran trazabilidad.

El alcance definitivo se decidirá al diseñar los modelos concretos.

------------------------------------------------------------------------

## 20. Principios para la implementación

Las siguientes reglas deben guiar el desarrollo:

1.  El Movimiento conserva la historia documental.
2.  El Pago representa hechos financieros y no debe reescribir
    arbitrariamente el documento original.
3.  Las Obligaciones representan compromisos abiertos.
4.  Una obligación vencida permanece pendiente hasta que una acción real
    la cierre o reemplace.
5.  Las alertas se derivan de obligaciones abiertas.
6.  Los Planes de Pago reemplazan obligaciones pendientes por
    obligaciones correspondientes a sus cuotas, sin destruir el
    Movimiento original.
7.  La Beta trabaja exclusivamente en ARS.
8.  La arquitectura debe permitir multimoneda futura sin implementarla
    prematuramente.
9.  Los registros preliminares del Vendedor no son Movimientos
    definitivos.
10. Los datos discriminados deben conservarse para permitir Reportes
    futuros.
11. La seguridad y autorización reales pertenecen al backend.
12. Los permisos de usuario y la habilitación comercial por plan son
    controles diferentes.
13. Debe evitarse agregar complejidad futura que todavía no sea
    necesaria, pero también evitar decisiones que bloqueen
    funcionalidades ya previstas.

------------------------------------------------------------------------

## 21. Decisiones todavía no tomadas

Los siguientes temas están deliberadamente pendientes y NO deben
interpretarse como resueltos:

-   Modelo definitivo para resúmenes y pagos de tarjetas de crédito.
-   Reglas definitivas de multimoneda.
-   Conversión ARS/USD y tipos de cambio.
-   Pagos cruzados entre monedas.
-   Fórmula y política de intereses por mora.
-   Reglas definitivas de apertura y cierre de ejercicios.
-   Implementación técnica definitiva de alertas.
-   Implementación de notificaciones móviles.
-   Configuración de anticipación de alertas.
-   Diseño definitivo de Planes de Pago.
-   Diseño definitivo del módulo del Vendedor.
-   Flujo definitivo de aprobación de Registros Pendientes.
-   Integración concreta con proveedor de pagos.
-   Política de webhooks y contingencias.
-   Alcance definitivo de auditoría y trazabilidad.
-   Reglas completas de transición entre estados del Movimiento.

------------------------------------------------------------------------

## 22. Estado de la Beta al momento de esta decisión

La Beta se está construyendo inicialmente alrededor de Carga Simple y
Pagos.

Se ha definido que:

-   los pagos de la Beta operan en ARS;
-   Transferencias / Depósitos no deben permitir utilizar cuentas USD;
-   Retenciones forman parte del importe aplicado al Pago;
-   posteriormente se implementará el registro persistente de
    Movimientos con y sin Pago;
-   luego se desarrollarán las operaciones de Registrar Pago y Modificar
    / Eliminar;
-   posteriormente se incorporará Carga Planificada / Convertir a Plan;
-   Reportes, Pendientes y Alertas recorrerán la información persistida
    en el núcleo financiero.

Antes de implementar el guardado definitivo de Carga Simple debe
diseñarse el modelo de datos concreto respetando las decisiones de este
documento.

------------------------------------------------------------------------

## 23. Próximo paso de desarrollo

El próximo paso recomendado es diseñar los modelos Django concretos que
representarán este núcleo, comenzando por Movimiento y sus relaciones
inmediatas.

Antes de crear migraciones debe verificarse el código existente para:

-   detectar referencias al modelo Movimiento actual;
-   determinar compatibilidad con campos existentes;
-   confirmar las relaciones reales con Empresa, Ejercicio, Proveedor,
    Tipo de Gasto, Centro Operativo y Recurso Operativo;
-   evitar eliminar campos todavía utilizados;
-   diseñar una migración segura.

Una vez definido y migrado el modelo, podrá conectarse \[Guardar
registro\] comenzando por el flujo sin Pago y posteriormente el flujo
con Pago.
