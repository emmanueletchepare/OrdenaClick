# OrdenaClick — Rumbo y estado actual

**Última actualización:** 10/10/2026
**Objetivo operativo:** llegar a una Beta usable, estable y segura durante noviembre de 2026.

Este documento es el punto de entrada para entender qué es OrdenaClick, qué estamos construyendo ahora y qué queda deliberadamente para después.

**Corte Base Server (10/10/2026):** B1 (`7b67b28`), B2 (`5d68cfb`), B3 (`874cf1a`) y B4 (`95847d4`) publicados. B1+B2: 16 pruebas HTTP/financieras aprobadas en casa; B3: 8 pruebas de débito automático aprobadas en casa (24 pruebas en B1–B3); B4: 4 pruebas de eliminación segura de Pagos aprobadas en casa (28 en B1–B4); B5 (`7eb847a`): 7 pruebas de aislamiento en lecturas de vencimientos, alertas y edición de Movimientos aprobadas en casa (35 en B1–B5); B6 (`6912dd0`): 2 pruebas de inventario dinámico de rutas privadas aprobadas en casa (37 en B1–B6); B7 (`45ae87a`): 7 pruebas de sesiones y estados de acceso aprobadas en casa (44 en B1–B7); B8 (`a2af447`, corrección `ee852cb`): 4 pruebas HTTP/CSRF/cookies aprobadas en casa (48 en B1–B8); migración `usuarios.0041` aplicada y `manage.py check` sin observaciones. Siguen pendientes auditoría exhaustiva de rutas, ampliación de pruebas financieras, infraestructura de producción y recorrido visual integral posterior al cierre de seguridad. Los respaldos SQLite locales de casa no se alteran.

**Cierre técnico B9 (10/10/2026):** B9a (`42d1cb8`): 3 pruebas de reenvíos secuenciales aprobadas. B9b (`2df790b`): idempotencia por clave única para pagos manuales, integración de envío, migración `usuarios.0042_idempotencia_pago_manual` aplicada y 4 pruebas nuevas aprobadas. B9c (`7dd9a91`): 2 pruebas de concurrencia aprobadas sobre PostgreSQL 17 real, para igual clave y para claves distintas con saldo insuficiente. **57 pruebas de regresión aprobadas en B1–B9c** (48 + 3 + 4 + 2). El diagnóstico B9b anterior (2 tests) documentó el riesgo original y no integra ese total. B9 queda cerrado en el alcance ensayado; no equivale a despliegue ni seguridad de producción certificados.

## Decisión B10a — adjuntos, fotografías y almacenamiento (10/10/2026)

- Límite técnico inicial: **20 MiB por archivo** empresarial/financiero (denominado «20 MB» en la interfaz); certificados y claves ARCA: **1 MiB por archivo**.
- Facturas y comprobantes: contemplar PDF y fotografías desde celular (futuro perfil vendedor/operativo). Admitir sólo formatos permitidos después de validar contenido real, no confiar sólo en extensión o MIME declarado. La validación profunda de formatos y su cobertura completa siguen **pendientes**.
- Archivos en almacenamiento **privado**; en PostgreSQL conservar relaciones y metadatos de titularidad, tamaño, tipo validado, integridad, fechas y trazabilidad. Verificar autorización por Empresa en cada acceso. No almacenar permanentemente binarios de comprobantes en PostgreSQL.
- Medición y cuota futura por **Empresa**, planes/capacidad adicional y costo de proveedor, backups, tráfico y retención: **decisiones comerciales/infraestructura pendientes**, sin valores de cuota o precios aprobados. El límite por archivo **no equivale** a cuota total.
- La compresión/optimización automática y elección de proveedor de objetos quedan para etapa posterior. No eliminar ni bloquear consulta de documentos históricos al alcanzar una cuota: los límites comerciales futuros afectan nuevas cargas.
- Antes de un rechazo por upload inválido, preservar campos no sensibles del formulario; no alterar visual, navegación o botones sin aprobación. No introducir límites sin control previo de persistencia parcial.
- **B10a cerrado técnicamente en las rutas probadas; validación integral pendiente**: queda cubrir documentos del panel Empresa, formatos reales, rutas privadas y controles completos; Base Server no certificada.

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

## 6.2. Avance verificado de Base Server — 10/10/2026

Estado: **EN CURSO**, no cerrada ni autorizada para Internet.

- A1, validación de contraseñas en registro: cerrado (`3b30b60`).
- A2, límite de intentos de login por origen y ventana: cerrado (`ded0e90`).
- A3, cambio de contraseña con contraseña actual, validación de nueva contraseña, rechazo si es igual y conservación de datos no sensibles ante errores: cerrado (`62fba91`), 10 tests y pruebas visuales confirmadas.
- A4, robustez del contador de login ante IP inválida y actualizaciones atómicas: cerrado (`1296e26`), 15 tests de A2/A4 aprobados localmente. **No** equivale a prueba de concurrencia real en PostgreSQL.
- Configuración de producción separada (`ordenaclick/settings_production.py`), con PostgreSQL, HTTPS y almacenamiento privado: existe como base; falta validación de despliegue.
- Se avanzó en autorizaciones por Empresa, archivos legales privados y backup temporal; **no** equivalen a auditoría final de todas las rutas ni de todos los archivos.

Pendientes relevantes: recuperación de contraseña, política y pruebas de sesión, avisos de error no visibles en la plantilla actual del login, verificación de correo según alcance, registro/rate limiting y auditoría de eventos sensibles, proxy confiable y concurrencia real con PostgreSQL, rutas privadas, uploads, secretos, cabeceras/CSP, logging, finanzas e idempotencia, Backup adversarial, dependencias y `check --deploy`.

**Decisión de producto:** seguridad y refactors no autorizan cambios visuales, botones, navegación ni flujos. Requieren acuerdo explícito. Un error de validación conserva los datos no sensibles ingresados; la contraseña nunca se repuebla. Mantener el retorno contextual `[+]` sin perder estado. La reautenticación para revelar claves empresariales **no está autorizada actualmente**: no implementarla por iniciativa propia aunque figure como objetivo histórico del documento de seguridad. Superusuario mantiene su excepción de acceso acordada.

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

## Actualización de continuidad B10a–B10c (11/10/2026)

**Estado de Base Server: EN CURSO.** Los cierres siguientes son técnicos y se limitan al alcance probado; no certifican un servidor público ni una auditoría integral.

- **B10a — cierre técnico en las rutas ensayadas.** Importación temporal protegida (`bb04ef2`); descargas privadas con pruebas (`d3936a5`); límite de 1 MiB para archivos ARCA (`c49324d`); límite de 20 MiB para adjuntos de Movimientos (`6f7d9d7`) y Pago manual (`07691d2`); documentos de Empresa validados (`7517ec7`). Se aprobaron las pruebas focalizadas y la verificación manual de UX del panel Empresa. **Pendiente fuera del alcance B10a probado:** validación profunda de contenido/formato, inventario exhaustivo de otras rutas de carga, acceso privado de punta a punta y configuración del almacenamiento productivo.
- **B10b — cierre técnico de casos adversariales ensayados.** Validación de backup ZIP ante entradas adversariales (`aa7d64c`) y pruebas de reversión de archivos/restauración (`1222c66`). La ejecución focalizada concluyó **12/12 pruebas aprobadas**, incluyendo rollback. No equivale a ensayar almacenamiento externo, cifrado, retención ni recuperación real en infraestructura productiva.
- **B10c — cierre técnico de dependencias en el entorno local.** Python 3.12.10, Django 6.0.9 y sqlparse 0.6.0; `pip check` y `manage.py check` sin observaciones; `pip-audit` reportó **0 vulnerabilidades conocidas** para el inventario auditado el 11/10/2026; **11/11 pruebas de regresión focalizadas aprobadas**. Versiones exactas registradas en `requirements.txt` (`33645d2`). La suite global se interrumpió por aparente bloqueo y **no debe presentarse como aprobada**; instalación reproducible por hashes y despliegue CI/productivo siguen pendientes.
- **Último HEAD de referencia comprobado:** `33645d2` en `main`, sincronizado con `origin/main` antes de este cambio documental. Verificar el nuevo HEAD después de publicarlo.
- **Protecciones de producto:** preservar sin cambios pantallas, estilos, navegación contextual `[+]`, botones, datos no sensibles ante errores, contraseñas no repobladas y la excepción vigente de superusuario. No introducir reautenticación para revelar claves de Empresa sin autorización expresa.
- **Próximos pendientes Base Server:** revisión de rutas privadas y permisos/capacidades por Empresa; exposición de archivos y `/media/`; recuperación de cuenta y sesiones; logging/auditoría; configuración de producción detrás de proxy, cabeceras/CSP/HSTS, `check --deploy`, backups externos y recorrido visual final. No declarar Base Server certificada.

## B11 — cierre técnico de rutas y permisos (11/10/2026)

- **Alcance revisado:** 84 rutas activas con nombre en `usuarios/urls.py`: 2 públicas (login/registro) y 82 privadas. Se revisaron las 24 vistas HTTP del proyecto y la capa de capacidades. La prueba dinámica B6 mantiene la exigencia de login por GET y POST para rutas privadas; B1/B5/B7/B8 y las pruebas existentes de maestros complementan la cobertura.
- **Hallazgo corregido:** se eliminó en `usuarios/http/administrador.py` el borrado físico de una Empresa durante el alta de otra por indicadores de sesión del importador ZIP antiguo. El alta ahora descarta esos indicadores sin borrar otras Empresas. Backup Empresa v1 continúa como mecanismo autorizado de restauración.
- **Regresión nueva:** `usuarios/pruebas/test_b11_rutas_permisos_y_altas.py` protege altas con sesión heredada, lecturas y escrituras entre Empresas, diferencias entre administrador general, administrador de Centro y colaborador, excepción vigente de superusuario, eliminación de Empresa mediante POST y ausencia de publicación de funciones de importación ZIP antiguo. **10 pruebas B11** con subcasos por ruta; cierre técnico sujeto al resultado local de la batería focalizada.
- **Sin cambios de producto:** no cambian estética, CSS, JS, botones, pantallas, formularios, navegación `[+]`, roles vigentes ni recuperación de entradas no sensibles. Se preserva la excepción actual de superusuario y no se añade reautenticación al revelado de claves.
- **Límites del cierre:** este bloque no certifica todas las combinaciones de objetos/roles ni la seguridad de un servidor público; quedan B12/B13 para cuentas, medios privados, recuperación, registros de auditoría, proxy, TLS/CSP, `check --deploy`, pruebas de infraestructura y revisión final. La suite global no se considera aprobada por este bloque. **Base Server continúa EN CURSO.**

## B12 — cierre técnico condicionado a verificación local (11/10/2026)

- **Rutas públicas de recuperación:** se añaden cuatro rutas de recuperación a las dos públicas existentes; la prueba dinámica B6 se actualiza para excluir esas cuatro rutas públicas, conservando cobertura de todas las privadas.
- **Recuperación de cuentas:** se activa el enlace «No recuerdo mi contraseña» que ya existía en el login, sin agregar botones ni cambiar su aspecto. Django genera enlaces de un solo uso válidos por 30 minutos; se confirma la nueva contraseña con validadores existentes, sin identificar cuentas inexistentes en la respuesta. El flujo de correo real exige un proveedor SMTP configurado al desplegar; las pruebas usan email simulado y no demuestran envío público real.
- **Registro y abusos:** registro y recuperación limitan 25 solicitudes por origen/10 minutos, en buckets separados del login (sin permitir bloquear contraseñas de otros usuarios). El registro conserva los datos no sensibles ante rechazo; jamás repuebla contraseñas.
- **Archivos privados:** se elimina la ruta genérica `/media/` también en desarrollo; las descargas legales autorizadas por Empresa y Backup v1 siguen mediante sus endpoints. En producción `MEDIA_ROOT` permanece privado y fuera del proyecto; servidor/proxy no deben servirlo de manera directa. Los demás adjuntos financieros requieren cobertura progresiva de descargas autorizadas al publicarse su consulta.
- **CSP/TLS:** se prepara CSP **sólo report-only** en producción, sin bloquear scripts o estilos existentes. Cookies seguras y HTTPS del settings productivo se conservan. HSTS permanece desactivado (`0`) hasta validar proxy, TLS y subdominios reales. El recolector CSP externo y endurecimiento de CSP activa corresponden a despliegue/recorrido UI, no se simulan como aprobados.
- **Auditoría:** eventos mínimos de login/registro, cambio y recuperación de contraseña, exportación/restauración de Backup y revelación de claves; los mensajes contienen sólo tipo de evento e identificadores internos, nunca contraseñas, tokens, correos, ZIP ni claves. Infraestructura de logs, retención y centralización se eligen al desplegar.
- **Cierre de sesión aprobado:** se sustituye GET por POST con CSRF en los cinco accesos actuales (Inicio, Administración, Colaborador, Contable y Legal), preservando ubicación, texto y estilos. GET deja de cerrar sesiones y se verifica la exigencia de CSRF.
- **UX:** se preservan apariencia de pantallas actuales, botones, navegación contextual `[+]`, lógica financiera, jerarquías y excepción del superusuario. Las páginas nuevas de recuperación replican el lenguaje visual del ingreso; no se añadió reautenticación para ver secretos empresariales.
- **Límites de prueba:** cobertura focalizada de B12 y regresiones previas condicionada a ejecución local. No está ejecutada la suite global; faltan pruebas con proveedor de correo, proxy real, HSTS/CSP y `check --deploy`, además de el inventario final de recursos públicos y pruebas de integración con infraestructura. Estos son asuntos de B13/despliegue. **Base Server continúa EN CURSO y no está certificada para producción.**

## B13 — verificacion final LOCAL de Base Server (11/10/2026)

- **Estado:** cierre tecnico/arquitectonico LOCAL, condicionado a bateria focalizada y auditoria `verificar_b13.py` ejecutadas en la instalacion de desarrollo; NO equivale a certificacion ni autorizacion para publicar OrdenaClick en Internet.
- **Configuracion de publicacion de archivos estaticos:** `settings_production.py` exige `ORDENACLICK_STATIC_ROOT` fuera del repositorio y distinto de `ORDENACLICK_PRIVATE_MEDIA_ROOT` sin solapamientos; se mantiene prohibida la exposicion directa del media empresarial. No cambia `settings.py` de desarrollo ni las pantallas.
- **Comprobaciones B13:** suite de regresion seleccionada A1–B12 (sin la suite global que anteriormente se interrumpio), `manage.py check` de desarrollo, `manage.py check --deploy` con variables FICTICIAS y sin conexiones reales, y `collectstatic --dry-run` con destino temporal externo. El test `test_b13_configuracion_produccion.py` comprueba aislamiento static/media, HTTPS/cookies/CSP configurados, valores obligatorios y ausencia de `/media/` publico.
- **Advertencia expresamente pendiente:** `security.W004` por `SECURE_HSTS_SECONDS=0` es deliberada hasta comprobar certificado, proxy y subdominios REALES; no se silencia ni se describe como seguridad aprobada. CSP continua en modo `report-only`, sin habilitar una politica bloqueante que rompa la UI.
- **Fuera del alcance de la comprobacion local:** despliegue real WSGI/ASGI, PostgreSQL productivo, proxy confiable, TLS y HSTS, DNS, SMTP y entregabilidad/recuperacion real, permisos de filesystem/objeto, persistencia y restauracion de backups externos cifrados, monitorizacion/retencion de logs, inspeccion de CSP y recorrido integral visual/funcional del navegador. Requieren infraestructura real, pruebas y decisiones posteriores.
- **Continuidad:** se puede retomar REGISTROS como desarrollo funcional tras publicar el cierre B13 validado localmente; no anunciar Base Server como certificada para produccion. Permanecen intocables la estetica, botones, navegacion contextual `[+]`, historial financiero y excepcion de superusuario. Conservados los cuatro archivos historicos no rastreados.

## Repriorizacion funcional tras cierre local Base Server — 11/10/2026

- **Prioridad vigente: CAJA**, antes de retomar REGISTROS y antes de Ordenes de Pago. Esta actualizacion prevalece sobre las listas de prioridades historicas que colocaban REGISTROS primero.
- **Caja 1:** registro manual de entradas y salidas de efectivo, saldo por moneda y Caja, historial paginado y alcance Admin general/Administrador de Centro. Usa `MovimientoCaja` existente y agrega deduplicacion tecnica por UUID; su cierre depende de check, migracion y pruebas locales.
- Luego: bandeja de transferencias/depositos y e-Cheqs pendientes de recibo/aplicacion en el sistema externo, operables por cualquier persona autorizada del Centro, no solamente Nicolas; supervisan administradores si siguen pendientes. Esta gestion no crea una segunda Cobranza.
- Siguientes: Cartera/disponibilidad y pagos individuales, envios internos entre Cajas con recepcion/conflictos, Bancos (descubierto configurado en ABM de Cuentas Bancarias), y finalmente Orden de Pago colaborativa.
- Todo modulo nuevo mantiene las garantias de Base Server: autorizacion backend por Empresa/Centro, CSRF, idempotencia, transacciones, aislamiento multiempresa, auditoria y Backup Empresa v1. El cierre local de Base Server no certifica despliegue publico.

## Caja 1 — ajuste UX de historial (11/10/2026; cierre sujeto a prueba local)
El listado de entradas, salidas y efectivo de cobranzas se traslada al panel principal **Movimientos del día**, con selector **Hoy / Rango de fechas**, paginacion y alcance por Caja o Todas. La pantalla **Movimiento de Caja** queda dedicada a registrar sin historial duplicado. El endpoint del listado impone Empresa y Cajas autorizadas en servidor; no modifica saldos ni migraciones.

**Decisión para Caja 2:** se autoriza que Administradores generales asignen explicitamente Centros para gestionar pendientes bancarios a Colaboradores, sin conceder Caja ni saldos bancarios. Todavia no implementado en este ajuste; requiere modelo, administración, pruebas de alcance y respaldo.

## Caja 2 — Pendientes bancarios y corrección UX Caja 1 (11/10/2026)
Bloque de Caja posterior al historial `44f4b33`. Implementación **sujeta a aprobación de migración y pruebas locales**: gestión de depósitos, transferencias y e-Cheqs observados en banco como pendientes de aplicación externa; permisos explícitos por Centro para colaboradores; resolución con referencia y actor, sin crear Pago/Cobranza ni alterar saldos. Vista de Caja 1: Desde/Hasta en paralelo, columnas y encabezados coherentes con Registros, acciones Editar/Eliminar exclusivamente sobre movimientos manuales mediante contraasiento, motivo y auditoría. Eliminar equivale a **anular contablemente**, nunca DELETE físico. Nueva migración aditiva `0044`. Backup Empresa v1 incorpora hechos nuevos, sin importar privilegios de Colaboradores; restauración compatible con ZIP v1 anteriores.
Pendientes posteriores: traslados internos y controversias de recepción, Cartera/e-Cheqs financieros, depósitos/arqueos, descubierto desde ABM Cuenta Bancaria, disponibilidad real para Pago y luego OP colaborativas; auditoría con casos de conflicto. No certificar instalación pública.
