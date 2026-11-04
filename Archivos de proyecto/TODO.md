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

## Caja — nueva prioridad funcional (11/10/2026)

- [ ] Validar localmente Caja 1: movimientos de efectivo, historial, saldos, limites, permisos Empresa/Centro/Caja, idempotencia y migracion `0043`; publicar codigo y docs selectivamente.
- [ ] Bandeja de movimientos bancarios pendientes de aplicacion: deteccion, identificacion de Centro, recibo externo, marca de resuelto y escalamiento administrativo.
- [ ] Cartera fisica/electronica y disponibilidad por estado/custodia/circulacion; uso de cheques existentes en pagos individuales, no duplicarlos.
- [ ] Envio simple entre Cajas: despacho, transito, recepcion, rechazo parcial, discrepancias y caso de Auditoria.
- [ ] Arqueo fisico y correcciones auditadas; conciliacion de diferencias sin borrar hechos.
- [ ] ABM Cuenta Bancaria: descubierto/vigencia/alerta; posicion bancaria informada y prevision de acreditaciones.
- [ ] Orden de Pago colaborativa sobre disponibilidad real, confirmaciones individuales, aviso al creador y cierre separado.
- [ ] Para cada etapa: validacion en backend, regresion multiempresa, reversas, Backup Empresa v1 e infraestructura PostgreSQL donde corresponda.

## Caja: seguimiento de la etapa operativa (11/10/2026)
- [ ] Verificar en entorno Django/migración `0044` bloque Caja 2 integrado y revisar UI en navegador: Desde/Hasta en línea, encabezados, alineaciones e iconos, correcciones con motivo.
- [ ] Validar casos de permisos de Colaborador por Centro, revocación, consulta y resolución sin duplicar Caja, acceso por Empresa y Backup Empresa v1 con ZIP anterior.
- [x] Asignar Centro a pendientes aún no clasificados mediante acción de administrador general y evento auditable, sujeto a pruebas Caja 2.
- [ ] Cartera física/e-Cheqs, estados, reservas, depósito/salida, rechazos después de salida; no duplicar valores al pagar.
- [ ] Traslados internos sencillos por Caja, recepción parcial y conflictos de Auditoría trazables.
- [ ] ABM Cuentas Bancarias: acuerdo de descubierto, monto, vencimiento y alertas; previsión y rechazados.
- [ ] Arqueo físico y conciliación de diferencias.
- [ ] Pago individual utilizando Caja/valores disponibles; luego preparación y cierre de Órdenes de Pago.
- [ ] Recorridos visuales/funcionales reales sin cambios no aprobados y tests PostgreSQL de concurrencia antes de despliegue.


## Caja 2 — revisión de pendientes globales (12/10/2026)

La definición vigente es: **todos los pendientes bancarios y e-Cheqs son
visibles globalmente dentro de la Empresa activa** para los usuarios con
capacidad de gestión; no se asigna Centro al detectar el ingreso. Al
confirmar en modal, el usuario identifica cliente, elige Centro de su
alcance y registra la verificación/recibo externo; desde allí es resuelto
**propiedad operativa de ese Centro**. Una Empresa activa nunca muestra
otra ni ofrece selector de Empresa. La carga de depósitos/transferencias y
la de e-Cheqs tienen formularios separados, filas temporales editables y
Guardado atómico de lote. E-Cheq `A la orden` por defecto; `No a la orden`
disponible. Permisos de colaboradores van en Configuración de Empresa,
no en bandeja; no conceden Caja. `Volver` lleva al menú de origen. Consulte
`ORDENACLICK_DISENO_CAJA_CARTERAS_OP.md` para el detalle completo.

### Revisión visual y operacional Caja 2 — próximo control

- [ ] Aplicar y aprobar pruebas para banco emisor buscable del ABM y `[+]`.
- [ ] En navegador, verificar búsqueda mientras se escribe, alta contextual
      y regreso sin perder filas; también edición/eliminación temporal de filas.
- [ ] Revisar categorías turquesa/violeta en Pendientes y Resueltos, incluidos
      importes alineados y acceso desde perfiles autorizados.
- [ ] Revisar juntos la pantalla actual de Configuración de permisos; sin
      conceder Caja ni ampliar Centros o Empresas.
- [ ] Publicar código y documentación por separado después de aprobación.

### Caja 2 — e-Cheqs: formulario corregido, cuenta y ABM contextual (pendiente de pruebas)

- **No confundir e-Cheq con depósito bancario**: el e-Cheq recibido pertenece al CUIT
  de la Empresa; no requiere cuenta receptora ni crea movimiento de Caja. La cuenta
  sólo se elige en una futura operación de depósito. Depósito/transferencia sí
  requiere cuenta. Migración aditiva `0046` hace opcional la FK para e-Cheq;
  protege la obligación para depósitos/transferencias, sin borrar asociaciones
  históricas ni alterar saldos. Backup Empresa v1 conserva estos hechos.
- Número e-Cheq: `usuarios.services.cheques.normalizar_numero_cheque` es la regla
  canónica (únicamente dígitos, máximo ocho y relleno izquierdo: 185 → 00000185).
  En pantalla se aplica al salir; en servidor siempre se revalida.
- Importe: edición y presentación es-AR, por ejemplo 150 → 150,00 y 15000 →
  15.000,00; el servidor mantiene Decimal/validación de importes positivos.
- Se retira el N.º Banco adicional. Banco Emisor y Titular están alineados con los
  demás casilleros: búsqueda por teclado. Banco proviene del ABM activo de la
  Empresa y se valida por ID/Empresa. Titular sugiere Clientes activos de esa
  Empresa, pero conserva texto libre porque el titular no necesariamente es el
  cliente al que se le aplica el pago. El Centro y cliente definitivo se
  identifican al **resolver**, no durante el registro.
- `[+]` no abre modal inventado: navega al **ABM existente** de Banco/Cliente,
  incluso con alta de Centro anidada en Clientes, y retorna a la carga de e-Cheq
  restaurando formulario, edición y filas preparadas. El borrador temporal
  `sessionStorage` está aislado por Empresa y pestaña; si no se puede almacenar
  no sale de la pantalla. El servidor valida sesión Empresa y rol administrativo.
- Se conserva el listado ya aceptado: depósitos/transferencias en turquesa,
  e-Cheqs en violeta, estado Pendiente/Resuelto separado, modal Confirmar y
  permisos de administración por Centro; no introducir nuevos selectores.
- **Estado**: pendiente de tests reales, revisión visual y publicación selectiva.

### Caja 2 — búsqueda, fecha, auditoría y Designar perfiles (12/10/2026)

- **Bandeja global por Empresa activa:** se mantiene el alcance global de Pendientes; una vez resuelto, el Centro limita la consulta de Resueltos. Nuevo buscador incremental por Titular / Cliente, importe en es-AR y número del e-Cheq. La consulta filtra en servidor *antes* de paginar y siempre por Empresa; el filtro Centro sólo aparece en Resueltos. Las monedas e importes de los listados se muestran con miles mediante punto y decimales mediante coma; el formato lo asegura `usuarios.templatetags.caja_importes.importe_ar` y no depende del locale de Django.
- **e-Cheq:** la fecha de acreditación no puede superar los 30 días de antigüedad en el momento de la carga; UI `min` y validación de backend, sin reinterpretar registros históricos. Se mantienen e-Cheq sin cuenta receptora (migración 0046), banco emisor proveniente del ABM, ocho dígitos en número, monto es-AR y condición A la orden / No a la orden.
- **Depósitos/transferencias y e-Cheqs:** campo `Titular / Cliente` con búsqueda entre Clientes activos de la Empresa, `[+]` hacia ABM existente y vuelta conservando ambas listas temporales, datos y edición. El titular puede quedar sin identificar al detectar un depósito; la identificación real y el Centro quedan definidos al resolver.
- **Corrección de errores:** movimiento Pendiente sólo editable por quien lo registró o administración general, con motivo obligatorio, antes/después persistente, actor histórico e idempotencia UUID. No modifica Caja ni crea recibos/pagos. Para un movimiento ya Resuelto no se altera ningún dato financiero ni la imputación externa: el generador, resolvedor o administración general con alcance pueden **abrir una incidencia de auditoría** con motivo. El registro queda sin cambiar; incidencias abiertas visibles a administración general en Configuración de permisos. El procedimiento definitivo de resolución de incidencias se decidirá cuando se implemente Auditoría completa, sin editar silenciosamente resueltos.
- **Configuración de accesos:** el acceso a los permisos de Gestión Bancaria pasa de botón independiente en Configuración a **Configuración → Designar perfiles**, junto con relaciones. La pantalla de permisos conserva la validación administración general/propietario/superusuario; asigna Centro(s) a colaboradores, sin conceder Caja ni saldos, sin cambiar jerarquías estructurales. Permisos NO viajan en Backup Empresa v1.
- **Persistencia / backup:** migración aditiva `0047_revision_auditada_pendiente_bancario` y `RevisionPendienteBancario` para edición o incidencia, snapshots JSON antes/después, motivo, creador y estado. Backup Empresa v1 incluye esta nueva entidad como componente opcional, y serializa JSON como objeto para permitir su restauración; respaldos antiguos sin este componente siguen aceptados. Auditoría de permisos de usuarios permanece fuera del respaldo portable.
- **Seguridad:** POST+CSRF, verificación Empresa activa y roles/centro en backend, GET sólo lectura, transacción y bloqueo para evitar revisiones simultáneas, no cruce entre Empresas. Comprobar al ejecutar las pruebas locales y luego la disposición visual; no dar por aceptado lo no comprobado. Base Server aprobado localmente no implica certificado de producción para PostgreSQL, proxy/TLS o backups remotos.


## Producto futuro — Nómina de Empleados y revisión transversal de accesos (14/10/2026)

- [ ] Diseñar/revisar la **matriz de accesos por usuario**: jerarquías, roles, Empresa/Centro, permisos por acción y documentación; proponer lista con interruptores y concesión/revocación auditadas. **No** otorgar privilegios nuevos por defecto.
- [ ] Diseñar Nómina en el panel: **Activos verde / Inactivos rojo** como Próximos vencimientos, **[Registrar]**, consulta por CUIL/nombre/legajo/Centro.
- [ ] Implementar ficha personal y laboral, Centro `[+]`, Vehículo-Recurso `[+]`, Banco `[+]`, CBU, contrato, DNI frente/dorso, licencia, **Clave de Alta Temprana - CAT** y preocupacional con archivos privados.
- [ ] Implementar **Guardar/Desvincular/Abrir caso** con cronología auditable, antecedentes legales y restricciones de acceso; baja conserva historia e **inactiva todas las alertas activas asociadas al empleado**.
- [ ] Integrar al motor de Alertas aviso de **licencia un mes antes** para empleados activos; licencia vencida **no** desvincula. Definir regla exacta de fechas, reconocimiento/campana y renovación.
- [ ] Validar seguridad de documentos, permisos, retornos `[+]`/scroll, exportación/restauración por Empresa y regresión antes de publicar. **Módulo no implementado**.
- Especificación: `NOMINA_EMPLEADOS_Y_ACCESOS.md`. Mantener prioridades actuales de Beta; no confundir diseño futuro con tarea terminada.

## Pendientes surgidos en operación real — 15/10/2026

**Estado al 03/11/2026:** el usuario autorizó abordar estos hallazgos. Los dos ajustes de columnas ya estaban implementados en `babc4c7`; no reconstruir el listado. Se refuerza validación UX de precarga sin alterar estados ni movimientos financieros. La aceptación visual y las pruebas en el entorno de uso siguen pendientes.

### Caja 2 — revisión de lote e-Cheqs

- [x] **Número e-Cheq** y **Titular / Cliente** ya están en columnas distintas del listado de precarga (verificar en navegador).
- [x] **Fecha de acreditación** ya se muestra por fila en el listado de precarga (verificar en navegador).
- [ ] Diagnóstico del error «El importe no es válido»: el parser actual admite `126.785,71` en JS y backend; no se confirmó la causa histórica. El backend ya informa fila/campo, y la nueva validación también revisa importes de borradores anteriores antes del POST. Confirmar con pruebas y datos no sensibles.
- [ ] **Agregar / Editar / Guardar todos:** se incorporó mensaje de fila y campo, foco en el importe o la fila para editar y conservación completa del lote; pendiente regresión y revisión visual reales.
- [ ] Completar regresión Caja/finanzas y pruebas visuales con datos seguros antes de publicar; no alterar movimientos reales sin permiso.

### Colaborador / Permisos

- [ ] Diseñar reutilización del **mismo panel Administrador**: sidebar, navegaciones, módulos y ABM con capacidades filtradas; **no duplicar panel**.
- [ ] Auditar roles/capacidades existentes, Empresa/Centro y permisos backend; matriz mínima por módulo/acción, denegación por defecto, revocación y auditoría, preparada para futuro Panel de Permisos/Accesos.
- [ ] Primer circuito controlado: Colaborador habilitado a **Pendientes bancarios**, probado con permisos correctos sin otorgar Caja/saldos ni datos de otras Empresas/Centros.
- [ ] Incluir consideración explícita de Colaborador en **cada nuevo desarrollo del panel Administrador**, aunque todavía no se habilite a ese perfil.
- [ ] Probar ruta directa, GET/POST, cambios de Empresa, rol, alcance Centro, permisos revocados y seguridad de documentos.

### Estado de cierre a preservar

- [x] Oficina sincronizada con Casa/GitHub en `902cdeb` (corte 15/10).
- [x] Respaldo SQLite de Oficina íntegro antes de migrar; migraciones `0048`–`0050` aplicadas.
- [x] 35 tests dirigidos verdes en Casa y Oficina.
- [ ] Detalle individual de recorridos `[+]` de Nómina; ya hubo conformidad general del usuario, sin acta paso a paso.

**Relevo:** `CONTINUIDAD_OPERATIVA_20261015.md`. Los ítems históricos que aún indiquen «implementar Nómina desde cero» son obsoletos: revisar código antes de trabajar.

## CIERRE PERMISOS REGISTROS Y BANCARIOS 2026-10-22 — implementación controlada

- Gestión de Accesos: Registros (consultar, crear, editar, Obligaciones informativas) y Pendientes bancarios (consultar, precargar, editar/auditar, confirmar, estado y salidas e-Cheq) disponibles por casillas explícitas y auditadas; ninguna función inexistente muta datos. La pantalla Obligaciones sigue informativa/en desarrollo.
- Pendientes bancarios continúan GLOBALES dentro de la Empresa hasta la confirmación. El Centro Operativo se determina recién cuando el usuario confirma, y el backend valida los Centros de su alcance. Los Resueltos solo se ven por Centro autorizado, salvo administración general. No generar Caja, Pago, Recibo ni saldo por esa confirmación.
- Asignaciones bancarias POR CENTRO previamente otorgadas mantienen compatibilidad. La primera configuración explícita desde Gestión de Accesos prevalece sobre concesiones legadas, incluyendo revocaciones de acciones; la auditoría permanece intacta.
- Registros: leer selectores de ABM no permite modificarlos. Consultar/crear/editar comprobantes NO concede Registrar Pago, débito automático ni Caja; los endpoints de pago mantienen su autorización histórica independiente. Administrador de Centro queda limitado a sus Centros, sin abrir Configuración. La jerarquía Administrador general NO concede por sí sola la escritura de Movimientos, conforme a la prueba histórica de seguridad.
- Un solo sidebar compartido, sin nuevos botones flotantes, sin cambiar jerarquías, CSS ni retornos. Nómina por Centro, claves propias y permisos de Caja permanecen independientes.
- **Instalación y regresiones verificadas en Casa:** el helper aplicó los cambios, `manage.py check`, `makemigrations --check --dry-run` y la suite seleccionada terminaron sin fallos. **Aún falta aprobación visual/funcional por perfiles y commit selectivo.**


## Bloque A aprobado: separación de Alertas y Vencimientos — 23/10/2026

- [ ] Ejecutar helper controlado desde `0c09140` y validar backup externo.
- [ ] Comprobar Alertas como opción principal del mismo sidebar, cargada en el área operativa.
- [ ] Comprobar Próximos vencimientos con sólo Hoy, Esta semana y Rango de fechas.
- [ ] Comprobar campanita/sonido existente abriendo Alertas sin cambiar de panel.
- [ ] Verificar `alertas.ver`, permisos propios de fuentes, revocación, Empresa y Centros.
- [ ] Verificar alertas de Nómina sin movimientos, cero filtraciones y cero regresiones.
- [ ] Validar visualmente con el supervisor y realizar commit selectivo.
- [ ] Después, y sólo con autorización nueva: destinatarios/sonido por usuario, seguimiento y nuevas fuentes.

## Actualización de pendientes — Alertas documentales, 02/11/2026

**Esta sección prevalece sobre las casillas históricas del Bloque A (23/10) y la propuesta de Nómina/gestor anterior.** No se reabren características ya publicadas de FIN-02/FIN-03 ni el gestor unificado.

### Hecho en el bloque local, sujeto a publicación selectiva

- [x] Segmentación visual de Alertas (Compromisos / Cheques y e-Cheqs / Documentación), sin cambiar Próximos vencimientos.
- [x] Presentación coherente de cheques/e-Cheqs y avisos documentales; mantiene la fuente y los permisos de cada aviso.
- [x] DOC-01 (Directorio), DOC-03 (habilitaciones municipales por Centro) y DOC-04 (Designación de Autoridades/Asamblea) incorporadas a Alertas y al gestor de destinatarios. **DOC-02 histórico sin aviso operativo**.
- [x] Estatuto a ancho completo, Directorio y Designación/Asamblea en dos columnas con vencimientos. Sin un cuarto campo Asamblea visible ni acordeón/checkbox societario.
- [x] Habilitaciones con adjuntos privados e historial desde formulario superior del ABM Centros; listado sólo informativo. Centro activo sin habilitación genera aviso.
- [x] Compatibilidad con Backup Empresa v1 para habilitaciones nuevas y restauración de copias antiguas; permisos no se importan.
- [x] Respaldo SQLite verificado antes de `0057`; migración `0057` aplicada localmente; 59 pruebas dirigidas OK y otras 17 OK en cortes previos; aceptación visual del usuario.

### Antes de cerrar y publicar este bloque

- [ ] Comprobar `python manage.py showmigrations usuarios` y dejar constancia de si `0058` está aplicada en la base operativa; si no, respaldar y aplicar de forma controlada.
- [ ] Ejecutar regresión dirigida **sobre la rectificación societaria definitiva** (incluidos tests de Documentación, Destinatarios, Accesos, Backup y UX) y registrar el resultado.
- [ ] Revisar `git diff --check` y `git diff --cached --check`, hacer staging por lista blanca (no `git add .`; excluir `ordenaclick/settings.py`, SQLite y helpers), commit y push verificables.
- [ ] Eliminar helpers temporales sólo después de confirmar `main == origin/main` y la aceptación final.

### Pendientes globales que no cierra este trabajo

- [ ] Pruebas adversariales y restauración real de Backup Empresa v1 en entorno descartable; cierre pre-Beta, permisos y despliegue real.
- [ ] Auditoría de acciones y permisos por Empresa/Centro, adjuntos y concurrencia donde corresponda; no interpretar suite SQLite como prueba de producción PostgreSQL.
- [ ] Completar transferencias internas, arqueos, disponibilidad bancaria y Orden de Pago según el diseño vigente; sin alterar Caja en este bloque documental.
- [ ] Actualizar el resto de documentos de continuidad cuando se complete una nueva fase relevante; conservar historial y no confundir documentación con funcionalidades operativas.
