# Nómina de Empleados y gestión de accesos — diseño funcional (14/10/2026)

**Estado: diseño acordado; primera etapa de implementación propuesta en Casa, pendiente de pruebas y aprobación visual.** No existe todavía un módulo de Nómina ni un gestor general de permisos granulares. Esta especificación no autoriza migraciones, habilitación de accesos ni cambios al circuito de Alertas sin nueva revisión, pruebas y aceptación visual. Prioridad y calendario sujetos a la Beta.

## 1. Nómina en el panel de OrdenaClick

- Módulo **Nómina de Empleados**, por **Empresa activa**, integrado al panel y sidebar existentes; nunca mezclar empleados de Empresas distintas.
- Listado inspirado visualmente en **Próximos vencimientos**: arriba **Empleados activos** agrupados en **verde** y abajo **Empleados inactivos** agrupados en **rojo**, conservando la estética, fuentes y distribución de OrdenaClick. Esta agrupación refleja vínculo laboral, no vencimientos ni avisos de campana.
- Botón superior **[Registrar]** para alta de empleado; filas accesibles para consultar/editar la ficha según permiso. Buscar por nombre, CUIL o legajo; posibilidad de filtrar por Centro, sin ampliar permisos.
- Alta y edición auditables. **Desvincular** cambia a inactivo sin borrar ficha, adjuntos ni historial, registrando al menos fecha, causa y actor. Política de reingreso/reactivación y unicidad de legajo/CUIL: **por definir y validar** antes de implementar.

## 2. Ficha del empleado

### Datos personales

- **CUIL**; **Nombre y Apellido**; **Fecha de nacimiento**; **Número de legajo**.
- **Dirección**; **Teléfono personal**; **Mail personal**. Los contactos provistos por el empleador van en Datos laborales.
- **Vencimiento de licencia de conducir**.
- **Contacto de emergencia:** Nombre y Teléfono.
- Adjuntos diferenciados: **[Subir DNI frente]**, **[Subir DNI dorso]** y **[Subir Licencia de conducir]**.

### Datos laborales

- **Fecha de ingreso**.
- **Mail laboral** y **Teléfono laboral**, asignados por el empleador y separados del contacto personal.
- **Centro Operativo**: selector de Centros autorizados de la Empresa más **[+]** al ABM existente.
- **Vehículo asignado**: recurso operativo de tipo **Vehículo** de esa Empresa, más **[+]** a Recursos Operativos; no crear un catálogo paralelo.
- **Cuenta sueldo (CBU)** y **Banco**: selector de Bancos de la Empresa más **[+]** al ABM existente. Registrar el CBU como dato confidencial, sin convertirlo en cuenta bancaria de la Empresa ni generar movimientos.
- **Tipo de contratación**: selector **Jornada completa / Media jornada**.
- Documentación laboral: **[Clave de Alta Temprana - CAT]** y **[Preocupacional]**. Usar el nombre **CAT**, no rotular el primer documento simplemente «Alta AFIP». La futura documentación **Baja ARCA** se registra en el historial/caso correspondiente.
- Acciones de ficha: **[Guardar]**, **[Desvincular]** y **[Abrir caso]**, sujetas a capacidades distintas.

## 3. Casos e historial laboral

- **Abrir caso** crea un antecedente/expediente asociado a la ficha, con categoría: **Apercibimiento**, **Despido**, **Baja ARCA**, **Constancia de aportes**, **Juicio/reclamo laboral** u **Otro**.
- Registrar cronología de actuaciones con fecha, actor, contenido, documentos adjuntos y estado del caso. No sobrescribir silenciosamente actuaciones ni eliminar historia al desvincular.
- El futuro **perfil Legal** debe poder trabajar sobre los casos **expresamente autorizados**, no recibir automáticamente toda la ficha, el CBU ni documentación médica.
- No implementar ahora una gestión judicial, liquidación de sueldos, asistencia, cálculo de indemnizaciones ni presentaciones automáticas ante ARCA.

## 4. Alertas de licencia y desvinculación

- Al registrar el vencimiento de la **licencia de conducir** de un **empleado activo**, generar la alerta de seguimiento **un mes antes**. La interpretación técnica exacta de «un mes» (mes calendario o 30 días) se definirá en el servicio antes de implementarlo.
- **La licencia vencida no desvincula al empleado**: cambia solamente su situación documental y su seguimiento.
- **La desvinculación sí anula/desactiva todas las alertas activas vinculadas a ese empleado** y evita nuevos avisos mientras esté inactivo; incluye silenciar la campana. Conservar historial de alertas y motivos, sin borrar evidencia ni cambiar estados de obligaciones externas no relacionadas.
- Renovar la licencia actualiza el vencimiento y el seguimiento de forma auditable. La política de reconocimiento de avisos y campana sin repetición perpetua se integrará con el diseño general de Alertas, **aún pendiente** (incluidos cheques vencidos).
- Las reglas de fechas, elegibilidad y notificación se calculan en **backend**; nunca como permisos o estados supuestos por JavaScript.

## 5. Gestor de accesos por usuario — pendiente de revisión global

- Ubicación propuesta: **Configuración → Designar perfiles / Gestionar accesos**, reutilizando el sistema actual de usuarios vinculados y relaciones Empresa/rol/Centro; ubicación definitiva pendiente de UX.
- Interfaz propuesta: un **listado de capacidades** con un **interruptor ON/OFF por usuario**, legible y simple. No equivale a dar permisos por cambiar un elemento visual: cada permiso se valida y audita en servidor.
- Distinguir **jerarquía organizacional**, **roles funcionales** (Contable, Legal, etc.), **alcance por Empresa/Centro** y **capacidades específicas**. No sustituir a ciegas las políticas vigentes; realizar revisión transversal de accesos antes de habilitar el gestor.
- Ejemplos de capacidades separables: **ver Nómina**, **registrar/editar datos básicos**, **consultar/subir documentos administrativos**, **ver datos sensibles**, **desvincular**, **abrir/ver/gestionar casos**, **gestionar alertas**, **gestionar accesos**. Los permisos finos por tipo de documento quedan sujetos a diseño y pruebas.
- Un **colaborador interno**, administrativo, secretaria o contador autorizado puede **archivar documentación** sin ser jerárquico y **sin heredar** potestad para desvincular, gestionar causas legales, modificar Caja, realizar pagos o ver todos los datos sensibles.
- La concesión/revocación será auditable, revocable, de mínimo privilegio y restringida a quien tenga capacidad legítima de administrar accesos. **Denegar por defecto** lo no concedido expresamente, sin filtraciones entre Empresas o Centros.
- Respetar que permisos de usuarios son **contexto de autorización**, no un hecho empresarial portable: no incluir concesiones activas indiscriminadamente en Backup Empresa. Definir antes la portabilidad de nuevos datos y documentos de Nómina, con compatibilidad hacia atrás.

## 6. Documentos privados, navegación y seguridad

- DNI, CUIL, domicilio, teléfonos, CBU, contacto de emergencia, documentos laborales, preocupacionales y expedientes exigen **almacenamiento privado**, validación real de archivo, comprobación de permisos en **cada** lectura, descarga y escritura, y auditoría proporcional a su sensibilidad.
- El **Preocupacional** implica información especialmente sensible: limitar su exposición al mínimo necesario y no compartir automáticamente con perfiles administrativos o Legal. Revisar criterios de privacidad y retención antes de producción.
- No usar URLs públicas `/media/` ni confiar en campos ocultos, IDs enviados por navegador o simplemente ocultar botones; servidor valida **Empresa, Centro y capacidad**.
- `[+]` debe abrir los **ABM existentes** de Centros, Recursos Operativos y Bancos y volver a la ficha restaurando campos, documentos aún no enviados de modo seguro (sin inventar persistencia de archivos) y **posición de scroll**. Al abrir/cerrar modales, el contenido debe quedar en la parte **visible** de la pantalla/panel. Evitar JS/CSS inline nuevos.
- Incorporar modelos/documentos/eventos nuevos de manera aditiva y con auditoría, pruebas de permisos, respaldo/restauración y aceptación visual antes de commits/push. **No modificar ahora** la funcionalidad de Caja, Cartera, Pagos, REGISTROS o Alertas.

## 7. Alcance de la primera versión y decisiones aún abiertas

**Primera versión propuesta:** listado activos/inactivos, ficha, adjuntos privados, altas/correcciones/desvinculación auditadas, historial de casos básico y alertas de licencia integradas a backend.

**Abierto tras la primera etapa:** gestor granular, reingresos, permisos documentales/Legal, privacidad/retención, revisión de alertas generales y aceptación UX. No dar por aprobado sin pruebas y revisión.


## Etapa de implementación 0049 (pendiente de ejecutar en Casa)

La primera etapa monta el acceso en **Herramientas → Nómina de Empleados**.
Incluye ficha, documentos privados, historial y casos, alerta de licencia con
anticipación de **un mes calendario** (ajustando el último día cuando no existe),
reconocimiento de aviso y cancelación por desvinculación. La licencia vencida
no cambia el estado laboral. La campana y el listado Alertas pueden incluir
avisos laborales **sin mezclar saldos financieros**.

**Permisos transitorios:** lectura/escritura y descargas restringidas a
propietario, superusuario o Administración General, hasta implementar el gestor
por capacidades granulares. No se conceden permisos implícitos a Centro,
colaboradores o Legal. Una futura secretaria/administrativo podrá subir
archivos mediante permisos explícitos, todavía no disponibles.

**Reglas conservadoras:** CUIL válido y legajo únicos por Empresa, incluso
inactivos. Sin reactivación automatizada; requiere diseño posterior. Documentos
versionados (no reemplazo destructivo), expediente cronológico, copia dentro del
Backup Empresa v1 como nuevas secciones opcionales para backups anteriores.
Los `[+]` abren el ABM existente dentro del mismo panel, sin desmontar la
ficha ni perder los documentos aún seleccionados. Volver restaura la posición
y los campos; si el ABM registró un elemento nuevo, se preselecciona.
Revisión visual y pruebas de navegación pendientes de aceptación.
**Esta etapa no configura accesos, liquidaciones, ARCA, medicina laboral ni
avisos por correo.** La política general de alertas y la revisión de seguridad
integral siguen abiertas.
