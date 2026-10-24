# OrdenaClick — Fichas y requisitos para nuevas alertas

**Anexo del [Catálogo maestro de alertas](CATALOGO_ALERTAS_ORDENACLICK.md)** · 24/10/2026

Este archivo guarda las decisiones de diseño **sin recargar la lista rápida**. Registrar aquí las necesidades de cada tipo nuevo antes de construir la alerta. No se autoriza modificar código, modelos ni permisos por el solo hecho de anotarla.

## DOC-03 · Vencimiento de habilitación municipal

**Estado:** idea catalogada; **no implementada**.

**Registro documental previo:**

- **Pertenece al Centro Operativo**, dentro de una Empresa. No debe guardarse como un vencimiento global de la Empresa ni inventarse una relación directa con Caja.
- Diseñar un registro de habilitación asociado al Centro, considerando que puede haber **más de una habilitación o renovación** por Centro. Confirmar esa multiplicidad antes de decidir el esquema.
- Datos candidatos a evaluar: autoridad/municipio emisor, tipo/número de habilitación, fecha de otorgamiento, fecha de vencimiento cuando corresponda, estado y documento adjunto. **No imponer campos obligatorios ni plazos hasta revisar casos reales.**
- Definir alta, modificación, renovación, baja de vigencia y conservación de versiones/antecedentes, con autor y fecha de cada cambio. El documento adjunto requiere almacenamiento privado y descarga con autorización real.
- Si un Centro se desactiva, definir qué sucede con avisos y registros; **no eliminar antecedentes automáticamente**.

**Seguridad y alcance:**

- El backend debe validar Empresa y Centro en lectura, escritura, descarga y consulta de Alertas; no alcanza con esconder enlaces o casillas.
- No se presume que el Administrador de Centro pueda editar documentos: sus capacidades concretas deben aprobarse y aplicarse en el servidor. Un usuario con alcance a un solo Centro no debe acceder a habilitaciones de otro.
- Asignar un aviso **nunca concede permiso** para consultar el documento, la ficha ni otras informaciones del Centro.
- Configuración de destinatarios bajo Propietario/Administrador General autorizados; revocación de permisos y de alcance con efecto inmediato, con auditoría.

**Regla de aviso — por definir:**

- Acordar qué fecha real constituye vencimiento, cuántos días antes avisar, si hay distintos regímenes municipales y qué ocurre con documentos sin fecha de vencimiento.
- Una renovación debe actualizar o cerrar el aviso del documento anterior sin duplicaciones; reconocer una alerta **no renueva** la habilitación.
- Decidir mensaje mínimo visible sin revelar documentos a destinatarios no autorizados.

**Pruebas mínimas al implementar:** centros y empresas ajenos denegados; alta y renovación con histórico; vencimientos reales y ausentes; control de adjuntos; revocación inmediata; destinatarios efectivos; alertas duplicadas o canceladas; regresión de permisos existentes.

**Decisiones abiertas:** estructura del registro documental, permisos de lectura/edición, campos obligatorios, política de vencimientos, usuarios destinatarios y forma final en el panel. Requieren aprobación específica.

## Plantilla breve para cada alerta futura

Copiar esta ficha por identificador (`FIN-02`, `ADM-01`, etc.) cuando llegue su turno:

1. **Nombre, categoría e identificador.**
2. **Dónde se registra el hecho:** módulo, tipo de registro/documento y vínculo con Empresa/Centro.
3. **Datos que deben poder cargarse:** campos, adjuntos privados, renovación, historial y auditoría.
4. **Cuándo nace y termina el aviso:** disparador verificable, anticipación, actualización y cancelación; no inventar fechas legales.
5. **Quién accede:** permisos de origen, alcance por Empresa/Centro, lectura/escritura/descarga, privacidad y revocación.
6. **Destinatarios y notificación:** asignación explícita, campanita/sonido, usuarios elegibles y caso «Sin destinatarios».
7. **Pruebas obligatorias:** aislamiento multiempresa, Centros, permisos, filtraciones, duplicados, migraciones y regresión.
8. **Estado:** idea → fuente/registro diseñado → aprobado → implementado → probado.

## Regla permanente para el Gestor

«Sin destinatarios» muestra **tipos de alertas habilitados sin usuarios efectivos** y, donde exista soporte real, **ocurrencias vigentes sin receptor autorizado**. No mezcla ideas no implementadas con incidencias actuales. La asignación no sustituye Gestión de Accesos, ni permite leer datos sin permiso de origen.

**Límite:** este anexo documenta el análisis preliminar; no introduce funciones ni modifica el repositorio.
