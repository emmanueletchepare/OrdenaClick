# OrdenaClick — Relevo operativo para un nuevo chat (15/10/2026)

**Corte válido:** desarrollo sincronizado desde Casa a Oficina mediante GitHub `main`, commit **`902cdeb`** (`feat: incorpora primera version de nomina de empleados`). No declarar otro HEAD sin comprobar Git. **Este corte prevalece sobre los párrafos históricos que aún llaman «futuras» a Caja 2/Nómina.** Es continuidad de trabajo, no certificado de Beta ni de seguridad de producción.

## 1. Qué es, dónde está y qué se verificó

OrdenaClick es un SaaS Django de gestión multiempresa; preservar estrictamente Empresa activa, alcance Centro, permisos por acción, contabilidad financiera e historial auditable. Repositorio: `emmanueletchepare/OrdenaClick`. Casa: `D:\Programacion\Proyectos\Ordenaclick`. Oficina: `D:\Emmanuel\Ordenalick`. Desarrollo actual: **Oficina**, PowerShell con `(venv)`.

Se sincronizó Oficina de `b89ff5a` a `902cdeb` mediante `git fetch` y `git merge --ff-only origin/main`. El `git status --short` quedó limpio al terminar. **Cambios inconclusos anteriores de Caja 2 en Oficina** fueron guardados selectivamente como `stash@{0}: On main: Oficina Caja 2 inconclusa antes de sincronizar Casa 902cdeb`; **NO ejecutar `git stash pop` ni mezclar ese código antiguo**: la referencia válida es Casa/GitHub. Verificar que el stash siga ahí antes de tomar decisiones; no borrarlo sin autorización.

Oficina usa **SQLite** activo en `D:\Emmanuel\Ordenalick\db.sqlite3`. Antes de actualizar se hizo backup consistente con API `sqlite3.backup()` y `PRAGMA integrity_check = ok`, fuera del repo, en `C:\Users\Usuario\.ordenaclick\respaldos_codigo\oficina_db_antes_0048_0050_20261015_091154_798.sqlite3`. Se aplicaron correctamente migraciones `usuarios.0048` (e-Cheq), `0049` (Nómina) y `0050` (teléfono laboral). **35 pruebas pasaron en Oficina** (`usuarios.pruebas.test_nomina_empleados`, `test_alertas_vencimientos`, `test_backup_empresa`, `test_documentos_privados_b10a`, `test_b11_rutas_permisos_y_altas`); en Casa la misma batería pasó. No confundir una base temporal de tests con la base normal ni dar por hecha una comprobación de interfaz que no se realizó. En Casa existen tres respaldos SQLite sin seguimiento: preservarlos, no incluirlos en Git.

## 2. Estado funcional relevante

- **Caja 2 / Pendientes bancarios / e-Cheqs:** código publicado, precarga por lote y gestión de pendientes disponibles para revisión operativa. La bandeja de pendientes es global **dentro de la Empresa activa** para los usuarios autorizados; al resolver se identifica Centro/cliente. No transformar precarga en Movimiento de Caja, recibo o pago por defecto; un e-Cheq ingresa a cartera virtual conforme al circuito vigente.
- **Nómina de Empleados:** publicada, menú **Herramientas → Nómina de Empleados**. Listado activos/inactivos, ficha, CUIL autoformateado con guiones en UI y 11 dígitos normalizados en backend, documentos privados, casos, alertas y baja laboral. **Mail laboral y Teléfono laboral en Datos laborales**; mail y teléfono personales en Datos personales. CAT, DNI, licencia, preocupacional, Centro `[+]`, Vehículo `[+]`, Banco `[+]`. El acceso actual a Nómina sigue restringido a propietario/administración general/superusuario hasta disponer de permisos explícitos. En la revisión general en Oficina el usuario dijo **«Están todos bien»** y pasó a Caja 2; no quedó documentada una prueba individual de cada `[+]`, por lo que no inventar esos pasos.
- **Navegación visual general:** hay una infraestructura existente de sidebar/panel y navegación contextual heredada; antes de cambiar, inspeccionar los consumidores. No introducir pestañas nuevas para `[+]`.

## 3. Observaciones registradas en uso real de e-Cheqs — NO PROGRAMAR TODAVÍA

El usuario está cargando **movimientos reales** y desea **acumular hallazgos y resolverlos juntos** al terminar las pruebas. No modificar backend, JS, CSS, templates ni migraciones por estos hallazgos hasta su aprobación explícita.

1. En el **listado de precarga/revisión** separar **Número e-Cheq** y **Titular / Cliente**: deben ser columnas independientes, no `e-Cheq / Titular` combinadas.
2. Mostrar **Fecha de acreditación** en cada fila. Estructura sugerida: Número e-Cheq | Titular / Cliente | Banco | Fecha acreditación | Condición | Importe | Acciones. Adaptar a anchuras responsivas sin perder legibilidad ni patrón visual aprobado.
3. Al intentar **Guardar todos** aparece el mensaje **«El importe no es válido. El lote permanece en pantalla para reintentar.»** Sin indicación de qué fila/campo está mal. Debe validarse al **Agregar** (antes de incorporar al listado) y al **editar**, en frontend como ayuda y siempre en backend. En el guardado final identificar fila y campo, resaltar, explicar de manera entendible, ubicar/focalizar el error y **conservar todo el lote**, sin guardar parcialmente. Diagnosticar si la causa real es el formato local argentino (por ejemplo `126.785,71`) u otra condición: **aún no está diagnosticada**; no modificar números a ciegas. Preservar atomicidad, auditabilidad e idempotencia existentes.

## 4. Perfil Colaborador — decisión estructural para próximos desarrollos

**Colaborador = prácticamente el mismo panel Administrador, pero con menos funciones y operaciones autorizadas.** No crear un panel paralelo, duplicar templates ni reinventar menú, estética, formularios o ABMs; **reutilizar la infraestructura y componentes existentes**, mostrar/habilitar funciones según permisos efectivos. Cada nuevo desarrollo del panel Administrador debe **pensarse desde el inicio** para Colaborador, aunque se lo habilite después: no codificar supuestos rígidos de «solo admin» en funcionalidades potencialmente delegables. Esto NO significa concederle acceso automático.

El futuro **Panel de Permisos / Accesos** (en torno a Configuración → Designar perfiles / Gestionar accesos, ubicación final por validar) debe ser la **fuente central** de capacidades por usuario, módulo y acción. Distinguir rol/jerarquía, Empresa y Centro, capacidades de ver/registrar/editar/confirmar/eliminar/descargar/gestionar, y los datos sensibles. Por defecto, denegar toda capacidad no otorgada; concesión y revocación auditables y efectivas también en backend. Ocultar botones o URLs no reemplaza autorización HTTP y servicios. Sin cruces entre Empresas, sin alcance de Centro ampliado, sin Caja ni saldos por habilitar Pendientes. Permisos son contexto de acceso y **no se exportan como concesiones activas en Backup Empresa**.

**Primer recorrido candidato:** un usuario ya fue designado Colaborador para probar **Pendientes bancarios** con información real, pero **el perfil todavía no está desarrollado/funcionando para ese circuito**. Priorizar paridad visual/navegación con Administrador, acceso autorizado explícitamente a Pendientes y matriz mínima para mostrar/operar solo las acciones asignadas. Probar permitido/denegado, GET/POST, revocación, Empresa/Centro y accesos directos por URL. Mantener Nómina restringida hasta definir permisos sensibles finos. No asumir que el gestor granular está implementado por existir Designar perfiles.

## 5. Reglas de navegación, seguridad y visual que NO se negocian

- Botón `[+]` de un selector abre el **ABM real existente DENTRO del mismo panel**, nunca nueva pestaña ni modal inventado; volver restaura **borrador, listas temporales, campos, archivos seleccionados cuando el navegador lo permita de manera segura, foco, modo de edición y posición de scroll**, y selecciona automáticamente el nuevo registro. Pila contextual **LIFO anidable**, no retorno directo fijo. No desmontar la ficha ni perder entradas; botones «Volver» únicamente en el contexto correcto. Los ABM existentes tienen mecanismos heredados: analizarlos y no romperlos con sustituciones masivas.
- Estética: preservar fuentes, colores, sidebar, tamaño y alineación de botones, listas/encabezados, modales visibles y CSS del sistema. Reutilizar los estilos ya aprobados (Empresa, Caja 2, Próximos vencimientos), nada de rediseños espontáneos. **Sin JS/CSS inline nuevos**, código modular externo.
- Seguridad: sesión y Empresa activa, alcance Centro, capacidades por acción en backend, CSRF y POST para mutaciones; transacciones/locking donde correspondan; auditoría y aislamiento. Archivos DNI, CBU, preocupacional y documentos: privados con autorización por lectura/descarga. Sin secretos en Git ni fuga entre tenants. Mantener historial financiero y bajas controladas. Antes de migrar/base, respaldo verificable externo al repo.
- Los errores visibles deben **explicar qué corregir y dónde**, preservar estado no sensible, impedir operaciones parciales. Importes es-AR con validación real del Decimal, no solo formato visual.

## 6. Método de trabajo acordado — muy importante para el nuevo asistente

El usuario prefiere **español argentino preciso, directo, sin relleno**. No asumir que algo funciona solo porque `check` pasa. Buscar y reutilizar arquitectura, formularios/ABM reales y convenciones antes de proponer. **No desarrollar durante la etapa actual de recolección de hallazgos**; primero continuar anotando.

Al autorizar desarrollo: inspeccionar archivos de código y documentación vigentes y baseline (`git status --short`, `git log -1 --oneline`, migraciones, tests); proponer alcance acotado, invariantes, preflight y plan de pruebas antes de editar. **Entregar helper `.py` descargable en el chat**, para guardarlo en **raíz junto a `manage.py`** y ejecutarlo con PowerShell. No pasar decenas de modificaciones manuales ni pedir copiar fragmentos de código en archivos. El helper debe:

1. detectar la ruta/commit/ancoras esperadas y si ya está aplicado; detenerse **SIN cambios** ante divergencias. No buscar nombres genéricos en TODO `models.py` (ya provocó un falso positivo por `telefono_laboral` en otro modelo); verificar clase o ubicación exacta;
2. hacer backup de **TODOS** los archivos existentes que tocará, **fuera del repo** (`$HOME\.ordenaclick\respaldos_codigo\...`), verificando hash; no incluir SQLite inadvertidamente ni copiar sobre el proyecto de Oficina sin proteger datos;
3. aplicar solamente archivos acordados, escritura atómica y rollback ante error, no borrar historial/adjuntos/migraciones, ni hacer `reset --hard`, `stash pop`, `git add .`, commits ni push silenciosos;
4. informar rutas, archivos, backups y comandos de validación. Probar `py_compile`, `manage.py check`, migraciones según alcance, pruebas unitarias y regresiones, revisión HTTP/visual/navegación y `git diff --check`;
5. una vez verificado, **hacer commit selectivo y push al GitHub** para continuar entre Casa y Oficina. **No demorar un commit solo porque queden observaciones visuales abiertas**: etiquetar correctamente «en desarrollo». GitHub es la herramienta de continuidad, no un sello de acabado.

Cuando haya modificaciones locales en Oficina, nunca hacer `git pull`/merge que las pise. Respaldar de forma comprobada, apartarlas solo con autorización y actualizar fast-forward; el stash de Caja 2 es histórico, no recuperarlo automáticamente. **No subir helpers temporales ni respaldos SQLite**.

## 7. Qué hacer primero en el nuevo chat

1. Pedir/inspeccionar `git status --short`, `git log -1 --oneline` para detectar si el helper documental de este corte fue ejecutado y publicado. Leer `00_RUMBO_Y_ESTADO.md`, `01_CONTINUIDAD_IA.md`, `REGLAS.md`, `DECISIONES.md`, `FLUJO_NAVEGACION.md`, `NOMINA_EMPLEADOS_Y_ACCESOS.md`, `TODO.md` y este relevo. No volver a preguntar decisiones ya asentadas.
2. **Mientras el usuario prueba e-Cheqs reales: solo registrar nuevas observaciones**, agrupadas con las tres anteriores y sin cambios de código.
3. Cuando el usuario autorice el desarrollo, revisar juntos el backlog y acordar un bloque acotado. Posibles prioridades: corrección de la precarga e-Cheq y base compartida Administrador/Colaborador con permisos de Pendientes; no imponer un orden sin consultarlo.
4. En el primer desarrollo de Colaborador, asegurar herencia de **pantallas compartidas, no de permisos administrativos**. Todo módulo nuevo de Administrador debe contemplar su posible habilitación a Colaborador desde el diseño y ser probado bajo ambos roles cuando aplique.

**Importante:** este corte se escribió desde el estado verificado en la conversación y docs de GitHub `902cdeb`. El resultado de las últimas operaciones de Git después de las pruebas en Oficina, ni los detalles individuales de las pruebas visuales de Nómina **se han vuelto a comprobar**; sí consta la conformidad general del usuario «Están todos bien».
