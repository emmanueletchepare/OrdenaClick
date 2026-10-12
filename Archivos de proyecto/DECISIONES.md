# Nota de uso — 08/10/2026

Este documento conserva decisiones funcionales cerradas. No es un checklist
de estado de implementación.

Para saber qué está hecho y qué sigue, consultar `00_RUMBO_Y_ESTADO.md`,
`TODO.md` y `PRE_BETA.md`.

---

# DECISIONES.md --- Decisiones importantes ya tomadas

## 1. Producto

1.  La Beta es el primer objetivo.
2.  La Beta se mide por flujos completos, especialmente todo
    **REGISTROS**, no por cantidad de pantallas.
3.  OrdenaClick debe anticipar obligaciones, no sólo registrar pasado.
4.  Próximos Vencimientos y Alertas son parte central.
5.  Una sola arquitectura de datos debe servir desde uso simple hasta
    empresa compleja.

## 2. Suscripciones

6.  Los planes habilitan capacidades.
7.  Mejorar de plan no hace perder ni migrar destructivamente
    información.
8.  Simplificar experiencia no significa simplificar/destruir
    estructura.
9.  Autenticación y habilitación comercial son capas distintas.
10. Se trabajará conceptualmente con niveles Persona, Intermedio y
    Empresas; la matriz exacta queda por definir.

## 3. Seguridad

11. OrdenaClick se desplegará en servidor y la seguridad se considera en
    cada implementación.
12. Los backups son información sensible.
13. Secretos, claves maestras y credenciales de infraestructura no se
    exportan ni se guardan en texto plano.
14. Toda operación debe respetar aislamiento de Empresa, rol y
    capacidad.

## 4. Navegación y ABM

15. La navegación forma parte de la arquitectura.
16. Todo ABM debe funcionar desde menú y desde `[+]`.
17. Desde `[+]`: crear → volver → conservar formulario → seleccionar
    alta nueva.
18. Edición integrada, sin `prompt()`.
19. Baja lógica por defecto.
20. `PROTECT` antes que `CASCADE` en relaciones históricas/maestras.
21. Si existe equivalente inactivo, se reactiva en lugar de duplicar.
22. Baja física sólo en excepciones explícitas.
23. El lenguaje visual debe mantenerse uniforme.
24. La navegación contextual `[+]` es apilable: cada salto conserva su
    propio contexto y cada retorno restaura el nivel anterior en orden
    LIFO.
25. Cada contexto conserva formulario, estado, origen y posición visual;
    un alta/reactivación contextual selecciona automáticamente el
    registro resultante al regresar.
26. Los ABM no implementan retornos particulares para cada llamador. Se
    adopta una infraestructura común de pila contextual y los mecanismos
    heredados se retiran sólo después de migrar y probar sus
    consumidores.

## 5. Comprobantes y Obligaciones

24. Tipo de Gasto reemplaza conceptualmente al Rubro simple.
25. Tipo de Gasto y Proveedor tienen relación muchos-a-muchos.
26. "Relacionado con" pasa a llamarse Recurso Operativo.
27. Recurso Operativo se vincula a Centro Operativo.
28. Movimiento conserva Centro y Recurso históricos.
29. Usuario y Recurso Operativo son entidades independientes.
30. Archivos de Movimiento pueden ser independientes y múltiples.
31. Cuenta Contable queda visible/deshabilitada hasta Plan Contable.
32. Giras/Rendiciones no se implementan ahora, pero no deben quedar
    bloqueadas.
33. Registro, Pago y Plan son etapas relacionadas pero visualmente
    distintas.
34. El circuito actualmente denominado Carga Simple queda
    conceptualmente destinado a Comprobantes.
35. No todo Movimiento nace de una factura o comprobante con punto de
    venta y número.
36. Sueldos, aportes y contribuciones, VEP/impuestos, tasas y
    obligaciones similares tendrán un circuito separado denominado
    Obligaciones.
37. El circuito de Comprobantes conserva las validaciones documentales
    ya desarrolladas, incluyendo Proveedor, Tipo de Comprobante, Punto
    de Venta y Número cuando correspondan.
38. Obligaciones no debe forzar conceptos propios de una factura, como
    Proveedor, Punto de Venta, Número de Factura o Recurso Operativo
    cuando éstos no tengan sentido.
39. Obligaciones / Liquidaciones se diseñará inicialmente con los
    siguientes datos conceptuales:
    -   Concepto: Sueldos / Aportes y Contribuciones / VEP - Impuestos /
        Tasas y otros.
    -   Organismo / beneficiario.
    -   Período.
    -   Referencia.
    -   Centro Operativo, cuando corresponda.
    -   Importe.
    -   Vencimiento.
    -   Forma de pago.
40. Comprobantes y Obligaciones deben converger en el núcleo financiero
    común de Movimiento, Pago, AplicaciónPago, Vencimiento y Alerta
    cuando corresponda.
41. La definición definitiva del modelo de datos de Obligaciones queda
    pendiente; no se debe adaptar artificialmente el modelo de factura
    para implementarlo.

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
43. Plan de Pago trabaja sobre saldo restante y no reescribe el
    Movimiento original.
44. Las cuotas del Plan generan obligaciones propias.
45. La Beta opera en ARS, dejando el modelo preparado para multimoneda.

### Regla cerrada: aplicación máxima de un Pago

-   El importe aplicado directamente a un Movimiento nunca puede superar
    su saldo pendiente actual.
-   En Carga Simple, Carga Planificada y edición directa sólo se
    permiten aplicación nula, parcial o exacta.
-   Si el Movimiento ya tiene Pagos históricos, una nueva aplicación se
    valida contra el saldo restante y no contra el total original.
-   Los Pagos históricos no se reescriben silenciosamente durante la
    edición del Movimiento.
-   Un Pago real superior al saldo de un Movimiento pertenece al
    circuito **Registrar Pago**, donde podrá distribuirse entre varios
    Movimientos y/o conservar un remanente a cuenta.
-   No se genera automáticamente saldo a favor desde la carga o edición
    individual de un Movimiento.
-   Débito automático conserva su excepción por mora: el importe real
    debitado puede superar el saldo, pero el importe aplicado al
    Movimiento no; la diferencia confirmada se registra como costo
    financiero.
-   Esta regla se centraliza en backend/servicios y se reutiliza en
    todos los circuitos.

## 7. Exportación / Importación

46. Exportar Empresa debe producir una copia completa y portable.
47. Si eliminar+reimportar haría perder un dato, ese dato debe estar en
    el backup salvo exclusión documentada.
48. La importación no depende de conservar IDs físicos: usa mapas de
    IDs.
49. Activos e inactivos relevantes se exportan.
50. Toda entidad nueva de Empresa obliga a revisar
    exportación/importación.
51. El formato de backup debe estar versionado.

Decisiones cerradas para el primer formato estable:

-   El nuevo subsistema comienza directamente en **Backup Empresa v1**; no se
    soportarán ZIP legacy generados durante esta etapa de desarrollo previa a
    Beta.
-   Importar Empresa será un proceso guiado de restauración y puesta en marcha,
    no una restauración ciega.
-   El backup conserva historia, pero los datos operativos que puedan haber
    cambiado se confirman o ajustan durante el flujo de importación.
-   Los usuarios históricos no se eliminan por una importación. Se conserva su
    trazabilidad y se decide explícitamente quién continúa activo, quién queda
    inactivo y qué jerarquía vigente corresponde.
-   Los privilegios escritos en el ZIP son información histórica/de origen; no
    otorgan autorización automáticamente en destino.
-   El propietario de la Empresa restaurada no lo decide el backup.
-   Si ya existe una Empresa con el mismo CUIT, no se elimina antes de validar
    y planificar la restauración. La operación debe evitar estados parciales y
    permitir rollback ante fallas críticas.
-   La futura precarga de datos estándar de inicio es independiente del backup
    empresarial.
-   Queda como dirección futura evaluar un wizard similar para el alta inicial
    de Empresa, de modo que el usuario avance por pasos sin necesitar conocer
    de antemano toda la configuración requerida.

## 8. Arquitectura de código

52. No JavaScript inline nuevo.
53. No CSS inline nuevo como práctica normal.
54. Las reglas de negocio reutilizables se centralizan.
55. No duplicar cálculo financiero entre vistas.
56. Al tocar código viejo se extraen progresivamente JS/CSS y
    responsabilidades mal ubicadas.
57. La limpieza técnica acompaña el desarrollo sin desviar la Beta salvo
    seguridad/integridad.
58. Funciones relevantes deben tener docstrings y comentarios
    importantes no se eliminan sin entenderlos.

## 9. Usuarios, relaciones y roles multiempresa

59. La cuenta de usuario pertenece a OrdenaClick y puede existir sin Empresa.
60. Crear una Empresa convierte a ese usuario en fundador mediante `Empresa.propietario`; no se crea una asignación jerárquica duplicada para acreditar propiedad.
61. Un usuario puede vincularse con múltiples Empresas y tener roles distintos en cada una.
62. La jerarquía administrativa/operativa actual sigue siendo excluyente por Empresa: Administrador general, Administrador de Centro o Colaborador.
63. Contable y Legal son roles funcionales acumulables y pueden coexistir con una jerarquía; por ejemplo, Colaborador + Contable en la misma Empresa.
64. Administradores, Colaboradores, Contables y Legales se designan mediante solicitudes dirigidas a usuarios existentes.
65. Una solicitud pendiente no concede acceso. La relación nace únicamente cuando el destinatario la acepta.
66. El usuario resuelve solicitudes desde el perfil Relaciones.
67. Fundador y Administrador general pueden enviar solicitudes de relación para la Empresa; Administrador de Centro y Colaborador no obtienen esa capacidad por defecto.
68. El perfil Relaciones pertenece al usuario, no a una Empresa, y concentra solicitudes y vínculos.
69. Colaborador/Contable/Legal pueden ser internos o externos; esa condición no define permisos.
70. El futuro marketplace de disponibilidad, postulaciones, búsqueda, ranking, contratación, actividad y pagos estará separado del sistema de autorización.
71. Desarrollador sigue siendo un perfil global de instalación reservado a superusuario.
72. Las solicitudes pendientes son estado transitorio de la instalación y no forman parte del Backup Empresa ordinario; las relaciones activas sí deben tener política de export/import.

## 9. Futuro preservado

59. La arquitectura no debe bloquear Reportes, Estado de Resultados,
    Balance, Plan Contable, perfiles Contable/Legal, órdenes de pago,
    autorizaciones, agenda, cartera de cheques, conciliaciones, nuevos
    medios/impuestos, notificaciones móviles, multimoneda ni nuevos
    niveles de permisos.

------------------------------------------------------------------------

## Decisión: Alertas no utilizará una regla temporal universal

Se decide que la condición para aparecer en Alertas será determinada por
el backend según el tipo de compromiso.

No se implementará en JavaScript una regla general del tipo:

    vencimiento <= hoy + 3 días

Motivo:

OrdenaClick tendrá distintas fuentes de Alertas con políticas temporales
diferentes.

Primera política:

-   obligaciones económicas comunes: aviso desde 3 días antes del
    vencimiento.

Política prevista para Cartera:

-   cheques/e-Cheqs de terceros: atención desde la fecha de acreditación
    durante una ventana de 30 días corridos;
-   agotada esa ventana sin depósito/cobro, el valor pasa a vencido.

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

## Decisiones cerradas: Caja, Cartera y Orden de Pago

-   El ingreso de un cheque/e-Cheq de tercero comienza cuando el valor
    entra en poder de la Empresa; no se modelará la venta/cobranza
    externa de origen.
-   Se incorporará un ABM mínimo de Clientes relacionado con Centro
    Operativo, con N.º de cliente manual y datos básicos de
    identificación/contacto.
-   En formularios, Centro Operativo se elige antes que Cliente. El
    selector de Cliente tendrá `[+]` y respetará el flujo contextual
    estándar.
-   La regla `[+]` es universal: todo selector de una entidad con ABM
    debe ofrecer ese acceso contextual.
-   Cheques y e-Cheqs de terceros se mostrarán en listados
    diferenciados.
-   Todo cheque/e-Cheq distinguirá condición `A la orden` /
    `No a la orden`.
-   Cheque físico no a la orden: no puede endosarse ni cederse; sólo
    depósito en cuenta propia y nunca se ofrece como valor para Pago.
-   e-Cheq no a la orden: puede utilizarse mediante cesión, no mediante
    endoso.
-   e-Cheq a la orden: utilización mediante endoso.
-   La ventana de alerta de Cartera comienza en la fecha de acreditación
    y dura 30 días corridos; agotada sin salida, aparece como vencido en
    Próximos Vencimientos.
-   La salida de Cartera puede ser por utilización en Pago/Orden de Pago
    o por depósito en cuenta bancaria propia.
-   La Orden de Pago distinguirá valores de terceros de instrumentos
    propios. Los terceros ya existen en Cartera; los propios se emiten
    para el Pago.
-   En Orden de Pago, los e-Cheqs de terceros se agrupan operativamente
    en `Endosados` y `Cedidos`, manteniendo un total común de e-Cheqs.
-   Cheques y e-Cheqs propios emitidos tendrán registro histórico propio
    y procedimiento separado.
-   El circuito de rechazados se diseñará después, preservando la
    historia del cheque original y analizando deuda, gastos, Pago y
    documentación asociada antes de implementar.

## Decisión visual: controles segmentados

Las botoneras principales de selección dentro de un mismo módulo
evolucionarán hacia un control segmentado de aspecto compacto.

Referencia conceptual:

-   contenedor único redondeado;
-   opciones internas;
-   una opción activa claramente destacada;
-   opciones inactivas integradas al mismo control.

No se copiará la identidad visual de productos externos.

El componente deberá conservar la estética propia de OrdenaClick y podrá
reutilizarse inicialmente en:

-   Registros: Carga Simple / Carga Planificada / Registrar Pago /
    Modificar-Eliminar.

-   Próximos Vencimientos: Alertas / Hoy / Esta semana / Rango de
    fechas.

------------------------------------------------------------------------

## Decisiones cerradas --- edición, Pagos y eliminación

-   Sin `AplicacionPago` histórica, el Movimiento puede modificarse y
    recibir varios Pagos nuevos en un único `Guardar cambios`.
-   Si en esa operación cambia el total, la capacidad de aplicación usa
    el nuevo total validado.
-   Los Pagos nuevos todavía no persistidos no congelan retroactivamente
    esa misma edición.
-   Desde la primera aplicación histórica se congela la estructura
    económica/documental.
-   Con historia sólo se permite factura/archivo, forma prevista de
    pago/cuenta prevista y nuevos Pagos contra saldo.
-   Para modificar cualquier otro dato deben eliminarse/revertirse
    primero todos los Pagos aplicados.
-   Los Pagos históricos se gestionan desde la edición del Movimiento.
-   Un Pago aplicado no se modifica silenciosamente: la corrección se
    realiza mediante eliminación/reversión controlada y, cuando
    corresponda, un Pago nuevo.
-   La posibilidad de eliminar/revertir un Pago puede depender de
    consecuencias financieras posteriores de sus componentes.
-   Para eliminar un Movimiento sólo importa si existe `AplicacionPago`:
    con aplicaciones se rechaza; sin aplicaciones puede haber baja
    física por error de carga.
-   La baja física de Movimiento es una excepción explícita a la baja
    lógica general.
-   Operaciones financieras/destructivas nuevas: autenticación, Empresa
    autorizada, `POST`, CSRF, transacción, bloqueos de concurrencia,
    recálculo backend y errores controlados.

------------------------------------------------------------------------

## Decisiones cerradas --- Perfil Desarrollador y seguridad de instalación

-   El Perfil Desarrollador pertenece a la instalación de OrdenaClick y
    no a una Empresa.
-   Su acceso queda reservado a superusuarios y cada operación sensible
    vuelve a validar esa condición en backend.
-   La configuración técnica sensible global se mantiene fuera del
    repositorio, `static/`, `media/`, JavaScript y backups de Empresa.
-   `SECRET_KEY` se resuelve primero desde `ORDENACLICK_SECRET_KEY` del
    entorno y, si no existe, desde la configuración privada de la
    instalación. Si ninguna fuente existe, OrdenaClick no debe arrancar
    con una clave insegura incorporada al código.
-   Una `SECRET_KEY` administrada por variable de entorno tiene
    prioridad y no puede reemplazarse desde el Perfil Desarrollador.
-   La rotación privada de `SECRET_KEY` se genera exclusivamente en
    servidor, nunca devuelve el secreto al navegador y requiere
    reiniciar Django para entrar en vigencia.
-   Mientras la clave privada persistida difiera de la clave activa del
    proceso existe un reinicio pendiente y se bloquea una segunda
    rotación.
-   La interfaz debe advertir que una rotación puede invalidar sesiones
    y otros datos firmados con la clave anterior.
-   Las operaciones sensibles del Perfil Desarrollador utilizan
    autenticación, superusuario validado en backend, `POST`, CSRF y
    errores controlados sin exposición de secretos.
-   `LOGIN_URL` apunta al login propio de OrdenaClick para que una
    sesión ausente o invalidada no termine en `/accounts/login/`.
-   Las credenciales globales de integraciones futuras, incluida ARCA,
    pertenecen a esta misma configuración de instalación y no a Empresa.
-   La organización nueva específica por perfil comienza separando
    `templates/usuarios/desarrollador/`, `static/css/desarrollador/` y
    `static/js/desarrollador/`; la migración de áreas existentes se hará
    progresivamente y sin desviar la Beta.

------------------------------------------------------------------------

## Decisiones cerradas --- Base Server, superusuario y protección del producto

- Antes de retomar desarrollo funcional intensivo se cierra `BASE_SERVER_SEGURIDAD.md`.
- El objetivo formal es **BASE ARQUITECTÓNICA Y DE SEGURIDAD PARA SERVER: CERRADA**.
- El superusuario conserva por ahora acceso global a Empresas.
- Esa excepción no concede privilegios a ningún otro perfil.
- El Perfil Desarrollador evolucionará hacia un panel global de plataforma.
- Ese panel administrará habilitación, inhabilitación, suspensión, capacidades y suscripción sin depender de operar directamente la base.
- El superusuario podrá exportar una copia autorizada de Empresa.
- Se desarrollará posteriormente un resumen administrativo de Empresa.
- La política futura sobre acceso directo del superusuario a pantallas operativas se revisará cuando exista ese panel.
- Producción utilizará PostgreSQL; SQLite queda para desarrollo local.
- Archivos de Empresa serán privados por defecto en producción.
- Configuración de producción se separará de desarrollo.
- La lógica diferencial permanecerá principalmente en backend; no se adoptará ofuscación como sustituto de seguridad o protección comercial.

## Decisiones cerradas para Caja operativa — 11/10/2026

- CAJA antes de REGISTROS. No se implementan Ordenes de Compra; se implementaran Ordenes de Pago despues de cerrar disponibilidad real.
- Movimientos simples de entrada/salida de efectivo sin OP. Cada uno pertenece a Caja concreta y conserva historial; saldo derivado de `MovimientoCaja` y prohibicion de egresos superiores al efectivo disponible en la moneda.
- El selector «Todas» es solo vista para Administrador general (y propietario/superusuario). Para alta/egreso se exige una sola Caja autorizada; Administrador de Centro ve y opera exclusivamente su Centro. Colaborador no opera Caja por jerarquia.
- Pendientes bancarios son gestion administrativa, independientes de saldo de Caja. Cualquier usuario autorizado del Centro puede resolverlos; no dependen de Nicolas. Si siguen pendientes interviene administrador. Confirmar resolucion requiere comprobar y, si falta, emitir recibo en el sistema externo.
- Envio de efectivo o cheques entre Cajas no es egreso manual comun: tiene origen, destino, despacho, transito, recepcion, diferencia y eventual caso en Auditoria. Preservar versiones de emisor/receptor.
- Acuerdo de descubierto (importe, vigencia, vencimiento) se configura en el ABM de Cuentas Bancarias con alertas de vencimiento.
- Orden de Pago lista para cerrar solo cuando cada salida fue confirmada por responsable; notificar al creador. Cierre definitivo tras revision.
- Una sola persona con autorizaciones suficientes puede realizar varias acciones, sin exigencias artificiales de actores distintos. No aflojar controles de seguridad por simplicidad visual.

## Decisiones Caja — ajuste visual y pendientes bancarios (11/10/2026)
- Historial de `MovimientoCaja` en **Movimientos del día** del dashboard, con Hoy/Rango y Caja/Todas conforme permisos backend; la pantalla Movimiento de Caja queda como formulario de alta. No duplicar ni reescribir hechos financieros.
- Para Caja 2, el Colaborador no adquiere Centro ni capacidades de Caja por su jerarquía. Un administrador general **autorizará explicitamente Centros de gestión administrativa bancaria** por colaborador. Esta autorización permitirá ver/resolver pendientes de aplicación del Centro, no saldos ni Caja. Permiso nuevo pendiente de implementación y de pruebas adversariales.

## Decisiones aprobadas tras experiencia OLAFIL — Caja, bancos y OP (11/10/2026)
- **UI Caja:** filtros Desde/Hasta contiguos, tabla con encabezados y columnas alineadas como en Registros, acciones icono Editar/Eliminar en extremo derecho. En Movimiento de Caja queda el formulario; los listados se consultan desde «Movimientos del día» con Hoy/Rango y Caja/Todas. «Eliminar» un hecho financiero significa anulación con contraasiento y motivo, no borrar registros; las cobranzas mantienen circuito propio.
- **Pendientes bancarios:** quien observa transferencias, depósitos y e-Cheqs en banco los registra como trabajo de comprobar el recibo/imputación externa. Una fila puede tener Centro identificado o estar por identificar. No depende de Nicolás; cualquier usuario autorizado puede verificar y marcar resuelto con referencia. Si sigue pendiente, un administrador exige acción. Registro/gestión no altera Caja ni duplica la Cobranza.
- **Permiso por Centro:** admin general/propietario/superusuario administran toda la Empresa; administrador de Centro sólo su Centro; colaborador sólo Centros habilitados individualmente por admin general. Esta capacidad no concede Caja ni saldos. Cambios de permisos deben auditarse y no viajar como autorizaciones en Backup v1.
- **Caja interna:** envíos simples como salida con destino, custodia en tránsito, recepción verificada. Discrepancias conservan declaraciones de emisor/receptor, generan caso en Auditoría y exigen resolución; nunca acreditar valor no recibido.
- **Bancos:** acuerdos de descubierto (importe/vigencia/vencimiento/alerta) se configurarán en ABM Cuentas Bancarias. Posición bancaria informada, acreditaciones pendientes y descubierto no equivalen a saldo contable seguro.
- **OP:** sólo después de Caja/Cartera y Pago individual. Reserva de terceros, preparación por responsables de efectivo/cheques/e-Cheqs propios, confirmación real de cada salida; con todas confirmadas pasa a «Lista para cerrar», aviso al creador y cierre posterior autorizado. En empresa unipersonal la misma persona puede completar varias acciones, sin rol ficticio.
- **Cartera:** cheques físicos por Caja y e-Cheqs electrónicos separados; estados y trazabilidad de depósitos, reservas, endosos, cesiones, rechazo posterior y custodia. Cheque físico «No a la orden» no utilizable en Pago.


## Caja 2 — revisión de pendientes globales (12/10/2026)

La definición vigente es: **todos los pendientes bancarios y e-Cheqs son
visibles globalmente dentro de la Empresa activa** para los usuarios con
capacidad de gestión; no se asigna Centro al detectar el ingreso. Al
confirmar en modal, el usuario identifica cliente, elige Centro de su
alcance y registra la verificación/recibo externo; desde allí es resuelto
**propiedad operativa de ese Centro**. Una Empresa activa nunca muestra
otra ni ofrece selector de Empresa. La carga de depósitos/transferencias y
la de e-Cheqs tienen formularios separados, filas temporales editables y
Guardado atómico de lote. E-Cheq `A la orden` por defecto; `No a la orden`
disponible. Permisos de colaboradores van en Configuración de Empresa,
no en bandeja; no conceden Caja. `Volver` lleva al menú de origen. Consulte
`ORDENACLICK_DISENO_CAJA_CARTERAS_OP.md` para el detalle completo.
