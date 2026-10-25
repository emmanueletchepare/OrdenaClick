# OrdenaClick — Catálogo maestro de alertas

**Listado rápido de consulta y ampliación** · Actualizado: 24/10/2026 · Referencia: `f79b303`

**Leyenda:** `[x]` = ya se muestra en Alertas; `[ ]` = registrada como idea o futura integración, **todavía no genera esta alerta**. Los identificadores son únicamente documentales; no son permisos ni códigos del software.

## 1. Alertas financieras

- [x] **FIN-01** · Vencimiento de Movimientos con saldo pendiente.
- [x] **FIN-02** · Vencimiento de cheques físicos (cartera y propios emitidos).
- [x] **FIN-03** · Vencimiento de e-Cheqs (cartera electrónica y propios emitidos).
- [ ] **FIN-04** · Vencimiento de cuotas de registros planificados.

## 2. Alertas administrativas

- [ ] **ADM-01** · Orden de Pago lista para imprimir o aplicar.

## 3. Alertas de Nómina

- [x] **NOM-01** · Vencimiento de licencia de conducir.
- [ ] **NOM-02** · Vencimiento de plazos de documentación de cese laboral.

## 4. Alertas documentales

**Documentación de Empresa**

- [ ] **DOC-01** · Renovación o revisión de acta de directorio.
- [ ] **DOC-02** · Renovación o revisión de acta de asamblea.

**Documentación de cada Centro Operativo**

- [ ] **DOC-03** · Vencimiento de habilitación municipal.

---

### Para agregar nuevas ideas

Agregar una línea bajo la categoría apropiada, con un identificador nuevo. **No es necesario implementar la alerta para incluirla en esta lista.** Si aparece otra categoría, crear su sección.

Antes de implementar una línea pendiente, completar su **registro de origen, vencimiento/disparador, Empresa/Centro, permisos, destinatarios, privacidad y pruebas** en [Fichas y requisitos de implementación](FICHAS_ALERTAS_ORDENACLICK.md).

**Gestor de Alertas:** debe incluir **«Sin destinatarios»** para tipos realmente operativos y ocurrencias activas sin receptores autorizados. Una alerta futura no debe aparecer allí como incidencia.

**Estado del documento:** propuesta de catálogo para incorporar al repositorio con aprobación; ninguna línea pendiente implica una función existente.
