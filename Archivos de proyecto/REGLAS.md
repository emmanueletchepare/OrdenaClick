# REGLAS.md — Reglas obligatorias de desarrollo

## 1. Reglas no negociables
- No JavaScript inline nuevo.
- No CSS inline nuevo salvo excepción mínima y documentada.
- No eliminar comentarios importantes.
- Cada función nueva o modificada de relevancia debe tener docstring útil.
- Mantener el estilo de código del proyecto.
- Respetar siempre la arquitectura y la navegación.
- No duplicar reglas de negocio.
- Backend valida siempre; el frontend mejora UX pero no es autoridad.
- Cambios de seguridad e integridad tienen prioridad sobre comodidad.
- No introducir refactors masivos que desvíen la Beta sin necesidad real.

## 2. Regla de ABM
Todo ABM debe funcionar tanto desde el centro/menú de ABM como desde un botón `[+]` de otro formulario.

**Apertura**
- Desde menú.
- Desde `[+]`.

**Cierre**
- Si nació en menú, vuelve al menú/origen correspondiente.
- Si nació en `[+]`, vuelve exactamente al formulario llamador.
- Conserva el estado previo del formulario.
- El registro recién creado queda seleccionado automáticamente.

**Edición**
- Sin `prompt()`.
- La tarjeta/listado carga datos en el formulario.
- Guardar pasa a Actualizar.
- Aparece Cancelar.
- Cancelar limpia y vuelve a Alta.

**Eliminación**
- Confirmación previa.
- Baja lógica por defecto.
- `PROTECT` antes que `CASCADE` para información histórica/maestra.
- Baja física solamente por decisión explícita y excepcional.
- Validaciones de negocio.
- Refresco sin abandonar el ABM.

**Reactivación**
- Si ya existe un registro equivalente inactivo, no duplicarlo: reactivarlo cuando corresponda.
- Debe existir una futura función Ver inactivos / Reactivar.

**Visual**
- Mismo lenguaje visual, botones, radios, tamaños, acordeones y espaciados.
- Bancos y Centros Operativos son referencias de comportamiento consistente.
- Buscador dinámico en listados de tarjetas queda como mejora general.

## 3. Flujo `[+]`
Regla invariable:
```text
formulario
→ [+]
→ ABM
→ crear
→ volver
→ conservar formulario
→ seleccionar nuevo elemento
```

## 4. Seguridad
- Autorización por usuario + empresa + rol + capacidad.
- Nunca confiar en parámetros del cliente para pertenencia.
- Secretos y credenciales fuera del repositorio.
- Contraseñas nunca en texto plano.
- Backups tratados como información sensible.
- Toda nueva entidad sensible debe evaluar cifrado, exposición, exportación, logs y permisos.
- Desarrollador/superuser no habilita filtraciones entre empresas ni perfiles.
- Aplicar protección CSRF, sesiones/cookies seguras, HTTPS y configuración segura de producción.
- Errores no deben revelar secretos o datos de otras empresas.
- Dependencias y despliegue deben mantenerse actualizados y revisados.

## 5. Datos e histórico
- Información financiera/contable/histórica no se borra físicamente en operación normal.
- No reconstruir historia usando relaciones maestras actuales.
- Movimiento conserva centro/recurso históricos.
- Factura/archivo del gasto pertenece al Movimiento.
- Pago y Movimiento son entidades separadas.
- Vencimiento y Alerta son conceptos separados.
- Costos financieros y capital aplicado se guardan separados.
- El importe aplicado directamente a un Movimiento nunca puede superar su saldo pendiente actual.
- Carga Simple, Carga Planificada y edición directa sólo admiten aplicación nula, parcial o exacta.
- Una nueva aplicación se valida contra el saldo pendiente actual, no contra el total original cuando existen Pagos previos.
- Un Pago superior al saldo de un único Movimiento debe resolverse mediante Registrar Pago, distribuyéndolo entre destinos y/o dejando remanente a cuenta.
- Ningún frontend puede autorizar una sobreaplicación que el backend no valide.
- La excepción de Débito automático con mora separa importe debitado de importe aplicado: el costo financiero excedente no cancela capital.

## 6. Suscripciones
Las capacidades se habilitan/ocultan por lógica comercial. Cambiar de plan no destruye ni migra historia. Nunca condicionar la integridad del modelo a que una pantalla esté visible en un plan.

## 7. Exportación
Cada modelo nuevo/modificado relacionado con Empresa debe responder:
1. ¿Se exporta?
2. ¿Se importa?
3. ¿Tiene archivos?
4. ¿Qué relaciones se reconstruyen?
5. ¿Contiene información sensible?
6. ¿Se conservan inactivos?
7. ¿Afecta compatibilidad con backups anteriores?

## 8. Checklist para funcionalidad nueva
Antes de implementarla:
1. ¿Pertenece al entorno Empresa?
2. ¿Debe conservar historia?
3. ¿Puede generar Vencimiento?
4. ¿Puede generar Alerta?
5. ¿Tiene impacto contable futuro?
6. ¿Debe exportarse/importarse?
7. ¿Usa baja lógica?
8. ¿Qué pasa si el cliente crece?
9. ¿Qué plan/capacidad la habilita?
10. ¿Qué perfil puede verla/usarla/modificarla?
11. ¿Acerca la Beta a estar usable?
12. ¿Agrega JS/CSS o lógica que debería extraerse a archivos/capas correctas?

## 9. Método de trabajo al modificar código
Indicar archivo exacto, qué buscar y qué reemplazar/agregar. Si cambia una función, trabajar con la función completa para evitar parches ambiguos. Explicar brevemente el propósito. Tomar como patrón componentes que ya funcionan antes de inventar otra solución.

---

## Reglas de Alertas

1. Una Alerta no crea una obligación.
2. Una Alerta no modifica el Vencimiento real.
3. Cancelar una Alerta no cancela el compromiso.
4. Reprogramar una Alerta no cambia la fecha real del Vencimiento.
5. Las reglas temporales de Alertas se calculan en backend.
6. El JavaScript no debe duplicar políticas de vencimiento o alerta.
7. Distintos tipos de compromiso pueden utilizar distintas políticas.
8. Una obligación vencida pendiente no desaparece.
9. El histórico debe conservarse.
10. El Llamador de OrdenaClick consume Alertas; no determina por sí mismo qué
    constituye una Alerta.

### Política inicial de obligaciones

Una obligación económica común pendiente comienza a requerir aviso tres días
antes de su vencimiento y continúa requiriendo atención mientras permanezca
pendiente.

### Política prevista de Cartera

Un cheque/e-Cheq de terceros disponible para depósito/cobro comienza a
alimentar Alertas desde su fecha de acreditación.

La ventana será de 30 días corridos.

Agotada esa ventana sin haberse producido el depósito/cobro correspondiente,
el instrumento se considera vencido a efectos de gestión.

Los límites exactos de la ventana deberán probarse mediante tests específicos.

