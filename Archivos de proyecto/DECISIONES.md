# DECISIONES.md — Decisiones importantes ya tomadas

## 1. Producto
1. La Beta es el primer objetivo.
2. La Beta se mide por flujos completos, especialmente todo **REGISTROS**, no por cantidad de pantallas.
3. OrdenaClick debe anticipar obligaciones, no sólo registrar pasado.
4. Próximos Vencimientos y Alertas son parte central.
5. Una sola arquitectura de datos debe servir desde uso simple hasta empresa compleja.

## 2. Suscripciones
6. Los planes habilitan capacidades.
7. Mejorar de plan no hace perder ni migrar destructivamente información.
8. Simplificar experiencia no significa simplificar/destruir estructura.
9. Autenticación y habilitación comercial son capas distintas.
10. Se trabajará conceptualmente con niveles Persona, Intermedio y Empresas; la matriz exacta queda por definir.

## 3. Seguridad
11. OrdenaClick se desplegará en servidor y la seguridad se considera en cada implementación.
12. Los backups son información sensible.
13. Secretos, claves maestras y credenciales de infraestructura no se exportan ni se guardan en texto plano.
14. Toda operación debe respetar aislamiento de Empresa, rol y capacidad.

## 4. Navegación y ABM
15. La navegación forma parte de la arquitectura.
16. Todo ABM debe funcionar desde menú y desde `[+]`.
17. Desde `[+]`: crear → volver → conservar formulario → seleccionar alta nueva.
18. Edición integrada, sin `prompt()`.
19. Baja lógica por defecto.
20. `PROTECT` antes que `CASCADE` en relaciones históricas/maestras.
21. Si existe equivalente inactivo, se reactiva en lugar de duplicar.
22. Baja física sólo en excepciones explícitas.
23. El lenguaje visual debe mantenerse uniforme.

## 5. Comprobantes y Obligaciones
24. Tipo de Gasto reemplaza conceptualmente al Rubro simple.
25. Tipo de Gasto y Proveedor tienen relación muchos-a-muchos.
26. “Relacionado con” pasa a llamarse Recurso Operativo.
27. Recurso Operativo se vincula a Centro Operativo.
28. Movimiento conserva Centro y Recurso históricos.
29. Usuario y Recurso Operativo son entidades independientes.
30. Archivos de Movimiento pueden ser independientes y múltiples.
31. Cuenta Contable queda visible/deshabilitada hasta Plan Contable.
32. Giras/Rendiciones no se implementan ahora, pero no deben quedar bloqueadas.
33. Registro, Pago y Plan son etapas relacionadas pero visualmente distintas.
34. El circuito actualmente denominado Carga Simple queda conceptualmente destinado a Comprobantes.
35. No todo Movimiento nace de una factura o comprobante con punto de venta y número.
36. Sueldos, aportes y contribuciones, VEP/impuestos, tasas y obligaciones similares tendrán un circuito separado denominado Obligaciones.
37. El circuito de Comprobantes conserva las validaciones documentales ya desarrolladas, incluyendo Proveedor, Tipo de Comprobante, Punto de Venta y Número cuando correspondan.
38. Obligaciones no debe forzar conceptos propios de una factura, como Proveedor, Punto de Venta, Número de Factura o Recurso Operativo cuando éstos no tengan sentido.
39. Obligaciones / Liquidaciones se diseñará inicialmente con los siguientes datos conceptuales:
    - Concepto: Sueldos / Aportes y Contribuciones / VEP - Impuestos / Tasas y otros.
    - Organismo / beneficiario.
    - Período.
    - Referencia.
    - Centro Operativo, cuando corresponda.
    - Importe.
    - Vencimiento.
    - Forma de pago.
40. Comprobantes y Obligaciones deben converger en el núcleo financiero común de Movimiento, Pago, AplicaciónPago, Vencimiento y Alerta cuando corresponda.
41. La definición definitiva del modelo de datos de Obligaciones queda pendiente; no se debe adaptar artificialmente el modelo de factura para implementarlo.

## 6. Núcleo financiero
34. Movimiento y Pago son hechos distintos.
35. Un Movimiento admite cero, uno o múltiples Pagos.
36. Un Pago puede combinar medios.
37. El saldo se determina por importes efectivamente aplicados.
38. Costos financieros no son importe aplicado.
39. Pago y sus aplicaciones conservan historia.
40. Vencimiento representa el compromiso; Alerta representa el aviso.
41. Una Alerta no modifica/elimina un Vencimiento.
42. Una obligación vencida sigue abierta mientras quede pendiente.
43. Plan de Pago trabaja sobre saldo restante y no reescribe el Movimiento original.
44. Las cuotas del Plan generan obligaciones propias.
45. La Beta opera en ARS, dejando el modelo preparado para multimoneda.

### Regla cerrada: aplicación máxima de un Pago

- El importe aplicado directamente a un Movimiento nunca puede superar su saldo pendiente actual.
- En Carga Simple, Carga Planificada y edición directa sólo se permiten aplicación nula, parcial o exacta.
- Si el Movimiento ya tiene Pagos históricos, una nueva aplicación se valida contra el saldo restante y no contra el total original.
- Los Pagos históricos no se reescriben silenciosamente durante la edición del Movimiento.
- Un Pago real superior al saldo de un Movimiento pertenece al circuito **Registrar Pago**, donde podrá distribuirse entre varios Movimientos y/o conservar un remanente a cuenta.
- No se genera automáticamente saldo a favor desde la carga o edición individual de un Movimiento.
- Débito automático conserva su excepción por mora: el importe real debitado puede superar el saldo, pero el importe aplicado al Movimiento no; la diferencia confirmada se registra como costo financiero.
- Esta regla se centraliza en backend/servicios y se reutiliza en todos los circuitos.

## 7. Exportación / Importación
46. Exportar Empresa debe producir una copia completa y portable.
47. Si eliminar+reimportar haría perder un dato, ese dato debe estar en el backup salvo exclusión documentada.
48. La importación no depende de conservar IDs físicos: usa mapas de IDs.
49. Activos e inactivos relevantes se exportan.
50. Toda entidad nueva de Empresa obliga a revisar exportación/importación.
51. El formato de backup debe estar versionado.

## 8. Arquitectura de código
52. No JavaScript inline nuevo.
53. No CSS inline nuevo como práctica normal.
54. Las reglas de negocio reutilizables se centralizan.
55. No duplicar cálculo financiero entre vistas.
56. Al tocar código viejo se extraen progresivamente JS/CSS y responsabilidades mal ubicadas.
57. La limpieza técnica acompaña el desarrollo sin desviar la Beta salvo seguridad/integridad.
58. Funciones relevantes deben tener docstrings y comentarios importantes no se eliminan sin entenderlos.

## 9. Futuro preservado
59. La arquitectura no debe bloquear Reportes, Estado de Resultados, Balance, Plan Contable, perfiles Contable/Legal, órdenes de pago, autorizaciones, agenda, cartera de cheques, conciliaciones, nuevos medios/impuestos, notificaciones móviles, multimoneda ni nuevos niveles de permisos.


---

## Decisión: Alertas no utilizará una regla temporal universal

Se decide que la condición para aparecer en Alertas será determinada por el
backend según el tipo de compromiso.

No se implementará en JavaScript una regla general del tipo:

    vencimiento <= hoy + 3 días

Motivo:

OrdenaClick tendrá distintas fuentes de Alertas con políticas temporales
diferentes.

Primera política:

- obligaciones económicas comunes: aviso desde 3 días antes del vencimiento.

Política prevista para Cartera:

- cheques/e-Cheqs de terceros: atención desde la fecha de acreditación durante
  una ventana de 30 días corridos;
- agotada esa ventana sin depósito/cobro, el valor pasa a vencido.

Consecuencia arquitectónica:

    fuentes económicas
          ↓
    servicios de vencimientos
          ↓
    políticas de alerta
          ↓
    Alertas
          ↓
    Próximos Vencimientos / Llamador

El frontend únicamente presenta el resultado.

## Decisión visual: controles segmentados

Las botoneras principales de selección dentro de un mismo módulo evolucionarán
hacia un control segmentado de aspecto compacto.

Referencia conceptual:

- contenedor único redondeado;
- opciones internas;
- una opción activa claramente destacada;
- opciones inactivas integradas al mismo control.

No se copiará la identidad visual de productos externos.

El componente deberá conservar la estética propia de OrdenaClick y podrá
reutilizarse inicialmente en:

- Registros:
  Carga Simple / Carga Planificada / Registrar Pago / Modificar-Eliminar.

- Próximos Vencimientos:
  Alertas / Hoy / Esta semana / Rango de fechas.