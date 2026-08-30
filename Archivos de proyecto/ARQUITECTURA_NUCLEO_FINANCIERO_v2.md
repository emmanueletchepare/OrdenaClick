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

------------------------------------------------------------------------

## 24. Previsión de pago, Próximos Vencimientos y Llamador de OrdenaClick

### 24.1 Previsión de pago del Movimiento

Antes de cerrar la carga de un gasto, el Movimiento debe indicar cómo se prevé atender su saldo pendiente:

- **Pago Manual**.
- **Débito automático**, asociado a una Cuenta Bancaria propia.

Durante la Beta, las cuentas ofrecidas para débito automático deben estar activas, pertenecer a la Empresa y operar en ARS.

Elegir Débito automático **NO crea un Pago**. Representa una previsión de cancelación y una futura necesidad de fondos. El hecho financiero se registra recién cuando el débito ocurre o se confirma.

La previsión debe conservar conceptualmente:

- modalidad prevista de pago;
- Cuenta Bancaria prevista, cuando corresponda;
- fecha de vencimiento del Movimiento.

### 24.2 Regla común de saldo y compromisos

Para Movimientos pendientes:

```text
Saldo pendiente =
Total del Movimiento - Aplicaciones de Pago válidas
```

Un Movimiento parcialmente pagado muestra únicamente su saldo pendiente. Uno totalmente pagado no aparece como obligación pendiente del Movimiento. Una obligación vencida continúa visible mientras siga abierta.

Los Cheques/e-Cheqs propios también generan previsibilidad: aunque ya hayan aplicado su importe a un Pago, representan una salida futura de fondos según su cuenta y fecha de acreditación/débito. Débitos automáticos y Cheques propios pueden agruparse visualmente por Cuenta Bancaria, pero conservan entidades, estados e histórico independientes.

### 24.3 Próximos Vencimientos

Dentro del menú Operativo, Próximos Vencimientos tendrá:

```text
[ Alerta ] [ Hoy ] [ Esta semana ] [ Rango de fechas ]

Listar:
[ Todos / Tipo de gasto / Proveedor / Centro Operativo /
  Recurso Operativo / Débitos por cuenta ]
```

Si `Listar` es distinto de `Todos`, deberá permitirse seleccionar el valor concreto del criterio elegido.

**Hoy** muestra los compromisos del día, sus importes pendientes y un total del día.

**Esta semana** y **Rango de fechas** agrupan por día, muestran subtotal por día y finalizan con un **TOTAL GENERAL**.

Los filtros modifican el conjunto mostrado, pero no deben implementar motores financieros diferentes.

### 24.4 Vista especial Alerta

`Alerta` no es simplemente otro rango. Es una vista inmediata de previsión de tesorería.

La ventana inicial comprende cuatro días corridos:

```text
HOY
HOY + 1
HOY + 2
HOY + 3
```

Dentro de cada día, los compromisos se agrupan cuando corresponda por Cuenta Bancaria:

```text
HOY · fecha                                      $ TOTAL DÍA

Caja de ahorro Banco Provincia                   $ subtotal cuenta
Cheque 0002545 | Gasto | Proveedor               $ importe
Débito        | Gasto | Proveedor                $ importe

Cuenta Corriente Banco Comafi                     $ subtotal cuenta
Débito        | Gasto | Proveedor                $ importe

Otros / Pagos manuales                            $ subtotal manual
Gasto | Proveedor                                 $ importe
```

Cada subtotal debe ser la suma real de sus renglones. La vista debe ser clara, resumida y concreta, orientada a responder cuánto debe preverse y en qué Cuenta Bancaria.

### 24.5 Fuente común

Alerta, Hoy, Esta semana y Rango de fechas deben reutilizar una única lógica capaz de proporcionar como mínimo:

- Empresa;
- fecha;
- tipo y origen del compromiso;
- importe pendiente o comprometido;
- Cuenta Bancaria, cuando corresponda;
- Tipo de gasto;
- Proveedor;
- Centro Operativo;
- Recurso Operativo;
- observaciones relevantes.

La misma fuente deberá poder reutilizarse posteriormente por Reportes, el Llamador y notificaciones móviles.

### 24.6 Llamador de OrdenaClick

Se define un componente visual genérico denominado conceptualmente **Llamador de OrdenaClick**. No debe quedar acoplado visualmente a Vencimientos porque en el futuro podrá utilizarse para otros motivos que requieran atención.

Para su primera implementación:

1. Al seleccionar una Empresa se consulta silenciosamente si existen compromisos para la vista Alerta.
2. Si no existen, el Llamador no aparece.
3. Si existen, espera aproximadamente 60 segundos.
4. Si cambia la Empresa durante la espera, se cancela el temporizador anterior.
5. Luego emerge mediante una animación breve y una campana produce un sonido corto.
6. Después permanece quieto.

El Llamador **no muestra texto, importes, cantidad, Empresa ni motivo**. Su función es llamar la atención y despertar la consulta.

Debe permitir **drag & drop**, permanecer dentro del área visible y conservar su posición durante la interacción. No es necesario persistir inicialmente esa posición en la base.

Si continúa pendiente, aproximadamente cada **20 minutos** puede realizar un pequeño movimiento de campana y reproducir un sonido corto. No debe mantener animaciones o sonidos constantes. El funcionamiento crítico no dependerá exclusivamente del audio debido a posibles restricciones del navegador.

Al hacer clic:

```text
Operativo
→ Próximos Vencimientos
→ Alerta
```

La vista debe abrirse directamente configurada como Alerta y el Llamador desaparece.

### 24.7 Separación conceptual

```text
VENCIMIENTO / COMPROMISO
= fuente de verdad.

VISTA ALERTA
= presentación inmediata y resumida.

LLAMADOR DE ORDENACLICK
= componente de interfaz que reclama atención.
```

Ni la vista Alerta ni el Llamador crean obligaciones.

### 24.8 Reutilización futura

No se implementará ahora un sistema genérico completo, pero el Llamador no debe quedar limitado a compromisos financieros.

Posibles usos futuros:

- proximidad de cierre contable;
- vencimiento de acta de designación de autoridades;
- documentación que requiera atención;
- otros compromisos administrativos u operativos;
- nuevas necesidades surgidas de usuarios reales.

### 24.9 Notificaciones móviles futuras

La futura versión móvil deberá permitir que el usuario elija si desea recibir una notificación cuando exista una Alerta aunque no haya abierto OrdenaClick.

Debe reutilizarse la misma fuente común de compromisos. Configuración, horarios, anticipación y tecnología push quedan para una etapa posterior.

### 24.10 Orden de implementación acordado

```text
1. Previsión de pago:
   Pago Manual / Débito automático + Cuenta Bancaria.

2. Próximos Vencimientos:
   Alerta / Hoy / Esta semana / Rango de fechas / Listar.

3. Llamador de OrdenaClick:
   condición + delay + animación + sonido + drag & drop +
   recordatorio + navegación a Alerta.

4. Reportes:
   reutilizando la lógica financiera común.
```

El objetivo es que OrdenaClick no se limite a registrar hechos pasados, sino que transforme esos datos en previsibilidad concreta de compromisos futuros.


### 24.11 Registro del Pago real de un Débito automático

Cuando un Movimiento tenga como modalidad prevista **Débito automático**, la interfaz de carga del Pago debe simplificarse porque OrdenaClick ya conoce el medio previsto y la Cuenta Bancaria asociada.

En este caso el botón habitual:

```text
[ + Agregar pago ]
```

debe presentarse como:

```text
[ Registrar Pago ]
```

Al utilizarlo no debe mostrarse el conjunto completo de medios de pago. El acordeón debe contener únicamente:

```text
▼ Pago 1                                      $ 0,00

Fecha de Pago                     Importe
[ dd/mm/aaaa ]                    [          ]
```

El campo que en el formulario general corresponde visualmente a `Efectivo` debe denominarse **Importe** en este flujo.

No deben volver a solicitarse Banco, Cuenta Bancaria ni forma de pago, porque esos datos provienen de la previsión de Débito automático del Movimiento.

El importe ingresado representa el débito real observado en la Cuenta Bancaria.

#### Importe igual, menor o mayor al compromiso

Si:

```text
Importe debitado = saldo pendiente
```

se registra una cancelación total normal.

Si:

```text
Importe debitado < saldo pendiente
```

se registra un Pago parcial y el compromiso continúa abierto por el saldo restante.

Si:

```text
Importe debitado > saldo pendiente
```

la diferencia NO debe aplicarse automáticamente al Movimiento.

Cuando además la fecha real del Pago sea posterior al vencimiento, OrdenaClick debe solicitar confirmación antes de guardar.

Ejemplo:

```text
Saldo pendiente:                 $100.000
Importe debitado:                $107.500
Diferencia:                        $7.500
```

Modal conceptual:

```text
El débito se produjo después del vencimiento y el importe ingresado
supera en $7.500 el saldo pendiente.

¿Los $7.500 corresponden a intereses por mora?

[ Sí ] [ No ]
```

Si el usuario selecciona **Sí**:

- se registra como importe aplicado únicamente el saldo que corresponde cancelar;
- la diferencia se conserva separadamente como interés/costo financiero;
- el interés NO incrementa el importe aplicado al Movimiento;
- se registra la fecha real del Pago;
- se actualiza el saldo y estado del compromiso.

Si selecciona **No**:

- no se guarda el Pago;
- no se modifica el Movimiento ni el compromiso;
- se vuelve al acordeón;
- deben conservarse Fecha e Importe ingresados para permitir su corrección.

La confirmación del usuario es necesaria: OrdenaClick no debe asumir automáticamente que todo excedente corresponde a intereses.

Si el importe es superior al saldo pero la fecha NO es posterior al vencimiento, no debe clasificarse automáticamente la diferencia como interés por mora. La clasificación definitiva de otros excedentes queda pendiente de definición.

Este flujo debe respetar la regla general del núcleo financiero:

> Los intereses y costos financieros son económicamente reales, pero no aumentan el importe aplicado a la cancelación del Movimiento.