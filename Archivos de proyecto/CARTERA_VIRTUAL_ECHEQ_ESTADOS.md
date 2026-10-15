# Cartera virtual e-Cheqs — decisión operativa (14/10/2026)

- Un e-Cheq registrado en Pendientes bancarios integra de inmediato la cartera
  virtual de la Empresa, sin duplicarse como `Cheque`.
- Su estado de cartera **es distinto** de `Pendiente/Resuelto`, que representa
  la gestión administrativa de su imputación.
- Primera etapa: En cartera, Rechazado, Devuelto, Vencido (tras 30 días desde
  la acreditación). Fecha y observación
  por evento, actor histórico, idempotencia y trazabilidad.
- Rechazado puede continuar como Devuelto, conservando ambos eventos.
- Estados futuros Depositado/Endosado/Cedido, reemplazos, pérdida y vínculo con
  ND/proveedores/REGISTROS requieren circuitos específicos, aún no realizados.
- El cambio de estado no mueve dinero, crea Pago/Recibo ni modifica alertas
  artificialmente. Falta incorporar e-Cheqs al servicio de alertas y permitir
  reconocer un aviso vencido sin campana perpetua ni eliminar el pendiente.
- Las reglas de backend verifican Empresa, rol, sesión, fecha, transición e
  idempotencia. El frontend no concede permisos.
