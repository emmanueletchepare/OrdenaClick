# Auditoria.md — Riesgos y estado de OrdenaClick

**Actualizado:** 08/10/2026
**Estado:** desarrollo previo a Beta.

Este documento registra riesgos actuales y evidencia de cierres. Las prioridades funcionales viven en `TODO.md`; el rumbo general vive en `00_RUMBO_Y_ESTADO.md`.

## 1. Criterio

### 🔴 Crítico

Bloquea datos reales o exposición pública:

- acceso no autorizado;
- filtración entre Empresas;
- pérdida/corrupción;
- operación financiera incorrecta;
- eliminación destructiva insegura;
- secretos expuestos;
- backup no confiable;
- configuración de producción insegura.

### 🟠 Importante

Debe resolverse antes de cerrar Beta o al tocar el circuito:

- errores funcionales;
- navegación rota;
- estados/saldos ambiguos;
- cobertura insuficiente;
- comportamiento inconsistente.

### 🟡 Deuda técnica

No debe desviar la Beta salvo que impida seguridad, integridad o mantenimiento inmediato.

### 🟢 Base correcta

Se preserva y extiende.

## 2. Estado general

| Área | Estado actual |
| --- | --- |
| Visión de producto | 🟢 clara |
| Arquitectura conceptual | 🟢 sólida |
| Núcleo Movimiento/Pago/AplicacionPago | 🟢 buena base |
| Aislamiento por Empresa | 🟢/🟠 muy avanzado; falta auditoría final de rutas |
| Gestión de Claves | 🟠 aislada por Empresa; falta reautenticación/auditoría de revelado |
| Backup Empresa v1 | 🟢/🟠 implementado; falta batería adversarial final |
| Caja/Cobranza | 🟢 base implementada |
| REGISTROS completos | 🟠 todavía incompleto |
| Navegación `[+]` | 🟠 requiere cierre integral LIFO |
| Testing | 🟠 buena base; falta regresión candidata |
| Producción | 🔴 pendiente |
| Uploads/archivos privados | 🔴 pendiente de revisión final |
| Dependencias reproducibles | 🟠 pendiente |

## 3. Seguridad por Empresa — avance

Los siguientes dominios ya fueron endurecidos con autorización central y pruebas específicas:

- Proveedores;
- Bancos;
- Cuentas Bancarias;
- Tarjetas;
- Retenciones;
- Centros Operativos;
- Recursos Operativos;
- Tipos de Gasto;
- Gestión de Claves;
- verificación de comprobantes;
- alta de Movimientos;
- eliminación de Empresa;
- Backup Empresa v1;
- Caja/Cobranza según alcance Empresa/Centro/Caja.

También se preservó deliberadamente el alcance restrictivo del panel/Movimientos históricos: una asignación `admin_general` no abre automáticamente todos los flujos legacy.

### Pendiente

- auditoría ruta por ruta de `usuarios/urls.py`;
- autenticación de endpoints privados;
- permisos funcionales por rol/capacidad;
- archivos y descargas;
- código legacy sin rutas;
- pruebas adversariales adicionales.

## 4. Gestión de Claves

### Resuelto

- cifrado Fernet con clave externa;
- aislamiento por Empresa;
- alta/listado/ver/modificar/eliminar/reactivar protegidos;
- tests IDOR;
- Backup Empresa v1 no transporta el secreto cifrado.

### Pendiente crítico/importante

- permiso explícito de revelado;
- reautenticación antes de mostrar contraseña;
- auditoría del evento de revelado;
- rotación/ciclo de vida de la clave maestra;
- confirmar que logs y respuestas de error no exponen valores.

## 5. Operaciones destructivas

### Resuelto

`eliminar_empresa`:

- autenticado;
- POST;
- CSRF por formulario Django;
- autorización de propietario/superusuario;
- admin_general no obtiene borrado por asignación;
- tests de método y Empresa ajena.

### Pendiente

Auditar todas las demás bajas físicas/reversiones financieras nuevas bajo la misma regla:

```text
autorización
→ transacción
→ bloqueo/revalidación
→ eliminación/reversión explícita
→ recálculo
```

## 6. Backup Empresa v1

### Base correcta

- servicios dedicados;
- manifest versionado;
- IDs portables;
- inspección defensiva;
- restauración transaccional;
- wizard;
- historia de usuarios separada de permisos vigentes;
- fundador protegido;
- no compatibilidad con ZIP legacy pre-v1;
- round-trip base.

### Pendiente antes de producción

- ZIP corrupto;
- límites anti-bomba;
- JSON malformado/tipos;
- referencias internas rotas;
- versión no soportada;
- autoelevación maliciosa;
- rollback forzado;
- archivos adjuntos;
- restore real sobre entorno descartable;
- almacenamiento/retención/cifrado operativo.

## 7. Producción

🔴 Aún no apto para exposición pública hasta verificar:

- `DEBUG=False`;
- `ALLOWED_HOSTS`;
- `CSRF_TRUSTED_ORIGINS` cuando corresponda;
- HTTPS;
- cookies seguras;
- HSTS/proxy headers;
- rate limiting;
- validadores de contraseña;
- permisos de archivos;
- logging;
- backups externos;
- dependencias reproducibles;
- `check --deploy`;
- procedimiento de rollback.

## 8. Archivos y uploads

🔴 Debe revisarse específicamente:

- validación de tamaño y tipo;
- rutas/nombres;
- autorización de lectura;
- almacenamiento privado;
- exposición desde `media/`;
- adjuntos de Movimiento/Empresa/Backup;
- limpieza de temporales.

## 9. Zona horaria y fecha operativa

🟠 OrdenaClick usa conceptos de día calendario sensibles:

- vence hoy;
- vencido;
- alertas;
- acreditación de cheques;
- débitos.

Antes de producción debe definirse la política temporal efectiva y evitar cálculos dispersos que dependan accidentalmente de UTC cuando la operación espera fecha local.

## 10. REGISTROS e integridad financiera

🟢 Decisiones correctas:

- Movimiento y Pago separados;
- saldo por AplicacionPago;
- aplicación máxima centralizada;
- histórico protegido desde la primera AplicacionPago;
- mora separada del capital.

🟠 Pendiente:

- completar Registrar Pago general;
- remanentes a cuenta;
- reversión segura de Pagos;
- Carga Planificada/Plan;
- verificar Vencimientos/Alertas después de toda transición;
- concurrencia e idempotencia.

## 11. Navegación y frontend

🟢 Dirección correcta:

- `[+]` contextual;
- pila LIFO;
- JS/CSS externo;
- mismo lenguaje visual.

🟠 Pendiente Beta:

- verificar todos los consumidores;
- retirar retornos heredados sólo después de cobertura;
- eliminar JavaScript inline de flujos publicados;
- smoke multinivel.

No se retomará la fragmentación arbitraria de archivos JavaScript ya externos si no produce valor funcional o de seguridad.

## 12. Código legacy y deuda técnica

Existe código legacy de Exportar/Importar Empresa y otras ramas ya reemplazadas por implementaciones nuevas.

No constituye prioridad mientras:

- no tenga rutas activas;
- no amplíe superficie de ataque;
- no interfiera con pruebas;
- no confunda ejecución real.

Debe eliminarse en una limpieza controlada después de verificar consumidores.

No hacer refactors por métricas de líneas.

## 13. Dependencias y reproducibilidad

🟠 Falta un manifiesto formal de dependencias.

Antes de Beta una instalación limpia debe poder reproducir:

```text
Python
→ dependencias declaradas
→ secretos/configuración
→ migraciones
→ tests
→ servidor
```

## 14. Próxima auditoría

La próxima revisión integral debe hacerse sobre el commit candidato a Beta e incluir:

- rutas;
- permisos;
- uploads;
- secretos;
- headers/cookies;
- logs;
- backup/restore;
- concurrencia;
- dependencias;
- configuración de producción.

No debe confundirse esta auditoría final con continuar hardening indefinidamente durante el desarrollo funcional.

## 15. Decisión de auditoría — Base Server

Se abre formalmente una etapa previa al desarrollo funcional intensivo cuyo alcance está definido en `BASE_SERVER_SEGURIDAD.md`.

Prioridades: capacidades/autorización, rutas privadas, autenticación, Gestión de Claves, archivos privados, PostgreSQL/settings production, CSP/HTTPS/cookies/headers, logging/auditoría, idempotencia/concurrencia, dependencias, Backup adversarial y auditoría final.

### Excepción aceptada

El acceso global actual de `is_superuser` a Empresas es una decisión vigente de producto. No clasificarlo como vulnerabilidad mientras sólo aplique a superusuario y no se propague a jerarquías normales.

La dirección futura es mover tareas comerciales/técnicas a un panel global del Perfil Desarrollador: habilitar, suspender, configurar capacidades/suscripción, exportar Empresa y generar un resumen administrativo.
