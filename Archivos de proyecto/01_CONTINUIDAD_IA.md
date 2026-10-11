# 01_CONTINUIDAD_IA.md — Instrucciones para continuar OrdenaClick en otro chat

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
- **B10a aún EN CURSO**: queda cubrir documentos del panel Empresa, formatos reales, rutas privadas y controles completos; Base Server no certificada.

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
