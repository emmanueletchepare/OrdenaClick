# TODO.md --- Qué falta y qué queremos agregar

## 1. BETA --- PRIORIDAD ABSOLUTA

Objetivo: circuito completo y estable de **REGISTROS**.

### 1.1 Cerrar flujos

-   [ ] Comprobantes de punta a punta.
-   [ ] Carga Planificada de punta a punta.
-   [ ] Registrar Pago de punta a punta.
-   [ ] Modificar / Eliminar con reglas financieras e históricas
    correctas.
-   [ ] Múltiples pagos por Movimiento.
-   [ ] Pagos parciales y saldo pendiente común.
-   [ ] Centralizar validación: nueva aplicación \<= saldo pendiente
    actual.
-   [ ] Aplicar esa validación en Comprobantes, edición y futura Carga
    Planificada.
-   [ ] Registrar Pago: distribuir un Pago entre múltiples Movimientos.
-   [ ] Registrar Pago: conservar remanente no aplicado a cuenta cuando
    corresponda.
-   [ ] Conversión a Plan respetando pagos previos.
-   [ ] Reversión/eliminación de Pago sin romper historia.
-   [ ] Registro real de débitos automáticos.
-   [ ] Vencimientos generados/actualizados desde la fuente financiera
    correcta.
-   [ ] Próximos Vencimientos consumiendo fuente común.
-   [ ] Alertas/llamador sin duplicar la lógica financiera.

### 1.2 ABM requeridos por REGISTROS

-   [ ] Verificar uno por uno apertura desde menú.
-   [ ] Verificar apertura desde `[+]`.
-   [ ] Conservar formulario llamador.
-   [ ] Volver al origen exacto.
-   [ ] Seleccionar automáticamente el alta nueva.
-   [ ] Edición integrada.
-   [ ] Baja lógica + reactivación.
-   [ ] Validaciones de pertenencia a Empresa.
-   [ ] Uniformidad visual.
-   [ ] Completar ABM necesarios para medios de pago (cuentas, tarjetas,
    bancos, etc.).

### 1.3 Seguridad antes de servidor/Beta

-   [ ] Revisar configuración de producción.
-   [ ] HTTPS.
-   [ ] Cookies/sesiones/CSRF seguras.
-   [x] SECRET_KEY fuera del código: entorno o configuración privada de
    instalación, sin fallback inseguro.
-   [ ] DEBUG desactivado.
-   [ ] ALLOWED_HOSTS/orígenes correctos.
-   [ ] Permisos por Empresa/rol/capacidad en backend.
-   [ ] Evitar IDOR/acceso cruzado entre empresas.
-   [ ] Validar uploads y acceso a archivos privados.
-   [ ] Backups cifrados/seguros y prueba de restauración.
-   [ ] Logging sin secretos/datos sensibles innecesarios.
-   [ ] Auditoría de operaciones críticas.
-   [ ] Dependencias y despliegue actualizados.
-   [ ] Estrategia de recuperación ante fallos.

### Seguridad de instalación ya implementada

-   [x] Perfil Desarrollador reservado a superusuarios.
-   [x] Configuración privada global fuera del repositorio para secretos
    de instalación.
-   [x] Prioridad `ORDENACLICK_SECRET_KEY` del entorno sobre
    configuración privada.
-   [x] Arranque bloqueado si no existe una `SECRET_KEY` válida.
-   [x] Rotación controlada de `SECRET_KEY` con confirmación, `POST`,
    CSRF, estado de reinicio pendiente y bloqueo de una segunda
    rotación.
-   [x] No exposición de `SECRET_KEY` al navegador ni a logs.
-   [x] `LOGIN_URL` configurado al login real de OrdenaClick.
-   [x] Tests específicos de seguridad del Perfil Desarrollador y
    servicio de rotación.
-   [ ] Definir almacenamiento privado definitivo y ACL/permisos de la
    cuenta de servicio para producción.
-   [x] Configurar credenciales ARCA de Homologación desde el Perfil
    Desarrollador.
-   [x] Configurar credenciales ARCA de Producción de forma separada.
-   [x] Implementar servicio ARCA/WSAA con TA reutilizable y renovación
    segura.
-   [x] Implementar autocompletado de Cliente por CUIT usando ARCA, sin
    bloquear la carga manual cuando ARCA no esté disponible.

### 1.4 Suscripciones

-   [ ] Definir matriz Persona / Intermedio / Empresas.
-   [ ] Implementar capacidades habilitables sin cambiar el modelo de
    datos.
-   [ ] Upgrade sin pérdida/migración destructiva.
-   [ ] Definir comportamiento ante vencimiento/suspensión sin destruir
    datos.
-   [ ] Separar autenticación de habilitación comercial.

### 1.5 Testing Beta

-   [ ] Tests de servicios financieros.
-   [ ] Tests de permisos y aislamiento por Empresa.
-   [ ] Tests de idas/vueltas de ABM.
-   [ ] Tests de pago parcial/múltiple/plan.
-   [ ] Tests de vencimientos/alertas.
-   [ ] Tests de exportar/importar Empresa.
-   [ ] Pruebas reales con datos representativos.

## 2. DEUDA TÉCNICA QUE SE CORRIGE PROGRESIVAMENTE

-   [ ] Extraer JavaScript inline existente cuando se toque cada
    pantalla.
-   [ ] Extraer CSS inline existente cuando se toque cada pantalla.
-   [ ] No incorporar JavaScript inline nuevo. Todo comportamiento nuevo
    debe vivir en archivos `.js` externos.
-   [ ] No incorporar CSS inline nuevo salvo excepción mínima,
    justificada y documentada. Todo estilo nuevo debe reutilizar las
    clases globales o vivir en archivos `.css` externos.
-   [ ] Mantener las pantallas nuevas dentro del lenguaje visual oscuro
    de OrdenaClick, reutilizando componentes y patrones existentes.
-   [ ] Reducir templates monolíticos.
-   [ ] Separar `views.py` por dominio cuando sea conveniente.
-   [ ] Mover reglas reutilizables a `services/`.
-   [ ] Eliminar duplicaciones de cálculo de saldo/vencimientos.
-   [ ] Agregar/mejorar docstrings.
-   [ ] Revisar comentarios importantes antes de limpiar código.

## 3. POST-BETA CERCANO

-   [ ] Dashboard.
-   [ ] Reportes con filtros.
-   [ ] Deudas pendientes.
-   [ ] Mejorar Próximos Vencimientos.
-   [ ] Estado de Resultados.
-   [ ] Plan Contable.
-   [ ] Balance.
-   [ ] Perfil Colaborador completo y permisos configurables.
-   [ ] Perfil Contable.
-   [ ] Perfil Legal.
-   [ ] Conciliaciones bancarias/tarjetas.
-   [ ] Configuración guiada inicial de Empresa.

## 4. FUNCIONES FUTURAS YA DEFINIDAS

-   [ ] Listado/cartera de cheques y e-Cheqs.
-   [ ] Agenda.
-   [ ] Orden de Pago.
-   [ ] Autorización de operaciones.
-   [ ] Gestión/Agenda de Claves con diseño seguro.
-   [ ] Ver inactivos y reactivar en ABM.
-   [ ] Buscador dinámico en listados/tarjetas de todos los ABM.
-   [ ] Scroll independiente entre sidebar y menú operativo.
-   [ ] Registro/Rendición del vendedor.
-   [x] ABM de Clientes.
-   [ ] Gestión avanzada de saldos a favor/a cuenta y su compensación
    posterior.
-   [ ] Multimoneda, tipos de cambio y conversiones.
-   [ ] Notificaciones móviles.
-   [ ] Nuevos impuestos, retenciones y medios de pago.
-   [ ] Calificación de colaboradores/contadores/abogados.
-   [ ] Giras/Rendiciones cuando se defina su alcance.

## 5. EXPORTAR / IMPORTAR EMPRESA

-   [ ] Mantener cobertura completa a medida que aparecen modelos.
-   [ ] Versionar formato.
-   [ ] Mapear IDs al importar.
-   [ ] Incluir inactivos e históricos.
-   [ ] Incluir archivos.
-   [ ] Resolver traslado seguro de información cifrada sin exportar la
    clave maestra.
-   [ ] Compatibilidad con backups anteriores.

## 6. DECISIONES PENDIENTES

-   [ ] Reglas exactas de ejercicio cerrado.
-   [ ] Fórmula/configuración definitiva de intereses por mora.
-   [ ] Reglas definitivas de multimoneda.
-   [ ] Alcance final de Carga Planificada.
-   [ ] Matriz detallada de capacidades por suscripción.
-   [ ] Matriz detallada de permisos por rol.

### Obligaciones / Liquidaciones

-   [ ] Diseñar el modelo definitivo de Obligaciones sin forzarlo dentro
    de la estructura documental de una factura.
-   [ ] Implementar circuito de Obligaciones separado de Comprobantes.
-   [ ] Conceptos iniciales: Sueldos / Aportes y Contribuciones / VEP -
    Impuestos / Tasas y otros.
-   [ ] Definir entidad y ABM para Organismo / beneficiario.
-   [ ] Definir reglas de Período y Referencia según tipo de obligación.
-   [ ] Definir cuándo corresponde Centro Operativo.
-   [ ] No exigir Recurso Operativo cuando no tenga sentido económico.
-   [ ] Integrar Obligaciones con Pago, AplicaciónPago, Vencimiento y
    Alertas.
-   [ ] Definir reglas particulares de duplicidad para cada tipo de
    obligación.

### Alertas / Próximos Vencimientos

-   [ ] Crear servicio común para determinar Alertas vigentes.
-   [ ] Implementar política inicial de obligaciones: 3 días antes +
    vencidas pendientes.
-   [ ] Incorporar filtro Alertas en Próximos Vencimientos.
-   [ ] Mantener reglas temporales fuera del JavaScript.
-   [ ] Agregar tests de Alertas.
-   [ ] Diseñar control segmentado reutilizable para botoneras
    superiores.
-   [ ] Aplicar control segmentado a Próximos Vencimientos.
-   [ ] Evaluar luego su aplicación a la botonera de Registros.
-   [ ] Implementar Cartera de Cheques / e-Cheqs.
-   [ ] Incorporar política de Cartera: fecha de acreditación + ventana
    de 30 días corridos.
-   [ ] Testear específicamente los límites de los 30 días.
-   [ ] Implementar Llamador de OrdenaClick después de estabilizar la
    vista Alertas.

## Caja --- Cartera --- Gestión Administrativa --- Órdenes de Pago

### Principios de esta etapa

-   [ ] Implementar en este orden funcional: **Ingreso → Caja/Cartera →
    Disponibilidad → Gestión Administrativa → Traslados internos → Orden
    de Pago**.
-   [ ] No comenzar Orden de Pago antes de que OrdenaClick conozca qué
    dinero/valores ingresaron, dónde están, quién puede utilizarlos y
    cuáles están disponibles.
-   [ ] Mantener la complejidad en backend y una interfaz simple para el
    usuario.
-   [ ] Conservar la composición de las pantallas financieras aprobadas
    y adaptarlas al tema oscuro, colores y componentes de OrdenaClick.
-   [ ] No duplicar contabilidad ni cuentas corrientes del sistema de
    gestión externo.
-   [ ] Toda operación financiera sensible debe validarse en backend. El
    frontend nunca constituye una barrera de seguridad.
-   [ ] Diseñar el circuito para servidor y acceso multiusuario seguro.
-   [ ] Aplicar aislamiento por Empresa y, cuando corresponda, por
    Centro Operativo/Caja. Cambiar un ID o URL nunca debe permitir
    acceso cruzado.
-   [ ] Usar POST/CSRF para escrituras y contemplar transacciones,
    concurrencia, doble clic/reintentos e idempotencia.
-   [ ] Registrar auditoría suficiente de operaciones y transiciones
    financieras.
-   [ ] No borrar ni reescribir silenciosamente historia financiera.

### Clientes relacionados con Caja

-   [x] ABM mínimo de Clientes implementado.
-   [x] Flujo contextual `[+]` implementado.
-   [ ] Normalizar presentación del N.º Cliente a cuatro cifras:
    `1 → 0001`, `25 → 0025`.
-   [ ] Revisar reactivación: validar CUIT, no sobrescribir historia
    automáticamente y permitir elegir recuperación histórica o datos
    actuales.
-   [ ] ARCA puede asistir, pero no decidir ni sobrescribir
    automáticamente.
-   [ ] Cliente será opcional como procedencia de valores recibidos.
-   [ ] La ubicación/custodia de un cheque no se deduce del Cliente.
-   [ ] Todo selector asociado a ABM debe conservar el patrón `[+]`.

### 1. Entrada de recursos / Cobranza

-   [ ] Crear base de Caja vinculada a Empresa y Centro Operativo,
    preparada para múltiples Cajas futuras sin sobrediseñar la Beta.
-   [ ] Implementar Nueva Cobranza como ingreso único de recursos.
-   [ ] Registrar fecha, referencia, vendedor opcional, total declarado,
    efectivo y detalle de cheques físicos.
-   [ ] Admitir efectivo ARS y USD como saldos separados.
-   [ ] Carga rápida por cheque: número, banco, acreditación,
    vencimiento e importe.
-   [ ] Mostrar conciliación: total declarado vs. efectivo + cheques y
    diferencia.
-   [ ] Definir si una cobranza con diferencia puede guardarse pendiente
    o debe bloquearse.
-   [ ] El cheque cargado en la cobranza debe crear su valor de Cartera
    en la misma operación.
-   [ ] Cartera es consecuencia del ingreso; no una segunda carga.
-   [ ] Cliente opcional en el cheque recibido.
-   [ ] No modelar la venta/cuenta corriente externa que originó la
    cobranza.

### 2. Caja y disponibilidad

-   [ ] Caja representa custodia y movimiento financiero físico.
-   [ ] Mostrar efectivo disponible por Caja/Centro y moneda.
-   [ ] Mantener cheques físicos individualizados y asociados a su
    custodia real.
-   [ ] Implementar Cartera física con estados y filtros.
-   [ ] Definir estados definitivos de valores físicos antes de
    implementar salidas.
-   [ ] Un valor reservado no puede ofrecerse a otra OP ni traslado.
-   [ ] Mantener historial del destino del valor.
-   [ ] Diseñar salida por depósito en Cuenta Bancaria propia.
-   [ ] Incorporar condición de circulación: A la orden / No a la orden.
-   [ ] Determinar disponibilidad en backend según Empresa, Caja/Centro,
    origen, estado, instrumento y condición.

### 3. Cartera electrónica y Gestión Administrativa

-   [ ] Implementar e-Cheqs de terceros separados de la custodia física.
-   [ ] Permitir estado financiero disponible y Gestión Administrativa
    pendiente simultáneamente.
-   [ ] Implementar Gestión Administrativa separada de Caja.
-   [ ] e-Cheq recibido: Gestión Pendiente → Gestionada.
-   [ ] Permitir devolver e-Cheq y excluirlo de disponibilidad,
    resolviendo reservas previas.
-   [ ] Registrar usuario y fecha de confirmación de gestión.
-   [ ] Registrar transferencias recibidas con Gestión Administrativa
    pendiente sin convertirlas en Caja física.
-   [ ] Incorporar alertas de gestiones pendientes.
-   [ ] Integrar Cartera con Vencimientos/Alertas según política
    definitiva.
-   [ ] Testear límites de la ventana temporal de alertas.

### 4. Traslados internos entre Cajas

-   [ ] Implementar Traslado Interno con Caja origen y destino.
-   [ ] Permitir efectivo y cheques físicos seleccionados
    individualmente.
-   [ ] Reservar recursos al preparar traslado.
-   [ ] Despacho: Disponible origen → Reservado → En tránsito.
-   [ ] Destino debe revisar antes de incorporar a disponibilidad.
-   [ ] Permitir aceptación total o parcial.
-   [ ] Permitir rechazo individual de cheques con motivo.
-   [ ] Definir diferencias/rechazo parcial de efectivo.
-   [ ] Un rechazo permanece ligado al traslado hasta
    devolución/resolución.
-   [ ] Preservar cadena de custodia.
-   [ ] e-Cheqs no se trasladan físicamente entre Cajas.

### 5. Disponibilidad bancaria informada

-   [ ] Implementar disponible bancario informado como apoyo, no
    conciliación exacta.
-   [ ] Registrar importe, usuario y fecha/hora de actualización.
-   [ ] No bloquear automáticamente transferencias por saldo informado
    insuficiente.
-   [ ] Mantenerlo separado de Caja física y Cartera.

### 6. Orden de Pago

-   [ ] Implementar OP después de estabilizar ingreso, disponibilidad,
    cartera y traslados.
-   [ ] Una OP preparada no es todavía un evento financiero definitivo.
-   [ ] Medios: Efectivo; Cheques de terceros; e-Cheqs de terceros;
    Transferencia; Depósito; Cheques propios a emitir; e-Cheqs propios a
    emitir.
-   [ ] Terceros ya existen y se reservan; propios nacen como
    instrumentos pendientes de emisión.
-   [ ] Instrumento propio pendiente: importe + acreditación prevista;
    completar número/datos al emitir.
-   [ ] No generar obligación/alerta de instrumento propio en etapa de
    propuesta.
-   [ ] Al confirmar emisión real, crear obligación/reminder.
-   [ ] Preparación colaborativa: las OP pendientes pertenecen al flujo
    de la Empresa, no a una persona.
-   [ ] Usuario autorizado puede confirmar componentes dentro de su
    alcance.
-   [ ] Guardar quién confirmó cada componente y cuándo.
-   [ ] Confirmar significa ejecución/preparación real, no sólo
    visualización.
-   [ ] Valores de terceros seleccionados: Disponible → Reservado.
-   [ ] Liberar reserva al cancelar/reemplazar antes de ejecución.
-   [ ] Definir estados definitivos de OP y componentes.
-   [ ] Con todos los componentes confirmados, marcar lista para
    revisión/cierre y notificar al creador.
-   [ ] Definir alternativa si el creador está ausente, desactivado o
    sin permisos.
-   [ ] Cierre definitivo actualiza movimientos, documentos, carteras,
    alertas y auditoría.
-   [ ] Diseñar reversión/cancelación parcial sin destruir historia.
-   [ ] Proteger reservas, confirmaciones y cierre con transacciones y
    validación de estado.

### 7. Jerarquía y permisos

-   [ ] Jerarquía: **Administrador general de la empresa / Administrador
    de sucursal / Colaborador en general**.
-   [ ] La jerarquía define alcance máximo; los permisos definen
    acciones dentro del alcance.
-   [ ] Administrador general: alcance Empresa y vista consolidada.
-   [ ] Administrador de sucursal: alcance Centro/sucursal habilitado y
    sus Cajas/operaciones.
-   [ ] Colaborador: acciones sólo por permisos funcionales explícitos.
-   [ ] Un colaborador administrativo no necesita ver saldos globales.
-   [ ] No confiar en botones ocultos para autorización.
-   [ ] No rigidizar `Usuario = Centro`; permitir ampliar alcance en el
    futuro.

### 8. Seguridad, integridad y servidor

-   [ ] Secretos, certificados, claves y credenciales fuera de frontend,
    `static`, `media` y Git.
-   [ ] Producción exclusivamente bajo HTTPS.
-   [ ] Cookies seguras (`Secure`, `HttpOnly`, `SameSite` apropiado),
    CSRF y hosts/orígenes permitidos.
-   [ ] Autorizar cada objeto por usuario, Empresa, Centro/Caja, permiso
    y estado.
-   [ ] Evitar IDOR y acceso cruzado mediante IDs manipulados.
-   [ ] Usar transacciones/bloqueo o validación de concurrencia en
    reservas, traslados, confirmaciones y cierres.
-   [ ] Una pantalla desactualizada no puede sobrescribir verdad del
    servidor.
-   [ ] Proteger contra duplicación por doble clic, retry o reenvío.
-   [ ] Documentos/descargas finales bajo autorización backend.
-   [ ] Logs sin secretos ni datos sensibles innecesarios.
-   [ ] Tests de aislamiento Empresa/Centro/Caja, permisos, concurrencia
    y transiciones inválidas.
-   [ ] Considerar cada nuevo modelo relacionado con Empresa para
    exportación/importación.

### 9. Pendientes de definición antes de cada bloque

-   [ ] Estados exactos de cheques físicos de terceros.
-   [ ] Estados exactos de e-Cheqs de terceros.
-   [ ] Estados exactos de instrumentos propios.
-   [ ] Estados exactos de OP y componentes.
-   [ ] Estados exactos de Traslado Interno, rechazo parcial y
    devolución.
-   [ ] Momento exacto en que cada medio afecta Caja/Cartera.
-   [ ] Reglas de cancelación/reversión.
-   [ ] Datos obligatorios de cada instrumento.
-   [ ] Tratamiento definitivo de cheque/e-Cheq rechazado.
-   [ ] Tratamiento de depósitos físicos.
-   [ ] Actualización del disponible bancario informado.
-   [ ] Granularidad de permisos Beta bajo las tres jerarquías.
-   [ ] Cierre de OP cuando el creador no esté disponible.
-   [ ] Contenido del documento final de OP.
-   [ ] Política de alertas por estado.
-   [ ] Regla de cobranza con diferencia.
-   [ ] Filtros de OP pendientes y Gestión Administrativa.
-   [ ] Una Caja por Centro en Beta vs. múltiples Cajas futuras.
