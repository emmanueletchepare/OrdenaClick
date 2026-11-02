# OrdenaClick — Fichas y requisitos para nuevas alertas

**Anexo del [Catálogo maestro de alertas](CATALOGO_ALERTAS_ORDENACLICK.md)** · 24/10/2026

Este archivo guarda las decisiones de diseño **sin recargar la lista rápida**. Registrar aquí las necesidades de cada tipo nuevo antes de construir la alerta. No se autoriza modificar código, modelos ni permisos por el solo hecho de anotarla.

## DOC-03 · Vencimiento de habilitación municipal

**Estado:** fuente documental implementada en este bloque, pendiente de validación local, migración y aceptación visual.

**Implementación inicial:** varias habilitaciones por Centro, registro/archivo privado,
archivado conservando antecedentes, alerta por vencimiento y por Centro activo sin
habilitaciones registradas. Anticipación de 30 días (política inicial a confirmar
con uso real). Una alerta no certifica vigencia municipal ni reemplaza trámites.
Administrador general/propietario: todos los Centros; administrador de Centro:
únicamente Centros autorizados y con permiso Alertas. Destinatarios por defecto
con opción de desactivar, registro B2 auditado.

**DOC-01, DOC-02 y DOC-04:** vencimientos de acta de directorio, asamblea y
designación de autoridades vinculados a Empresa; fecha de carga independiente.
Anticipación inicial de 30 días; solo administración general/propietario y
superusuario autorizados. No se inventan fechas si el campo está vacío.

**Revisiones futuras:** criterios legales específicos según municipio, mecanismo
de versionado de documentación societaria más allá del reemplazo existente,
y recorrido de wizzard de Empresa cuando éste se diseñe.

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

**Validaciones abiertas:** aceptación de la anticipación inicial de 30 días,
criterios de vigencia de cada municipio, historial societario más amplio,
restauración con adjuntos reales, recorrido del futuro wizard de Empresas y
validación completa con los perfiles autorizados antes de declarar el bloque cerrado.

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

## Cierre societario — acta de asamblea y designación (02/11/2026)

- Estatuto y Acta de Asamblea continúan como registros principales de Empresa.
- Una marca explícita `acta_incluye_designacion` permite declarar que el acta de asamblea acredita también la designación de autoridades. **No se presume automáticamente** para Empresas existentes.
- Acta de Directorio y Designación separada quedan como documentación complementaria opcional; no se borran PDFs, fechas ni antecedentes existentes.
- Si la marca está activa, **DOC-04 no genera una segunda ocurrencia** por el mismo mandato: DOC-02 concentra el aviso, utilizando el vencimiento de Asamblea o, si no lo hay, la fecha histórica de Designación. No se cambia ninguna fecha en la base.
- La fecha etiquetada como vencimiento se interpreta como seguimiento o fin de mandato cuando corresponda, no como vencimiento legal automático del PDF ni del acta. No se imponen plazos legales inventados.
- Una alerta no acredita vigencia, ni concede acceso a un archivo, y los destinatarios siguen dependiendo del gestor y permisos ya implementados.
- Sólo se agrega migración `0058` con booleano por defecto `False`; compatible con datos actuales y Backup Empresa v1.

## Rectificación de documentación societaria — 02/11/2026

El formulario de Empresa conserva sólo Estatuto (ancho completo), Acta de Directorio y
Acta de Designación de Autoridades (Asamblea). La Asamblea individual anterior no
se solicita en pantalla, ni genera aviso separado DOC-02. DOC-01 sigue Directorio;
DOC-04 sigue la fecha de Designación; DOC-03 corresponde a habilitaciones de Centros.
No se borran la fecha `vencimiento_acta`, el adjunto `acta` ni la marca
`acta_incluye_designacion` históricos. La UI no los utiliza. La marca preexistente
sólo autoriza fallback desde el vencimiento previo de Asamblea cuando Designación
carece de vencimiento propio. No se agrega ni revierte una migración.
