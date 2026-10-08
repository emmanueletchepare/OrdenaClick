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
