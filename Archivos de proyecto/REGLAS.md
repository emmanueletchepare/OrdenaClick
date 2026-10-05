# REGLAS.md --- Reglas obligatorias de desarrollo

## 1. Reglas no negociables

-   No JavaScript inline nuevo.
-   No CSS inline nuevo salvo excepción mínima y documentada.
-   No eliminar comentarios importantes.
-   Cada función nueva o modificada de relevancia debe tener docstring
    útil.
-   Mantener el estilo de código del proyecto.
-   Respetar siempre la arquitectura y la navegación.
-   No duplicar reglas de negocio.
-   Backend valida siempre; el frontend mejora UX pero no es autoridad.
-   Cambios de seguridad e integridad tienen prioridad sobre comodidad.
-   No introducir refactors masivos que desvíen la Beta sin necesidad
    real.
-   Código nuevo específico de un perfil debe organizarse en sus
    directorios propios de templates/CSS/JS cuando corresponda; lo
    compartido permanece separado y la migración del código existente es
    progresiva.

## 2. Regla de ABM

Todo ABM debe funcionar tanto desde el centro/menú de ABM como desde un
botón `[+]` de otro formulario.

**Apertura** - Desde menú. - Desde `[+]`.

**Cierre** - Si nació en menú, vuelve al menú/origen correspondiente. -
Si nació en `[+]`, vuelve exactamente al formulario llamador. - Conserva
el estado previo del formulario. - El registro recién creado queda
seleccionado automáticamente.

**Edición** - Sin `prompt()`. - La tarjeta/listado carga datos en el
formulario. - Guardar pasa a Actualizar. - Aparece Cancelar. - Cancelar
limpia y vuelve a Alta.

**Eliminación** - Confirmación previa. - Baja lógica por defecto. -
`PROTECT` antes que `CASCADE` para información histórica/maestra. - Baja
física solamente por decisión explícita y excepcional. - Validaciones de
negocio. - Refresco sin abandonar el ABM.

**Reactivación** - Si ya existe un registro equivalente inactivo, no
duplicarlo: reactivarlo cuando corresponda. - Debe existir una futura
función Ver inactivos / Reactivar.

**Visual** - Mismo lenguaje visual, botones, radios, tamaños, acordeones
y espaciados. - Bancos y Centros Operativos son referencias de
comportamiento consistente. - Buscador dinámico en listados de tarjetas
queda como mejora general.

## 3. Flujo `[+]` y navegación contextual apilable

Regla invariable para toda la aplicación: siempre que un formulario
permita elegir una entidad que posea ABM, el selector debe tener su
botón `[+]` con el mismo estilo y comportamiento contextual.

La navegación contextual debe ser **apilable**. Un ABM abierto desde un
`[+]` puede abrir otro ABM mediante otro `[+]`, y así sucesivamente.
Cada salto conserva un nivel independiente de contexto y cada retorno
restaura exactamente el nivel inmediatamente anterior (LIFO).

Cada nivel conserva como mínimo: pantalla/origen, valores y estado del
formulario, posición de scroll/ubicación visual, elemento que originó el
salto, información necesaria para reconstruir la pantalla y registro
creado/reactivado que deba seleccionarse al regresar.

``` text
formulario A
→ [+]
→ ABM B
→ [+]
→ ABM C
→ [+]
→ ABM D

volver → ABM C intacto y en la misma posición visual
volver → ABM B intacto y en la misma posición visual
volver → formulario A intacto y en la misma posición visual
```

Cuando un alta o reactivación nace de un selector, el registro
resultante debe quedar seleccionado automáticamente al volver.

Los ABM no deben codificar manualmente todos sus posibles orígenes. La
infraestructura común de navegación es responsable de apilar y restaurar
contexto. Las variables y funciones especiales de retorno por pantalla
son mecanismo heredado y deben migrarse progresivamente; sólo se
eliminan después de comprobar que ya no tienen consumidores.

Un botón de navegación normal de módulo no equivale a un retorno
contextual. Si una pantalla fue abierta mediante `[+]`, el retorno lo
determina la pila contextual.

## 4. Seguridad

-   Autorización por usuario + empresa + rol + capacidad.
-   Nunca confiar en parámetros del cliente para pertenencia.
-   Secretos y credenciales fuera del repositorio, `static/`, `media/`,
    JavaScript y backups de Empresa.
-   Los secretos globales de instalación pueden provenir del entorno o
    de configuración privada protegida fuera del repositorio; nunca debe
    existir un fallback inseguro incorporado al código.
-   Un secreto ya almacenado no se vuelve a mostrar en el frontend; se
    informa estado/origen y se permite reemplazo controlado cuando
    corresponda.
-   Las operaciones sensibles del Perfil Desarrollador requieren
    autenticación, superusuario validado en backend, `POST`, CSRF y
    errores controlados.
-   Contraseñas nunca en texto plano.
-   Backups tratados como información sensible.
-   Toda nueva entidad sensible debe evaluar cifrado, exposición,
    exportación, logs y permisos.
-   Desarrollador/superuser no habilita filtraciones entre empresas ni
    perfiles.
-   Aplicar protección CSRF, sesiones/cookies seguras, HTTPS y
    configuración segura de producción.
-   Errores no deben revelar secretos o datos de otras empresas.
-   Dependencias y despliegue deben mantenerse actualizados y revisados.

## 5. Datos e histórico

-   Información financiera/contable/histórica no se borra físicamente en
    operación normal.
-   No reconstruir historia usando relaciones maestras actuales.
-   Movimiento conserva centro/recurso históricos.
-   Factura/archivo del gasto pertenece al Movimiento.
-   Pago y Movimiento son entidades separadas.
-   Vencimiento y Alerta son conceptos separados.
-   Costos financieros y capital aplicado se guardan separados.
-   El importe aplicado directamente a un Movimiento nunca puede superar
    su saldo pendiente actual.
-   Carga Simple, Carga Planificada y edición directa sólo admiten
    aplicación nula, parcial o exacta.
-   Una nueva aplicación se valida contra el saldo pendiente actual, no
    contra el total original cuando existen Pagos previos.
-   Un Pago superior al saldo de un único Movimiento debe resolverse
    mediante Registrar Pago, distribuyéndolo entre destinos y/o dejando
    remanente a cuenta.
-   Ningún frontend puede autorizar una sobreaplicación que el backend
    no valide.
-   La excepción de Débito automático con mora separa importe debitado
    de importe aplicado: el costo financiero excedente no cancela
    capital.

## 6. Suscripciones

Las capacidades se habilitan/ocultan por lógica comercial. Cambiar de
plan no destruye ni migra historia. Nunca condicionar la integridad del
modelo a que una pantalla esté visible en un plan.

## 7. Exportación

Cada modelo nuevo/modificado relacionado con Empresa debe responder: 1.
¿Se exporta? 2. ¿Se importa? 3. ¿Tiene archivos? 4. ¿Qué relaciones se
reconstruyen? 5. ¿Contiene información sensible? 6. ¿Se conservan
inactivos? 7. ¿Afecta la versión o compatibilidad del formato de backup desde v1 en adelante?

## 8. Checklist para funcionalidad nueva

Antes de implementarla: 1. ¿Pertenece al entorno Empresa? 2. ¿Debe
conservar historia? 3. ¿Puede generar Vencimiento? 4. ¿Puede generar
Alerta? 5. ¿Tiene impacto contable futuro? 6. ¿Debe
exportarse/importarse? 7. ¿Usa baja lógica? 8. ¿Qué pasa si el cliente
crece? 9. ¿Qué plan/capacidad la habilita? 10. ¿Qué perfil puede
verla/usarla/modificarla? 11. ¿Acerca la Beta a estar usable? 12.
¿Agrega JS/CSS o lógica que debería extraerse a archivos/capas
correctas?

## 9. Método de trabajo al modificar código

Indicar archivo exacto, qué buscar y qué reemplazar/agregar. Si cambia
una función, trabajar con la función completa para evitar parches
ambiguos. Explicar brevemente el propósito. Tomar como patrón
componentes que ya funcionan antes de inventar otra solución.

------------------------------------------------------------------------

## Reglas de Alertas

1.  Una Alerta no crea una obligación.
2.  Una Alerta no modifica el Vencimiento real.
3.  Cancelar una Alerta no cancela el compromiso.
4.  Reprogramar una Alerta no cambia la fecha real del Vencimiento.
5.  Las reglas temporales de Alertas se calculan en backend.
6.  El JavaScript no debe duplicar políticas de vencimiento o alerta.
7.  Distintos tipos de compromiso pueden utilizar distintas políticas.
8.  Una obligación vencida pendiente no desaparece.
9.  El histórico debe conservarse.
10. El Llamador de OrdenaClick consume Alertas; no determina por sí
    mismo qué constituye una Alerta.

### Política inicial de obligaciones

Una obligación económica común pendiente comienza a requerir aviso tres
días antes de su vencimiento y continúa requiriendo atención mientras
permanezca pendiente.

### Política prevista de Cartera

Un cheque/e-Cheq de terceros disponible para depósito/cobro comienza a
alimentar Alertas desde su fecha de acreditación.

La ventana será de 30 días corridos.

La atención permanece vigente desde la fecha de acreditación y hasta
antes de cumplirse 30 días corridos. Si el valor continúa en Cartera al
agotarse esa ventana, pasa a vencido a efectos de gestión y debe
aparecer en `Próximos Vencimientos → Vencidos`.

La salida válida de Cartera cancela la condición de valor disponible,
pero no borra su historia. Esa salida puede producirse, según el
instrumento y su condición de circulación, por utilización en un
Pago/Orden de Pago o por depósito en una Cuenta Bancaria propia.

Los límites exactos de la ventana deberán probarse mediante tests
específicos.

------------------------------------------------------------------------

## Reglas obligatorias --- edición, Pagos y eliminación

### Sin Pagos históricos

-   Permitir edición estructural y uno o varios Pagos nuevos en el mismo
    `Guardar cambios`.
-   Si cambia el total, validar los Pagos contra el nuevo total backend.
-   La operación es atómica: un fallo no deja cambios ni Pagos
    parciales.

### Con Pagos históricos

-   Si existe `AplicacionPago` histórica, congelar estructura
    económica/documental.
-   Permitir únicamente factura/archivo, forma prevista/cuenta válida y
    nuevos Pagos contra saldo.
-   No congelar retroactivamente por Pagos nuevos de la misma petición.
-   Backend aplica la regla aunque el frontend deshabilite campos.
-   Para modificar el resto, primero eliminar/revertir todos los Pagos
    aplicados.

### Corrección de Pagos

-   Mostrar Pagos históricos y permitir gestionarlos desde la edición.
-   No modificar silenciosamente un Pago aplicado.
-   Corregir mediante eliminación/reversión controlada y nuevo Pago
    cuando corresponda.
-   Una operación rechazada no puede borrar parcialmente aplicaciones,
    componentes ni Pago.
-   Después de corregir, recalcular saldo, estado, Vencimiento y
    Alertas.

### Baja física de Movimiento

``` text
si existe AplicacionPago: no eliminar Movimiento
si no existe AplicacionPago: permitir baja física por error de carga
```

No crear reglas por medio de pago para esta decisión.

Requiere autenticación, Empresa autorizada, `POST`, CSRF,
`transaction.atomic()`, bloqueos necesarios, nueva comprobación de
aplicaciones y eliminación explícita de Alertas/Vencimientos derivados
antes del Movimiento. No usar `CASCADE` para simplificarla.

### Servidor y concurrencia

Toda funcionalidad financiera/destructiva nueva se diseña como si
OrdenaClick ya estuviera expuesto públicamente. No confiar en saldo,
estado, Empresa ni relaciones enviados por navegador; recalcular y
bloquear en backend cuando exista riesgo de competencia.
