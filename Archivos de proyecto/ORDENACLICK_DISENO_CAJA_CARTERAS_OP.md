# Alcance dentro del proyecto — 08/10/2026

Este documento sigue siendo la fuente funcional de verdad para Caja, Cartera,
Gestión Administrativa y Orden de Pago.

No reemplaza la prioridad Beta general definida en `00_RUMBO_Y_ESTADO.md`.
La base de Caja/Cobranza debe preservarse, pero la evolución hacia Cartera y
Orden de Pago no debe desplazar el cierre prioritario de REGISTROS.

---

# OrdenaClick --- Caja, Carteras, Gestión Administrativa y Órdenes de Pago

**Versión:** 2.0\
**Estado:** definición funcional base.\
**Fecha:** 22/09/2026.

> **Fuente funcional de verdad de esta etapa.** Pagos simples, planes de
> pago y futuros medios de cancelación deben apoyarse sobre este
> circuito y no crear una segunda lógica de disponibilidad de fondos.

## 1. Principio rector

**Complejidad por debajo, sencillez arriba.**

OrdenaClick debe funcionar tanto cuando una persona realiza toda la
operación como cuando intervienen varias personas y sucursales.

No se modelan nombres o puestos concretos. Se modelan Empresa, Centros
Operativos, Cajas, usuarios, jerarquía, permisos, recursos, estados,
acciones y trazabilidad.

**Primero ingresa el dinero/valor → se identifica dónde está y si está
disponible → recién después puede utilizarse para pagar.**

## 2. Separaciones fundamentales

**Centro Operativo ≠ Caja.** El Centro representa una unidad
física/organizativa. La Caja representa custodia y movimientos de
recursos físicos.

**Caja ≠ Gestión Administrativa.** Caja/Cartera responde "qué recursos
tenemos, dónde están y en qué estado". Gestión Administrativa responde
"qué operación recibida todavía requiere una acción administrativa".

**Cartera física ≠ Cartera electrónica.** Los cheques físicos tienen
ubicación/custodia. Los e-Cheqs son electrónicos y no se fuerzan dentro
de una Caja física.

**Jerarquía ≠ permisos.** La jerarquía determina el alcance máximo; los
permisos determinan qué puede hacer el usuario dentro de ese alcance.

## 3. Jerarquía

### Administrador general de Empresa

Alcance potencial sobre toda la Empresa, Centros, Cajas y visión
consolidada, siempre sujeto a permisos funcionales.

### Administrador de sucursal

Alcance limitado a su Centro Operativo/sucursal. Según permisos puede
operar Caja, cobranzas, cartera física, traslados, gestión
administrativa y participar en OP.

### Colaborador

Sin autoridad administrativa implícita. Sus capacidades dependen de
permisos. Puede, por ejemplo, resolver tareas administrativas sin ver
saldos de Caja.

Esto evita crear roles rígidos como cajero, tesorero, junior, bancos,
etc.

## 4. Flujo general canónico

``` text
INGRESO DE FONDOS / VALORES
        │
        ├── Cobranza en Centro
        │      ├── Efectivo ───────────────► CAJA DEL CENTRO
        │      └── Cheques físicos ────────► CARTERA FÍSICA DEL CENTRO
        │
        ├── e-Cheq recibido ───────────────► CARTERA ELECTRÓNICA
        │                                      ├── Estado financiero
        │                                      └── GESTIÓN ADMINISTRATIVA
        │
        └── Transferencia recibida ────────► GESTIÓN ADMINISTRATIVA
                                               │
                                               ▼
                                     Pendiente → Gestionada


CAJA TANDIL
   ├── Efectivo
   └── Cheques físicos disponibles
             │
             ▼
       TRASLADO INTERNO
             │
      Reserva / despacho
             │
             ▼
          EN TRÁNSITO
             │
             ▼
       CAJA OLAVARRÍA
             │
       Revisar recepción
          ┌──┴───┐
          ▼      ▼
      Aceptar  Rechazar
          │      │
          ▼      └──► devolución / resolución
      Disponible


DISPONIBILIDAD
      ├── Efectivo por Caja
      ├── Cheques físicos por Caja
      ├── e-Cheqs de terceros
      └── Bancos (disponible informado)
      │
      ▼
ORDEN DE PAGO
      ├── Efectivo
      ├── Cheques de terceros
      ├── e-Cheqs de terceros
      ├── Transferencia
      ├── Depósito
      ├── Cheque propio a emitir
      └── e-Cheq propio a emitir
      │
      ▼
PREPARACIÓN COLABORATIVA
      │
      ▼
TODOS LOS COMPONENTES CONFIRMADOS
      │
      ▼
OP LISTA PARA CERRAR / APLICAR
      │
      ▼
NOTIFICACIÓN AL CREADOR
      │
      ▼
REVISIÓN Y CIERRE
      │
      ▼
MOVIMIENTOS + DOCUMENTO + CARTERAS + ALERTAS + AUDITORÍA
```

## 5. Primera etapa: ingreso antes que pago

Antes de construir pagos, OrdenaClick debe responder:

1.  qué ingresó;
2.  dónde ingresó;
3.  quién lo registró;
4.  dónde está ahora;
5.  si está disponible;
6.  quién puede verlo;
7.  si tiene gestión administrativa pendiente.

Secuencia: **Ingreso → Caja/Cartera → Disponibilidad → Gestión
Administrativa → Orden de Pago.**

Esta será la fuente común para pagos simples, OP, planes de pago,
obligaciones y proyecciones.

## 6. Nueva Cobranza

Pantalla aprobada: - fecha; - referencia; - vendedor/origen opcional; -
total declarado; - efectivo recibido; - cheques recibidos; -
diferencia; - grilla rápida de cheques.

Ejemplo: cobranza \$16.500.000 = efectivo \$1.500.000 + cheques
\$15.000.000 → diferencia \$0.

Debe evaluarse permitir guardar diferencias como **Pendiente de
conciliar**. No obligar a reproducir recibo por recibo.

## 7. Cheques físicos y Cliente

Cada cheque se individualiza con número, banco, fechas, importe y
Cliente opcional.

Una sola carga debe producir: 1. movimiento de Caja; 2. creación
automática del valor en Cartera física.

**Cartera no es una segunda carga.**

Cliente es trazabilidad opcional. Su ausencia no bloquea el cheque.
Puede utilizar autocomplete y `[+]` contextual.

## 8. Caja por Centro Operativo

Ejemplo:

**Caja Olavarría:** efectivo ARS/USD + cheques físicos bajo custodia en
Olavarría.

**Caja Tandil:** efectivo ARS/USD + cheques físicos bajo custodia en
Tandil.

Un cheque ubicado en Tandil no puede presentarse como físicamente
disponible en Olavarría.

La arquitectura debe permitir en el futuro más de una Caja por Centro
aunque inicialmente exista una principal.

## 9. Traslado interno entre Cajas

Es una **orden interna de transferencia de recursos**, no dos
movimientos manuales desconectados.

Ejemplo: Tandil posee efectivo \$10.000.000 y cheques \$15.675.799,99.
Su administrador envía a Olavarría efectivo \$7.000.000 más cheques
seleccionados entre los disponibles.

``` text
Caja Tandil
    ↓
Crear traslado a Olavarría
    ├── Efectivo $7.000.000
    └── Cheques seleccionados
    ↓
Confirmar envío
    ↓
Recursos dejan de estar disponibles en Tandil
    ↓
EN TRÁNSITO
    ↓
Olavarría revisa recepción
    ├── Aceptar
    └── Rechazar total o parcialmente
    ↓
Aceptados → Caja Olavarría
Rechazados → devolución/resolución pendiente
```

La recepción puede ser parcial: efectivo aceptado, algunos cheques
aceptados y otros rechazados con motivo.

Un valor rechazado no reaparece mágicamente como disponible: permanece
en un estado de resolución/devolución hasta cerrar el circuito.

Debe auditarse origen, destino, usuarios, fechas, efectivo, valores,
despacho, recepción, aceptaciones, rechazos, motivos y resolución.

## 10. Cartera física

Estados conceptuales a cerrar antes de programar: - Disponible; -
Reservado; - En tránsito; - Entregado/Endosado; - Depositado; -
Devuelto; - otros necesarios.

Un valor no puede utilizarse simultáneamente en dos operaciones.

## 11. e-Cheqs

Los e-Cheqs se registran al detectarse en la cuenta bancaria. No
necesariamente provienen de una cobranza física.

Mantienen dos dimensiones:

**Estado financiero:** Disponible, Reservado, Cedido, etc.

**Gestión Administrativa:** Pendiente / Gestionada.

Así un e-Cheq puede estar disponible financieramente y a la vez
pendiente de recibo/aplicación en el sistema externo.

## 12. Gestión Administrativa

Circuito independiente de Caja. Puede recibir tareas de: - e-Cheqs; -
transferencias recibidas; - cheques físicos cuando corresponda; -
futuros movimientos.

Un usuario autorizado realiza la tarea externa y pulsa **Confirmar
gestión**. Se registra usuario, fecha/hora y observación si corresponde.

También debe contemplarse devolución del valor cuando corresponda.

Un Colaborador puede resolver pendientes sin acceder a saldos globales.

## 13. Transferencias recibidas

No pertenecen a Caja física.

Pueden: - registrarse como operación bancaria; - generar Gestión
Administrativa; - conservar Cliente/Centro/origen cuando corresponda.

Esto permite controlar recibo/aplicación sin duplicar el sistema
contable.

## 14. Bancos

Se utiliza **Disponible informado**, no saldo contable exacto.

Por cuenta: importe, usuario y fecha/hora de actualización.

Sirve para planificar; no bloquea rígidamente transferencias porque
pueden existir descubiertos, débitos, impuestos y movimientos
pendientes.

## 15. Disponibilidad

Según alcance/permisos: - efectivo ARS/USD por Caja; - cheques físicos
por Caja; - e-Cheqs de terceros; - bancos/disponibles informados.

Administrador general: posible visión consolidada.

Administrador de sucursal: sólo alcance autorizado.

Colaborador: puede no ver saldos globales.

**Ver no implica poder utilizar.**

## 16. Orden de Pago

La OP preparada todavía no es el hecho financiero definitivo.

Medios previstos: - Efectivo. - Cheques de terceros. - **e-Cheqs de
terceros.** - Transferencia. - Depósito. - **Cheque propio a emitir.** -
**e-Cheq propio a emitir.**

## 17. Reserva de terceros

Al seleccionar cheque/e-Cheq:

**Disponible → Reservado para OP**

No se ofrece para otra OP.

Si se cancela antes de ejecutar: **Reservado → Disponible**.

Al confirmar salida: cheque físico → Entregado/Endosado; e-Cheq →
Cedido, según reglas definitivas.

## 18. Preparación colaborativa

Las OP pendientes pertenecen al flujo de la Empresa, no a una persona.

Cualquier usuario autorizado abre una OP, ve qué falta y confirma lo que
puede concretar.

No hace falta asignar previamente cada componente.

**Confirmar no significa "lo vi"**: significa que fue realmente
preparado/ejecutado según la naturaleza del medio.

## 19. Instrumentos propios

La preparación puede conocer importe y fecha sin conocer número
definitivo.

Se permite: - Cheque propio a emitir --- importe/fecha. - e-Cheq propio
a emitir --- importe/fecha.

Luego un usuario autorizado emite, completa datos y confirma.

Esto permite que un empleado prepare y el titular autorice/emita.

## 20. OP completa y cierre

**Confirmar componentes ≠ cerrar OP.**

Cuando todos están confirmados:

**OP → Lista para cerrar/aplicar/despachar**

Se notifica al creador mediante la campanita.

El creador revisa y cierra. Debe existir alternativa autorizada si está
ausente/desactivado/sin permisos.

Al cerrar se consolidan movimientos, estados, documento definitivo,
Carteras, Alertas y Auditoría.

## 21. Alertas

Terceros: mientras permanecen en cartera generan recordatorios; al salir
definitivamente dejan de generarlos.

Propios: una propuesta no genera todavía obligación. Al emitir/confirmar
nace el instrumento y entra en Alertas.

También pueden alertarse OP incompletas, gestiones pendientes, cobranzas
sin conciliar y traslados pendientes.

## 22. Auditoría

Debe reconstruirse quién, cuándo, qué y desde dónde para: - ingresos; -
OP; - confirmaciones; - reservas; - traslados; - recepciones/rechazos; -
cambios de ubicación; - emisión de instrumentos; - gestión
administrativa; - cierre; - anulaciones/reversiones.

No borrar silenciosamente historia financiera.

## 23. Seguridad

**El backend es la autoridad.** Ocultar botones no es seguridad.

Cada endpoint sensible valida: - autenticación; - Empresa; - Centro/Caja
dentro del alcance; - permisos; - pertenencia del objeto; - estado
válido.

Cambiar IDs/URLs nunca debe permitir acceder a otra Empresa, sucursal,
Caja, OP o recurso no autorizado.

En producción: HTTPS, cookies `Secure`, `HttpOnly`, `SameSite`
apropiado, CSRF, métodos HTTP correctos y configuración segura de
host/proxy.

Nunca exponer secretos, claves, tokens o credenciales en
HTML/JS/static/media/Git.

### Concurrencia

El servidor debe impedir: - doble reserva; - confirmaciones
incompatibles; - recepción duplicada; - cierre simultáneo incorrecto; -
liberar valores utilizados.

Operaciones críticas usan transacciones y bloqueo/validación cuando
corresponda.

Doble clic o reintento no puede generar movimientos duplicados.

## 24. Integridad

-   Un valor no puede estar disponible y entregado simultáneamente.
-   Un valor no puede financiar dos OP.
-   Una reserva conoce su operación.
-   Un cheque físico conoce ubicación/custodia.
-   En tránsito no está disponible en origen ni destino.
-   Un rechazo requiere resolución explícita.
-   Cerrar OP exige componentes obligatorios confirmados.
-   Gestión Administrativa y estado financiero son independientes.
-   Todo respeta Empresa, alcance y permisos.

## 25. Pantallas aprobadas

Se toma como base visual/funcional el diseño presentado: 1. Dashboard
financiero. 2. Nueva Cobranza. 3. Cartera de Cheques/e-Cheqs. 4. Lista
de Órdenes de Pago. 5. Detalle colaborativo de OP. 6.
Confirmación/emisión de instrumento propio.

Se incorporarán progresivamente Gestión Administrativa, Traslados entre
Cajas, alcance por Centro/Caja, e-Cheqs de terceros y cheques propios.

## 26. Orden de implementación

**Bloque 1 --- Entrada:** Caja por Centro, Nueva Cobranza, efectivo,
carga rápida de cheques, creación automática de Cartera.

**Bloque 2 --- Disponibilidad:** Cartera física, estados, filtros,
alcance usuario/Centro.

**Bloque 3 --- Electrónicos y gestión:** e-Cheqs, transferencias
recibidas, Gestión Administrativa.

**Bloque 4 --- Traslados:** orden interna, reserva/despacho, tránsito,
recepción, rechazo parcial y resolución.

**Bloque 5 --- OP:** preparación, terceros, propios, reservas,
confirmación colaborativa, notificación y cierre.

**Bloque 6 --- Expansión:** pagos simples, planes de pago, proyecciones
e integración con obligaciones.

## 27. Regla para implementar cada bloque

Antes de programarlo se cierran: - estados; - transiciones; - datos
obligatorios; - permisos; - efectos sobre saldos; - efectos sobre
alertas; - reversiones; - concurrencia; - auditoría; - errores
parciales.

## 28. Resumen

``` text
EMPRESA
 ├── Centros Operativos
 │    └── Cajas
 │         ├── Efectivo
 │         └── Cheques físicos
 ├── Cartera electrónica → e-Cheqs
 ├── Bancos → Disponible informado
 ├── Gestión Administrativa → pendientes
 └── Usuarios
      ├── Administrador general
      ├── Administrador de sucursal
      └── Colaborador
           + permisos funcionales

ENTRADA
  ↓
CAJA / CARTERA
  ↓
UBICACIÓN + ESTADO + DISPONIBILIDAD
  ↓
TRASLADOS (si corresponde)
  ↓
ORDEN DE PAGO
  ↓
RESERVA
  ↓
CONFIRMACIÓN COLABORATIVA
  ↓
100 % PREPARADA
  ↓
NOTIFICACIÓN
  ↓
CIERRE
  ↓
MOVIMIENTOS + DOCUMENTO + ALERTAS + AUDITORÍA
```

**Primero ingresamos el dinero y los valores. Después sabemos dónde
están y si podemos disponer de ellos. Recién entonces los utilizamos
para pagar.**

## Actualizacion operativa basada en OLAFIL — 11/10/2026

Este capitulo actualiza la secuencia de implementacion previa. Caja ahora precede a REGISTROS. Primero **movimientos manuales de entrada/salida y saldos**, sin Orden de Pago; luego **pendientes bancarios**, **Cartera y disponibilidad real para pagos individuales**, **envios y recepcion**, **arqueos y prevision**, y finalmente **Ordenes de Pago**.

**Movimientos de Caja:** alta de efectivo con fecha, tipo, moneda, importe, concepto y Caja concreta. Ingresos de Cobranza existentes se incluyen en historial; nunca duplicar la Cobranza en formulario manual. Egresos deben respetar el saldo disponible de su moneda, con bloqueo y deduplicacion. Historial no editable ni borrable silenciosamente; correcciones futuras con contraasientos/reversiones auditadas. Cheques fisicos tienen su Cartera; operaciones bancarias su circuito.

**Centros y permisos:** Olavarria/Casa Central, Tandil y Bolivar son ejemplos, no roles o nombres codificados. Admin general puede consultar todas las Cajas o filtrar por una; Admin de Centro solo su(s) Caja(s). Colaborador no opera Caja por defecto. Una persona con capacidades suficientes puede cumplir varias funciones sin pasos artificiales entre usuarios.

**Pendiente bancario:** deteccion de transferencia/deposito de cliente por quien consulta los bancos; identifica posible Centro, conserva referencia y no implica una segunda Cobranza. Usuarios autorizados del Centro comprueban recibo existente, generan el recibo externo cuando falta, y marcan resuelto con quien/cuando/referencia. Cualquiera autorizado puede resolver: no depende de Nicolas. Administradores supervisan pendientes prolongados o sin Centro identificado.

**Envio interno futuro:** operacion sencilla con Caja origen, Caja destino e importe/cheques; descontar origen al despachar y mantener en transito hasta recepcion. Receptor ve detalle y compara. Si discrepa, registrar ambas declaraciones sin editar silenciosamente origen, permitir conciliacion y crear caso en Auditoria con responsabilidad y cierre trazable. No marcar la diferencia como efectivo disponible en ninguno de los Centros antes de resolverla.

**Bancos:** acuerdos de descubierto, importes y vencimientos se configuran en el ABM de Cuentas Bancarias y alimentan alertas. Posicion bancaria informada, acreditaciones proyectadas y efectivo de Caja no se confunden.

**Orden de Pago futura:** preparar componentes; cada responsable autorizado tilda cuando realmente confirmo la salida (efectivo/cheques/e-Cheq propio/etc.). Solo con todos los componentes confirmados pasa a **Lista para cerrar** y se avisa al creador; revision y cierre definitivo son posteriores. No crear una Orden de Compra.

**Regla transversal:** lo sencillo arriba, lo seguro por debajo. Empresa/Centro/Caja validados en backend; POST+CSRF, transacciones, idempotencia, auditoria, backup y pruebas adversariales en cada bloque. No certificar concurrencia real PostgreSQL con pruebas solo SQLite.

## Ajuste UX del historial de Caja / acceso bancario — 11/10/2026
- En la portada de Caja, la sección **Movimientos del día** es el lugar principal para consultar ingresos, egresos y efectivo de cobranzas. Filtro de fecha: **Hoy / Rango de fechas**. Filtro independiente: Caja X, Caja Z o Todas, sin ampliar alcance. Paginación.
- **Movimiento de Caja** sirve para registrar; no repetir el historial ahí. La información sigue persistida en `MovimientoCaja` y no se copia a otra tabla.
- Autorización aprobada para **Caja 2**: un administrador general podrá asignar a Colaboradores acceso a pendientes de aplicación bancaria de Centros específicos, sin darles permisos de Caja. Administradores de Centro acceden a pendientes de su Centro; generales supervisan todos y los no clasificados. No depender de Nicolás para asignar o resolver casos. **Pendiente de programar** con administración explícita, aislamiento por Empresa, backend y pruebas.

## Consolidado funcional de operación real y Caja 2 — 11/10/2026
### Usuarios, Centros y permisos
OLAFIL sólo es ejemplo de prueba: Olavarría Casa Central, Tandil y Bolívar sucursales. Emmanuel observa bancos y registra pendientes; Omar administra recursos y prepara OP; Matías/ Juan/ Fede administran sus Cajas; Nicolás y Enzo realizan comprobaciones de aplicación desde el sistema externo. **No codificar nombres ni hacer que Nicolás sea coordinador obligatorio.** Colaboradores trabajan sobre Centros autorizados expresamente (varios si hace falta), sin acceso automático a Caja ni disponibilidades; Admin de Centro únicamente su Centro; Admin general puede filtrar Caja individual o Todas las autorizadas. Empresas con una sola persona pueden completar todos los pasos con su única identidad autorizada.
### Fuente operativa y UI
Cinco planillas usadas como referencia: «Cartera de E-Cheqs» (datos de instrumento, control recibos, reservas por proveedor, salidas, devoluciones/rechazos), «Planilla Depósitos» (detección y comprobación de transferencias/depósitos, seguimiento desde último movimiento), «Estado de cuentas bancarias» (posición del día, descubierto, acreditaciones, rechazo y recuperación), «05-09-2026» (entradas, salidas, arqueos físicos) y «CHEQUES EN CARTERA» (custodia física y reservas). Los Excel no deben convertirse en cinco cargas redundantes. Mostrar operaciones una sola vez, actualizar estados relacionados; simplicidad de cara al usuario, integridad, permisos y auditabilidad detrás.
Caja 1: historial en dashboard, **Hoy/Rango**, Desde/Hasta juntos, encabezado compacto y columnas alineadas con Registros, botones discretos Editar y Eliminar. Editar/anular movimiento manual sólo mediante contraasiento fechado en la fecha real de rectificación, con motivo, actor, original intacto y, al editar, reemplazo; nunca permitir disponible negativo. Cobranzas/cheques no son editables por esa vía. Saldos derivados de `MovimientoCaja`, no números mutables. El usuario ve el efecto y una fila histórica explicativa.
### Caja 2: pendientes de aplicación bancaria
Tipos: transferencia recibida, depósito recibido, e-Cheq detectado. Se guarda Empresa, cuenta, fecha, tipo, importe, referencia, Centro opcional, quién detectó, estado; al resolver, si ya estaba imputado o generó recibo manual externo, referencia y usuario/fecha. Estado pendiente hasta comprobar realmente. Un pendiente sin Centro sólo visible a administración general hasta clasificarlo (asignación posterior de Centro por administrador general con evento auditable). Perfiles autorizados por jerarquía/Centro y concesiones específicas a Colaboradores; revocación inmediata. La bandeja y sus eventos NO crean por sí solos cobranzas, pagos, e-Cheqs de Cartera ni movimientos bancarios contables.
### Próximos circuitos, todavía no programados
1. Cartera: disponibilidad real de cheques físicos en Caja, e-Cheqs electrónicos con estado financiero y gestión administrativa independientes. Reservas y salidas para proveedores habituales (Guerrini/R Neto/Fercol son ejemplos, nunca constantes de código), terceros/custodia/depósito/endoso/cesión y rechazos aun después de salida, sin borrar hechos.
2. Envíos: un registro simple a Caja destino; recursos salen de origen y quedan «En tránsito» hasta confirmación; receptor revisa, acepta total/parcial o declara diferencia. Dos declaraciones inmutables, arqueo por cada parte y caso de Auditoría que requiere resolución. No acreditar importes disputados.
3. Bancos: configurable desde ABM Cuentas Bancarias el acuerdo de descubierto y su alerta por vencimiento; fecha/hora de saldo informado, registro de cheques depositados y acreditaciones proyectadas, rechazo/retirada pendientes, nunca confundir saldo informado con disponible garantizado.
4. Pago individual desde REGISTROS: consumir instrumentos existentes de Cartera, no crearlos nuevamente; bloquear reservas incompatibles y movimientos duplicados. Después OP con componentes colaborativos tildados sólo tras operación real, aviso al creador cuando 100% preparado, revisión y cierre definitivo separados.
5. Arqueos: registrar físico real y diferencias frente a saldo teórico sin reescritura económica silenciosa; políticas de auditoría y resolución.
### Seguridad y respaldo
Siempre Empresa/Centro/objeto en backend, POST/CSRF para cambios, transacciones/serialización e idempotencia; auditoría sin secretos, HTML escapado, no acceso de colaboradores a Caja. Backup Empresa v1 incluye hechos y eventos, no privilegios de la instalación; ZIP v1 anteriores se pueden leer sin nuevos componentes. Pruebas de concurrencia PostgreSQL e infraestructura real aún pendientes.


## Caja 2 — revisión funcional de pendientes globales (12/10/2026)

**Corrección explícita del diseño previo de Caja 2 (no volver a la bandeja por Centro).**
Dentro de una Empresa activa, *todos los pendientes bancarios y e-Cheqs* son
**globales dentro de esa Empresa mientras están pendientes**, aunque no se
sepa quién pagó ni a qué Centro corresponde. Ningún selector de Empresa ni de
Centro aparece en la consulta de pendientes. La Empresa operativa se fija en
sesión a través de una entrada autorizada desde el entorno de esa Empresa;
manipular parámetros de URL/POST no permite saltar a otra Empresa.

- Bandeja: `Fecha | Identificación (puede estar vacía) | Importe ARS formateado | Confirmar`.
- Confirmar abre modal: identificación real del cliente, Centro Operativo,
  resultado (ya imputado / recibo externo realizado), referencia del recibo
  cuando se generó. Guardar registra actor/fecha y evento; no contabiliza ni
  crea un recibo externo. No se cierra dos veces.
- Usuarios administrativos de Centro o colaboradores con permiso explícito
  para gestión pueden **ver todos los pendientes globales de SU Empresa**.
  Sólo pueden resolverlos **asignándolos a un Centro autorizado**. Admin
  general/propietario/superusuario puede resolver hacia cualquier Centro
  activo de la Empresa. Un colaborador sin permiso no accede. Esto NO da
  permisos de Caja ni saldos de cuentas bancarias.
- Tras resolver, el movimiento pasa al historial **del Centro elegido**.
  Los resueltos se consultan según alcance del usuario; allí sí puede
  existir filtro por Centro. No reabrir o reclasificar sin nuevo circuito de
  auditoría aprobado. Los pendientes legados con Centro precargado se tratan
  como globales mientras permanezcan pendientes y se fija el Centro final
  al confirmar.
- Registro para quien controla el banco (administración general): elegir
  cuenta bancaria, tipo depósito/transferencia, fecha, identificación
  opcional e importe. **Agregar fila** sólo modifica memoria del navegador;
  íconos Editar (carga de nuevo los casilleros) y Eliminar (quita fila).
  **Guardar todos** persiste lote atómico con idempotencia individual, sin
  registros parciales si alguna fila falla.
- Cargar e-Cheq: formulario separado con datos de la planilla real `Cartera
  de E-Cheqs` B–H: titular, número de cheque, código/nombre de banco emisor,
  importe y fecha de acreditación. Estado/historial se gestionan en el sistema.
  Selector `A la orden` por defecto, o `No a la orden`. Guardar en lote,
  editar y quitar filas antes de persistir. **No crear automáticamente un
  Cheque de Cartera ni un Pago** al detectar un e-Cheq: integrar instrumento
  y verificar recibo sin duplicación en el futuro bloque Cartera.
- Navegación: eliminar CTA Pendientes del selector general de perfiles y de
  accesos rápidos de Caja. Añadir en sidebar del entorno Empresa. Los
  colaboradores habilitados eligen la Empresa fuera de Gestión Bancaria,
  desde su entorno autorizado. `Volver` regresa al menú de origen, no al
  selector de perfiles. Los permisos se administran exclusivamente desde
  **Configuración de Empresa**, no junto a la bandeja.
- Seguridad obligatoria: POST+CSRF; GET no muta; validación Empresa/sesión,
  Centro permitido, relaciones y objetos en backend; transacción atómica;
  idempotencia por fila; auditabilidad por identidad histórica; no exponer
  cuentas/saldos a colaboradores; pruebas de Empresas cruzadas, Centros,
  reintentos y backup. La migración 0045 es aditiva; Backup Empresa v1
  serializa nuevos campos por especificación ya vigente; los permisos
  funcionales de instalación NO forman parte del backup portable.
- No confundir seguridad local probada con infraestructura productiva: el
  cierre local de Base Server no certifica concurrencia real PostgreSQL ni
  HTTPS/proxy, SMTP, políticas de retención y backup externo.

### UX complementaria aprobada — e-Cheqs y pendientes

- **Banco emisor:** buscar escribiendo entre Bancos activos de la Empresa
  (sugerencias relacionadas, sin desplegar una lista larga). `[+]` crea Banco
  usando el ABM de OrdenaClick, desde diálogo de contexto; al guardar,
  elegirlo automáticamente y mantener las filas y campos del lote de e-Cheqs.
  En edición de una fila, recargar su Banco; en alta se mantiene la selección.
  La comprobación definitiva Banco/Empresa/activo es del servidor.
- **Bandeja:** depósitos/transferencias distinguibles visualmente de
  e-Cheqs por tono y texto, como categorías, sin confundir con estados
  de vencimientos. Se respeta Fecha / Identificación / Importe / Confirmar.
- **Configuración de permisos:** revisión de la pantalla existente, sin
  rediseño adelantado. Globales dentro de la Empresa hasta resolver, y
  sólo Centros autorizados para la confirmación.

### Caja 2 — e-Cheqs: formulario corregido, cuenta y ABM contextual (pendiente de pruebas)

- **No confundir e-Cheq con depósito bancario**: el e-Cheq recibido pertenece al CUIT
  de la Empresa; no requiere cuenta receptora ni crea movimiento de Caja. La cuenta
  sólo se elige en una futura operación de depósito. Depósito/transferencia sí
  requiere cuenta. Migración aditiva `0046` hace opcional la FK para e-Cheq;
  protege la obligación para depósitos/transferencias, sin borrar asociaciones
  históricas ni alterar saldos. Backup Empresa v1 conserva estos hechos.
- Número e-Cheq: `usuarios.services.cheques.normalizar_numero_cheque` es la regla
  canónica (únicamente dígitos, máximo ocho y relleno izquierdo: 185 → 00000185).
  En pantalla se aplica al salir; en servidor siempre se revalida.
- Importe: edición y presentación es-AR, por ejemplo 150 → 150,00 y 15000 →
  15.000,00; el servidor mantiene Decimal/validación de importes positivos.
- Se retira el N.º Banco adicional. Banco Emisor y Titular están alineados con los
  demás casilleros: búsqueda por teclado. Banco proviene del ABM activo de la
  Empresa y se valida por ID/Empresa. Titular sugiere Clientes activos de esa
  Empresa, pero conserva texto libre porque el titular no necesariamente es el
  cliente al que se le aplica el pago. El Centro y cliente definitivo se
  identifican al **resolver**, no durante el registro.
- `[+]` no abre modal inventado: navega al **ABM existente** de Banco/Cliente,
  incluso con alta de Centro anidada en Clientes, y retorna a la carga de e-Cheq
  restaurando formulario, edición y filas preparadas. El borrador temporal
  `sessionStorage` está aislado por Empresa y pestaña; si no se puede almacenar
  no sale de la pantalla. El servidor valida sesión Empresa y rol administrativo.
- Se conserva el listado ya aceptado: depósitos/transferencias en turquesa,
  e-Cheqs en violeta, estado Pendiente/Resuelto separado, modal Confirmar y
  permisos de administración por Centro; no introducir nuevos selectores.
- **Estado**: pendiente de tests reales, revisión visual y publicación selectiva.

### Caja 2 — búsqueda, fecha, auditoría y Designar perfiles (12/10/2026)

- **Bandeja global por Empresa activa:** se mantiene el alcance global de Pendientes; una vez resuelto, el Centro limita la consulta de Resueltos. Nuevo buscador incremental por Titular / Cliente, importe en es-AR y número del e-Cheq. La consulta filtra en servidor *antes* de paginar y siempre por Empresa; el filtro Centro sólo aparece en Resueltos. Las monedas e importes de los listados se muestran con miles mediante punto y decimales mediante coma; el formato lo asegura `usuarios.templatetags.caja_importes.importe_ar` y no depende del locale de Django.
- **e-Cheq:** la fecha de acreditación no puede superar los 30 días de antigüedad en el momento de la carga; UI `min` y validación de backend, sin reinterpretar registros históricos. Se mantienen e-Cheq sin cuenta receptora (migración 0046), banco emisor proveniente del ABM, ocho dígitos en número, monto es-AR y condición A la orden / No a la orden.
- **Depósitos/transferencias y e-Cheqs:** campo `Titular / Cliente` con búsqueda entre Clientes activos de la Empresa, `[+]` hacia ABM existente y vuelta conservando ambas listas temporales, datos y edición. El titular puede quedar sin identificar al detectar un depósito; la identificación real y el Centro quedan definidos al resolver.
- **Corrección de errores:** movimiento Pendiente sólo editable por quien lo registró o administración general, con motivo obligatorio, antes/después persistente, actor histórico e idempotencia UUID. No modifica Caja ni crea recibos/pagos. Para un movimiento ya Resuelto no se altera ningún dato financiero ni la imputación externa: el generador, resolvedor o administración general con alcance pueden **abrir una incidencia de auditoría** con motivo. El registro queda sin cambiar; incidencias abiertas visibles a administración general en Configuración de permisos. El procedimiento definitivo de resolución de incidencias se decidirá cuando se implemente Auditoría completa, sin editar silenciosamente resueltos.
- **Configuración de accesos:** el acceso a los permisos de Gestión Bancaria pasa de botón independiente en Configuración a **Configuración → Designar perfiles**, junto con relaciones. La pantalla de permisos conserva la validación administración general/propietario/superusuario; asigna Centro(s) a colaboradores, sin conceder Caja ni saldos, sin cambiar jerarquías estructurales. Permisos NO viajan en Backup Empresa v1.
- **Persistencia / backup:** migración aditiva `0047_revision_auditada_pendiente_bancario` y `RevisionPendienteBancario` para edición o incidencia, snapshots JSON antes/después, motivo, creador y estado. Backup Empresa v1 incluye esta nueva entidad como componente opcional, y serializa JSON como objeto para permitir su restauración; respaldos antiguos sin este componente siguen aceptados. Auditoría de permisos de usuarios permanece fuera del respaldo portable.
- **Seguridad:** POST+CSRF, verificación Empresa activa y roles/centro en backend, GET sólo lectura, transacción y bloqueo para evitar revisiones simultáneas, no cruce entre Empresas. Comprobar al ejecutar las pruebas locales y luego la disposición visual; no dar por aceptado lo no comprobado. Base Server aprobado localmente no implica certificado de producción para PostgreSQL, proxy/TLS o backups remotos.
