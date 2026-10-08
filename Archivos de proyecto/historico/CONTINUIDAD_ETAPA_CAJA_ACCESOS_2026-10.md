# CONTINUIDAD_ETAPA_CAJA_ACCESOS.md

**Fecha de corte:** 04/10/2026\
**Commit estable de referencia:** `da16e88` ---
`feat: incorpora Caja, cobranzas y base de jerarquias de acceso`\
**Propósito:** permitir abrir un chat nuevo y continuar OrdenaClick
exactamente desde el estado actual, sin reconstruir la conversación ni
cambiar el enfoque de trabajo.

> Este documento está escrito principalmente como instrucción de
> continuidad para ChatGPT. Debe leerse junto con TODOS los `.md` de
> `Archivos de proyecto/` y con el código vigente del proyecto. El
> código real y las migraciones aplicadas mandan sobre cualquier
> descripción histórica desactualizada. Si dos documentos se
> contradicen, no improvisar: inspeccionar código, migraciones, tests y
> documentos autoritativos antes de modificar.

------------------------------------------------------------------------

## 0. INSTRUCCIÓN PARA INICIAR UN CHAT NUEVO

Al comenzar un chat nuevo, Emanuel puede subir el proyecto completo y
este archivo y decir simplemente:

> Leé primero `CONTINUIDAD_ETAPA_CAJA_ACCESOS.md`, después revisá los
> demás `.md` del proyecto y el código vigente. Continuamos exactamente
> desde el punto de reanudación, respetando la forma de trabajo
> indicada.

El asistente debe entonces:

-   [ ] Leer este documento completo antes de proponer código.
-   [ ] Revisar los demás `.md` de `Archivos de proyecto/`, en especial
    `ARQUITECTURA.md`, `Auditoria.md`, `DECISIONES.md`,
    `MODELO_DATOS.md`, `PRE_BETA.md`, `REGLAS.md`, `TODO.md`,
    `VISION.md`, `FLUJO_NAVEGACION.md`, `TRAZABILIDAD_FUENTES.md` y
    `ORDENACLICK_DISENO_CAJA_CARTERAS_OP.md`.
-   [ ] Inspeccionar el código real antes de asumir que un pendiente
    histórico sigue pendiente.
-   [ ] Verificar `git status --short` y `git log -1 --oneline` antes de
    decidir qué pertenece al commit estable y qué es trabajo posterior.
-   [ ] No pedirle a Emanuel que vuelva a pegar fragmentos o busque
    líneas si el archivo completo ya fue subido y puede ser
    inspeccionado por el asistente.
-   [ ] Retomar desde la sección **PUNTO EXACTO DE REANUDACIÓN** de este
    documento.

------------------------------------------------------------------------

## 1. FORMA DE TRABAJO Y FORMA DE COMUNICAR INSTRUCCIONES

Esta forma de trabajo es parte del proyecto y debe conservarse.

### 1.1 Comunicación con Emanuel

Las instrucciones de modificación deben ser concretas y no ambiguas.
Usar siempre este esquema cuando se pida un cambio manual:

**Archivo:** `ruta/al/archivo.py`\
**Función / clase / bloque:** `nombre()`\
**Buscar:** una línea o bloque que exista realmente en el archivo
inspeccionado\
**Acción:** agregar / reemplazar / eliminar\
**Ubicación exacta:** "inmediatamente después de..." / "antes de..."\
**Código:** bloque completo listo para copiar\
**Verificación:** comando o resultado esperado

Reglas adicionales:

-   [x] Trabajar en español.
-   [x] Dar un cambio manejable por vez cuando el cambio sea delicado.
-   [x] Si el asistente tiene el archivo completo, **debe buscar él
    mismo** la ubicación. No mandar a Emanuel a rastrear código que el
    asistente puede inspeccionar.
-   [x] No decir "en tu archivo" si hay varios archivos en contexto:
    nombrar siempre la ruta exacta.
-   [x] Para funciones/clases grandes o delicadas, preferir bloque
    completo de reemplazo si reduce el riesgo de indentación o ubicación
    incorrecta.
-   [x] Después de cada etapa pequeña, indicar qué quedó hecho y qué
    check puede tildarse.
-   [x] No adelantar cinco modificaciones si todavía no se verificó la
    primera cuando existe riesgo de arrastrar errores.
-   [x] No inventar nombres de campos, relaciones, endpoints o
    estructuras: inspeccionarlos primero.
-   [x] Si una decisión previa resulta técnicamente incorrecta al
    revisar el flujo real, decirlo explícitamente y corregirla antes de
    seguir.

### 1.2 Reglas de desarrollo

-   [x] No hacer refactors incidentales "porque sí".
-   [x] Sí hacer una refactorización estructural cuando sea necesaria
    para seguridad, escalabilidad o mantenibilidad y el bloque que se
    está tocando ya lo exige.
-   [x] No agregar JavaScript inline nuevo.
-   [x] No agregar CSS inline nuevo salvo excepción mínima, explícita y
    documentada.
-   [x] Lógica de negocio reutilizable en servicios; views para HTTP,
    autorización, coordinación y respuesta.
-   [x] El frontend mejora UX pero nunca decide autorización,
    pertenencia ni integridad.
-   [x] Diseñar pensando en ejecución real en servidor, usuarios
    concurrentes y entradas hostiles.
-   [x] Antes de un commit: `git status`, staging selectivo, revisar
    diff; no usar `git add .`.
-   [x] No versionar backups SQLite, ZIP runtime, temporales ni datos
    privados.
-   [x] Toda entidad nueva relacionada con Empresa obliga a revisar
    Exportar/Importar Empresa.
-   [x] "Se ve bien" no equivale a terminado: debe existir `check`,
    tests y prueba manual cuando corresponda.

------------------------------------------------------------------------

## 2. DOCUMENTOS DEL PROYECTO: CRITERIOS QUE NO DEBEN PERDERSE

Se revisaron los `.md` del proyecto al preparar esta continuidad. Las
reglas relevantes para la etapa actual son:

### `VISION.md`

OrdenaClick debe crecer sobre una sola arquitectura escalable. Seguridad
es requisito de producto, no agregado posterior.

### `ARQUITECTURA.md`

Exportar/Importar Empresa debe ser una copia completa y portable del
entorno Empresa. Si eliminar y reimportar haría perder un dato, debe
formar parte del backup salvo exclusión explícita. El formato debe estar
versionado y las relaciones deben reconstruirse sin asumir que los IDs
físicos se conservan.

### `DECISIONES.md`

Está cerrado que:

-   el backup debe ser portable;
-   activos e inactivos relevantes deben considerarse;
-   toda entidad nueva de Empresa obliga a revisar export/import;
-   el formato debe estar versionado;
-   la importación no debe depender de conservar PK físicos.

### `Auditoria.md`

Exportar Empresa todavía está auditado como **incompleto y crítico**:
hoy puede generar falsa sensación de backup. También está pendiente
reconstrucción segura de IDs y limpieza controlada de ZIP históricos
versionados.

### `PRE_BETA.md`

Importar Empresa es bloqueante de seguridad antes de servidor/Beta. Debe
contemplar:

-   autenticación y rol autorizado;
-   límites de upload y tamaño descomprimido;
-   validación ZIP y rutas permitidas;
-   esquema del contenido;
-   impedir reemplazo de Empresa ajena;
-   temporales privados y limpieza garantizada;
-   pruebas adversariales.

### `REGLAS.md`

Cada modelo nuevo/modificado relacionado con Empresa debe responder:

1.  ¿Se exporta?
2.  ¿Se importa?
3.  ¿Tiene archivos?
4.  ¿Qué relaciones se reconstruyen?
5.  ¿Contiene información sensible?
6.  ¿Se conservan inactivos?
7.  ¿Afecta la versión o compatibilidad del formato de backup desde v1 en adelante?

### `TODO.md`

Exportar/Importar completo continúa siendo trabajo real pendiente; no
debe marcarse terminado hasta reconstruir el ecosistema y probarlo.

### `MODELO_DATOS.md`

Las relaciones pertenecientes a Empresa deben mantenerse aisladas entre
Empresas y ser reconstruibles sin confiar en PK de otra instalación.

### `ORDENACLICK_DISENO_CAJA_CARTERAS_OP.md`

Caja, Cartera, Gestión Administrativa y OP deben conservar separación
conceptual, trazabilidad, integridad y seguridad para
servidor/concurrencia. El documento contiene nomenclatura histórica
"Administrador de sucursal"; la decisión vigente es mostrar
**Administrador** con alcance por Centro Operativo.

------------------------------------------------------------------------

## 3. ESTADO FUNCIONAL CERRADO ANTES DEL BLOQUE ACTUAL

### 3.1 Caja y Cobranza

-   [x] Caja es módulo principal del sidebar.
-   [x] Caja y Centro Operativo son entidades distintas.
-   [x] Una Caja puede pertenecer a Casa Central, Sucursal o Mostrador;
    no a Depósito.
-   [x] Puede haber varias Cajas por Centro.
-   [x] Dashboard de Caja existente.
-   [x] Selector de Caja concreta y `Todas` cuando corresponde.
-   [x] Para registrar cobranza se requiere Caja concreta.
-   [x] `obtener_caja_autorizada()` centraliza validación Empresa/Caja
    existente.
-   [x] Nueva Cobranza tiene composición visual aprobada.
-   [x] Número de cheque se normaliza a ocho posiciones.
-   [x] Diferencia de cobranza = Cobrado - Declarado.
-   [x] Efectivo USD no participa de conciliación del total declarado.

### 3.2 Total declarado

-   [x] `total_declarado` es opcional.
-   [x] Vacío = `NULL`, no cero.
-   [x] Informado =\> mayor que cero.
-   [x] Informado =\> concilia contra Efectivo ARS + Cheques.
-   [x] Vacío no impide guardar.
-   [x] Si está vacío no se muestran Total declarado ni Diferencia en la
    conciliación inferior.

### 3.3 Servicios y tests de Cobranza

Servicios existentes:

-   [x] `saldo_efectivo_caja`.
-   [x] `cheques_fisicos_disponibles_caja`.
-   [x] `resumen_disponibilidad_caja`.
-   [x] `validar_cobranza`.
-   [x] `crear_cobranza_validada`.
-   [x] normalización/validación común de cheques.

Se corrigieron tests de `CobranzaCajaTests` para usar datos de cheque
válidos según las reglas vigentes.

Resultado antes del commit estable:

-   [x] `python manage.py check` limpio.
-   [x] `python manage.py test usuarios.tests.CobranzaCajaTests -v 2`:
    6/6 OK.
-   [x] `python manage.py test`: 99/99 OK.

El POST real de Nueva Cobranza continúa sin conectarse hasta cerrar
autorización real.

------------------------------------------------------------------------

## 4. COMMIT ESTABLE YA REALIZADO

Commit:

`da16e88 feat: incorpora Caja, cobranzas y base de jerarquias de acceso`

Incluyó 23 archivos, entre ellos:

-   Caja CSS/JS/templates;
-   dashboard y Nueva Cobranza;
-   migraciones `0036`, `0037`, `0038`;
-   cambios en modelos, servicios financieros, seguridad, tests, urls y
    views;
-   documentación de proyecto.

Después del commit, `git status --short` mostraba únicamente tres
backups SQLite sin trackear:

-   `db_antes_limpieza_pruebas.sqlite3`
-   `db_antes_reset_pruebas_20260913.sqlite3`
-   `db_antes_reset_total_pruebas_20260913.sqlite3`

No deben versionarse.

**Nota sobre el ZIP de continuidad:** al inspeccionar el proyecto
comprimido pueden aparecer muchos archivos como modificados por
metadatos/normalización del ZIP. Para determinar cambios reales usar el
repositorio original de Emanuel y su `git diff`, no asumir que todo lo
listado dentro de una copia descomprimida representa modificaciones
funcionales.

------------------------------------------------------------------------

## 5. JERARQUÍA Y ACCESO: DECISIÓN FUNCIONAL VIGENTE

### Administrador fundador

-   [x] Es quien crea la Empresa.
-   [x] Fuente de verdad: `Empresa.propietario`.
-   [x] Tiene control total.
-   [x] No se duplica como `AsignacionUsuarioEmpresa` para acreditar
    propiedad.
-   [x] Ningún Administrador general puede desvincularlo.

### Administrador general

-   [x] Designado dentro de la Empresa.
-   [x] Alcance completo a toda la Empresa, todos los Centros y Cajas.
-   [x] Puede administrar estructura y operaciones según las capacidades
    que se vayan cerrando.
-   [x] No puede desvincular al fundador.

### Administrador

-   [x] Nombre visible: **Administrador**.
-   [x] La constante interna puede seguir siendo
    `JERARQUIA_ADMIN_CENTRO` por ahora.
-   [x] Se asigna a un Centro Operativo.
-   [x] Ve/opera lo correspondiente a ese Centro, incluidas sus Cajas.
-   [x] No se asigna Caja por Caja en esta etapa.

### Colaborador

-   [x] Acceso operativo limitado.
-   [x] **No tiene acceso a Caja.**
-   [x] Ejemplos actualmente definidos: Carga Simple y tareas/listados
    de e-Cheqs pendientes de documentar externamente.
-   [x] No inventar una matriz enorme de permisos todavía; las
    capacidades se agregan cuando aparecen necesidades reales.

------------------------------------------------------------------------

## 6. `AsignacionUsuarioEmpresa`: ESTADO REAL ACTUAL

El código vigente ya superó el punto histórico del documento anterior.

En `usuarios/models.py` existe `AsignacionUsuarioEmpresa` con:

-   [x] `empresa`.
-   [x] `usuario = settings.AUTH_USER_MODEL`.
-   [x] `jerarquia`.
-   [x] `centro_operativo` nullable.
-   [x] `activo`.
-   [x] timestamps.
-   [x] unicidad `empresa + usuario`.
-   [x] etiqueta visible `admin_centro` =\> `Administrador`.
-   [x] `CheckConstraint` `asignacion_jerarquia_centro_coherente`.

La coherencia actualmente impuesta por base es:

-   `admin_centro` =\> `centro_operativo` obligatorio;
-   `admin_general` y `colaborador` =\> `centro_operativo` nulo.

Migraciones:

-   [x] `0037_asignacionusuarioempresa.py`.
-   [x] `0038_asignacionusuarioempresa_centro_operativo_and_more.py`.
-   [x] `0038` aplicada correctamente.
-   [x] `python manage.py check` quedó limpio después de migrar.

**No volver a proponer generar `0038`: ya existe y fue aplicada.**

------------------------------------------------------------------------

## 7. SEGURIDAD QUE DEBE GUIAR TODO LO QUE SIGUE

Existe `usuarios/services/seguridad.py`. La autorización debe
centralizarse allí o en servicios equivalentes; no dispersarse por
views.

Reglas obligatorias:

-   [ ] Toda consulta por Empresa debe impedir IDOR.
-   [ ] Toda consulta por Centro debe comprobar pertenencia a Empresa
    autorizada.
-   [x] Toda consulta por Caja debe comprobar Empresa + Centro + Caja +
    estado + alcance del usuario. **Cerrado para el flujo Caja/Nueva Cobranza mediante servicio central y tests de jerarquías.**
-   [x] El propietario conserva acceso por `Empresa.propietario`.
-   [x] Administrador general obtiene alcance Empresa.
-   [x] Administrador obtiene alcance sólo de su Centro.
-   [x] Colaborador no obtiene Caja.
-   [x] El frontend nunca constituye autorización en los flujos cerrados de Backup/Import y Caja; la autorización se resuelve en backend.
-   [x] IDs recibidos desde navegador, sesión, JSON o ZIP son datos no
    confiables; Backup v1 y los servicios de seguridad validan pertenencia/referencias antes de operar.
-   [ ] Los POST financieros no se habilitan a perfiles sin autorización
    backend completa.
-   [x] Considerar concurrencia y transacciones para operaciones
    críticas. Backup/Restore v1 usa restauración transaccional y Cobranza conserva creación atómica.

------------------------------------------------------------------------

## 8. TRABAJO POSTERIOR AL COMMIT `da16e88`: CAMBIOS PROVISIONALES SIN CERRAR

Después del commit se comenzó a incorporar `AsignacionUsuarioEmpresa` al
mecanismo existente de Exportar/Importar Empresa.

Estos cambios **NO constituyen una implementación final**. Deben
tratarse como prototipo útil para entender el flujo y ser absorbidos o
reemplazados por la reconstrucción del subsistema.

### 8.1 `usuarios/views.py`

Se agregó/importó `AsignacionUsuarioEmpresa`.

En `exportar_empresa()` se agregó provisionalmente:

-   consulta de asignaciones de la Empresa;
-   `select_related("usuario", "centro_operativo")`;
-   escritura de `asignaciones_usuarios.json`;
-   datos actuales: username, email, jerarquía, centro `{id, nombre}` y
    `activo`.

**Problema conocido:** esto sigue dentro de la view, usa un ID físico
como parte del formato y no existe todavía un formato de backup
versionado ni un catálogo completo de entidades.

### 8.2 `importar_empresa()`

Se agregó lectura opcional de `asignaciones_usuarios.json`:

-   si existe, se carga;
-   si no existe, `datos_asignaciones = []` para no romper
    inmediatamente ZIP antiguos.

Luego se guarda provisionalmente:

`request.session["asignaciones_importadas"] = datos_asignaciones`

### 8.3 `panel_admin()`

Se agregó provisionalmente:

``` python
asignaciones_importadas = request.session.get(
    "asignaciones_importadas",
    []
)
```

Inicialmente se había usado `pop()`, pero se corrigió a `get()` porque
el GET que muestra los datos importados ocurre antes del POST que crea
la nueva Empresa; con `pop()` las asignaciones se perdían antes de poder
usarse.

### 8.4 Estado de estos cambios

-   [x] Se ejecutó `python manage.py check` después de los primeros
    cambios y quedó limpio.
-   [x] El prototipo fue absorbido/reemplazado por Backup Empresa v1; ya existe restauración real controlada de identidades/asignaciones.
-   [x] Existen tests específicos del subsistema nuevo; el prototipo legacy no se conserva como solución independiente.
-   [x] No se siguen agregando JSONs ad hoc dentro de `views.py`; el subsistema vive en servicios dedicados.
-   [x] Estos cambios dejaron de ser la solución vigente: fueron reemplazados por la implementación v1 probada.

------------------------------------------------------------------------

## 9. DECISIÓN NUEVA: RECONSTRUIR EXPORTAR/IMPORTAR EMPRESA COMO SUBSISTEMA

Este es el **punto arquitectónico actual**.

Al revisar el código y los documentos se confirmó que el mecanismo
actual de Exportar Empresa sólo representa una parte pequeña del
entorno. Por ejemplo, todavía no transporta adecuadamente Centros
Operativos y por lo tanto ni siquiera podría restaurar con seguridad un
Administrador asociado a una sucursal.

No continuar agregando archivos JSON uno por uno directamente a
`exportar_empresa()`.

### 9.1 Objetivo

Convertir Exportar/Importar Empresa en infraestructura estable, segura,
versionada, extensible y testeable.

Dirección acordada:

-   `views.py`: HTTP, autorización, recepción/entrega del archivo y
    coordinación mínima.
-   servicio de exportación: construir backup.
-   servicio de importación: inspeccionar, validar, planificar y
    restaurar.
-   formato versionado con manifest.
-   relaciones reconstruidas mediante identificadores portables/mapas,
    nunca confiando en PK de la instalación origen.
-   compatibilidad controlada entre versiones estables desde Backup Empresa v1 en adelante; no se soportan ZIP pre-v1 de desarrollo.
-   validación antes de persistir.
-   transacciones donde corresponda.
-   tests unitarios, integración y adversariales.

Los nombres exactos de módulos (`services/exportacion_empresa.py`,
`services/importacion_empresa.py`, etc.) deben confirmarse al diseñar el
bloque; la separación conceptual sí está acordada.

### 9.2 Manifest propuesto conceptualmente

El ZIP nuevo debería tener un manifiesto con, como mínimo:

-   identificador de formato (`ordenaclick_empresa` o equivalente);
-   versión de formato;
-   versión/aplicación que lo generó si resulta útil;
-   fecha de exportación;
-   componentes incluidos;
-   metadatos necesarios para validación/migración.

No fijar todavía el esquema definitivo sin inventariar las entidades.

### 9.3 Identidades y relaciones

-   PK Django de origen puede conservarse sólo como referencia histórica
    si resulta útil.
-   Nunca usar ese PK como identidad confiable en destino.
-   Construir mapas `identidad_origen -> objeto_destino` durante
    restauración.
-   Para entidades sin clave natural segura, definir identificador
    portable interno del backup.
-   Las referencias deben validarse contra la Empresa que se está
    restaurando.

### 9.4 Usuarios y privilegios: regla de máxima importancia

Un ZIP es entrada no confiable.

-   [x] Nunca importar passwords.
-   [x] Nunca importar sesiones.
-   [x] Nunca importar `is_staff`, `is_superuser`, permisos Django o
    grupos como instrucciones de privilegio.
-   [x] El propietario contenido en un backup no decide el propietario
    de la Empresa restaurada.
-   [x] Una Empresa nueva creada desde importación continúa teniendo
    como propietario al usuario autenticado autorizado que ejecuta la
    creación, salvo que en el futuro exista un flujo administrativo
    explícito y seguro diferente.
-   [x] Un `admin_general` escrito dentro de un ZIP no debe poder
    autoelevar privilegios por el solo hecho de aparecer en el archivo.
-   [x] Política explícita para usuarios/asignaciones: cuentas existentes
    coincidentes pueden vincularse/reactivarse sólo por decisión del usuario
    autorizado; usuarios ausentes quedan como identidad histórica y Backup v1
    no crea cuentas Django ni contraseñas automáticamente.
-   [x] El fundador no se duplica como asignación.

### 9.5 Seguridad del archivo ZIP

Antes de servidor/Beta contemplar como mínimo:

-   [x] autenticación y autorización para exportar/importar;
-   [x] límites de tamaño de upload;
-   [x] límite de tamaño total descomprimido;
-   [x] límite de cantidad de archivos/entradas;
-   [x] rechazo de rutas absolutas y `../` (Zip Slip);
-   [x] rechazo de nombres inesperados según versión/esquema;
-   [x] validación de JSON y tipos/campos;
-   [x] manejo de ZIP corrupto;
-   [x] temporales privados y limpieza en éxito/error;
-   [x] no confiar en MIME/extensión solamente;
-   [x] no permitir reemplazar Empresa ajena;
-   [x] no sobrescribir archivos arbitrarios;
-   [x] no incluir secretos de instalación;
-   [ ] ampliar pruebas adversariales específicas antes de servidor/Beta; hoy existen pruebas concretas de manifest/legacy, Zip Slip, permisos/alcance y round-trip.

### 9.6 Información que NO debe viajar como backup empresarial ordinario

Salvo diseño explícito futuro:

-   `SECRET_KEY`;
-   variables de entorno;
-   claves maestras;
-   credenciales de infraestructura;
-   passwords;
-   sesiones;
-   secretos/certificados privados cuya portabilidad no haya sido
    diseñada de forma segura;
-   permisos globales de instalación.

Configuraciones sensibles deben clasificarse individualmente antes de
decidir exportación.

### 9.7 Decisiones cerradas el 04/10/2026 para Backup Empresa v1

-   [x] No existe necesidad de compatibilidad con backups legacy: todavía no
    hay Beta ni clientes productivos y las Empresas actuales son de prueba.
-   [x] El subsistema nuevo comienza directamente con un formato estable
    **Backup Empresa v1**.
-   [x] La futura precarga de datos estándar (por ejemplo bancos comunes) será
    infraestructura independiente del backup empresarial.
-   [x] Importar Empresa se concibe como un proceso guiado de restauración y
    puesta en marcha, no como restauración ciega.
-   [x] El backup conserva historia, pero durante el wizard el usuario
    autorizado podrá confirmar o actualizar información que pueda haber
    cambiado desde el origen.
-   [x] Ejemplos ya definidos para el wizard: confirmar/cambiar categoría ante
    ARCA, actualizar documentación societaria y decidir qué usuarios continúan
    activos, cuáles quedan inactivos, su jerarquía vigente y altas nuevas.
-   [x] Los usuarios históricos no desaparecen: la trazabilidad de operaciones
    debe conservar quién las generó/modificó aunque el usuario quede inactivo.
-   [x] Separar identidad histórica de autorización actual. Un rol escrito en
    el ZIP no otorga por sí mismo privilegios en destino.
-   [x] Si el CUIT ya existe, no borrar primero la Empresa vigente. Validar,
    planificar, confirmar y recién entonces restaurar con protección frente a
    estados parciales/rollback.
-   [x] Dirección futura: evaluar un wizard análogo para el alta inicial de
    Empresa, de forma que el usuario complete la configuración por pasos sin
    necesitar conocer de antemano todo lo requerido.

------------------------------------------------------------------------

## 10. INVENTARIO PREVIO OBLIGATORIO PARA EL NUEVO BACKUP

Antes de escribir el exportador nuevo, inventariar modelos/relaciones
vigentes relacionados con Empresa.

Para cada entidad responder las siete preguntas de `REGLAS.md` y además
definir orden de restauración.

Como mínimo revisar:

-   [x] Empresa.
-   [x] documentación societaria/archivos de Empresa.
-   [x] Ejercicios.
-   [x] Centros Operativos.
-   [x] Recursos Operativos y relaciones multicentro.
-   [x] AsignacionUsuarioEmpresa.
-   [x] Bancos.
-   [x] Cuentas Bancarias.
-   [x] Proveedores.
-   [x] Tipos de Gasto y relaciones.
-   [x] Clientes.
-   [x] Cajas.
-   [x] Movimientos.
-   [x] Pagos.
-   [x] AplicacionPago.
-   [x] medios de pago específicos.
-   [x] Tarjetas.
-   [x] Cheques/e-Cheqs.
-   [x] Retenciones.
-   [x] Planes de Pago.
-   [x] Cuotas.
-   [x] Vencimientos.
-   [x] Alertas/configuraciones asociadas.
-   [x] Cobranzas.
-   [x] Movimientos de Caja.
-   [ ] futuras Carteras / Gestión Administrativa / Órdenes de Pago
    cuando existan.
-   [x] archivos adjuntos e históricos.
-   [x] registros inactivos relevantes.

No asumir que esta lista está completa: obtener la lista real desde
`usuarios/models.py` y relaciones del proyecto al iniciar el diseño.

------------------------------------------------------------------------

## 11. PLAN DE IMPLEMENTACIÓN DEL SUBSISTEMA EXPORT/IMPORT

### Fase 0 --- congelar el prototipo actual

-   [x] No seguir agregando JSON ad hoc a `views.py`.
-   [ ] Revisar diff real posterior a `da16e88` en el repositorio de
    Emanuel. **Pendiente para cierre/commit; el ZIP no reemplaza esta revisión.**
-   [x] Decidir qué partes del prototipo se reutilizan y cuáles se
    reemplazan. El prototipo quedó absorbido por Backup Empresa v1.

### Fase 1 --- inventario y contrato

-   [x] Inventariar modelos y archivos.
-   [x] Dibujar dependencias/orden de restauración.
-   [x] Clasificar datos sensibles.
-   [x] Definir qué se exporta y qué se excluye explícitamente.
-   [x] Definir formato v1 y manifest.
-   [x] Definir identificadores portables.
-   [x] Definir política legacy: no soportar backups previos a Backup Empresa v1 en esta etapa pre-Beta.

### Fase 2 --- servicio de exportación

-   [x] Crear servicio dedicado.
-   [x] Autorizar Empresa antes de exportar.
-   [x] Serializar componentes sin lógica HTTP.
-   [x] Incluir activos/inactivos según contrato.
-   [x] Empaquetar archivos de forma segura.
-   [x] Manifest versionado.
-   [x] Tests del exportador.

### Fase 3 --- inspector/validador de importación

-   [x] Validar ZIP antes de persistir.
-   [x] Validar manifest/versión.
-   [x] Validar esquema de cada componente.
-   [x] Validar referencias internas.
-   [x] Aplicar límites anti-bomba/anti-Zip-Slip.
-   [x] No implementar conversión de ZIP legacy pre-v1; esa compatibilidad quedó descartada para esta etapa.
-   [ ] Completar batería adversarial específica antes de servidor/Beta; ya están cubiertos Zip Slip, manifest legacy y reglas críticas de autorización.

### Fase 4 --- restaurador

-   [x] Restaurar en orden de dependencias.
-   [x] Construir mapas de identidades.
-   [x] Resolver Centros antes de asignaciones de Administrador.
-   [x] Política segura para usuarios/asignaciones.
-   [x] Transacción para bloques que deban ser atómicos.
-   [x] No dejar Empresa "medio restaurada" sin estado
    explícito/rollback.
-   [x] Restaurar archivos sólo en ubicaciones controladas.
-   [x] Tests de round-trip exportar -\> importar.

### Fase 5 --- integración HTTP

-   [x] Adelgazar `exportar_empresa()`.
-   [x] Adelgazar `importar_empresa()`.
-   [x] Eliminar de `panel_admin()` responsabilidades de reconstrucción
    que correspondan al servicio.
-   [x] Mantener confirmaciones de UX sin convertir sesión en fuente de
    autorización.
-   [x] Mensajes de error seguros, sin filtrar detalles internos
    innecesarios.

### Fase 6 --- documentación y cierre

-   [ ] Actualizar `ARQUITECTURA.md`.
-   [ ] Actualizar `Auditoria.md` sólo con lo realmente resuelto.
-   [ ] Actualizar `DECISIONES.md` si se cierran decisiones nuevas.
-   [ ] Actualizar `MODELO_DATOS.md`.
-   [ ] Actualizar `PRE_BETA.md`.
-   [ ] Actualizar `REGLAS.md` si nace una regla transversal.
-   [ ] Actualizar `TODO.md`.
-   [x] Actualizar este documento de continuidad.
-   [x] Regresión completa: 114/114 tests OK en el entorno real de Emanuel.
-   [ ] Commit selectivo.

------------------------------------------------------------------------

## 12. LIMPIEZA / SEPARACIÓN DE JS, HTML Y CSS

Emanuel planteó correctamente que, si esta etapa exige reconstrucción
para seguridad y escalabilidad, es momento de ordenar también
responsabilidades frontend cuando el código tocado lo justifique.

Criterio:

-   No hacer una reescritura cosmética de todo el proyecto.
-   Sí extraer JS/CSS inline cuando se toque ese flujo y la extracción
    reduzca deuda o permita reutilización/pruebas.
-   No mezclar esta limpieza con reglas de autorización backend.
-   Mantener módulos existentes (`static/js/...`, `static/css/...`) como
    dirección preferida.
-   `panel_admin.html` y `usuarios/views.py` están auditados como
    archivos demasiado grandes; la reducción debe hacerse por fronteras
    funcionales reales, no por cortar arbitrariamente.

Checklist durante esta etapa:

-   [x] Revisar si Exportar/Importar tiene JS inline heredado.
-   [x] Revisar si tiene CSS inline heredado.
-   [x] Si se toca, mover comportamiento a módulo JS específico.
-   [x] Si se toca, mover estilos a CSS específico o común según
    corresponda.
-   [x] No introducir nuevos handlers inline.
-   [x] No permitir que JS decida permisos.

------------------------------------------------------------------------

## 13. NAVEGACIÓN `[+]` QUE NO DEBE ROMPERSE

Toda navegación contextual debe converger a una pila LIFO común:

`formulario -> [+] -> ABM -> crear/reactivar/modificar -> volver -> conservar formulario -> seleccionar nuevo registro -> restaurar posición`

Debe soportar anidación A -\> B -\> C -\> D y retorno D -\> C -\> B -\>
A.

Cada nivel conserva:

-   pantalla/origen;
-   estado del formulario;
-   filas dinámicas;
-   scroll;
-   foco/originador;
-   registro creado/reactivado a seleccionar.

No crear mecanismos particulares nuevos para Caja o Export/Import si el
problema pertenece a infraestructura común.

------------------------------------------------------------------------

## 14. PRUEBAS MÍNIMAS ANTES DE CERRAR EL BLOQUE ACTUAL

Histórico ya cumplido antes de `da16e88`:

-   [x] `python manage.py check`.
-   [x] migraciones `0037`/`0038` aplicadas sin errores.
-   [x] `CobranzaCajaTests` verdes.
-   [x] regresión de 99 tests verde.

Para el nuevo bloque Export/Import deberán agregarse, como mínimo:

-   [ ] tests HTTP específicos de autorización para exportar.
-   [x] restauración por Administrador general probada sin reemplazar al fundador.
-   [ ] test HTTP específico de Empresa ajena no exportable/importable por IDOR.
-   [ ] test específico de ZIP inválido/corrupto.
-   [x] path traversal / Zip Slip.
-   [ ] tests específicos de límites de tamaño/entradas/descompresión.
-   [x] manifest ausente/backup legacy rechazado.
-   [ ] test específico de versión de manifest no soportada.
-   [ ] tests específicos de JSON malformado y tipos inválidos.
-   [ ] test específico de referencias internas inexistentes.
-   [x] IDs de origen distintos de destino: round-trip reconstruye relaciones sin conservar PK de hijos.
-   [x] Centros reconstruidos antes de dependientes dentro del restaurador/round-trip.
-   [ ] test adversarial específico de usuario del ZIP intentando autoelevarse a admin general.
-   [x] fundador del backup/restauración no reemplaza al propietario vigente.
-   [x] Gestión de Claves no exporta el secreto cifrado y Backup v1 no importa passwords/permisos globales.
-   [ ] test específico de activos/inactivos según contrato para todos los tipos relevantes.
-   [x] round-trip de una Empresa representativa.
-   [x] compatibilidad legacy descartada para esta etapa pre-Beta; no implementar soporte pre-v1.
-   [ ] test forzado de rollback/atomicidad ante falla intermedia.
-   [ ] test específico de round-trip de archivos adjuntos.
-   [x] `python manage.py check` final.
-   [x] regresión completa final: 114/114 OK.

------------------------------------------------------------------------

## 15. GIT Y CIERRE

Antes de cualquier commit nuevo:

-   [ ] `git status --short`.
-   [ ] `git --no-pager diff --stat`.
-   [ ] revisar cambios reales posteriores a `da16e88`.
-   [ ] confirmar que backups SQLite y ZIP runtime no se stagean.
-   [ ] no usar `git add .`.
-   [ ] stage selectivo.
-   [ ] `git --no-pager diff --cached --stat` y diff de partes críticas.
-   [ ] `python manage.py check`.
-   [ ] tests específicos.
-   [ ] regresión completa.
-   [ ] commit coherente.
-   [ ] registrar hash aquí.

No confundir el commit estable `da16e88` con el futuro commit que cierre
Export/Import.

------------------------------------------------------------------------

## 16. ADVERTENCIAS PARA EL PRÓXIMO CHAT

1.  **No pedir archivos que ya fueron subidos sin comprobar primero si
    siguen disponibles.**
2.  **No pedirle a Emanuel que busque código si el asistente tiene el
    archivo completo.**
3.  **Nombrar siempre archivo + función + ubicación exacta.**
4.  **No volver a generar `0038`: ya existe y está aplicada.**
5.  **No duplicar al fundador en `AsignacionUsuarioEmpresa`.**
6.  **No volver a "Administrador de sucursal" como nombre visible; es
    `Administrador` con alcance Centro.**
7.  **No crear `AccesoCaja` usuario\<-\>Caja como solución primaria.**
    Administrador opera Cajas de su Centro; Colaborador no opera Caja.
8.  **No habilitar POST financieros a colaboradores sin autorización
    real.**
9.  **No confiar en IDs provenientes del navegador o del backup.**
10. **No seguir extendiendo el exportador actual con JSONs ad hoc dentro
    de `views.py`.**
11. **No restaurar asignaciones antes de restaurar/identificar sus
    Centros.**
12. **No permitir que el backup decida privilegios globales ni propiedad
    de la Empresa.**
13. **No tratar Exportar Empresa como backup completo hasta que
    round-trip y cobertura estén probados.**
14. **No agregar JS/CSS inline nuevo.**
15. **No romper la pantalla aprobada de Nueva Cobranza mientras se
    trabaja en infraestructura.**
16. **No tocar SECRET_KEY, claves privadas, certificados o configuración
    de instalación como parte del backup empresarial sin diseño
    explícito.**
17. **No hacer limpieza destructiva del historial Git de ZIP privados
    improvisadamente.** Está auditado como pendiente y requiere
    procedimiento controlado.

------------------------------------------------------------------------

## 17. PUNTO EXACTO DE REANUDACIÓN

Este es el punto desde el cual debe arrancar el próximo chat.

### Ya cerrado

-   [x] Commit estable histórico `da16e88`.
-   [x] Caja/Cobranza base incorporadas.
-   [x] `AsignacionUsuarioEmpresa` + alcance por Centro.
-   [x] `IdentidadUsuarioEmpresa` incorporada mediante migración `0039`.
-   [x] Auditoría histórica desacoplada de `auth.User` para Cobranza/MovimientoCaja.
-   [x] Backup Empresa v1 implementado con manifest, identificadores portables y servicios dedicados.
-   [x] Inspector defensivo ZIP/JSON/referencias implementado.
-   [x] Restauración transaccional y round-trip probado.
-   [x] Wizard Empresa -> Usuarios -> Resumen implementado.
-   [x] Gestión de Claves no transporta el secreto cifrado.
-   [x] JS/CSS del flujo nuevo separados y agrupados; sin JS inline nuevo.
-   [x] Seguridad de jerarquías incorporada al servicio central para Empresa/Centro/Caja.
-   [x] Fundador protegido.
-   [x] Administrador general con alcance Empresa.
-   [x] Administrador con alcance sólo de su Centro y sus Cajas.
-   [x] Colaborador sin acceso a Caja.
-   [x] `panel_caja` filtra Cajas según alcance real.
-   [x] Nueva Cobranza respeta alcance de Caja en backend.
-   [x] `python manage.py check` limpio.
-   [x] `JerarquiasSeguridadTests`: 10/10 OK.
-   [x] `BackupEmpresaV1Tests`: 5/5 OK.
-   [x] `CobranzaCajaTests`: 6/6 OK.
-   [x] Regresión completa: 114/114 OK.

### Pendientes inmediatos

-   [ ] Conectar el **POST real de Nueva Cobranza** usando la autorización backend ya cerrada.
-   [ ] Ejecutar manualmente el último POST de confirmación del wizard sobre una copia/entorno descartable y revisar el resultado restaurado; la UI previa ya fue revisada y aprobada.
-   [ ] Revisar `git status --short` y diff real del repositorio original.
-   [ ] Sincronizar los `.md` autoritativos que todavía describan Export/Import como incompleto.
-   [ ] Hacer staging selectivo, revisar diff cached y realizar commit coherente.
-   [ ] Registrar el nuevo hash estable en este documento.

### No volver atrás

-   No retomar desde `0038`: esa etapa terminó.
-   No reconstruir Export/Import desde el prototipo legacy: Backup Empresa v1 ya lo reemplazó.
-   No abrir indiscriminadamente todas las views a `AsignacionUsuarioEmpresa`; habilitar capacidades módulo por módulo.
-   No permitir que una asignación, sesión, ID del navegador o ZIP sustituya la autorización backend.
-   No duplicar al fundador como asignación.
-   No dar Caja a Colaborador.

**Próximo trabajo funcional recomendado:** conectar el POST real de Nueva Cobranza con el servicio de seguridad ya validado; luego continuar con el circuito de designación de Administradores generales / Administradores / Colaboradores.

------------------------------------------------------------------------

## 18. ETAPAS QUE SIGUEN DESPUÉS DE EXPORT/IMPORT

No perderlas, pero no mezclarlas antes de tiempo:

-   [x] incorporar jerarquías/asignaciones al servicio de seguridad de
    forma completa;
-   [x] alcance Empresa/Centro/Caja;
-   [x] proteger fundador;
-   [x] asegurar que Colaborador no accede a Caja;
-   [ ] ABM seguro de Cajas si corresponde al bloque;
-   [ ] circuito para designar Administradores generales /
    Administradores / Colaboradores;
-   [ ] origen desde recursos/personas/postulantes cuando se diseñe;
-   [ ] conectar POST real de Nueva Cobranza sólo con autorización
    backend cerrada;
-   [ ] continuar Cartera / Gestión Administrativa / Orden de Pago según
    documento funcional.

------------------------------------------------------------------------

## 19. CRITERIO DE ETAPA CERRADA

La etapa global Caja + Accesos no está cerrada sólo por tener el modelo
de asignaciones.

Se considerará cerrada cuando, según el alcance finalmente acordado:

-   [x] jerarquías sin ambigüedad;
-   [x] fundador protegido;
-   [x] admin general con alcance Empresa;
-   [x] Administrador con alcance Centro;
-   [x] Colaborador sin Caja;
-   [ ] autorización backend aplicada;
-   [x] export/import considera las entidades nuevas de forma segura;
-   [x] tests específicos y regresión verdes;
-   [ ] documentación sincronizada con código;
-   [ ] commit selectivo realizado y hash registrado.

Si Export/Import se cierra en un commit independiente antes del resto de
Accesos, registrarlo explícitamente y continuar desde ese nuevo
baseline.

---

## ACTUALIZACIÓN 04/10/2026 — BACKUP EMPRESA V1 IMPLEMENTADO PARA PRUEBA

Después del bloque de `IdentidadUsuarioEmpresa` (`0039`) se implementó una primera versión integral de Backup Empresa v1.

Estado a verificar en el repositorio de Emanuel antes de considerar commit:

- [x] servicios separados en `usuarios/services/backup_empresa/`;
- [x] exportador con manifest v1 y componentes inventariados;
- [x] inspector defensivo de ZIP/JSON/referencias;
- [x] restaurador transaccional sin depender de PK de origen;
- [x] wizard de Empresa -> usuarios -> resumen;
- [x] sin passwords ni privilegios globales importados;
- [x] Gestión de Claves sin secreto cifrado portable;
- [x] JS/CSS nuevos separados en carpetas agrupadas;
- [x] tests específicos nuevos;
- [x] round-trip ejecutado sobre una copia de OLAFIL con igualdad de cantidades por componente;
- [x] `python manage.py check` ejecutado en el entorno real de Emanuel: limpio;
- [x] tests específicos ejecutados en el entorno real: Jerarquías 10/10, Backup v1 5/5 y CobranzaCaja 6/6;
- [x] regresión completa ejecutada: 114/114 OK;
- [x] revisión manual visual/funcional del flujo Exportar/Importar y wizard realizada; **no se ejecutó el último POST de confirmación sobre la Empresa real para evitar modificarla durante la revisión**;
- [ ] revisar diff real del repositorio original y recién entonces decidir commit.

No considerar este bloque cerrado sólo por haber copiado los archivos. El baseline final será el resultado de las verificaciones anteriores.


---

## ACTUALIZACIÓN 04/10/2026 — JERARQUÍAS Y ALCANCE DE CAJA VALIDADOS

Se cerró el bloque de seguridad central necesario para continuar Caja/Cobranza sin abrir accidentalmente todos los módulos administrativos.

- [x] resolución central de asignación activa;
- [x] fundador con acceso total por `Empresa.propietario`;
- [x] Administrador general con alcance completo de Empresa;
- [x] Administrador restringido a su Centro Operativo;
- [x] Administrador sólo ve/opera Cajas de su Centro;
- [x] Colaborador no accede a Caja;
- [x] asignación inactiva no concede Caja;
- [x] `panel_caja` filtra Cajas por alcance backend;
- [x] Nueva Cobranza valida Caja según alcance;
- [x] el panel administrativo general no se abre implícitamente sólo por existir una asignación;
- [x] Administrador general puede operar Backup/Restore sin reemplazar al fundador;
- [x] tests de jerarquías: 10/10 OK;
- [x] Backup Empresa v1: 5/5 OK;
- [x] Cobranza Caja: 6/6 OK;
- [x] regresión completa: 114/114 OK.

Queda pendiente, antes de servidor/Beta, ampliar la batería adversarial específica de Backup v1 (ZIP corrupto, límites, JSON inválido, referencias rotas, rollback forzado y adjuntos), aunque las defensas correspondientes ya están implementadas.

**Siguiente check funcional:** conectar el POST real de Nueva Cobranza con esta autorización backend ya cerrada.



---

## ACTUALIZACIÓN 05/10/2026 — RELACIONES MULTIEMPRESA Y ROLES FUNCIONALES

Decisión e implementación base:

- [x] el usuario pertenece a OrdenaClick y puede existir sin Empresa;
- [x] fundador continúa definido por `Empresa.propietario`;
- [x] jerarquía administrativa/operativa se mantiene en `AsignacionUsuarioEmpresa`;
- [x] Contable y Legal pasan a roles funcionales acumulables mediante `RolFuncionalUsuarioEmpresa`;
- [x] un usuario puede ser, por ejemplo, Colaborador + Contable en la misma Empresa;
- [x] se incorpora `SolicitudRelacionEmpresa` para designaciones con aceptación explícita;
- [x] solicitud pendiente no concede permisos;
- [x] Fundador/Admin general pueden enviar solicitudes;
- [x] usuario acepta/rechaza desde perfil `Relaciones`;
- [x] inicio muestra aviso de solicitudes pendientes;
- [x] perfil visible: Administrador / Colaborador / Contable / Legal / Relaciones; Desarrollador sólo superusuario;
- [x] solicitudes sólo a usuarios existentes; no se inventan cuentas ni credenciales;
- [x] solicitudes pendientes quedan fuera del Backup Empresa ordinario por ser workflow transitorio ligado a cuentas de la instalación;
- [x] roles funcionales activos se incorporan a Backup Empresa v1 y deben ser confirmados durante importación;
- [ ] marketplace de disponibilidad/postulaciones/ranking/contratación/actividad/pagos queda para etapa futura;
- [ ] definir capacidades concretas de Contable y Legal antes de abrir módulos.

**Regla que no debe perderse:** marketplace, reputación u origen interno/externo nunca sustituyen la autorización backend por Empresa/rol/capacidad.
