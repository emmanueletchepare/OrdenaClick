# TODO.md — Hoja de ruta actual

**Actualizado:** 08/10/2026

La prioridad no se decide por el tamaño de una tarea sino por cuánto acerca una Beta usable, estable y segura.

## 1. Prioridad inmediata — cerrar REGISTROS

### Comprobantes

- [ ] Recorrer Carga Simple de punta a punta con datos representativos.
- [ ] Verificar alta sin Pago, Pago parcial, Pago total y múltiples Pagos.
- [ ] Verificar Débito automático real y mora.
- [ ] Verificar edición sin historia y con Pagos históricos.
- [ ] Verificar factura/archivo y reglas documentales.
- [ ] Confirmar que saldo, estado, Vencimiento y Alertas quedan coherentes.

### Registrar Pago

- [ ] Cerrar circuito general independiente del formulario de Movimiento.
- [ ] Permitir distribuir un Pago entre múltiples Movimientos.
- [ ] Impedir que una AplicacionPago supere el saldo de su destino.
- [ ] Definir/persistir remanente a cuenta cuando corresponda.
- [ ] Reutilizar servicios financieros existentes; no duplicar reglas.

### Modificar / Eliminar

- [ ] Mostrar y gestionar Pagos históricos desde edición.
- [ ] Cerrar eliminación/reversión controlada de Pago.
- [ ] Recalcular saldo, estado, Vencimiento y Alerta después de una reversión.
- [ ] Permitir baja física de Movimiento sólo sin AplicacionPago.
- [ ] Rechazar baja física si existe historia aplicada.
- [ ] Verificar transacción y locking en operaciones destructivas.

### Carga Planificada / Plan

- [ ] Cerrar alcance Beta de Carga Planificada.
- [ ] Convertir a Plan sobre saldo restante.
- [ ] Conservar historia del Movimiento y Pagos previos.
- [ ] Generar Cuotas/Vencimientos coherentes.
- [ ] No desarrollar más del Plan de Pago que lo necesario para el circuito Beta acordado.

## 2. Navegación y UX bloqueantes de Beta

- [ ] Auditar todos los `[+]` usados por REGISTROS.
- [ ] Verificar pila LIFO de 1, 2, 3 y más niveles.
- [ ] Conservar formulario, filas dinámicas, scroll y elemento originador.
- [ ] Autoseleccionar alta/reactivación al volver.
- [ ] Eliminar mecanismos heredados sólo después de migrar consumidores.
- [ ] Eliminar JavaScript inline de los flujos publicados en Beta.
- [ ] Mantener estilos y componentes consistentes.

## 3. Seguridad e integridad — pendientes reales

### Ya endurecido

- [x] Proveedores por Empresa.
- [x] Bancos por Empresa.
- [x] Cuentas Bancarias por Empresa.
- [x] Tarjetas por Empresa.
- [x] Retenciones por Empresa.
- [x] Centros Operativos por Empresa.
- [x] Recursos Operativos por Empresa.
- [x] Tipos de Gasto por Empresa.
- [x] Gestión de Claves por Empresa.
- [x] Verificación de comprobantes por Empresa.
- [x] Alta de Movimientos por Empresa.
- [x] Eliminación de Empresa por POST y autorización.
- [x] Backup Empresa v1 usa autorización central.
- [x] Alcance Empresa/Centro/Caja centralizado.
- [x] Colaborador sin acceso implícito a Caja.
- [x] Perfil Desarrollador reservado a superusuario.
- [x] SECRET_KEY fuera del código sin fallback inseguro.

### Pendiente antes de Beta pública

- [ ] Auditoría final de todas las rutas privadas de `usuarios/urls.py`.
- [ ] Tests de usuario anónimo para rutas privadas relevantes.
- [ ] Revisar permisos funcionales por rol/capacidad, no sólo pertenencia a Empresa.
- [ ] Reautenticación/auditoría para revelar una contraseña de Gestión de Claves.
- [ ] Uploads: tamaño, tipo, almacenamiento y acceso privado.
- [ ] Revisar código legacy sin rutas antes de eliminarlo.
- [ ] Rate limiting/backoff para login/registro.
- [ ] Logging/auditoría de eventos sensibles sin secretos.
- [ ] Concurrencia/idempotencia en operaciones financieras críticas.
- [ ] Revisar historia Git/runtime por secretos o ZIP privados.
- [ ] Segunda auditoría de seguridad sobre candidato Beta.

## 4. Backup Empresa v1

### Base implementada

- [x] Manifest versionado.
- [x] identificadores portables.
- [x] exportador dedicado.
- [x] inspector defensivo.
- [x] restaurador transaccional.
- [x] wizard de importación.
- [x] usuarios históricos separados de autorización actual.
- [x] ZIP no concede privilegios automáticamente.
- [x] Gestión de Claves no exporta secreto cifrado portable.
- [x] round-trip base probado.
- [x] integración HTTP usa servicios dedicados.

### Pendiente de cierre pre-Beta

- [ ] ZIP corrupto.
- [ ] límites de tamaño/entradas/descompresión.
- [ ] JSON malformado y tipos inválidos.
- [ ] referencias internas rotas.
- [ ] versión no soportada.
- [ ] autoelevación maliciosa.
- [ ] activos/inactivos representativos.
- [ ] rollback forzado.
- [ ] round-trip de adjuntos.
- [ ] restore real sobre entorno descartable.
- [ ] política operativa/cifrado de backups en producción.

## 5. Vencimientos y Alertas

- [ ] Verificar fuente común contra todos los cambios de saldo.
- [ ] Verificar obligaciones próximas, hoy y vencidas.
- [ ] Confirmar que una obligación vencida pendiente nunca desaparece por tiempo.
- [ ] Revisar política temporal/zona horaria antes de producción.
- [ ] Tests de frontera temporal.
- [ ] Mantener toda regla temporal fuera del JavaScript.

## 6. Caja / Cartera

### Base ya incorporada

- [x] Caja ligada a Empresa/Centro.
- [x] alcance de Caja según jerarquía.
- [x] Nueva Cobranza base.
- [x] MovimientoCaja e identidad histórica.
- [x] Clientes como ABM.
- [x] Backup v1 contempla Caja/Cobranza.

### Próxima evolución, después del cierre prioritario de REGISTROS

- [ ] Cartera física.
- [ ] e-Cheqs / Cartera electrónica.
- [ ] disponibilidad canónica.
- [ ] Gestión Administrativa.
- [ ] traslados internos.
- [ ] disponibilidad bancaria informada.
- [ ] Orden de Pago.
- [ ] reservas y estados concurrentes.
- [ ] reversas con conservación histórica.

El orden obligatorio es:

```text
Ingreso
→ Caja/Cartera
→ Disponibilidad
→ Gestión Administrativa
→ Traslados
→ Orden de Pago
```

## 7. Producción / instalación

- [ ] Crear manifiesto reproducible de dependencias.
- [ ] Separar configuración development/production.
- [ ] `DEBUG=False` en producción.
- [ ] `ALLOWED_HOSTS` y CSRF origins explícitos.
- [ ] HTTPS y cookies seguras.
- [ ] HSTS/proxy headers según hosting.
- [ ] validadores de contraseña.
- [ ] almacenamiento privado definitivo y permisos del servicio.
- [ ] backup externo/retención/restore.
- [ ] `manage.py check --deploy`.
- [ ] procedimiento de despliegue y rollback.

## 8. Documentación

- [x] Definir un punto de entrada único: `00_RUMBO_Y_ESTADO.md`.
- [x] Separar documentación vigente de histórico.
- [ ] Mantener TODO/PRE_BETA/Auditoria sincronizados con cada bloque grande.
- [ ] Actualizar documentos funcionales cuando una decisión realmente cambie.
- [ ] No usar archivos históricos como fuente operativa vigente.

## 9. Post-Beta

- [ ] Dashboard.
- [ ] Reportes avanzados.
- [ ] Estado de Resultados.
- [ ] Balance.
- [ ] Plan Contable.
- [ ] conciliaciones avanzadas.
- [ ] Contable completo.
- [ ] Legal completo.
- [ ] marketplace, disponibilidad, postulaciones y ranking.
- [ ] billing completo.
- [ ] Agenda.
- [ ] multimoneda.
- [ ] notificaciones móviles.
- [ ] onboarding guiado.
- [ ] refactors estructurales no necesarios para Beta.

## 10. Regla de prioridad

Antes de iniciar una tarea nueva:

> ¿Cierra un flujo Beta, corrige un riesgo real o protege una decisión arquitectónica?

Si no, debe esperar.
