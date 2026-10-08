# OrdenaClick — Rumbo y estado actual

**Última actualización:** 08/10/2026
**Objetivo operativo:** llegar a una Beta usable, estable y segura durante noviembre de 2026.

Este documento es el punto de entrada para entender qué es OrdenaClick, qué estamos construyendo ahora y qué queda deliberadamente para después.

## 1. Qué es OrdenaClick

OrdenaClick es una aplicación web de gestión para registrar, ordenar y anticipar la actividad económica y operativa de una persona, actividad o Empresa.

No busca guardar solamente “cuánto se gastó”. Debe permitir reconstruir y entender:

- qué Empresa realizó una operación;
- qué ocurrió y cuándo;
- quién la registró;
- a qué Proveedor, Centro Operativo o Recurso se vinculó;
- cuánto se pagó y cuánto queda pendiente;
- qué medio financiero se utilizó;
- qué obligaciones futuras siguen abiertas;
- qué hechos requieren atención.

El objetivo es transformar información operativa cotidiana en historia confiable, previsibilidad financiera y, más adelante, reportes y contabilidad.

## 2. Principio de producto

OrdenaClick utiliza una sola arquitectura de datos capaz de acompañar crecimiento.

**Simplificar la interfaz, no empobrecer los datos.**

Una persona o Empresa puede comenzar con una operación simple y habilitar mayor complejidad con el tiempo sin migrar a otro producto ni reconstruir su historia.

Los planes comerciales habilitarán capacidades. No existirán arquitecturas incompatibles por plan.

## 3. Núcleo conceptual

```text
EMPRESA
└── EJERCICIO
    └── MOVIMIENTO
        ├── PAGOS
        │   └── APLICACIONES DE PAGO
        ├── PLAN DE PAGOS
        │   └── CUOTAS
        └── VENCIMIENTOS
            └── ALERTAS
```

Reglas que no se negocian:

- Movimiento = hecho económico/documental.
- Pago = hecho financiero.
- AplicacionPago = cuánto de un Pago cancela un destino.
- saldo pendiente = total - aplicaciones efectivas.
- un Movimiento no puede recibir una aplicación mayor a su saldo pendiente.
- intereses y costos financieros no aumentan artificialmente el capital aplicado.
- Vencimiento = compromiso abierto.
- Alerta = aviso; no sustituye al Vencimiento.
- la historia no se reescribe silenciosamente.

## 4. Usuarios, Empresas y permisos

La cuenta de usuario pertenece a OrdenaClick, no a una Empresa.

- `Empresa.propietario` representa al fundador.
- `AsignacionUsuarioEmpresa` representa jerarquía administrativa/operativa.
- Administrador general: alcance de Empresa.
- Administrador: alcance de Centro Operativo.
- Colaborador: capacidades operativas explícitas; no obtiene autoridad administrativa implícita.
- Contable y Legal son roles funcionales separados y acumulables.
- Relaciones gestiona solicitudes y vínculos.
- Desarrollador es global de instalación y sólo para superusuario.

Una solicitud pendiente no concede acceso. Ranking, marketplace, contratación o reputación futura tampoco conceden permisos.

La autorización real siempre pertenece al backend.

## 5. Qué significa Beta

La Beta no se mide por cantidad de pantallas, commits o refactors.

La Beta se considera útil cuando una persona puede completar un circuito real sin perder contexto ni depender de datos ficticios.

Prioridad central:

```text
REGISTROS
├── Comprobantes
├── Carga Planificada
├── Registrar Pago
└── Modificar / Eliminar
```

Debe cerrarse de punta a punta con:

- ABM necesarios;
- navegación contextual `[+]`;
- pagos parciales y múltiples;
- saldos correctos;
- edición e historia de Pagos;
- vencimientos y alertas coherentes;
- aislamiento por Empresa;
- pruebas automatizadas y recorrido manual.

Obligaciones / Liquidaciones tienen definición conceptual propia y no deben forzarse dentro del modelo de factura. Su implementación definitiva puede quedar posterior al circuito Beta mínimo si hacerlo ahora pone en riesgo el cierre de los flujos principales.

## 6. Estado real al 08/10/2026

### Base ya construida

- núcleo Movimiento / Pago / AplicacionPago;
- pagos parciales y reglas de saldo en servicios;
- Carga Simple / Comprobantes con guardado y edición;
- registro de Débito automático real con separación de mora;
- Próximos Vencimientos y Llamador con base funcional;
- ABM principales de Empresa;
- Clientes;
- Caja y Nueva Cobranza como base;
- jerarquía Empresa / Centro / Caja;
- Relaciones y roles funcionales;
- IdentidadUsuarioEmpresa para trazabilidad portable;
- Backup Empresa v1 con servicios dedicados, manifest, inspección, restauración y wizard;
- Perfil Desarrollador y secretos de instalación fuera del código;
- integración base ARCA;
- separación progresiva de vistas, templates, servicios y estáticos;
- hardening de aislamiento por Empresa en maestros, Tipos de Gasto, Gestión de Claves, comprobantes, Movimientos y eliminación de Empresa.

### Lo que NO debe interpretarse como cerrado

- auditoría final de todas las rutas privadas;
- permisos funcionales completos por rol/capacidad;
- Carga Planificada completa;
- Registrar Pago distribuido entre múltiples Movimientos;
- remanentes a cuenta;
- conversión completa a Plan;
- reversión integral de Pagos con todas sus consecuencias;
- navegación `[+]` LIFO verificada en todos los consumidores;
- eliminación de todo JavaScript inline en los flujos Beta;
- Cartera física/electrónica completa;
- Gestión Administrativa;
- Traslados internos;
- Orden de Pago;
- producción segura y despliegue;
- requisitos reproducibles;
- batería adversarial final de Backup;
- regresión completa candidata a Beta.

## 6.1. Decisión de etapa — Base Server

Antes de retomar el desarrollo funcional intensivo se cierra una etapa específica de arquitectura y seguridad orientada a servidor.

Documento rector: `BASE_SERVER_SEGURIDAD.md`.

Objetivo formal:

> **BASE ARQUITECTÓNICA Y DE SEGURIDAD PARA SERVER: CERRADA**

Por decisión vigente, el superusuario conserva por ahora acceso a Empresas. Más adelante el Perfil Desarrollador incorporará un panel global para administrar habilitación, suspensión, capacidades/suscripciones, exportar una Empresa y generar un resumen administrativo, reduciendo la necesidad de operar directamente sobre la base.

Al cerrar Base Server se retoma REGISTROS como prioridad funcional Beta.

## 7. Orden de trabajo desde este punto

### Prioridad 1 — cerrar riesgos activos reales

Seguridad e integridad sólo cuando exista un hallazgo activo o un requisito bloqueante. No continuar “hardening por inercia”.

Incluye todavía:

- auditoría final de rutas privadas y autenticación;
- uploads/archivos privados;
- reautenticación y auditoría del revelado de Gestión de Claves;
- configuración segura de producción;
- revisión de secretos históricos y runtime;
- concurrencia/idempotencia en operaciones financieras críticas.

### Prioridad 2 — cerrar REGISTROS

Orden recomendado:

1. verificar Comprobantes punta a punta;
2. completar Registrar Pago general;
3. cerrar gestión/reversión de Pagos históricos;
4. cerrar Modificar / Eliminar;
5. completar Carga Planificada / Convertir a Plan según alcance Beta;
6. verificar saldo, Vencimiento y Alerta después de cada transición.

### Prioridad 3 — navegación y UX Beta

- pila contextual `[+]` LIFO en todos los flujos publicados;
- no perder formularios, filas dinámicas, scroll ni selección;
- eliminar retornos heredados sólo después de migrar consumidores;
- eliminar JavaScript inline de los flujos Beta;
- mantener lenguaje visual único.

### Prioridad 4 — Caja/Cartera

La base de Caja/Cobranza ya existe y se preserva.

La evolución funcional debe respetar:

```text
Ingreso
→ Caja / Cartera
→ Disponibilidad
→ Gestión Administrativa
→ Traslados
→ Orden de Pago
```

No comenzar Orden de Pago antes de que la disponibilidad real de dinero y valores esté cerrada.

### Prioridad 5 — cierre pre-Beta

- suite completa verde;
- recorridos manuales completos;
- segunda auditoría de seguridad;
- `manage.py check --deploy`;
- configuración de producción;
- dependencias reproducibles;
- backup/restore real y adversarial;
- revisión visual final;
- commit candidato y despliegue.

## 8. Qué dejamos para después

Preparar el futuro no significa programarlo hoy.

Post-Beta o posterior, salvo que sea necesario para cerrar un flujo actual:

- Dashboard;
- Reportes avanzados;
- Estado de Resultados;
- Balance;
- Plan Contable;
- marketplace de perfiles;
- ranking y reputación;
- billing completo;
- agenda;
- conciliaciones avanzadas;
- multimoneda;
- notificaciones móviles;
- Legal y Contable completos;
- refactors cosméticos sin impacto en Beta.

## 9. Documentos autoritativos

Para decidir trabajo nuevo, usar este orden:

1. `00_RUMBO_Y_ESTADO.md` — objetivo y prioridad actual.
2. `VISION.md` — identidad y horizonte del producto.
3. `REGLAS.md` — reglas obligatorias de desarrollo.
4. `DECISIONES.md` — decisiones funcionales ya cerradas.
5. `ARQUITECTURA.md` — límites técnicos y reglas transversales.
6. `MODELO_DATOS.md` — invariantes de información.
7. `FLUJO_NAVEGACION.md` — experiencia y navegación.
8. `TODO.md` — trabajo pendiente actual.
9. `PRE_BETA.md` — condiciones bloqueantes de salida.
10. documentos funcionales específicos, como Caja/Cartera o Backup.

`Auditoria.md` registra riesgos actuales y resueltos.

`TRAZABILIDAD_FUENTES.md` y `historico/` sirven como memoria histórica. No deben usarse como instrucciones vigentes cuando contradicen documentos actuales o el código probado.

## 10. Criterio para aceptar una tarea

Antes de abrir un bloque de trabajo debe responderse:

1. ¿Acerca una Beta usable?
2. ¿Corrige un riesgo real de seguridad o integridad?
3. ¿Respeta las decisiones ya tomadas?
4. ¿Evita duplicar reglas?
5. ¿Preserva historia y aislamiento?
6. ¿Tiene pruebas razonables?
7. ¿Evita desarrollar hoy infraestructura futura innecesaria?

Si la respuesta es “no” a las primeras tres, probablemente no sea la tarea correcta ahora.
