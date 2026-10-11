# BASE_SERVER_SEGURIDAD.md — Base de arquitectura y seguridad orientada a servidor

**Fecha de decisión:** 08/10/2026
**Estado:** rumbo obligatorio antes de retomar el desarrollo funcional intensivo.

## Estado de ejecución al 10/10/2026

**EN CURSO.** Esta hoja de ruta no certifica por sí misma que OrdenaClick sea seguro para Internet.

Cerrados y publicados: registro con validación de contraseña (A1 `3b30b60`); rate limiting de login (A2 `ded0e90`); cambio de contraseña con comprobación de actual y preservación de datos ante errores (A3 `62fba91`); manejo de IP inválida y actualización atómica de contador (A4 `1296e26`); errores visibles del login (`8c1fa5b`); respuestas `never_cache` al revelar claves (`a5062aa`); auditoría HTTP B1 (`7b67b28`), financiera B2 (`5d68cfb`), débito automático B3 (`874cf1a`), eliminación segura de Pagos B4 (`95847d4`) y lecturas financieras entre Empresas B5 (`7eb847a`) , inventario dinámico de rutas privadas B6 (`6912dd0`) y auditoría de sesiones B7 (`45ae87a`) y seguridad HTTP B8 (`a2af447`, corrección `ee852cb`). A3: 10 tests y verificación visual; A2/A4: 15 tests locales; B1+B2: 16 tests aprobados en casa el 10/10/2026; B3: 8 tests aprobados en casa (24 para B1–B3); B4: 4 tests aprobados en casa (28 para B1–B4); B5: 7 tests aprobados en casa (35 para B1–B5); B6: 2 tests aprobados en casa (37 para B1–B6); B7: 7 tests aprobados en casa (44 para B1–B7); B8: 4 tests HTTP/CSRF/cookies aprobados en casa (48 para B1–B8; commits `a2af447` y `ee852cb`). PostgreSQL y concurrencia multiproceso **sin verificar**.

**B9 — cierre técnico (10/10/2026):** B9a (`42d1cb8`): 3 pruebas secuenciales aprobadas. B9b (`2df790b`): idempotencia persistida e integración JS para pagos manuales, migración `usuarios.0042_idempotencia_pago_manual` aplicada, 4 pruebas nuevas aprobadas. B9c (`7dd9a91`): 2 pruebas de concurrencia aprobadas contra PostgreSQL 17 real, con la misma clave y con claves distintas sin exceder el saldo. **57 pruebas de regresión aprobadas entre B1 y B9c**. Dos tests diagnósticos originales B9b documentan el riesgo previo y no cuentan en el total. Cierre limitado a escenarios probados, sin certificar servidor expuesto, infraestructura de producción ni concurrencia de otros módulos.

Existe `ordenaclick/settings_production.py` como configuración separada; **no** hay despliegue validado. Quedan pendientes: prueba detrás de proxy real, recuperación de cuenta, política de sesión y pruebas de caducidad, verificación de correo según alcance, auditoría/rate limiting de registro, revisión exhaustiva de archivos privados y de todas las rutas/capacidades, logging, CSP, dependencias, backups adversariales, ampliación de cobertura financiera a otros circuitos y pruebas `check --deploy`. La revisión visual y funcional integral se hará después de terminar la implementación de seguridad.

**Precedencia de decisiones de producto:** no modificar UX, navegación, botones o flujo en nombre de la seguridad sin autorización explícita. Ante validaciones, preservar todos los datos no sensibles ingresados; no repoblar passwords. Respetar navegación contextual `[+]`. La reautenticación para revelar secretos empresariales descripta en la sección 7 es una **meta pendiente no autorizada para implementación** por decisión expresa del propietario; no introducirla unilateralmente. Se preserva el acceso especial del superusuario indicado en la sección 3.

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

## 1. Objetivo

OrdenaClick continuará su desarrollo sobre una base pensada desde ahora como producto SaaS real, expuesto a Internet, multiusuario y multiempresa.

No existe riesgo cero en un sistema conectado a Internet. El objetivo es aplicar defensa en profundidad, impedir accesos no autorizados, limitar el impacto de una cuenta comprometida y conservar trazabilidad suficiente para investigar operaciones sensibles.

La etapa se considera cerrada únicamente cuando podamos declarar:

> **BASE ARQUITECTÓNICA Y DE SEGURIDAD PARA SERVER: CERRADA**

Después de ese punto, el desarrollo funcional continúa respetando esta base sin rediseñar autenticación, autorización, archivos, secretos, concurrencia o configuración de producción en cada módulo.

## 2. Principios obligatorios

1. Backend como autoridad.
2. Denegar por defecto.
3. Autenticación explícita en toda ruta privada.
4. Autorización por capacidad y alcance.
5. Todo objeto hijo se reconsulta dentro de la Empresa autorizada.
6. IDs enviados por navegador nunca prueban autorización.
7. Operaciones sensibles usan POST, CSRF y validación backend.
8. Operaciones financieras críticas usan transacción, locking e idempotencia.
9. Secretos nunca se envían al frontend salvo revelación explícita autorizada.
10. Archivos empresariales son privados por defecto.
11. Configuración de producción separada de desarrollo.
12. Logs y auditoría no almacenan secretos.
13. El conocimiento de negocio valioso permanece principalmente en servidor.
14. Seguridad visual no sustituye controles backend.
15. Los controles nuevos deben ser reutilizables y testeables.

## 3. Superusuario / Perfil Desarrollador — decisión vigente

Por decisión de producto, **el superusuario de OrdenaClick conserva por ahora acceso a las Empresas**. No se eliminará en esta etapa la posibilidad de que `is_superuser` atraviese las barreras de Empresa existentes. Esta excepción es deliberada y temporal.

El Perfil Desarrollador evolucionará hacia un panel global de administración de plataforma. Ese panel deberá permitir al superusuario:

- listar/localizar Empresas;
- consultar estado comercial y técnico;
- habilitar, inhabilitar o suspender acceso;
- configurar capacidades, plan o suscripción;
- resolver incidencias de acceso;
- exportar una copia autorizada de la Empresa;
- generar un resumen administrativo de la Empresa, a desarrollar posteriormente;
- ejecutar funciones técnicas globales expresamente definidas.

El objetivo es que el superusuario no necesite operar directamente sobre la base de datos para administrar la plataforma.

Cuando ese panel exista se revisará si el acceso directo del superusuario a pantallas operativas se mantiene, se limita, requiere modo soporte o queda sujeto a auditoría reforzada. Esa decisión no se anticipa ahora.

## 4. Capacidades y alcance

La autorización debe evolucionar desde helpers estructurales hacia una capa explícita de capacidades.

Ejemplos:

```text
empresa.administrar
empresa.backup
empresa.restaurar
movimientos.ver
movimientos.crear
movimientos.modificar
pagos.crear
pagos.revertir
claves.ver_metadatos
claves.revelar_secreto
caja.ver
caja.operar
```

Cada capacidad se resuelve con un alcance: Empresa, Centro Operativo, Caja o ninguno.

No implementar una matriz futura completa antes de necesitarla, pero toda nueva funcionalidad debe encajar en este modelo.

## 5. Auditoría de rutas privadas

Antes de cerrar Base Server se revisa `usuarios/urls.py` ruta por ruta. Cada endpoint privado debe tener:

- autenticación explícita;
- método HTTP correcto;
- CSRF cuando corresponda;
- Empresa autorizada;
- capacidad/rol;
- objeto hijo acotado a Empresa;
- respuesta controlada;
- test anónimo;
- test cross-Empresa cuando corresponda.

No aceptar seguridad accidental porque una función interna termine lanzando `PermissionDenied`.

## 6. Autenticación

Antes de servidor público:

- validadores de contraseña realmente aplicados en registro/cambio;
- cambio de contraseña con reautenticación;
- recuperación de cuenta;
- verificación de correo cuando corresponda;
- rate limiting/backoff de login y registro;
- política de sesiones;
- MFA para perfiles de alto privilegio cuando se implemente esa etapa;
- hash de contraseñas adecuado para producción;
- auditoría de eventos sensibles.

## 7. Gestión de Claves

La revelación de una contraseña empresarial es una operación de alto privilegio.

Objetivo:

```text
usuario autorizado
→ capacidad claves.revelar
→ reautenticación
→ descifrado
→ respuesta no-cache
→ evento de auditoría
```

Migrar la revelación fuera de GET. Nunca registrar la contraseña.

## 8. Archivos y uploads

Los archivos de Empresa no deben exponerse como directorio público en producción.

Arquitectura objetivo:

```text
usuario
→ endpoint autenticado
→ Empresa/capacidad
→ archivo
→ descarga controlada
```

o almacenamiento privado con URL firmada de vida corta.

Controles mínimos: tamaño, tipo/extensión, nombres seguros, `Content-Disposition`, `nosniff`, no ejecución, acceso privado, limpieza de temporales y futura evaluación de antivirus.

## 9. Base de datos y concurrencia

SQLite queda para desarrollo local. Producción debe usar PostgreSQL.

Los tests que dependan de locking real deben ejecutarse contra PostgreSQL.

Operaciones críticas:

```text
autorización
→ idempotencia
→ transaction.atomic
→ select_for_update
→ recalcular
→ persistir
→ auditoría
```

Aplica especialmente a Pago, AplicacionPago, Cobranza, Traslados, Orden de Pago, reversas y disponibilidad.

## 10. Configuración de producción

Separar configuración:

```text
settings/
    base.py
    development.py
    production.py
```

Producción debe exigir: `DEBUG=False`, hosts/orígenes explícitos, HTTPS, cookies seguras, HSTS según infraestructura, cabeceras seguras, proxy correcto, PostgreSQL, staticfiles de producción, storage privado, logging, secretos externos y `manage.py check --deploy`.

No utilizar `runserver` como servidor público.

## 11. CSP y frontend

Adoptar Content Security Policy.

Primero report-only e inventario de violaciones. Después CSP activa. Eliminar JavaScript inline en flujos Beta. El frontend contiene UX, no autoridad de negocio.

## 12. Logging y auditoría

`PermissionDenied` no debe ser absorbido por `except Exception`.

Errores inesperados:

```text
logger.exception
→ mensaje genérico al cliente
→ sin secreto/payload sensible en logs
```

Auditar: login/fallos, cambio de contraseña, roles/capacidades, suspensión/habilitación, revelación de claves, export/restore, eliminaciones/reversiones, operaciones financieras sensibles y cambios técnicos de Desarrollador.

## 13. Dependencias y cadena de suministro

Antes de Beta pública: dependencias reproducibles, versiones controladas, análisis de vulnerabilidades, repo privado, CI/CD privado, secretos fuera del repo y `.git` fuera del deploy.

## 14. Backup Empresa v1

Completar batería adversarial: ZIP corrupto, límites, JSON inválido, referencias rotas, versión no soportada, autoelevación, rollback, adjuntos y restore real.

En producción: backups cifrados, copia externa, retención y restore probado.

El superusuario conserva capacidad de exportar una Empresa.

## 15. Protección del producto y dificultad de réplica

No basar la protección en ofuscación frágil.

El valor diferencial debe permanecer principalmente en servidor: reglas financieras, autorización, disponibilidad, motores de vencimientos/alertas, Backup/Restore, relaciones, integridad, suscripciones y futuros algoritmos.

Mantener backend y repo privados, no desplegar `.git`, `DEBUG=False`, documentación técnica interna no pública, CI/CD privado y secretos externos. Evaluar marca, términos y licencia por vía legal/comercial.

## 16. Infraestructura objetivo

```text
Internet
   ↓
DNS / CDN / WAF cuando corresponda
   ↓
reverse proxy con TLS
   ↓
servidor de aplicación
   ↓
OrdenaClick
   ├── PostgreSQL privado
   ├── archivos privados
   ├── secretos privados
   └── logs/monitorización
   ↓
backups cifrados externos
```

Servidor con usuario de servicio sin privilegios administrativos, firewall, SSH por clave, DB no expuesta públicamente, actualizaciones de seguridad, monitorización y restore probado.

## 17. Orden de implementación — Base Server

1. Modelo definitivo de autorización/capacidades, preservando excepción actual de superusuario.
2. Auditoría completa de rutas privadas.
3. Autenticación y reautenticación.
4. Gestión de Claves endurecida.
5. Uploads/archivos privados.
6. PostgreSQL y settings production.
7. CSP, HTTPS, cookies y headers.
8. Logging/auditoría y manejo seguro de excepciones.
9. Idempotencia/concurrencia financiera.
10. Dependencias reproducibles y tests server-oriented.
11. Backup adversarial final.
12. `check --deploy` y auditoría final de la base.

Al finalizar:

> **BASE ARQUITECTÓNICA Y DE SEGURIDAD PARA SERVER: CERRADA**

Luego se retoma REGISTROS como prioridad funcional Beta.

## 18. Servicios externos / contrataciones

No contratar por impulso.

Resolver por un chat separado cuando llegue el momento:

1. hosting/VM o plataforma de aplicación;
2. PostgreSQL administrado o equivalente;
3. almacenamiento privado de archivos;
4. DNS/CDN/WAF;
5. correo transaccional;
6. monitorización/logs;
7. backup externo;
8. gestor de secretos si la plataforma elegida lo requiere.

Dominios disponibles:

- `ordenaclick.com`
- `ordenaclick.com.ar`

No hace falta contratar toda la infraestructura antes de cerrar Base Server. Sí conviene definir hosting + PostgreSQL + almacenamiento privado antes de la etapa final de despliegue, porque esas decisiones afectan settings, archivos y pruebas de producción.

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
