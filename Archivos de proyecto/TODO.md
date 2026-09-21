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
-   [x] Configuración privada global fuera del repositorio para secretos de
    instalación.
-   [x] Prioridad `ORDENACLICK_SECRET_KEY` del entorno sobre configuración
    privada.
-   [x] Arranque bloqueado si no existe una `SECRET_KEY` válida.
-   [x] Rotación controlada de `SECRET_KEY` con confirmación, `POST`, CSRF,
    estado de reinicio pendiente y bloqueo de una segunda rotación.
-   [x] No exposición de `SECRET_KEY` al navegador ni a logs.
-   [x] `LOGIN_URL` configurado al login real de OrdenaClick.
-   [x] Tests específicos de seguridad del Perfil Desarrollador y servicio
    de rotación.
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

## Caja --- Cheques y e-Cheqs

-   [x] Diseñar e implementar ABM mínimo de Clientes:

    -   [x] Empresa.
    -   [x] Centro Operativo.
    -   [x] N.º de cliente manual.
    -   [x] Nombre / Razón social.
    -   [x] Dirección.
    -   [x] Celular.
    -   [x] Teléfono.
    -   [x] Activo.
    -   Considerar Cliente en exportación/importación por Empresa.

-   [x] Aplicar al selector de Cliente el flujo contextual estándar:
    formulario → \[+\] → ABM → crear → volver → conservar formulario →
    seleccionar nuevo elemento.

-   [ ] Normalizar la presentación del N.º Cliente a cuatro cifras:
    `1 → 0001`, `25 → 0025`, manteniendo la identidad por Empresa +
    Centro Operativo + N.º Cliente.

-   [ ] Revisar el flujo de reactivación de Clientes:

    -   comprobar la correspondencia del CUIT antes de reactivar;
    -   si los datos actuales no corresponden con el registro histórico,
        no sobrescribir automáticamente;
    -   solicitar al usuario si desea recuperar los datos históricos o
        reemplazarlos con los datos actuales;
    -   definir expresamente qué campos se conservan o reemplazan;
    -   ARCA puede asistir en la consulta del CUIT, pero no debe decidir ni
        sobrescribir automáticamente información histórica.

-   [ ] Mantener como regla general que todo selector asociado a un ABM
    tenga su botón \[+\] con el estilo y flujo contextual definidos para
    OrdenaClick.

-   [ ] Diseñar e implementar Caja → Cheques de terceros.

-   [ ] Diseñar e implementar Caja → e-Cheqs de terceros.

-   [ ] Registrar el ingreso del valor sin intentar modelar la venta,
    cobranza u operación externa que le dio origen.

-   [ ] Relacionar cada cheque/e-Cheq de tercero con el Cliente del que
    fue recibido y, mediante éste, con su Centro Operativo.

-   [ ] Al ingresar un cheque/e-Cheq de tercero, incorporarlo a Cartera
    como valor disponible y sin Pago asociado.

-   [ ] Integrar cheques/e-Cheqs de terceros con Vencimientos y Alertas.

-   [ ] Para valores de terceros en Cartera, iniciar la atención desde
    la fecha de acreditación/disponibilidad y mantener la ventana de
    alerta correspondiente hasta antes de los 30 días corridos.

-   [ ] Si el cheque permanece pendiente y alcanza su vencimiento,
    reflejarlo en Próximos Vencimientos → Vencidos.

-   [ ] Diseñar salida de Cartera por utilización en Pago / Orden de
    Pago.

-   [ ] Diferenciar visual y operativamente Cheque de e-Cheq al elegir
    valores para una Orden de Pago:

    -   cheque físico: retirar/buscar el valor;
    -   e-Cheq: realizar endoso mediante el banco.

-   [ ] Diseñar salida de Cartera por depósito en Cuenta Bancaria
    propia.

-   [ ] Registrar históricamente el destino del valor:

    -   utilizado en Pago;
    -   depositado en banco;
    -   otros destinos futuros que correspondan.

-   [ ] Diseñar seguimiento separado de Cheques y e-Cheqs propios
    emitidos desde Pagos.

-   [ ] Diseñar posteriormente el circuito completo de cheque/e-Cheq
    rechazado. No implementar todavía una solución provisoria.

-   [ ] Evaluar para cheque rechazado la creación de un nuevo registro
    que preserve intacta la historia del cheque original.

-   [ ] Analizar los distintos casos de rechazo antes de definir modelo
    definitivo, incluyendo:

    -   reaparición de deuda con proveedor;
    -   importe original del cheque;
    -   gastos derivados del rechazo;
    -   relación con el Pago original;
    -   relación con el cheque original;
    -   eventual Nota de Débito;
    -   punto de venta y número de comprobante;
    -   impacto en Vencimientos y Alertas.

-   [ ] Una vez implementada Cartera, retomar eliminar_pago_movimiento()
    y definir correctamente la devolución a Cartera de un cheque/e-Cheq
    de tercero cuando se elimina o revierte el Pago que lo utilizó.

-   [ ] Incorporar condición de circulación en cheque/e-Cheq:

    -   A la orden.
    -   No a la orden.

-   [ ] Aplicar disponibilidad para Pago según instrumento y condición:

    -   Cheque a la orden: Pago/endoso o depósito.
    -   Cheque no a la orden: sólo depósito en cuenta propia; excluir de
        Pago.
    -   e-Cheq a la orden: Pago mediante endoso o depósito.
    -   e-Cheq no a la orden: Pago mediante cesión o depósito.

-   [ ] Determinar en backend la disponibilidad de Cartera para Pago
    usando Empresa, origen Tercero, estado EnCartera, instrumento y
    condición de circulación.

-   [ ] No pedir Endoso/Cesión al usuario cuando la condición del e-Cheq
    ya determina automáticamente el procedimiento.

-   [ ] Aplicar las mismas reglas de disponibilidad tanto en Orden de
    Pago como al generar un Pago directamente desde una
    factura/Movimiento.

-   [ ] Diseñar Orden de Pago con agrupación operativa:

    -   Efectivo.
    -   Retenciones.
    -   Total Cheques de terceros + detalle.
    -   Total e-Cheqs de terceros + detalle separado en Endosados y
        Cedidos.
    -   Cheques propios emitidos.
    -   e-Cheqs propios emitidos.
    -   Total general de la Orden de Pago.

-   [ ] Mantener separados conceptualmente los valores de terceros y
    propios:

    -   terceros: ya existen en Cartera y se seleccionan;
    -   propios: se emiten para la Orden de Pago/Pago.

-   [ ] Diseñar registro histórico y consulta de Cheques propios
    emitidos.

-   [ ] Diseñar registro histórico y consulta de e-Cheqs propios
    emitidos.
