# 01_CONTINUIDAD_IA.md — Instrucciones para continuar OrdenaClick en otro chat
> **LEER EL CORTE 15/10/2026:** `CONTINUIDAD_OPERATIVA_20261015.md` y la sección final de este documento prevalecen sobre estados históricos. Código sincronizado hasta `902cdeb`; Colaborador y nuevas mejoras e-Cheq siguen pendientes.


## LEER PRIMERO

Sos una nueva instancia de ChatGPT continuando OrdenaClick. No empieces preguntando de nuevo qué es el proyecto ni proponiendo un rediseño general.

Antes de sugerir cambios:

1. leer `00_RUMBO_Y_ESTADO.md`;
2. leer `BASE_SERVER_SEGURIDAD.md`;
3. leer `VISION.md`;
4. leer `REGLAS.md`;
5. leer `DECISIONES.md`;
6. consultar `ARQUITECTURA.md`, `MODELO_DATOS.md`, `TODO.md`, `PRE_BETA.md` y `Auditoria.md` según la tarea;
7. verificar código/tests actuales antes de confiar en checkboxes.

Código y tests prevalecen sobre documentación histórica.

## Decisión B10a — adjuntos, fotografías y almacenamiento (10/10/2026)

- Límite técnico inicial: **20 MiB por archivo** empresarial/financiero (denominado «20 MB» en la interfaz); certificados y claves ARCA: **1 MiB por archivo**.
- Facturas y comprobantes: contemplar PDF y fotografías desde celular (futuro perfil vendedor/operativo). Admitir sólo formatos permitidos después de validar contenido real, no confiar sólo en extensión o MIME declarado. La validación profunda de formatos y su cobertura completa siguen **pendientes**.
- Archivos en almacenamiento **privado**; en PostgreSQL conservar relaciones y metadatos de titularidad, tamaño, tipo validado, integridad, fechas y trazabilidad. Verificar autorización por Empresa en cada acceso. No almacenar permanentemente binarios de comprobantes en PostgreSQL.
- Medición y cuota futura por **Empresa**, planes/capacidad adicional y costo de proveedor, backups, tráfico y retención: **decisiones comerciales/infraestructura pendientes**, sin valores de cuota o precios aprobados. El límite por archivo **no equivale** a cuota total.
- La compresión/optimización automática y elección de proveedor de objetos quedan para etapa posterior. No eliminar ni bloquear consulta de documentos históricos al alcanzar una cuota: los límites comerciales futuros afectan nuevas cargas.
- Antes de un rechazo por upload inválido, preservar campos no sensibles del formulario; no alterar visual, navegación o botones sin aprobación. No introducir límites sin control previo de persistencia parcial.
- **B10a cerrado técnicamente en las rutas probadas; validación integral pendiente**: queda cubrir documentos del panel Empresa, formatos reales, rutas privadas y controles completos; Base Server no certificada.

## Estado B10a — corte de continuidad 10/10/2026

Publicados y confirmados en `main`: `bb04ef2` (documentos temporales de importación), `d3936a5` (pruebas de descargas privadas), `c49324d` (1 MiB para ARCA), `6f7d9d7` (20 MiB en alta/edición de Movimientos), `07691d2` (20 MiB al registrar Pago manual). El HEAD de código verificado antes de **este commit documental** fue `07691d2`; verificar nuevo HEAD tras publicación. Pruebas de cada tramo aprobadas localmente; no afirmar que eso cierre auditoría integral.

Pendientes de Base Server además de B10a: backup adversarial B10b, dependencias reproducibles y auditoría de vulnerabilidades B10c, todas las rutas y capacidades/roles/Empresa, almacenamiento privado y exposición accidental por `/media/`, recuperación de cuentas, logging/auditoría sensible, proxy real, CSP, HSTS y configuración de producción, `check --deploy`, pruebas integrales de seguridad, revisión visual posterior y despliegue real. Conservar tres respaldos SQLite y el diagnóstico B9b histórico sin seguimiento.

## Corte de continuidad — 10/10/2026

Último commit publicado y confirmado: `7dd9a91` en `main`, sincronizado en la computadora de casa el 10/10/2026. Verificar HEAD y estado antes de aplicar un bloque nuevo. Tres respaldos SQLite antiguos permanecen sin seguimiento en casa; conservarlos y no incorporarlos a Git.

**Cierre técnico B9 (10/10/2026):** B9a (`42d1cb8`): 3 pruebas de reenvíos secuenciales aprobadas. B9b (`2df790b`): idempotencia de pagos manuales por clave, integración JS y migración `usuarios.0042_idempotencia_pago_manual` aplicada; 4 pruebas nuevas aprobadas. B9c (`7dd9a91`): 2 pruebas simultáneas aprobadas con PostgreSQL 17 real (misma clave sin duplicar y claves distintas sin superar saldo). **57 pruebas de regresión aprobadas B1–B9c**. Dos pruebas diagnósticas originales de B9b no se suman; `usuarios/pruebas/test_diagnostico_idempotencia_b9b.py` continúa sin seguimiento local. La configuración de B9c crea `test_test_b9c_ordenaclick` como base temporal; PostgreSQL instalado localmente, SQLite y tres backups sin alteraciones. B9 cerrado para escenarios probados; no representa validación integral de producción.

Autenticación implementada:

- A1 `3b30b60`: validación de contraseñas de registro.
- A2 `ded0e90`: límite de 25 fallos de login por origen durante 10 minutos; requiere migración `usuarios.0041_intentos_login_origen` en cada instalación.
- A3 `62fba91`: contraseña actual requerida sólo al cambiar contraseña; no permite reutilizar la misma, preserva el resto de datos del formulario ante error; mantiene la sesión. 10 tests y UX manual verificados.
- A4 `1296e26`: IP inválida controlada e incremento atómico del contador. 15 tests A2/A4 aprobados. Falta prueba real de concurrencia en PostgreSQL y configuración correcta de proxy.

Desde A4 también publicados: mensajes de error de login y retención de usuario (`8c1fa5b`), `never_cache` al revelar claves empresariales (`a5062aa`), auditoría HTTP B1 (`7b67b28`, 8 tests) y auditoría financiera B2 (`5d68cfb`, 8 tests). B1+B2: 16/16 pruebas aprobadas en casa, luego de aplicar `usuarios.0041` y ejecutar `manage.py check` sin observaciones. B3 de débito automático (`874cf1a`): 8 pruebas HTTP adversariales aprobadas en casa; B4 de eliminación segura de Pagos (`95847d4`): 4 pruebas adversariales aprobadas en casa, incluido fallo simulado que no deja cambios parciales; B5 de lecturas financieras entre Empresas (`7eb847a`): 7 pruebas HTTP adversariales aprobadas en casa; B6 de inventario dinámico de rutas privadas (`6912dd0`): 2 pruebas aprobadas en casa; total B1–B6: 37 pruebas aprobadas en los bloques. B7 de sesiones y estados de acceso (`45ae87a`): 7 pruebas aprobadas en casa; B8 de seguridad HTTP (`a2af447`, ajuste `ee852cb`): 4 pruebas aprobadas en casa tras corregir el test de cookie de sesión; total B1–B8: 48 pruebas aprobadas. No se cambió el flujo de revelación de claves.

Pendientes: recuperación de cuentas, pruebas reales de caducidad de sesiones en navegador, proxy real, autenticación de producción completa, auditoría exhaustiva de rutas, ampliación de pruebas de concurrencia y resto de Base Server y revisión visual integral tras terminar la seguridad. No confundir tests locales con certificación de servidor público.

**Instrucción de UX prevalente:** nunca alterar aspecto, navegación, botones o flujos por seguridad sin aprobación del propietario. Evitar pérdida de datos ingresados ante error; no repoblar contraseñas. Preservar pila `[+]` y retorno al formulario tal como estaba. Los avisos del login ya fueron implementados sin rediseñar la plantilla; cualquier cambio futuro de UX requiere autorización.

**Gestión de Claves:** el propietario rechazó agregar reautenticación al revelado sin autorización expresa. El documento `BASE_SERVER_SEGURIDAD.md` describe una meta, no autoriza imponerla. Mantener la excepción superusuario vigente.

**Cierre de bloque:** tests y revisión manual cuando corresponda; stage selectivo, commit/push; actualizar MD rectores en un commit documental separado cuando cambie el estado. No marcar Base Server cerrada por cierre de subbloques.

## 1. Etapa actual

No agregar nuevas funciones de negocio todavía.

Estamos cerrando una base de arquitectura y seguridad para un SaaS real en servidor público.

Objetivo:

> **BASE ARQUITECTÓNICA Y DE SEGURIDAD PARA SERVER: CERRADA**

Después se vuelve a desarrollo funcional Beta, con REGISTROS como prioridad.

Seguir el orden definido en `BASE_SERVER_SEGURIDAD.md`.

## 2. Superusuario — decisión obligatoria

NO eliminar el acceso actual del superusuario a Empresas.

Por decisión del propietario:

- puede seguir entrando por ahora a Empresas;
- más adelante existirá un panel global dentro del Perfil Desarrollador;
- desde allí podrá habilitar, inhabilitar o suspender acceso;
- configurar capacidades/plan/suscripción;
- exportar una copia de Empresa;
- generar un resumen administrativo futuro.

No implementar ese panel salvo que la tarea lo indique. No ampliar esta excepción a usuarios normales.

## 3. Seguridad

- backend autoridad;
- deny by default;
- auth explícita;
- Empresa autorizada;
- capacidad/rol;
- objetos hijos dentro de Empresa;
- IDs del navegador no prueban autorización;
- POST/CSRF en mutaciones;
- transacciones/locks/idempotencia en finanzas;
- secretos fuera del código;
- archivos privados;
- logs sin secretos;
- `PermissionDenied` no se traga en `except Exception`.

## 4. Arquitectura de usuarios

- fundador = `Empresa.propietario`;
- `AsignacionUsuarioEmpresa` = jerarquía administrativa/operativa;
- admin_general = Empresa;
- admin_centro = Centro;
- colaborador = alcance operativo explícito;
- Contable/Legal = roles funcionales separados;
- Relaciones = solicitudes/vínculos;
- Desarrollador = instalación/superusuario.

Solicitudes pendientes y marketplace futuro no conceden permisos.

## 5. Núcleo financiero

```text
Movimiento != Pago
AplicacionPago = importe aplicado
saldo = total - aplicaciones
Vencimiento = compromiso
Alerta = aviso
```

Nunca aplicar más que saldo. Intereses/costos separados. Desde primera `AplicacionPago` histórica no reescribir estructura económica/documental. Correcciones por reversión controlada.

## 6. Caja/Cartera

```text
Ingreso
→ Caja/Cartera
→ Disponibilidad
→ Gestión Administrativa
→ Traslados
→ Orden de Pago
```

No adelantar Orden de Pago. Caja no desplaza REGISTROS.

## 7. Backup Empresa v1

Existe implementación real. No rediseñar desde cero.

Toda nueva entidad ligada a Empresa exige revisar Export/Import. ZIP es input hostil. No exportar secretos de instalación. Usuarios históricos no equivalen a autorización actual.

## 8. Forma de trabajar

Idioma: español. Estilo compacto, preciso y práctico.

Preferencias del usuario:

- cambios incrementales;
- ZIP aplicadores;
- no edición manual masiva;
- no commit hasta verificación limpia;
- stage selectivo;
- nunca `git add .`;
- no refactors laterales;
- agrupar sólo cuando sea seguro;
- confiabilidad sobre velocidad.

Antes de entregar bloque:

1. baseline exacto;
2. repo limpio;
3. `py_compile` del Python tocado;
4. `manage.py check`;
5. render HTTP real de pantallas afectadas;
6. tests nuevos;
7. regresión de dominio;
8. `git diff --check`;
9. stage selectivo;
10. recién después commit.

Si helper modifica y luego falla, no rerun ciegamente.

## 9. Entorno local

Ruta habitual:

`D:\Emmanuel\Ordenalick`

PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\venv\Scripts\Activate.ps1
```

Secretos de desarrollo por entorno. Nunca pedir valores reales.

## 10. Refactor

Ya hubo separación de templates/assets/HTTP/servicios/tests.

No iniciar nueva campaña por tamaño de archivo. No volver a fragmentar arbitrariamente `panel_pagos.js`: un intento previo rompió Agregar Pago.

## 11. Seguridad ya realizada

Ya se endureció aislamiento por Empresa en Proveedores, Bancos, Cuentas, Tarjetas, Retenciones, Centros, Recursos, Tipos de Gasto, Gestión de Claves, comprobantes, Movimientos, eliminación de Empresa, Backup v1 y Caja.

No repetir desde cero; auditar faltantes.

## 12. Orden Base Server

1. autorización/capacidades;
2. rutas privadas;
3. autenticación/reautenticación;
4. Gestión de Claves;
5. uploads privados;
6. PostgreSQL + settings production;
7. CSP/HTTPS/cookies/headers;
8. logging/auditoría;
9. idempotencia/concurrencia;
10. dependencias/tests server;
11. Backup adversarial;
12. `check --deploy` + auditoría final.

## 13. Después de Base Server

Volver a REGISTROS:

1. Comprobantes punta a punta;
2. Registrar Pago general;
3. Pagos históricos/reversión;
4. Modificar/Eliminar;
5. Carga Planificada/Convertir a Plan;
6. saldo/Vencimientos/Alertas;
7. navegación `[+]` LIFO.

## 14. Protección del producto

El usuario quiere dificultar la réplica. No usar ofuscación inútil.

Mantener valor real en backend: reglas financieras, autorización, disponibilidad, vencimientos, alertas, backup, suscripciones y lógica de negocio.

Repo privado, backend no distribuido, `.git` fuera del deploy, documentación interna no pública, CI/CD privado y secretos externos.

## 15. Infraestructura

El propietario posee:

- `ordenaclick.com`
- `ordenaclick.com.ar`

No pedir contratar todo ahora. Cuando una decisión dependa de infraestructura, indicar claramente qué resolver en chat separado: hosting, PostgreSQL, storage privado, DNS/CDN/WAF, email, monitorización, backup externo o secretos.

## 16. Continuidad

No improvisar nuevo rumbo.

Precedencia:

1. código probado;
2. `00_RUMBO_Y_ESTADO.md`;
3. `BASE_SERVER_SEGURIDAD.md`;
4. `VISION.md`;
5. `REGLAS.md`;
6. `DECISIONES.md`;
7. resto vigente;
8. histórico sólo como contexto.

Al abrir un chat nuevo: verificar HEAD y repo limpio; continuar por el primer punto Base Server no cerrado. No empezar por legacy cleanup, estética, Reportes, marketplace u Orden de Pago.

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

## Continuidad prioritaria: CAJA 1 — 11/10/2026

La instruccion anterior «Caja no desplaza REGISTROS» quedo superada por decision expresa: ahora CAJA es el frente funcional antes de REGISTROS. El codigo base estable es `65b1ab8` (cierre B13 local). No confundir esta etapa con ordenes de compra: se trata de **Ordenes de Pago**.

Primer bloque funcional Caja 1: ingresos/egresos manuales de efectivo en Caja autorizada, saldo no negativo por moneda, historial real por Caja y deduplicacion UUID. No registrar envios internos como egresos sueltos: requieren una operacion con origen, destino y recepcion. No generar pagos de REGISTROS ni recibos externos en este bloque. Los nuevos movimientos usan `MovimientoCaja`, ya incluido en Backup Empresa v1; la tabla de idempotencia es una proteccion local tecnica, no un hecho financiero exportable, siguiendo B9b.

Autorizacion: Fundador/superusuario conservan excepcion; Administrador general puede elegir cualquier Caja habilitada de la Empresa o «Todas» para vistas consolidadas; Administrador de Centro solamente sus Cajas; Colaborador no opera Caja por defecto. El selector nunca otorga autoridad. Para movimientos concretos siempre se exige Caja unica.

Siguiente pendiente funcional: movimientos bancarios detectados por Emmanuel que precisan comprobacion y eventual recibo en sistema externo. Nicolas, Enzo, Juan, Fede u otro autorizado del Centro pueden resolverlos; no dependen de Nicolas. Administradores intervienen ante pendientes prolongados. La bandeja administrativa no concede saldos ni facultad de mover Caja.

No modificar UI preexistente salvo acceso aprobado a funciones nuevas, ni romper pila `[+]`, reautenticacion vigente, aislamiento entre Empresas, backup y servicios financieros. Verificacion local de Caja 1 y commits selectivos de codigo/docs en dos pasos antes de marcar el bloque cerrado.

## Caja 1 — continuidad del historial en dashboard (11/10/2026)
Ajuste propuesto y sujeto a verificaciones locales sobre `b1bf399`: mostrar historial en el panel de Caja, dentro de **Movimientos del día**, por Hoy o Rango de fechas. Selector superior de Caja concreta o Todas (solo alcance autorizado). El formulario Movimiento de Caja no duplica el historial; consume el mismo `MovimientoCaja`. Sin migraciones. No publicar antes de pruebas y revisión.

Caja 2: se aprobó una capacidad independiente de Caja, **gestión de pendientes bancarios por Centro explícitamente autorizado para cada Colaborador**. No asumir que su asignación jerárquica incluye un Centro: en Base Server el Colaborador no lo tiene. Implementar con alcance en backend, sin conceder Caja ni movimiento financiero. Pendientes no identificados: admin general; cualquier usuario autorizado del Centro puede resolver. Esta capacidad NO esta incluida en el parche UX Caja 1.

## Continuidad: Caja 2, permisos y ajustes de historial (11/10/2026)
Base git previa `44f4b33`. Bloque Caja 2 sujeto a verificación local: modelos `PendienteBancario`, `EventoPendienteBancario`, `PermisoPendienteBancarioCentro`, `EventoPermisoBancario`, `CorreccionMovimientoCaja`; migración aditiva `0044`; vistas nuevas de gestión por Empresa/Centro; autorización **en backend**. Admin general/propietario/superusuario: todos los Centros y pendientes por identificar. Admin Centro: su Centro. Colaborador: sólo Centros expresamente concedidos por admin general; sin Caja, sin saldos. Usuario autorizado puede resolver sin depender de Nicolás. El registro de transferencia, depósito o e-Cheq detectado **no crea ingreso, Pago, recibo, ni cartera financiera**: se requiere comprobar imputación en sistema externo y dejar referencia. Eventos auditables de resolución y cambios de permisos. Formularios POST/CSRF, bloqueo transaccional/idempotencia, no asumir producción PostgreSQL comprobada en SQLite.
Caja 1: controles de fecha alineados, encabezado/table de Registros y edición/anulación no destructiva con motivo; sólo movimientos manuales; cobranzas quedan inalterables desde el historial; se generan contraasientos y reemplazos conservando historia y no permitiendo saldo negativo. Backup v1 de hechos actualizado, ZIP antiguos v1 sin nuevas secciones admitidos, privilegios no restaurados. Tras test, commits selectivos código y MD por separado, cuatro archivos locales históricos intactos. Priorizar revisión visual manual.


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

### Retomar Caja 2: Banco buscable, [+] y tipos de pendientes

Base publicada previa: `57cd48d`. Código local preparado, NO asumir push.
En e-Cheq, Banco emisor se elige por sugerencias del ABM activo de la Empresa;
`[+]` invoca el alta existente de Banco desde un modal en la misma página,
conserva la preparación del lote y vuelve con nuevo Banco elegido. En backend
se exige ID de Banco activo de la Empresa: no se aceptan nombres libres ni
IDs ajenos. No requiere migración; el pendiente conserva nombre histórico.
En ambas vistas de bandeja, etiqueta de categoría + color sobrio: depósito/
transferencia turquesa; e-Cheq violeta. No cambiar permisos ni navegación.
Verificar `makemigrations --check`, `check`, tests, revisión en navegador y
recién entonces commit/push código y docs por separado.

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


## Continuidad — Nómina de Empleados y gestor de accesos (14/10/2026)

- **Leer `NOMINA_EMPLEADOS_Y_ACCESOS.md` antes de diseñar el nuevo módulo o modificar perfiles.** Nómina, documentos privados, casos, CAT, licencia y baja laboral están especificados como **futuros**, no implementados.
- Nómina: listado activos verdes / inactivos rojos como Próximos vencimientos, botón Registrar, ficha personal/laboral, DNI frente/dorso, licencia, **Clave de Alta Temprana - CAT**, preocupacional y casos históricos (Legal futuro).
- Vencimiento de licencia: aviso un mes antes mientras el empleado esté activo; **licencia vencida NO desvincula**, **desvincular SÍ desactiva alertas del empleado** conservando historia.
- **Permisos sin decidir definitivamente:** gestión de accesos por usuario, lista de capacidades con interruptores, autorización auditable por Empresa/Centro; colaborador/administrativo/secretaria/contador puede archivar documentación sin ser jerárquico ni obtener Caja o facultades sensibles. No conceder accesos nuevos por inferencia.
- Navegación `[+]` a ABM existentes con regreso al borrador/scroll; modales en zona visible. Datos personales, médicos y laborales privados con controles backend y backup compatibles. Código publicado previo: `e5ace71` (Estado e historial e-Cheqs, pruebas 67); este bloque no contiene implementación de Nómina ni Alertas.

## Corte de continuidad prioritario — 15/10/2026, Oficina

**No comenzar desde cero.** Código Casa/GitHub/Oficina alineado en `902cdeb`, previo estado Oficina `b89ff5a`. Backup SQLite de Oficina fuera de repo verificado mediante `sqlite3.backup` e integridad; migraciones usuarios `0048`/`0049`/`0050` aplicadas; 35 pruebas de regresión aprobadas en Oficina (también Casa). Antiguos cambios locales Oficina Caja 2 inconclusos guardados en `stash@{0}`: **no recuperar ni eliminar automáticamente**. Comprobar estado Git antes de trabajar.

**Estado actualizado:** Caja 2 y Nómina existen en código. Nómina bajo **Herramientas**, mail y teléfono laboral separados de contactos personales; gestor granular no implementado; el usuario expresó conformidad visual general en Oficina («Están todos bien»); no dejó detalle separado de cada recorrido `[+]`. Las frases de este documento de 10–14/10 que las describen «futuras» ya no expresan el estado vigente.

**Capturas / observaciones de uso real e-Cheq (SIN implementar aún):** en tabla de precarga/revisión separar Número e-Cheq y Titular; sumar Fecha acreditación; guardado de lote arroja «El importe no es válido» sin identificar ni resaltar dónde. Validar al Agregar y editar, conservar el lote si falla y revisar parseo de `126.785,71` sin asumir causa. Seguir tomando notas hasta que el usuario autorice abordar los cambios juntos.

**Colaborador:** casi idéntico al panel Administrador en experiencia e infraestructura, **con menos funciones según permisos**. No duplicar panel ni ABM; diseñar cada nueva función admin pensando en posible habilitación a Colaborador. Preparar permisos por usuario/módulo/acción para futuro panel de accesos, siempre aplicados en backend según Empresa/Centro y denegados por defecto. Primer caso para probar: Pendientes bancarios con datos reales; todavía falta desarrollar el acceso funcional Colaborador. Nómina sensible sigue restringida.

**Entrega de cambios cuando se autoricen:** revisar código actual y componentes reales antes de crear un helper `.py` descargable a raíz junto a `manage.py`, con preflight exacto, backup externo verificado, escritura atómica/rollback, pruebas y revisión visual. No retocar otros módulos ni copiar carpetas enteras, no `git add .`, `reset --hard` o `stash pop`. Tras verificación, **commit selectivo y push** como trabajo en desarrollo: GitHub es continuidad Casa/Oficina, no requisito de aceptación final.

**Documento completo de relevo:** `CONTINUIDAD_OPERATIVA_20261015.md` (incluye contexto de Casa/Oficina, rutas, SQLite, seguridad, navegación `[+]` LIFO, estética, permisos y criterios de helpers). Leerlo antes de sugerir implementación o hacer preguntas ya resueltas.

## CIERRE PERMISOS REGISTROS Y BANCARIOS 2026-10-22 — implementación controlada

- Gestión de Accesos: Registros (consultar, crear, editar, Obligaciones informativas) y Pendientes bancarios (consultar, precargar, editar/auditar, confirmar, estado y salidas e-Cheq) disponibles por casillas explícitas y auditadas; ninguna función inexistente muta datos. La pantalla Obligaciones sigue informativa/en desarrollo.
- Pendientes bancarios continúan GLOBALES dentro de la Empresa hasta la confirmación. El Centro Operativo se determina recién cuando el usuario confirma, y el backend valida los Centros de su alcance. Los Resueltos solo se ven por Centro autorizado, salvo administración general. No generar Caja, Pago, Recibo ni saldo por esa confirmación.
- Asignaciones bancarias POR CENTRO previamente otorgadas mantienen compatibilidad. La primera configuración explícita desde Gestión de Accesos prevalece sobre concesiones legadas, incluyendo revocaciones de acciones; la auditoría permanece intacta.
- Registros: leer selectores de ABM no permite modificarlos. Consultar/crear/editar comprobantes NO concede Registrar Pago, débito automático ni Caja; los endpoints de pago mantienen su autorización histórica independiente. Administrador de Centro queda limitado a sus Centros, sin abrir Configuración. La jerarquía Administrador general NO concede por sí sola la escritura de Movimientos, conforme a la prueba histórica de seguridad.
- Un solo sidebar compartido, sin nuevos botones flotantes, sin cambiar jerarquías, CSS ni retornos. Nómina por Centro, claves propias y permisos de Caja permanecen independientes.
- **Instalación y regresiones verificadas en Casa:** el helper aplicó los cambios, `manage.py check`, `makemigrations --check --dry-run` y la suite seleccionada terminaron sin fallos. **Aún falta aprobación visual/funcional por perfiles y commit selectivo.**


## Continuidad de implementación — Alertas Bloque A (23/10/2026)

Baseline verificado GitHub `main`: `0c09140b4f38db3005d290d8120349e044b32b83`.
La nota de 22/10 que indicaba "commit pendiente" es histórica: ese commit se publicó.
La siguiente evolución aprobada separa Alertas como módulo principal del sidebar,
sin reemplazar el panel Administrar ni agregar navegación superior. Próximos
vencimientos conserva Hoy, Esta semana y Rango de fechas. La campanita conserva
animación y sonido, con navegación dentro de `#contenido-operativo`.
`alertas.ver` no sustituye permisos de origen ni habilita información sensible.
No se configura aún suscripción/lectura por destinatario ni eventos de Pendientes
bancarios u Órdenes de Pago. Helpers: `--plan`, `--apply`, SHA, backup externo,
rollback y pruebas con aprobación visual antes de commit.
La aplicación de este helper NO certifica Beta ni sustituye pruebas locales.
