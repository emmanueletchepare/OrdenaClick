# BASE_SERVER_SEGURIDAD.md — Base de arquitectura y seguridad orientada a servidor

**Fecha de decisión:** 08/10/2026
**Estado:** rumbo obligatorio antes de retomar el desarrollo funcional intensivo.

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
