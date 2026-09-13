# FLUJO_NAVEGACION.md — Cómo se mueve el usuario

## 1. Regla central
La navegación es parte de la arquitectura. No se considera correcto un módulo que “funciona” si rompe el origen, pierde el estado del usuario o lo obliga a reconstruir una carga.

## 2. Entrada
```text
OrdenaClick
└── Login
    └── Selección de Rol
```

Roles previstos: Administrador, Colaborador, Contable/Contador y Legal/Abogado. Además existen Modificar datos personales, Volver a roles y Cerrar sesión según contexto.

## 3. Administrador
```text
ADMINISTRADOR
├── Alta nueva empresa
├── Seleccionar Empresa
│   └── Empresa seleccionada
│       ├── REGISTROS
│       │   ├── Comprobantes
│       │   ├── Obligaciones
│       │   ├── Carga Planificada
│       │   ├── Registrar Pago
│       │   └── Modificar / Eliminar
│       ├── Dashboard
│       ├── Próximos Vencimientos
│       ├── Reportes
│       ├── Estado de Resultados
│       ├── Balance
│       ├── ABMs
│       │   ├── Centros Operativos
│       │   ├── Recursos Operativos
│       │   │   ├── Personas
│       │   │   ├── Vehículos
│       │   │   ├── Inmuebles
│       │   │   ├── Equipos
│       │   │   └── Otros
│       │   ├── Tipos de Gastos
│       │   │   ├── Proveedores relacionados
│       │   │   └── Cuenta Contable (futuro)
│       │   ├── Proveedores
│       │   └── Plan Contable
│       ├── Configuración
│       │   ├── Modificar Empresa
│       │   └── Designar Colaboradores
│       ├── Cambiar Empresa
│       └── Volver a inicio
├── Volver a roles
└── Cerrar sesión
```

## 4. Colaborador
Trabaja únicamente sobre empresas aceptadas/asignadas. Su navegación empresarial conserva REGISTROS y los ABM necesarios. Dashboard, vencimientos, reportes, resultados, balance y ABM adicionales dependen de permisos. Configuración estructural de empresa debe permanecer oculta cuando corresponda.

## 5. Contable
Trabaja sobre empresas que lo hayan contratado/asignado. Comparte la estructura general de empresa, con visibilidad determinada por permisos y futuras capacidades contables. Plan Contable, Estado de Resultados, Balance e imputaciones forman parte de la evolución prevista.

## 6. Legal
Perfil futuro. Debe trabajar sobre empresas asignadas y funciones legales, sin romper el patrón común de selección de rol/empresa/origen.

## 7. REGISTROS — objetivo Beta
Todo este bloque debe cerrar su circuito:
```text
REGISTROS
├── Comprobantes
├── Obligaciones
├── Carga Planificada
├── Registrar Pago
└── Modificar / Eliminar
```
Cada pantalla debe poder llamar a los ABM necesarios y regresar correctamente.

## 8. Comprobantes
Flujo conceptual:
```text
Datos del gasto
→ [Guardar] o [Cargar pago] o [Convertir a plan] o [Cancelar]
```
Datos del gasto incluye Tipo de Gasto, Proveedor, Centro Operativo, Recurso Operativo, comprobante, fecha, descripción, importes, impuestos/percepciones, total y archivo/factura.

Guardar permite Movimiento sin Pago. Cargar pago despliega el bloque financiero. Convertir a plan trabaja sobre el saldo restante y no pierde pagos previos.

En Comprobantes, Carga Planificada y edición directa del Movimiento, el Pago aplicado sólo puede ser nulo, parcial o exacto respecto del saldo pendiente actual. Si supera ese saldo, el usuario debe utilizar el circuito general **Registrar Pago**.

## 9. Obligaciones

Flujo conceptual pendiente de desarrollo:

```text
OBLIGACIÓN / LIQUIDACIÓN
Concepto (Sueldos / Aportes y Cont. / VEP - Impuestos / Tasas y otros)
Organismo / beneficiario
Período
Referencia
Centro Operativo (cuando corresponda)
Importe
Vencimiento
Forma de pago
```

Obligaciones constituye un circuito separado de Comprobantes para no forzar datos documentales propios de una factura cuando no correspondan. Por el momento permanecerá visible como módulo **En desarrollo**.

## 10. ABM invocado desde `[+]`
```text
Carga en curso
→ [+] junto a un selector
→ ABM correspondiente
→ alta/edición
→ volver al origen exacto
→ restaurar valores ya cargados
→ refrescar selector
→ seleccionar registro recién creado
```
No debe confundirse con abrir el mismo ABM desde el menú.

## 11. Pago
Registrar Pago debe permitir encontrar el Movimiento/obligación correspondiente y aplicar uno o varios medios. Los componentes del Pago no deben alterar la navegación ni perder lo ya cargado.

Este es también el circuito para registrar un Pago cuyo importe real supera el saldo de un único Movimiento. Debe permitir distribuir el Pago entre varios Movimientos y, cuando exista un remanente no aplicado, conservarlo a cuenta según la política financiera correspondiente.

La distribución nunca autoriza que una `AplicacionPago` individual supere el saldo pendiente de su destino.

## 12. Próximos Vencimientos
La campanita/llamador dirige a Próximos Vencimientos. Esta vista consume Vencimientos abiertos y distingue próximos, hoy y vencidos. Una vista de Alerta puede ser una presentación especial, no una fuente financiera distinta.

## 13. Navegación visual
Sidebar y menú operativo deben conservar jerarquía y contexto. Como mejora futura, ambos podrán tener scroll independiente para evitar que la botonera lateral desaparezca cuando el contenido operativo es largo.

## 14. Cierre de sesión y cambios de contexto
Cambiar Empresa debe invalidar el contexto/temporizadores de la empresa anterior. Volver a roles regresa a selección de rol. Cerrar sesión vuelve al ingreso inicial y no debe dejar información sensible accesible.

---

## Próximos Vencimientos

Navegación:

Operativo
→ Próximos Vencimientos

El módulo tendrá como selector principal:

    Alertas | Hoy | Esta semana | Rango de fechas

"Alertas" muestra los compromisos que requieren atención de acuerdo con la
política correspondiente a cada origen.

No equivale a "Hoy + 3 días".

El futuro Llamador de OrdenaClick navegará directamente a:

Operativo
→ Próximos Vencimientos
→ Alertas

La vista Alertas seguirá siendo accesible manualmente aunque el usuario haya
cerrado o abierto previamente el Llamador.