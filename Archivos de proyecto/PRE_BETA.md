# PRE_BETA.md — Checklist bloqueante para publicar OrdenaClick

**Actualizado:** 08/10/2026

Este archivo enumera condiciones de salida. Un punto no se considera resuelto porque “parece funcionar”: debe existir evidencia por tests, revisión de código, configuración o prueba manual documentada.

## 1. Condición general

- [ ] No quedan riesgos críticos de seguridad abiertos.
- [ ] Suite completa candidata a Beta verde.
- [ ] Flujos Beta recorridos manualmente de punta a punta.
- [ ] Segunda auditoría de seguridad sobre el commit candidato.
- [ ] `python manage.py check --deploy` sin bloqueantes.
- [ ] Backup y restore real probados.
- [ ] Configuración de producción documentada y verificada.

## 2. Rutas, autenticación y aislamiento

### Cobertura ya endurecida

- [x] Proveedores.
- [x] Bancos.
- [x] Cuentas Bancarias.
- [x] Tarjetas.
- [x] Retenciones.
- [x] Centros Operativos.
- [x] Recursos Operativos.
- [x] Tipos de Gasto.
- [x] Gestión de Claves — aislamiento por Empresa.
- [x] verificación de comprobantes.
- [x] alta/edición/pagos de Movimientos usan autorización central en los flujos revisados.
- [x] eliminación de Empresa requiere POST y autorización.
- [x] Backup Empresa v1 autoriza mediante servicio central.
- [x] Caja usa alcance Empresa/Centro/Caja.

### Falta para cerrar R-01

- [ ] Revisar **todas** las rutas privadas de `usuarios/urls.py`.
- [ ] Confirmar `login_required` o equivalente donde corresponda.
- [ ] Probar usuario anónimo en endpoints privados críticos.
- [ ] Revisar permisos por rol/capacidad además del aislamiento de Empresa.
- [ ] Confirmar que objetos hijos siempre se reconsultan dentro de la Empresa autorizada.
- [ ] Revisar endpoints legacy sin rutas antes de eliminarlos.

## 3. Gestión de Claves

- [x] listar/crear/ver/modificar/eliminar/reactivar aislado por Empresa.
- [x] tests IDOR/cross-Empresa.
- [x] clave de cifrado fuera del repositorio.
- [x] secretos no viajan en Backup Empresa v1.
- [ ] definir permiso/capacidad específica de revelado.
- [ ] implementar reautenticación antes de mostrar contraseña si se mantiene esa función.
- [ ] auditar evento de revelado sin registrar el secreto.
- [ ] definir ciclo de vida/rotación de la clave maestra de Gestión de Claves.

## 4. Exportar / Importar Empresa

- [x] Backup Empresa v1 reemplaza el flujo legacy en rutas activas.
- [x] manifest versionado.
- [x] IDs portables.
- [x] inspector ZIP dedicado.
- [x] defensa Zip Slip.
- [x] restaurador con transacciones.
- [x] wizard Empresa → Usuarios → Resumen.
- [x] fundador no lo decide el ZIP.
- [x] jerarquías del ZIP no conceden privilegios automáticamente.
- [x] usuarios históricos separados de autorización vigente.
- [x] round-trip base.
- [ ] test explícito ZIP corrupto.
- [ ] límites de upload, cantidad de entradas y descompresión.
- [ ] JSON malformado / tipos inválidos.
- [ ] referencias internas inexistentes.
- [ ] manifest v1 con versión futura/no soportada.
- [ ] intento de autoelevación.
- [ ] activos/inactivos representativos.
- [ ] rollback forzado.
- [ ] round-trip de archivos adjuntos.
- [ ] prueba manual de restore final sobre entorno descartable.

## 5. REGISTROS

- [ ] Comprobantes punta a punta.
- [ ] múltiples Pagos.
- [ ] Pago parcial y total.
- [ ] Débito automático real.
- [ ] saldo pendiente centralizado.
- [ ] edición sin historia.
- [ ] edición con Pagos históricos.
- [ ] gestión/reversión de Pagos.
- [ ] baja física sólo sin AplicacionPago.
- [ ] Registrar Pago distribuido.
- [ ] remanente a cuenta definido.
- [ ] Carga Planificada cerrada para Beta.
- [ ] Convertir a Plan según alcance Beta.
- [ ] Vencimientos/Alertas coherentes después de cada transición.

## 6. Navegación `[+]`

- [ ] pila común LIFO en todos los consumidores Beta.
- [ ] prueba de uno, dos, tres y más niveles.
- [ ] conservar valores, filas dinámicas, scroll y foco.
- [ ] autoseleccionar alta/reactivación al volver.
- [ ] ABM destino independiente del llamador.
- [ ] eliminar retornos heredados sólo después de migrarlos.
- [ ] no queda JavaScript inline en flujos Beta publicados.

## 7. Integridad financiera

- [x] Movimiento y Pago separados.
- [x] AplicacionPago como base del saldo.
- [x] validación de aplicación máxima en servicio común.
- [x] mora separada de capital aplicado en Débito automático.
- [ ] revisar todas las rutas que crean/revierten AplicacionPago.
- [ ] locking/concurrencia en operaciones críticas.
- [ ] idempotencia/doble envío donde corresponda.
- [ ] reversas restituyen estado financiero y fuentes derivadas.
- [ ] Vencimientos/Alertas contrastados con fuente financiera común.

## 8. Archivos y uploads

- [ ] límites por tipo/tamaño.
- [ ] nombres/rutas seguras.
- [ ] documentos sensibles no servidos como contenido público indiscriminado.
- [ ] autorización para descargar/visualizar archivos de Empresa.
- [ ] backup incluye adjuntos según contrato.
- [ ] logs no exponen rutas/secreto/contenido sensible innecesario.

## 9. Seguridad de instalación y producción

- [x] SECRET_KEY fuera del código.
- [x] no existe fallback inseguro.
- [x] Perfil Desarrollador sólo superusuario.
- [x] LOGIN_URL propio.
- [x] credenciales ARCA separadas por ambiente.
- [ ] verificar tratamiento de SECRET_KEY histórica versionada.
- [ ] revisar ZIP/runtime históricos en Git.
- [ ] `DEBUG=False`.
- [ ] hosts/orígenes explícitos.
- [ ] HTTPS.
- [ ] cookies seguras.
- [ ] CSRF seguro detrás de proxy/hosting.
- [ ] HSTS/cabeceras.
- [ ] validadores de contraseña.
- [ ] rate limiting/backoff.
- [ ] almacenamiento privado y ACL del servicio.
- [ ] dependencias reproducibles.
- [ ] escaneo de secretos/dependencias.
- [ ] backup cifrado/retención/copia externa.

## 10. Cierre técnico

- [ ] `git status --short` limpio.
- [ ] stage selectivo; nunca `git add .`.
- [ ] `git diff --cached --check`.
- [ ] suite completa verde.
- [ ] `manage.py check`.
- [ ] `manage.py check --deploy`.
- [ ] smoke manual con datos representativos.
- [ ] revisión UX/coherencia visual.
- [ ] revisión final de logs.
- [ ] commit candidato a Beta identificado.
- [ ] restore real probado desde ese candidato.

Sólo entonces se publica la Beta.
