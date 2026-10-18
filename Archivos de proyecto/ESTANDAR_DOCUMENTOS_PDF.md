# OrdenaClick — Estándar institucional de documentos PDF

**Estado:** aprobado visualmente el 15/10/2026; formato institucional obligatorio para los documentos nuevos.

**Ubicación definitiva:** `Archivos de proyecto/ESTANDAR_DOCUMENTOS_PDF.md`. Referenciar este documento desde `Archivos de proyecto/REGLAS.md` (norma obligatoria de presentación), `Archivos de proyecto/ARQUITECTURA.md` (componente técnico reutilizable) y `Archivos de proyecto/DECISIONES.md` (decisión institucional). Mantener los recursos de marca versionados dentro de `static/branding/` o el directorio estático de marca existente si lo hubiera; no duplicar logotipos en cada módulo.

## Objetivo

Establecer una plantilla única, profesional e imprimible para detalles de gestión bancaria, órdenes de pago, comprobantes y reportes institucionales. El documento se genera desde datos autorizados del servidor, nunca desde importes o listas manipulables en el navegador.

## Identidad visual

- Usar **exclusivamente** el logotipo oficial aportado por el usuario, sin redibujarlo. Para documentos claros, proponer la variante horizontal azul y negra sobre fondo blanco, sujeta a aprobación.
- Membrete con logo arriba a la izquierda; identificación del tipo documental y número de referencia a la derecha.
- Paleta discreta del proyecto: azul marino, azul OrdenaClick, gris suave y blanco. Evitar fondos oscuros extensos salvo el bloque final de total.
- Formato A4 vertical, márgenes de impresión generosos, jerarquía legible y tipografía incrustada o disponible para renderizado PDF.
- Pie institucional con emisor, referencia, paginación y aclaración sobre el alcance del documento.
- Para documentos de varias páginas, repetir encabezados de tablas, controlar cortes de filas y numerar páginas.

## Campos comunes

1. Logo / marca OrdenaClick.
2. Tipo y título del documento.
3. Identificador único de documento / operación, si existe.
4. Empresa y fecha-hora de emisión (zona horaria local).
5. Emisor autorizado; según clase de documento, referencia de origen.
6. Datos específicos del trámite.
7. Tablas y subtotales, total destacado cuando corresponda.
8. Pie con aclaraciones y número de página.

Evitar incluir información sensible innecesaria. No mostrar datos financieros de otra Empresa. Proteger la ruta PDF con las mismas capacidades del registro asociado.

## Tipo: Detalle para gestión bancaria — e-Cheqs

- Título: **Detalle para gestión bancaria**.
- Subtítulo: Listado de e-Cheqs para endoso y cesión.
- Emisor, fecha-hora, empresa, ID de operación, proveedor, banco y CBU o destino consignado.
- Sección **Cheques a endosar**, con importe subtotal y listado numerado de número de e-Cheq, fecha de acreditación e importe.
- Sección **Cheques a ceder**, con importe subtotal y mismo detalle.
- **Total operación** = subtotales de endoso + cesión.
- Mantener el orden por fecha de acreditación ascendente dentro de cada sección.
- Si una sección no tiene ítems, decidir en el desarrollo si se omite o se indica «Sin cheques», preservando totales exactos.
- Aclaración: «Documento de gestión. No acredita depósito ni recepción bancaria».
- Los datos se obtienen de la **operación confirmada y sus ítems persistidos**, no de la selección del frontend.
- El PDF se ofrece mediante modal **posterior** a confirmar: «¿Desea generar un PDF con el detalle?» y acciones **Aceptar / Cancelar**. Cancelar no revierte la operación; debe existir recuperación posterior del comprobante desde su detalle auditado, sujeta a autorización.
- No almacenar ni registrar un PDF ficticio como si fuera acuse del banco.

## Reutilización técnica prevista

Crear un módulo o servicio central de generación PDF con componentes para membrete, metadatos, tablas, subtotales, pie y paginación. Las plantillas de tipos documentales aportan contenido pero no duplican el membrete. Todo contenido dinámico requiere escape, corte seguro de cadenas, control de páginas y autorización en backend. Mantener pruebas de importes/totales, permisos por Empresa y existencia del logo.

## Validación y mantenimiento

Antes de implementar en producción: aprobar visualmente el boceto; validar PDF con múltiples ítems, textos largos y documentos de varias páginas; comprobar impresión A4, legibilidad y paginación; verificar que no se escape información entre Empresas. Cambios posteriores a logo, paleta o membrete requieren aprobación: **ninguna decisión estética unilateral**.

**Nota:** el PDF de ejemplo `OrdenaClick_boceto_detalle_gestion_bancaria.pdf` contiene solo datos ilustrativos y no representa una operación real.
