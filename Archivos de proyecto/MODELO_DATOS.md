# MODELO_DATOS.md --- Organización de la información

## 1. Regla general

Los datos se diseñan para conservar historia y permitir crecimiento sin
migraciones destructivas por cambio de plan.

## 2. Jerarquía principal

``` text
Empresa
└── Ejercicio
    └── Movimiento
        ├── Pago
        │   ├── componentes por medio
        │   └── AplicacionPago
        ├── PlanPago
        │   └── Cuota
        └── Vencimiento
            └── Alerta
```

## 3. Empresa

Contiene datos generales, fiscales, contacto, autoridades y
configuraciones. Su entorno incluye documentación societaria,
ejercicios, centros, recursos, bancos, cuentas bancarias, tarjetas,
proveedores, tipos de gasto, relaciones y datos operativos/financieros.

## 4. Ejercicio

Todo Movimiento debe quedar asociado a Empresa y Ejercicio. Cerrar un
ejercicio no elimina historia. Las restricciones exactas sobre ejercicio
cerrado siguen siendo una decisión funcional a terminar.

## 5. Movimiento

Representa el hecho económico/documental. Debe conservar como mínimo: -
Empresa y Ejercicio. - Tipo de Gasto. - Proveedor. - Centro Operativo
histórico. - Recurso Operativo histórico. - Fecha de registro y
vencimiento cuando corresponda. - Tipo/número de comprobante. -
Descripción. - Neto gravado, no gravado/exento. - IVA discriminado. -
Recargos/intereses propios del comprobante. - Redondeos. -
Percepciones. - Total. - Archivo/factura. - Estado, observaciones,
moneda y auditoría.

Estados previstos: Pendiente, Parcial, Pagado, Vencido, Cancelado.

## 6. Tipo de Gasto / Proveedor

Tipo de Gasto reemplaza conceptualmente al Rubro simple. Tipo de Gasto y
Proveedor tienen relación muchos-a-muchos. Cuenta Contable puede
mostrarse deshabilitada hasta desarrollar Plan Contable.

## 7. Centro y Recurso Operativo

Todo Recurso Operativo debe poder vincularse a Centro Operativo mediante
asignación. Movimiento guarda el recurso y centro imputados al momento
del hecho. Usuario y Recurso Operativo son entidades independientes.

## 8. Pago

Entidad independiente del Movimiento. Puede existir más de uno por
Movimiento y combinar medios.

## 9. AplicacionPago

Une el Pago con el destino cancelado (Movimiento o Cuota según
implementación). Conserva importe aplicado. Es la base para pagos
parciales y múltiples.

``` text
saldo = total_movimiento - suma_aplicaciones
```

Una nueva `AplicacionPago` sobre un Movimiento no puede superar el saldo
pendiente actual de ese destino. Esta restricción es una regla de
negocio del núcleo financiero y debe validarse en backend.

Un `Pago` puede tener un importe real superior al saldo de un Movimiento
si se distribuye entre varios destinos o conserva un remanente a cuenta.
Esto no habilita a sobreaplicar un Movimiento individual.

Los costos financieros, incluidos intereses por mora confirmados, se
registran separados del importe aplicado.

## 10. Medios de pago

-   Efectivo.
-   Transferencia/Depósito.
-   Tarjeta.
-   Cheque/e-Cheq.
-   Retención.
-   Débito automático cuando se registre su impacto real. Cada medio
    conserva sus datos específicos y su relación con Pago.

## 11. Tarjeta

Pertenece a Empresa. Mínimo: nombre, tipo crédito/débito, cuenta
bancaria propia asociada y estado. En Beta no es necesario modelar
plástico individual, titular, vencimiento o recurso asignado.

Una operación de crédito puede guardar importe aplicado, cuotas e
intereses de financiación. Las cuotas de tarjeta no son Cuotas de
PlanPago.

## 12. Cuenta Bancaria

Empresa, Banco, nombre, tipo, moneda, número, CBU, alias,
activo/inactivo. Se relaciona con transferencias, cheques propios,
tarjetas, débito automático y futuras conciliaciones.

## 13. Cheque / e-Cheq

Debe conservar datos del instrumento, banco, fechas, estado, pago
relacionado y vencimiento cuando corresponda. Cheque propio emitido
puede generar obligación futura. La cartera de valores recibidos es una
función posterior.

## 14. Retención

Tipo, importe, comprobante/certificado y Pago relacionado. El importe
aplicado mediante retención forma parte de la cancelación.

## 15. PlanPago y Cuota

Plan trabaja sobre saldo financiado, condiciones, tasa y cantidad de
cuotas. Cuota conserva capital, interés, impuestos, vencimiento,
punitorios, estado y pagos/comprobantes relacionados.

## 16. Vencimiento

Es la representación técnica de la obligación financiera abierta.
Conserva origen, fecha, importe original, importe pendiente y estado. No
desaparece por pasar la fecha.

Fuentes: Movimiento impago, Cuota, Cheque propio, Débito automático y
futuras obligaciones.

## 17. Alerta

Aviso asociado al Vencimiento: anticipación, fecha/estado de atención o
reprogramación. No reemplaza ni modifica la verdad financiera del
Vencimiento.

## 18. Archivos

Los archivos de Movimientos son registros independientes y múltiples
cuando corresponda. Facturas pertenecen al Movimiento; comprobantes de
pago al Pago; documentación societaria a Empresa/entidad
correspondiente.

## 19. Baja lógica

Tablas maestras usan baja lógica por defecto. Los inactivos se conservan
porque pueden participar en historia. No duplicar un equivalente
inactivo: reactivar cuando corresponda.

## 20. Exportación

La importación reconstruye relaciones mediante mapas de IDs
originales→nuevos. Deben incluirse activos e inactivos y todos los
archivos vinculados. El formato lleva versión.

## 21. Preparación futura

El modelo no debe impedir Giras/Rendiciones, Registro/Rendición del
vendedor, clientes, saldo a favor, órdenes de pago, autorizaciones,
conciliaciones, contabilidad, multimoneda ni nuevos medios/impuestos.

------------------------------------------------------------------------

## Alertas y múltiples orígenes

Alerta no debe depender exclusivamente de Movimiento.

La arquitectura deberá permitir que una Alerta esté originada por
distintos tipos de compromiso económico.

Fuentes previstas:

-   Movimiento.
-   Cuota de Plan de Pago.
-   Cheque propio.
-   Cheque de tercero en cartera.
-   e-Cheq propio.
-   e-Cheq de tercero en cartera.
-   otros compromisos futuros.

La implementación deberá evitar una relación rígida que obligue a crear
un sistema de Alertas separado para cada origen.

### Cliente y Cartera de Cheques / e-Cheqs

`Cliente` será un ABM mínimo, perteneciente a Empresa y relacionado con
Centro Operativo. Su objetivo inicial no es modelar ventas ni cobranzas,
sino identificar de manera simple de quién se recibió un valor y
facilitar su localización ante un rechazo. Datos mínimos previstos:

-   Empresa.
-   Centro Operativo.
-   N.º de cliente manual.
-   Nombre / Razón social.
-   Dirección.
-   Celular.
-   Teléfono.
-   Activo.

El ingreso de un cheque/e-Cheq de tercero comienza cuando el valor entra
en poder de la Empresa. OrdenaClick no necesita modelar la venta o
cobranza externa que lo originó.

La Cartera deberá conservar, como mínimo:

-   Empresa.
-   Cliente y, por relación, Centro Operativo de origen.
-   instrumento: Cheque o e-Cheq.
-   origen: Propio o Tercero cuando corresponda.
-   condición de circulación: A la orden / No a la orden.
-   tipo: Común / Diferido.
-   banco y número.
-   importe.
-   fecha de emisión.
-   fecha de acreditación cuando corresponda.
-   estado real del instrumento.
-   comprobante/imagen y observaciones cuando correspondan.
-   relación eventual con Pago.
-   datos históricos de salida por depósito u otro destino.
-   relación con Vencimientos y Alertas.

Un cheque/e-Cheq de tercero ingresado queda en Cartera como valor
disponible sin Pago asociado.

La condición de circulación determina su disponibilidad:

-   Cheque a la orden: puede depositarse en cuenta propia o utilizarse
    en un Pago mediante endoso/entrega.
-   Cheque no a la orden: no puede endosarse ni cederse; no es
    seleccionable para Pago y sólo puede salir de Cartera mediante
    depósito en cuenta propia.
-   e-Cheq a la orden: puede depositarse o utilizarse en Pago mediante
    endoso.
-   e-Cheq no a la orden: puede depositarse o utilizarse en Pago
    mediante cesión; no debe tratarse como endoso.

Estar `EnCartera` no implica por sí solo estar disponible para pagar. La
disponibilidad debe derivarse en backend de Empresa, origen, estado,
tipo de instrumento y condición de circulación.

La fecha de acreditación inicia la atención del valor. La ventana de
Cartera es de 30 días corridos. Si continúa pendiente al agotarse, el
valor pasa a vencido para gestión y aparece en
`Próximos Vencimientos → Vencidos`.

La llegada de una fecha no modifica automáticamente hechos financieros
como depósito, cobro o utilización en un Pago.

Los cheques/e-Cheqs propios no son activos de Cartera: se emiten como
medio de pago y deben conservar un registro histórico separado de
instrumentos propios emitidos. Pueden coexistir en una Orden de Pago con
valores de terceros, pero su origen y procedimiento son distintos.

El rechazo se diseñará posteriormente. La hipótesis de trabajo es
preservar intacto el instrumento original y generar un nuevo hecho
relacionado cuando corresponda, contemplando deuda reabierta, gastos,
Pago original y eventual Nota de Débito/punto de venta/número. No se
implementará una solución provisoria antes de estudiar los casos.
------------------------------------------------------------------------

## Invariantes de edición y eliminación

`AplicacionPago` es además de la base del saldo la frontera histórica
del Movimiento.

``` text
sin AplicacionPago histórica -> estructura editable
con AplicacionPago histórica -> estructura congelada
                               + factura/archivo editable
                               + forma prevista editable
                               + nuevos Pagos contra saldo
```

La condición se evalúa sobre datos persistidos al iniciar la operación.
Los Pagos nuevos de esa misma edición no son historia previa.

Un Pago es un hecho financiero independiente. Su corrección no debe
reescribir silenciosamente historia aplicada: se elimina/revierte de
forma controlada cuando sea seguro y se registra el Pago correcto cuando
corresponda.

Baja física de Movimiento: - cero `AplicacionPago`: permitida por error
de carga; - una o más `AplicacionPago`: prohibida.

No existen reglas distintas por efectivo, transferencia, tarjeta,
cheque/e-Cheq, retención o débito automático para decidir la baja del
Movimiento.

Después de retirar una aplicación deben recalcularse total aplicado,
saldo, estado financiero, Vencimiento y Alertas. No debe quedar un
Vencimiento/Alerta reflejando un estado financiero anterior.
