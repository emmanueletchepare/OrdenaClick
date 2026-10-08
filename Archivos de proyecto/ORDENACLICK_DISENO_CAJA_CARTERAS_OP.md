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
