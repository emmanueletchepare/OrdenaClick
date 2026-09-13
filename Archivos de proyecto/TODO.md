# TODO.md — Qué falta y qué queremos agregar

## 1. BETA — PRIORIDAD ABSOLUTA
Objetivo: circuito completo y estable de **REGISTROS**.

### 1.1 Cerrar flujos
- [ ] Comprobantes de punta a punta.
- [ ] Carga Planificada de punta a punta.
- [ ] Registrar Pago de punta a punta.
- [ ] Modificar / Eliminar con reglas financieras e históricas correctas.
- [ ] Múltiples pagos por Movimiento.
- [ ] Pagos parciales y saldo pendiente común.
- [ ] Centralizar validación: nueva aplicación <= saldo pendiente actual.
- [ ] Aplicar esa validación en Comprobantes, edición y futura Carga Planificada.
- [ ] Registrar Pago: distribuir un Pago entre múltiples Movimientos.
- [ ] Registrar Pago: conservar remanente no aplicado a cuenta cuando corresponda.
- [ ] Conversión a Plan respetando pagos previos.
- [ ] Reversión/eliminación de Pago sin romper historia.
- [ ] Registro real de débitos automáticos.
- [ ] Vencimientos generados/actualizados desde la fuente financiera correcta.
- [ ] Próximos Vencimientos consumiendo fuente común.
- [ ] Alertas/llamador sin duplicar la lógica financiera.

### 1.2 ABM requeridos por REGISTROS
- [ ] Verificar uno por uno apertura desde menú.
- [ ] Verificar apertura desde `[+]`.
- [ ] Conservar formulario llamador.
- [ ] Volver al origen exacto.
- [ ] Seleccionar automáticamente el alta nueva.
- [ ] Edición integrada.
- [ ] Baja lógica + reactivación.
- [ ] Validaciones de pertenencia a Empresa.
- [ ] Uniformidad visual.
- [ ] Completar ABM necesarios para medios de pago (cuentas, tarjetas, bancos, etc.).

### 1.3 Seguridad antes de servidor/Beta
- [ ] Revisar configuración de producción.
- [ ] HTTPS.
- [ ] Cookies/sesiones/CSRF seguras.
- [ ] SECRET_KEY y credenciales sólo por entorno/secret manager.
- [ ] DEBUG desactivado.
- [ ] ALLOWED_HOSTS/orígenes correctos.
- [ ] Permisos por Empresa/rol/capacidad en backend.
- [ ] Evitar IDOR/acceso cruzado entre empresas.
- [ ] Validar uploads y acceso a archivos privados.
- [ ] Backups cifrados/seguros y prueba de restauración.
- [ ] Logging sin secretos/datos sensibles innecesarios.
- [ ] Auditoría de operaciones críticas.
- [ ] Dependencias y despliegue actualizados.
- [ ] Estrategia de recuperación ante fallos.

### 1.4 Suscripciones
- [ ] Definir matriz Persona / Intermedio / Empresas.
- [ ] Implementar capacidades habilitables sin cambiar el modelo de datos.
- [ ] Upgrade sin pérdida/migración destructiva.
- [ ] Definir comportamiento ante vencimiento/suspensión sin destruir datos.
- [ ] Separar autenticación de habilitación comercial.

### 1.5 Testing Beta
- [ ] Tests de servicios financieros.
- [ ] Tests de permisos y aislamiento por Empresa.
- [ ] Tests de idas/vueltas de ABM.
- [ ] Tests de pago parcial/múltiple/plan.
- [ ] Tests de vencimientos/alertas.
- [ ] Tests de exportar/importar Empresa.
- [ ] Pruebas reales con datos representativos.

## 2. DEUDA TÉCNICA QUE SE CORRIGE PROGRESIVAMENTE
- [ ] Extraer JavaScript inline existente cuando se toque cada pantalla.
- [ ] Extraer CSS inline existente cuando se toque cada pantalla.
- [ ] Reducir templates monolíticos.
- [ ] Separar `views.py` por dominio cuando sea conveniente.
- [ ] Mover reglas reutilizables a `services/`.
- [ ] Eliminar duplicaciones de cálculo de saldo/vencimientos.
- [ ] Agregar/mejorar docstrings.
- [ ] Revisar comentarios importantes antes de limpiar código.

## 3. POST-BETA CERCANO
- [ ] Dashboard.
- [ ] Reportes con filtros.
- [ ] Deudas pendientes.
- [ ] Mejorar Próximos Vencimientos.
- [ ] Estado de Resultados.
- [ ] Plan Contable.
- [ ] Balance.
- [ ] Perfil Colaborador completo y permisos configurables.
- [ ] Perfil Contable.
- [ ] Perfil Legal.
- [ ] Conciliaciones bancarias/tarjetas.
- [ ] Configuración guiada inicial de Empresa.

## 4. FUNCIONES FUTURAS YA DEFINIDAS
- [ ] Listado/cartera de cheques y e-Cheqs.
- [ ] Agenda.
- [ ] Orden de Pago.
- [ ] Autorización de operaciones.
- [ ] Gestión/Agenda de Claves con diseño seguro.
- [ ] Ver inactivos y reactivar en ABM.
- [ ] Buscador dinámico en listados/tarjetas de todos los ABM.
- [ ] Scroll independiente entre sidebar y menú operativo.
- [ ] Registro/Rendición del vendedor.
- [ ] ABM de Clientes.
- [ ] Gestión avanzada de saldos a favor/a cuenta y su compensación posterior.
- [ ] Multimoneda, tipos de cambio y conversiones.
- [ ] Notificaciones móviles.
- [ ] Nuevos impuestos, retenciones y medios de pago.
- [ ] Calificación de colaboradores/contadores/abogados.
- [ ] Giras/Rendiciones cuando se defina su alcance.

## 5. EXPORTAR / IMPORTAR EMPRESA
- [ ] Mantener cobertura completa a medida que aparecen modelos.
- [ ] Versionar formato.
- [ ] Mapear IDs al importar.
- [ ] Incluir inactivos e históricos.
- [ ] Incluir archivos.
- [ ] Resolver traslado seguro de información cifrada sin exportar la clave maestra.
- [ ] Compatibilidad con backups anteriores.

## 6. DECISIONES PENDIENTES
- [ ] Reglas exactas de ejercicio cerrado.
- [ ] Fórmula/configuración definitiva de intereses por mora.
- [ ] Reglas definitivas de multimoneda.
- [ ] Alcance final de Carga Planificada.
- [ ] Matriz detallada de capacidades por suscripción.
- [ ] Matriz detallada de permisos por rol.

### Obligaciones / Liquidaciones

- [ ] Diseñar el modelo definitivo de Obligaciones sin forzarlo dentro de la estructura documental de una factura.
- [ ] Implementar circuito de Obligaciones separado de Comprobantes.
- [ ] Conceptos iniciales: Sueldos / Aportes y Contribuciones / VEP - Impuestos / Tasas y otros.
- [ ] Definir entidad y ABM para Organismo / beneficiario.
- [ ] Definir reglas de Período y Referencia según tipo de obligación.
- [ ] Definir cuándo corresponde Centro Operativo.
- [ ] No exigir Recurso Operativo cuando no tenga sentido económico.
- [ ] Integrar Obligaciones con Pago, AplicaciónPago, Vencimiento y Alertas.
- [ ] Definir reglas particulares de duplicidad para cada tipo de obligación.

### Alertas / Próximos Vencimientos

- [ ] Crear servicio común para determinar Alertas vigentes.
- [ ] Implementar política inicial de obligaciones: 3 días antes + vencidas pendientes.
- [ ] Incorporar filtro Alertas en Próximos Vencimientos.
- [ ] Mantener reglas temporales fuera del JavaScript.
- [ ] Agregar tests de Alertas.
- [ ] Diseñar control segmentado reutilizable para botoneras superiores.
- [ ] Aplicar control segmentado a Próximos Vencimientos.
- [ ] Evaluar luego su aplicación a la botonera de Registros.
- [ ] Implementar Cartera de Cheques / e-Cheqs.
- [ ] Incorporar política de Cartera: fecha de acreditación + ventana de 30 días corridos.
- [ ] Testear específicamente los límites de los 30 días.
- [ ] Implementar Llamador de OrdenaClick después de estabilizar la vista Alertas.
