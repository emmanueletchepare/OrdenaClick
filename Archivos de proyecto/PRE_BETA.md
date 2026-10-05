# PRE_BETA.md --- Checklist bloqueante para publicar OrdenaClick

**Fecha de consolidación:** 27/09/2026

## 1. Regla de salida

Un punto no se marca como resuelto porque la interfaz parezca funcionar.
Debe existir evidencia mediante tests, revisión de código, configuración
o prueba manual documentada.

-   [ ] No quedan bloqueantes críticos de seguridad abiertos.
-   [ ] Regresión automatizada completa verde.
-   [ ] Flujos Beta recorridos manualmente de punta a punta.
-   [ ] Segunda auditoría de seguridad sobre el commit candidato.
-   [ ] Configuración de producción verificada con
    `manage.py check --deploy`.
-   [ ] Backup y restauración real probados.

## 2. Bloqueantes de la auditoría de seguridad 24/09/2026

### R-01 --- Autenticación/autorización de todos los endpoints

-   [ ] Revisar todas las rutas privadas de `usuarios/urls.py`.
-   [ ] Exigir autenticación.
-   [ ] Centralizar autorización por Empresa; no confiar en IDs del
    navegador.
-   [ ] Consultar objetos hijos dentro de la Empresa autorizada.
-   [ ] Tests: anónimo, autorizado, otra Empresa e IDs inconsistentes.

### R-02 --- Exportar/eliminar Empresa

-   [ ] Revalidar autenticación y autorización.
-   [ ] Exportar sólo con permiso explícito.
-   [ ] Eliminar sólo por POST, con CSRF y permisos.
-   [ ] Tests de método HTTP y aislamiento.

### R-03 --- Gestión de claves

-   [ ] Proteger listar/crear/ver/modificar/eliminar/reactivar.
-   [ ] Exigir Empresa autorizada y permiso específico.
-   [ ] No devolver contraseñas en listados/logs.
-   [ ] Definir reautenticación para revelado y auditar el evento.
-   [ ] Tests IDOR.

### R-04 --- SECRET_KEY e historial público

El TODO actual documenta como implementada la salida de SECRET_KEY del
código, el arranque sin fallback inseguro y la rotación controlada. La
auditoría exige además tratar como comprometida la clave histórica
versionada. - \[ \] Revalidar que la clave histórica no sea válida en
ningún entorno. - \[ \] Documentar rotación de entornos que pudieron
usarla. - \[ \] Decidir/documentar tratamiento del historial Git
público. - \[ \] Confirmar que producción sólo arranca con secreto
externo/privado.

### R-05 --- Runtime/importaciones fuera de Git

-   [ ] Revisar ZIP que estuvieron bajo `media/importaciones`.
-   [ ] Documentar si eran ficticios o reales.
-   [ ] Retirar de Git runtime, bases, ZIP, dumps, claves y secretos.
-   [ ] Prevenir reincidencia mediante revisión/CI.

### R-06 --- Importar Empresa

-   [ ] Autenticación y rol autorizado.
-   [ ] Límites de upload, entradas y tamaño descomprimido.
-   [ ] Validación ZIP, rutas permitidas, `manifest` versionado y esquema de
    todos los componentes del Backup Empresa v1.
-   [ ] No soportar como contrato los ZIP legacy previos a v1.
-   [ ] Impedir restaurar/modificar una Empresa ajena.
-   [ ] Si el CUIT ya existe, validar y planificar antes de modificar la Empresa
    vigente; no borrar primero para intentar recrear después.
-   [ ] Wizard de importación: permitir confirmar/actualizar los datos que
    pueden haber cambiado antes de ejecutar la restauración.
-   [ ] Usuarios: conservar trazabilidad histórica, resolver activo/inactivo y
    jerarquía actual mediante decisión explícita de un usuario autorizado.
-   [ ] Ningún rol o privilegio contenido en el ZIP se aplica automáticamente.
-   [ ] Resumen y confirmación explícita antes de persistir la restauración.
-   [ ] Atomicidad/rollback suficiente para no dejar una Empresa parcial ante
    una falla crítica.
-   [ ] Temporales privados y limpieza garantizada.
-   [ ] Pruebas adversariales.

## 3. Seguridad necesaria antes del primer despliegue público

-   [ ] Separar desarrollo/producción; `DEBUG=False`, hosts/orígenes
    explícitos.
-   [ ] HTTPS, cookies seguras, CSRF y configuración correcta de
    proxy/HSTS.
-   [ ] Validadores de contraseña Django en backend.
-   [ ] Rate limiting/backoff seguro en login/registro.
-   [ ] Permisos reales Administrador/Colaborador/Contable/Legal.
-   [ ] Alcance Centro/Caja antes de habilitar POST financieros a
    colaboradores.
-   [ ] Uploads con límites/tipos y documentos sensibles privados.
-   [ ] Ciclo de vida, backup y rotación de clave maestra de Gestión de
    claves.
-   [ ] Dependencias reproducibles y escaneo de
    vulnerabilidades/secretos.
-   [ ] Backups cifrados, retención, copia externa y restore probado.
-   [ ] Logging/auditoría de eventos sensibles sin secretos.
-   [ ] Revisión de cabeceras de seguridad/CSP.

## 4. Navegación contextual `[+]`

-   [ ] Implementar pila común de contextos.
-   [ ] Cada `[+]` apila; cada Volver desapila exactamente un nivel
    (LIFO).
-   [ ] Admitir `[+] → ABM → [+] → ABM ...` sin límite funcional de
    diseño.
-   [ ] Conservar valores, estado, control originador y posición visual.
-   [ ] Refrescar selector y autoseleccionar alta/reactivación al
    volver.
-   [ ] El ABM destino no conoce manualmente todos sus llamadores.
-   [ ] Migrar todos los `[+]` existentes.
-   [ ] Eliminar `origenABM`, `contenidoAnterior...` y equivalentes sólo
    después de migrar/probar consumidores.
-   [ ] Tests y pruebas manuales de 1, 2, 3 y más niveles.

## 5. Normalización de comportamientos reutilizables

-   [ ] Inventariar todos los lugares donde se cargan cheques/e-Cheqs.
-   [ ] Número de cheque: entrada numérica de hasta 8 dígitos y
    persistencia normalizada a 8 posiciones con ceros a la izquierda.
-   [ ] Aplicar la misma normalización a todos los ingresos de número de
    cheque.
-   [ ] Reutilizar reglas Simple/Diferido y todas las validaciones de
    fechas.
-   [ ] Reutilizar `[+]` para Banco y Cliente.
-   [ ] Normalizar todos los importes al formato pactado de
    miles/decimales.
-   [ ] Revisar CUIT, fechas, importes y selectores repetidos para
    evitar contratos distintos.
-   [ ] Backend normaliza/valida siempre; JS sólo mejora UX.

## 6. JavaScript/CSS y limpieza

-   [ ] Eliminar todo JavaScript inline de los flujos publicados en
    Beta.
-   [ ] No introducir JavaScript inline nuevo.
-   [ ] Extraer CSS inline heredado necesario sin crear un segundo
    sistema visual.
-   [ ] Eliminar retornos reemplazados por la pila contextual.
-   [ ] Eliminar código muerto confirmado, rutas/templates/JS/CSS/assets
    descartados y placeholders temporales.
-   [ ] Preservar comentarios importantes y no borrar código cuyo uso no
    haya sido verificado.

## 7. Integridad financiera

-   [ ] Validaciones críticas centralizadas en servicios.
-   [ ] Frontend no decide autorización, saldo ni transición válida.
-   [ ] Revisar transacciones, locking/concurrencia e idempotencia donde
    corresponda.
-   [ ] Caja/Cartera/OP usan estados y disponibilidad canónicos.
-   [ ] Cheques vencidos no aparecen disponibles aunque el estado
    almacenado esté desactualizado.
-   [ ] Reversas conservan historia y restituyen valores cuando
    corresponda.
-   [ ] Vencimientos/alertas se contrastan con la fuente financiera
    común.

## 8. Datos e instalación

-   [ ] Limpieza de desarrollo sólo sobre datos operativos.
-   [ ] Nunca borrar configuración privada de instalación, SECRET_KEY,
    certificados/claves ARCA ni configuración técnica del Perfil
    Desarrollador.
-   [ ] Revisar Exportar/Importar Empresa por cada modelo nuevo de
    Empresa.
-   [ ] Probar compatibilidad/versionado de backup.

## 9. Testing y cierre

-   [ ] Suite completa verde.
-   [ ] Tests financieros, permisos/aislamiento, IDOR, navegación
    multinivel, validaciones compartidas, export/import,
    uploads/archivos privados, reversas/estados.
-   [ ] Pruebas con datos representativos y recorrido manual completo.
-   [ ] `manage.py check` y `manage.py check --deploy`.
-   [ ] `git status` revisado y stage selectivo; nunca `git add .`.
-   [ ] Confirmar que no se versionan DB, backups, ZIP, `.env`, claves
    privadas, certificados ni runtime.
-   [ ] Segunda auditoría de rutas/seguridad.
-   [ ] Restore probado.
-   [ ] Revisión final UX/coherencia visual.
-   [ ] Sólo entonces publicar Beta.
