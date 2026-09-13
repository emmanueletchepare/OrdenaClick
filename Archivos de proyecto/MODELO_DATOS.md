# MODELO_DATOS.md — Organización de la información

## 1. Regla general
Los datos se diseñan para conservar historia y permitir crecimiento sin migraciones destructivas por cambio de plan.

## 2. Jerarquía principal
```text
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
Contiene datos generales, fiscales, contacto, autoridades y configuraciones. Su entorno incluye documentación societaria, ejercicios, centros, recursos, bancos, cuentas bancarias, tarjetas, proveedores, tipos de gasto, relaciones y datos operativos/financieros.

## 4. Ejercicio
Todo Movimiento debe quedar asociado a Empresa y Ejercicio. Cerrar un ejercicio no elimina historia. Las restricciones exactas sobre ejercicio cerrado siguen siendo una decisión funcional a terminar.

## 5. Movimiento
Representa el hecho económico/documental. Debe conservar como mínimo:
- Empresa y Ejercicio.
- Tipo de Gasto.
- Proveedor.
- Centro Operativo histórico.
- Recurso Operativo histórico.
- Fecha de registro y vencimiento cuando corresponda.
- Tipo/número de comprobante.
- Descripción.
- Neto gravado, no gravado/exento.
- IVA discriminado.
- Recargos/intereses propios del comprobante.
- Redondeos.
- Percepciones.
- Total.
- Archivo/factura.
- Estado, observaciones, moneda y auditoría.

Estados previstos: Pendiente, Parcial, Pagado, Vencido, Cancelado.

## 6. Tipo de Gasto / Proveedor
Tipo de Gasto reemplaza conceptualmente al Rubro simple. Tipo de Gasto y Proveedor tienen relación muchos-a-muchos. Cuenta Contable puede mostrarse deshabilitada hasta desarrollar Plan Contable.

## 7. Centro y Recurso Operativo
Todo Recurso Operativo debe poder vincularse a Centro Operativo mediante asignación. Movimiento guarda el recurso y centro imputados al momento del hecho. Usuario y Recurso Operativo son entidades independientes.

## 8. Pago
Entidad independiente del Movimiento. Puede existir más de uno por Movimiento y combinar medios.

## 9. AplicacionPago
Une el Pago con el destino cancelado (Movimiento o Cuota según implementación). Conserva importe aplicado. Es la base para pagos parciales y múltiples.

```text
saldo = total_movimiento - suma_aplicaciones
```

Una nueva `AplicacionPago` sobre un Movimiento no puede superar el saldo pendiente actual de ese destino. Esta restricción es una regla de negocio del núcleo financiero y debe validarse en backend.

Un `Pago` puede tener un importe real superior al saldo de un Movimiento si se distribuye entre varios destinos o conserva un remanente a cuenta. Esto no habilita a sobreaplicar un Movimiento individual.

Los costos financieros, incluidos intereses por mora confirmados, se registran separados del importe aplicado.

## 10. Medios de pago
- Efectivo.
- Transferencia/Depósito.
- Tarjeta.
- Cheque/e-Cheq.
- Retención.
- Débito automático cuando se registre su impacto real.
Cada medio conserva sus datos específicos y su relación con Pago.

## 11. Tarjeta
Pertenece a Empresa. Mínimo: nombre, tipo crédito/débito, cuenta bancaria propia asociada y estado. En Beta no es necesario modelar plástico individual, titular, vencimiento o recurso asignado.

Una operación de crédito puede guardar importe aplicado, cuotas e intereses de financiación. Las cuotas de tarjeta no son Cuotas de PlanPago.

## 12. Cuenta Bancaria
Empresa, Banco, nombre, tipo, moneda, número, CBU, alias, activo/inactivo. Se relaciona con transferencias, cheques propios, tarjetas, débito automático y futuras conciliaciones.

## 13. Cheque / e-Cheq
Debe conservar datos del instrumento, banco, fechas, estado, pago relacionado y vencimiento cuando corresponda. Cheque propio emitido puede generar obligación futura. La cartera de valores recibidos es una función posterior.

## 14. Retención
Tipo, importe, comprobante/certificado y Pago relacionado. El importe aplicado mediante retención forma parte de la cancelación.

## 15. PlanPago y Cuota
Plan trabaja sobre saldo financiado, condiciones, tasa y cantidad de cuotas. Cuota conserva capital, interés, impuestos, vencimiento, punitorios, estado y pagos/comprobantes relacionados.

## 16. Vencimiento
Es la representación técnica de la obligación financiera abierta. Conserva origen, fecha, importe original, importe pendiente y estado. No desaparece por pasar la fecha.

Fuentes: Movimiento impago, Cuota, Cheque propio, Débito automático y futuras obligaciones.

## 17. Alerta
Aviso asociado al Vencimiento: anticipación, fecha/estado de atención o reprogramación. No reemplaza ni modifica la verdad financiera del Vencimiento.

## 18. Archivos
Los archivos de Movimientos son registros independientes y múltiples cuando corresponda. Facturas pertenecen al Movimiento; comprobantes de pago al Pago; documentación societaria a Empresa/entidad correspondiente.

## 19. Baja lógica
Tablas maestras usan baja lógica por defecto. Los inactivos se conservan porque pueden participar en historia. No duplicar un equivalente inactivo: reactivar cuando corresponda.

## 20. Exportación
La importación reconstruye relaciones mediante mapas de IDs originales→nuevos. Deben incluirse activos e inactivos y todos los archivos vinculados. El formato lleva versión.

## 21. Preparación futura
El modelo no debe impedir Giras/Rendiciones, Registro/Rendición del vendedor, clientes, saldo a favor, órdenes de pago, autorizaciones, conciliaciones, contabilidad, multimoneda ni nuevos medios/impuestos.

---

## Alertas y múltiples orígenes

Alerta no debe depender exclusivamente de Movimiento.

La arquitectura deberá permitir que una Alerta esté originada por distintos
tipos de compromiso económico.

Fuentes previstas:

- Movimiento.
- Cuota de Plan de Pago.
- Cheque propio.
- Cheque de tercero en cartera.
- e-Cheq propio.
- e-Cheq de tercero en cartera.
- otros compromisos futuros.

La implementación deberá evitar una relación rígida que obligue a crear un
sistema de Alertas separado para cada origen.

### Cartera de Cheques / e-Cheqs

La futura entidad de Cartera deberá conservar, como mínimo, los datos
necesarios para determinar:

- Empresa.
- instrumento.
- condición propio/tercero cuando corresponda.
- fecha de acreditación o disponibilidad.
- estado real del instrumento.
- fecha de depósito/cobro cuando ocurra.
- relación con Vencimientos y Alertas.

La llegada de una fecha no modifica automáticamente el estado financiero real
del cheque/e-Cheq.
