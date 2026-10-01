# CONTINUIDAD_ETAPA_CAJA_ACCESOS.md

**Fecha de corte:** 28/09/2026\
**Propósito:** documento de continuidad para retomar esta etapa de
OrdenaClick en un chat nuevo sin cambiar el enfoque, repetir decisiones
ni rehacer trabajo.

> Este archivo está escrito como instrucción de trabajo para ChatGPT.
> Debe leerse junto con los demás `.md` del proyecto y con el código
> vigente. Si existe una diferencia entre este documento y el código
> real, primero inspeccionar el código y los documentos fuente antes de
> modificar nada.

------------------------------------------------------------------------

## 1. FORMA DE TRABAJO QUE DEBE CONSERVARSE

-   [x] Trabajar en español.
-   [x] Dar cambios concretos indicando archivo y ubicación exacta.
-   [x] Para funciones/clases grandes o delicadas, entregar el bloque
    completo a reemplazar.
-   [x] No hacer refactors incidentales ni cambios "de paso".
-   [x] No agregar JavaScript inline.
-   [x] No agregar CSS inline salvo excepción mínima, explícita y
    documentada.
-   [x] Las reglas de negocio reutilizables viven en servicios; las
    views coordinan HTTP, autorización, formularios y respuestas.
-   [x] El frontend mejora UX pero nunca decide autorización,
    pertenencia ni integridad.
-   [x] Todo debe diseñarse para vivir de forma segura en un dominio
    web.
-   [x] Antes de cambiar una conducta existente, inspeccionar cómo está
    implementada y reutilizar/normalizar la regla.
-   [x] No hacer trabajar al usuario innecesariamente: normalizar
    automáticamente cuando sea seguro.
-   [x] Antes de un commit: `git status`, staging selectivo y nunca
    `git add .`.
-   [x] No versionar backups SQLite ni archivos runtime.
-   [x] Toda entidad nueva relacionada funcionalmente con Empresa debe
    revisarse para Exportar/Importar Empresa.
-   [x] No declarar que algo está terminado sólo porque "se ve bien":
    debe haber check/tests/prueba manual según corresponda.

------------------------------------------------------------------------

## 2. CONTEXTO FUNCIONAL YA CERRADO

### 2.1 Caja y Cobranza

-   [x] Caja es un módulo principal del sidebar, no un submódulo de
    REGISTROS.
-   [x] Caja representa custodia/movimiento de recursos físicos.
-   [x] Centro Operativo y Caja son entidades distintas.
-   [x] Una Caja puede pertenecer a:
    -   Casa Central.
    -   Sucursal.
    -   Mostrador.
-   [x] No corresponde Caja a Depósito.
-   [x] Puede haber más de una Caja dentro de un mismo Centro Operativo.
-   [x] El dashboard de Caja ya existe y muestra disponibilidad.
-   [x] El selector de Caja permite una Caja concreta y, cuando
    corresponde, `Todas`.
-   [x] Para registrar una cobranza debe existir una Caja concreta;
    `Todas` no es una Caja operable.
-   [x] `obtener_caja_autorizada()` centraliza actualmente la validación
    Empresa/Caja.
-   [x] Nueva Cobranza tiene composición visual aprobada.
-   [x] Número de cheque se normaliza a 8 posiciones con ceros a la
    izquierda.
-   [x] Diferencia de cobranza usa `Cobrado - Declarado`.
-   [x] Diferencia cero = verde; distinta de cero = roja.
-   [x] Efectivo USD no participa de la conciliación del total
    declarado.

### 2.2 Total declarado

Regla funcional cerrada:

-   [x] `total_declarado` es opcional.
-   [x] Vacío se representa como `NULL`, no como cero.
-   [x] Si se informa debe ser mayor que cero.
-   [x] Si se informa, se compara contra Efectivo ARS + Cheques.
-   [x] Si no se informa, la ausencia no impide guardar.
-   [x] Si está vacío, en la conciliación inferior no deben mostrarse
    Total declarado ni Diferencia.
-   [x] Esta regla todavía debe incorporarse a los `.md` autoritativos
    en la próxima actualización documental.

### 2.3 Modelos financieros existentes

Migraciones ya aplicadas:

-   [x] `0032` Caja.
-   [x] `0033` Cobranza.
-   [x] `0034` MovimientoCaja.
-   [x] `0035` Cheque.
-   [x] `0036` Total declarado opcional.
-   [x] `0037` AsignacionUsuarioEmpresa.

Servicios financieros ya existentes:

-   [x] `saldo_efectivo_caja`.
-   [x] `cheques_fisicos_disponibles_caja`.
-   [x] `resumen_disponibilidad_caja`.
-   [x] `validar_cobranza`.
-   [x] `crear_cobranza_validada`.
-   [x] Normalización/validación común de cheques.

El POST real de Nueva Cobranza todavía **no está conectado**.

------------------------------------------------------------------------

## 3. SEGURIDAD ACTUAL QUE NO DEBE ROMPERSE

Existe `usuarios/services/seguridad.py`.

### `obtener_empresa_autorizada(usuario, empresa_id)`

Estado actual:

-   Superusuario: puede obtener Empresa.
-   Propietario de Empresa: autorizado.
-   Las asignaciones reales de colaboradores/administradores todavía no
    estaban incorporadas al servicio al iniciar esta etapa.

### `obtener_caja_autorizada(usuario, empresa_id, caja_id)`

Ya existe y:

-   primero autoriza Empresa;
-   exige Caja de esa Empresa;
-   exige Caja activa;
-   exige Centro activo;
-   permite Centro tipo Casa Central, Sucursal o Mostrador.

Este servicio debe evolucionar con el nuevo sistema de asignaciones.
**No duplicar autorización en cada view.**

Bloqueante pre-Beta:

-   permisos reales Administrador/Colaborador/Contable/Legal;
-   alcance Centro/Caja antes de habilitar POST financieros a
    colaboradores;
-   auditoría completa de endpoints/IDOR.

------------------------------------------------------------------------

## 4. REGLA DE NAVEGACIÓN QUE DEBE CONSERVARSE

Toda navegación `[+]` debe terminar usando una pila contextual común
LIFO.

Invariante:

`formulario → [+] → ABM → crear/reactivar/modificar → volver → conservar formulario → seleccionar nuevo registro cuando corresponda → restaurar misma posición visual`

Debe admitir:

`A → [+] B → [+] C → [+] D → volver D→C→B→A`

Cada nivel conserva:

-   pantalla/origen;
-   estado/valores del formulario;
-   filas dinámicas;
-   scroll/posición visual;
-   elemento originador/foco;
-   mecanismo de restauración;
-   registro creado/reactivado que debe seleccionarse al regresar.

No crear nuevas variables particulares tipo `origenABM` para Caja. Los
mecanismos heredados se migrarán gradualmente y sólo se eliminan cuando
todos sus consumidores hayan sido migrados/probados.

------------------------------------------------------------------------

## 5. DECISIÓN NUEVA SOBRE JERARQUÍA Y ACCESO

Esta es la definición funcional dada por Emanuel y debe guiar esta
etapa.

### Administrador fundador

-   [x] Es el usuario que crea la Empresa.
-   [x] Actualmente esa verdad estructural está representada por
    `Empresa.propietario`.
-   [x] Tiene control total de la Empresa.
-   [x] No necesita una fila duplicada en `AsignacionUsuarioEmpresa`
    para acreditar que es fundador.
-   [x] Ningún Administrador general designado puede desvincular al
    fundador.

### Administrador general

-   [x] Es designado dentro de la Empresa.
-   [x] Tiene acceso completo a toda la Empresa.
-   [x] Incluye todos los Centros Operativos y todas sus Cajas.
-   [x] Puede administrar estructura y operaciones.
-   [x] No puede desvincular al Administrador fundador.

### Administrador

-   [x] Se asigna a un Centro Operativo.
-   [x] Puede ver y operar todo lo correspondiente a ese Centro.
-   [x] Eso incluye las Cajas del Centro.
-   [x] No se asigna Caja por Caja en esta etapa.
-   [x] En código existente la constante puede seguir llamándose
    temporalmente `JERARQUIA_ADMIN_CENTRO`; el nombre visible acordado
    es `Administrador`.

### Colaborador

-   [x] Tiene acceso operativo limitado.
-   [x] No tiene acceso a Caja.
-   [x] Por ahora se identificaron como ejemplos:
    -   Carga Simple / Comprobantes operativos.
    -   Listados/tareas de e-Cheqs pendientes de documentar en sistema
        externo.
-   [x] Los demás permisos se definirán cuando aparezcan necesidades
    reales.
-   [x] No crear ahora una matriz artificial de decenas de permisos no
    definidos.

### Origen de personas designables

La definición funcional indica que el Administrador fundador puede
designar personas:

-   desde recursos/personas disponibles de la Empresa, según
    corresponda;
-   o desde postulantes/solicitudes.

**No inventar todavía el circuito exacto de postulaciones si el código
no lo implementa.** La documentación histórica dice que ese submenú
estaba a desarrollar.

------------------------------------------------------------------------

## 6. MODELO `AsignacionUsuarioEmpresa`: ESTADO ACTUAL

Se agregó en `usuarios/models.py` inmediatamente antes de `Caja`.

La migración:

`0037_asignacionusuarioempresa.py`

ya fue creada y aplicada correctamente.

`python manage.py check` quedó limpio después de migrar.

La clase creada conceptualmente contiene:

-   `empresa`;
-   `usuario`;
-   `jerarquia`;
-   `activo`;
-   `creado`;
-   `actualizado`;
-   unicidad `empresa + usuario`.

Las jerarquías creadas fueron:

-   `admin_general` → Administrador general.
-   `admin_centro` → originalmente "Administrador de sucursal".
-   `colaborador` → Colaborador.

Se corrigió el FK de usuario para usar:

`settings.AUTH_USER_MODEL`

porque `User` no estaba importado en `models.py`.

### Cambio que se estaba por hacer cuando se creó este documento

Todavía **no debe asumirse aplicado** salvo que el código real lo
confirme.

Se indicó cambiar la etiqueta:

`Administrador de sucursal`

por:

`Administrador`

y agregar, inmediatamente después de `jerarquia`:

``` python
centro_operativo = models.ForeignKey(
    "CentroOperativo",
    on_delete=models.PROTECT,
    related_name="asignaciones_usuarios",
    blank=True,
    null=True,
)
```

**IMPORTANTE:** en el momento de crear este documento, se había indicado
NO ejecutar todavía `makemigrations` para este cambio. Primero falta
implementar correctamente las validaciones del modelo.

------------------------------------------------------------------------

## 7. SIGUIENTE BLOQUE EXACTO DE TRABAJO

### A. Completar integridad de `AsignacionUsuarioEmpresa`

-   [x] Confirmar en el código real si ya se cambió la etiqueta visible
    a `Administrador`.
-   [x] Confirmar si ya se agregó `centro_operativo`.
-   [x] Implementar `clean()` con reglas explícitas.
-   [x] Evaluar si hace falta `save()` llamando `full_clean()` o si la
    validación quedará garantizada por servicio/form + constraints;
    decidir antes de codificar.
-   [x] Agregar constraints de DB que sean razonablemente expresables y
    útiles.
-   [x] Ejecutar `python manage.py check`.
-   [x] Crear `0038` sólo cuando el modelo esté completo.
-   [x] Inspeccionar la migración.
-   [x] Aplicar migración.
-   [x] Ejecutar `python manage.py check`.

Reglas mínimas esperadas para `clean()`:

1.  Un `Administrador` (`admin_centro`) **debe** tener
    `centro_operativo`.
2.  Ese Centro debe pertenecer a la misma Empresa de la asignación.
3.  El Centro debe ser apto según la semántica que se cierre para
    administración operativa.
4.  Administrador general no debe quedar artificialmente restringido a
    un Centro.
5.  Colaborador tampoco debe recibir accidentalmente alcance
    administrativo por Centro sólo por completar ese FK.
6.  No permitir crear una asignación que pretenda sustituir/duplicar al
    fundador de forma ambigua.
7.  Mantener Empresa+Usuario únicos y usar reactivación cuando
    corresponda, no duplicados.

**No decidir silenciosamente puntos funcionales que no estén cerrados.
Preguntar si una regla cambia comportamiento real.**

### B. Revisar exportación/importación

`AsignacionUsuarioEmpresa` depende funcionalmente de Empresa.

-   [ ] Inspeccionar Exportar Empresa.
-   [ ] Inspeccionar Importar Empresa.
-   [ ] Decidir cómo representar asignaciones de usuarios en un backup
    portable.
-   [ ] No exportar secretos.
-   [ ] No crear usuarios ajenos ni relaciones inseguras automáticamente
    durante importación sin una regla explícita.
-   [ ] Si no se implementa en este bloque, dejarlo registrado como
    pendiente pre-Beta explícito.

### C. Incorporar asignaciones al servicio de seguridad

Una vez establecida la estructura:

-   [ ] Modificar `obtener_empresa_autorizada()` para reconocer las
    asignaciones activas que correspondan.
-   [ ] Mantener al fundador (`Empresa.propietario`) como autoridad
    estructural.
-   [ ] Superuser continúa según política actual, sin usarlo para
    saltarse aislamiento funcional en interfaces de clientes.
-   [ ] Administrador general: Empresa completa.
-   [ ] Administrador: Empresa autorizada pero alcance operativo
    limitado a su Centro.
-   [ ] Colaborador: Empresa asignada, pero las acciones deben seguir
    dependiendo de capacidad funcional.
-   [ ] No convertir "puede entrar a Empresa" en "puede hacer cualquier
    cosa".

Probablemente convenga separar servicios:

-   autorización de pertenencia a Empresa;
-   alcance máximo por Centro;
-   permiso/capacidad para acción.

No convertir una única función en un bloque monolítico difícil de
auditar.

### D. Actualizar `obtener_caja_autorizada()`

-   [ ] Fundador: puede operar Cajas de su Empresa.
-   [ ] Administrador general: puede operar Cajas de toda la Empresa.
-   [ ] Administrador: sólo Cajas cuyo `centro_operativo` sea su Centro
    asignado.
-   [ ] Colaborador: **no puede operar Caja**.
-   [ ] Caja y Centro deben seguir activos.
-   [ ] Caja debe seguir perteneciendo a Empresa.
-   [ ] Centro debe seguir siendo Casa Central, Sucursal o Mostrador
    para Caja.
-   [ ] IDs del navegador nunca acreditan autorización.

Agregar tests de:

-   [ ] fundador;
-   [ ] administrador general;
-   [ ] administrador de su Centro;
-   [ ] administrador intentando Caja de otro Centro;
-   [ ] colaborador intentando Caja;
-   [ ] usuario de otra Empresa;
-   [ ] Caja inactiva;
-   [ ] Centro inactivo;
-   [ ] Caja inexistente/malformed ID.

### E. Diseñar/implementar ABM de Cajas

Objetivo: permitir crear y administrar Cajas explícitamente.

-   [ ] Ubicar el ABM dentro de la estructura existente, sin inventar un
    sistema visual paralelo.
-   [ ] Reutilizar patrones de Bancos/Centros Operativos.
-   [ ] Caja debe seleccionar Centro Operativo.
-   [ ] Sólo ofrecer Centros aptos: Casa Central, Sucursal, Mostrador.
-   [ ] Permitir más de una Caja por Centro.
-   [ ] Baja lógica.
-   [ ] Reactivación si existe equivalente inactivo según la regla que
    se defina.
-   [ ] `PROTECT` para relaciones históricas.
-   [ ] Backend valida Empresa y Centro.
-   [ ] Sin JS inline.
-   [ ] Sin CSS inline nuevo.
-   [ ] Preparado para funcionar desde menú y desde `[+]` cuando exista
    un selector contextual.
-   [ ] No agregar retorno particular nuevo; usar/migrar hacia pila
    contextual común.

### F. Designar colaboradores / administradores

No improvisar un ABM separado de la arquitectura existente.

-   [ ] Inspeccionar `views.py`, templates, JS y models reales antes de
    implementar.
-   [ ] Distinguir:
    -   fundador;
    -   administrador general;
    -   administrador;
    -   colaborador.
-   [ ] Administrador requiere Centro.
-   [ ] Administrador general no requiere Centro.
-   [ ] Colaborador no recibe Caja.
-   [ ] Nadie salvo reglas explícitas puede desvincular al fundador.
-   [ ] Definir baja/desvinculación lógica y trazabilidad.
-   [ ] Definir qué ocurre con asignaciones al desactivar
    usuario/Centro/Empresa.
-   [ ] No implementar postulaciones/aceptaciones completas hasta
    revisar lo que ya existe y cerrar el flujo funcional.

### G. Recién después: POST real de Nueva Cobranza

No habilitarlo para colaboradores.

-   [ ] Resolver contrato de `fecha`.
-   [ ] Resolver contrato de `referencia`.
-   [ ] No inventar esos valores: la definición funcional original de
    Nueva Cobranza menciona fecha y referencia, pero la pantalla visual
    aprobada actual no los muestra.
-   [ ] Crear endpoint POST autenticado.
-   [ ] CSRF normal.
-   [ ] Parseo seguro.
-   [ ] Empresa/Caja desde backend autorizado.
-   [ ] Llamar `crear_cobranza_validada()`.
-   [ ] Errores de negocio controlados.
-   [ ] Guardado atómico.
-   [ ] Evitar doble submit en frontend.
-   [ ] Considerar idempotencia/concurrencia como bloqueante pre-Beta.
-   [ ] Refrescar dashboard luego del alta.
-   [ ] Tests de aislamiento y reglas de cobranza.

------------------------------------------------------------------------

## 8. PRUEBAS MÍNIMAS ANTES DE CERRAR ESTA ETAPA

No hacer un commit final de la etapa hasta cubrir como mínimo:

-   [ ] `python manage.py check`.
-   [ ] Migraciones aplicadas sin cambios inesperados.
-   [ ] Tests del modelo/asignaciones.
-   [ ] Tests de seguridad Empresa/Centro/Caja.
-   [ ] Tests de `obtener_caja_autorizada()`.
-   [ ] Tests de Caja ABM si se implementa en este bloque.
-   [ ] Tests de Cobranza POST si se llega a implementar.
-   [ ] Regresión completa del proyecto.
-   [ ] Prueba manual fundador.
-   [ ] Prueba manual Administrador general.
-   [ ] Prueba manual Administrador limitado a Centro.
-   [ ] Prueba manual Colaborador sin Caja.
-   [ ] Verificar que el dashboard de Caja existente no se rompió.
-   [ ] Verificar Nueva Cobranza visual y comportamiento aprobado.
-   [ ] Verificar Total declarado opcional.
-   [ ] Verificar cheque `1698 → 00001698`.
-   [ ] Verificar que no apareció JS inline nuevo.
-   [ ] Verificar que no apareció CSS inline nuevo.
-   [ ] Revisar export/import para todos los modelos nuevos relacionados
    con Empresa.

Baseline conocido antes de estas modificaciones: **99 tests verdes**. No
asumir que sigue siendo el número actual; usarlo sólo como referencia
histórica.

------------------------------------------------------------------------

## 9. DOCUMENTACIÓN A ACTUALIZAR ANTES DEL COMMIT FINAL

-   [ ] `MODELO_DATOS.md`: AsignacionUsuarioEmpresa, jerarquía y
    alcance.
-   [ ] `ARQUITECTURA.md`: fundador / admin general / admin /
    colaborador y separación jerarquía-permisos.
-   [ ] `DECISIONES.md`: reglas cerradas de acceso.
-   [ ] `FLUJO_NAVEGACION.md`: Designar Colaboradores y Caja si cambia
    navegación.
-   [ ] `REGLAS.md`: sólo si aparece una regla transversal nueva.
-   [ ] `TODO.md`: marcar avances y conservar pendientes reales.
-   [ ] `PRE_BETA.md`: reflejar avance en permisos reales y alcance
    Centro/Caja, sin marcar completo lo que no esté probado.
-   [ ] Documento Caja/Carteras/OP: actualizar jerarquía si el texto
    anterior dice "Administrador de sucursal".
-   [ ] Incorporar la regla pendiente de **Total declarado opcional**.

No modificar documentación para aparentar que algo está implementado
antes de que el código/tests lo respalden.

------------------------------------------------------------------------

## 10. CHECKLIST DE GIT Y COMMIT DE CIERRE

Cuando toda la etapa esté funcional y probada:

-   [ ] Ejecutar `git status --short`.
-   [ ] Revisar cada archivo modificado.
-   [ ] Confirmar que backups SQLite continúan sin trackear.
-   [ ] No usar `git add .`.
-   [ ] Stagear selectivamente sólo código, migraciones, tests y
    documentación de esta etapa.
-   [ ] Revisar `git diff --cached`.
-   [ ] Ejecutar regresión final.
-   [ ] Hacer un único commit de cierre coherente o commits funcionales
    claramente separados si la etapa termina siendo demasiado grande.
-   [ ] Registrar hash del commit en este documento o en la continuidad
    siguiente.
-   [ ] No afirmar que fue pusheado sin comprobarlo.

Backups conocidos que no deben committearse:

-   `db_antes_limpieza_pruebas.sqlite3`
-   `db_antes_reset_pruebas_20260913.sqlite3`
-   `db_antes_reset_total_pruebas_20260913.sqlite3`

------------------------------------------------------------------------

## 11. CRITERIO DE "ETAPA CERRADA"

Esta etapa se considera cerrada sólo cuando:

-   [ ] La jerarquía Fundador / Administrador general / Administrador /
    Colaborador está representada sin ambigüedad.
-   [ ] El Administrador tiene alcance por Centro.
-   [ ] El Administrador general tiene alcance Empresa.
-   [ ] El fundador queda protegido.
-   [ ] El Colaborador no accede a Caja.
-   [ ] La autorización backend de Caja respeta esas reglas.
-   [ ] Existe una forma segura de configurar las Cajas necesarias por
    Centro.
-   [ ] Las nuevas entidades fueron consideradas para export/import.
-   [ ] Tests específicos y regresión están verdes.
-   [ ] Documentación refleja exactamente lo implementado.
-   [ ] `git status` fue revisado y el commit de cierre fue realizado
    selectivamente.

El POST de Cobranza puede formar parte de este mismo cierre si se
completa correctamente. Si por tamaño conviene separarlo, debe quedar
explícitamente indicado como siguiente etapa y no fingirse terminado.

------------------------------------------------------------------------

## 12. ADVERTENCIAS PARA UN CHAT NUEVO

1.  **No volver a proponer `AccesoCaja` usuario↔Caja como primera
    solución.** La decisión actual es que el Administrador opera las
    Cajas de su Centro; el Colaborador no opera Caja.
2.  **No duplicar al fundador en `AsignacionUsuarioEmpresa`.** La fuente
    actual es `Empresa.propietario`.
3.  **No crear una matriz genérica de permisos antes de definir las
    capacidades reales.**
4.  **No habilitar POST financieros a colaboradores mientras no exista
    autorización real por alcance/capacidad.**
5.  **No tocar la configuración privada de instalación, SECRET_KEY,
    certificados ni claves ARCA durante limpieza de datos operativos.**
6.  **No romper la pantalla de Nueva Cobranza aprobada.**
7.  **No reemplazar mecanismos existentes sin inspeccionarlos primero.**
8.  **No crear JS/CSS inline nuevo.**
9.  **No olvidar la futura pila contextual `[+]`; ningún ABM nuevo debe
    empeorar la deuda con retornos especiales.**
10. **Leer los `.md` del proyecto y el código vigente antes de
    continuar; este documento es un puente de continuidad, no sustituto
    del repositorio.**

------------------------------------------------------------------------

## 13. PUNTO EXACTO DE REANUDACIÓN

Al momento de escribir este archivo:

-   `0037_asignacionusuarioempresa` está aplicada.
-   `python manage.py check` está limpio.
-   Se acaba de cerrar funcionalmente la jerarquía de acceso.
-   El próximo trabajo es completar `AsignacionUsuarioEmpresa` con
    alcance por Centro y validaciones **antes de generar `0038`**.
-   Se había propuesto cambiar la etiqueta visible
    `Administrador de sucursal` → `Administrador`.
-   Se había propuesto agregar `centro_operativo` nullable al modelo.
-   Todavía hay que confirmar en el código si Emanuel llegó a realizar
    esos dos cambios.
-   **No generar `0038` hasta completar y revisar las reglas de
    integridad.**

Ese es el punto desde el cual debe continuar el próximo chat.
