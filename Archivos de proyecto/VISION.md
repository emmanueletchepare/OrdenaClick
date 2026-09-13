# VISION.md — Qué queremos que sea OrdenaClick

## 1. Propósito
OrdenaClick es una aplicación web de gestión orientada a ordenar gastos, registros, pagos, vencimientos, alertas e información de gestión. No debe limitarse a guardar lo que ya ocurrió: debe ayudar a anticipar obligaciones económicas, evitar olvidos y conservar información útil para gestión, reportes y futura contabilidad.

El producto debe poder acompañar desde una persona que organiza gastos familiares hasta una empresa con colaboradores, permisos, conciliaciones y acceso a toda la aplicación web.

## 2. Primer objetivo: Beta
La prioridad inmediata es alcanzar una **Beta usable, estable y segura**. Para considerar cumplido este objetivo debe funcionar de punta a punta todo lo que pertenece al botón **REGISTROS**, incluyendo:
- Carga Simple.
- Carga Planificada.
- Registrar Pago.
- Modificar / Eliminar.
- Los ABM necesarios para esos flujos.
- Las idas y vueltas entre formularios y ABM.
- Conservación del estado del formulario al abrir un ABM desde `[+]`.
- Selección automática del registro recién creado al regresar.
- Pagos, saldo pendiente, vencimientos y alertas que correspondan al circuito.
- Pruebas del flujo completo, no solamente pantallas aisladas.

Primero se cierran flujos utilizables de punta a punta; después se estabilizan y testean. Los refactors o mejoras secundarias no deben bloquear la Beta, salvo que afecten seguridad, integridad de datos o hagan inviable seguir creciendo.

## 3. Una sola arquitectura escalable
No habrá arquitecturas de datos separadas para usuarios “simples” y “complejos”.

**Regla:** simplificar la interfaz, no empobrecer ni destruir los datos.

Una persona o empresa puede comenzar usando pocas funciones y luego habilitar otras sin migrar, reconstruir ni perder su historia.

## 4. Suscripciones y capacidades
Los planes comerciales habilitan **capacidades**, no modelos de datos incompatibles.

Perfiles conceptuales de suscripción:
- **Persona:** organización de gastos familiares/personales con experiencia simple.
- **Intermedio:** registra ingresos y gastos de una actividad, requiere reportes y registros más complejos.
- **Empresas:** colaboradores, permisos, conciliaciones y acceso a la aplicación web completa.

Un usuario puede mejorar su suscripción y continuar sobre exactamente la misma información ya cargada. El crecimiento significa habilitar funciones.

La autenticación y la habilitación comercial son conceptos distintos. Debe poder existir usuario pendiente, habilitado, suspendido, con suscripción activa, vencida, demo o período de prueba.

## 5. Seguridad como requisito de producto
OrdenaClick estará alojado en un servidor y manejará información sensible e importante de clientes. La seguridad no se agrega al final: debe evaluarse en **cada implementación**.

Esto incluye autenticación, autorización por empresa/rol/capacidad, validación backend, aislamiento entre empresas, secretos fuera del código, cifrado cuando corresponda, backups seguros, auditoría, trazabilidad y despliegue seguro.

## 6. Perfiles funcionales
- **Administrador:** crea/administra empresas, configura estructura y ABM, registra operaciones, designa colaboradores y define permisos.
- **Colaborador:** perfil operativo sobre empresas asignadas; registra movimientos/pagos y usa ABM permitidos.
- **Contable / Contador:** preparado para Plan Contable, imputaciones, Estado de Resultados, Balance y configuración contable.
- **Legal / Abogado:** futuro, sobre empresas asignadas y módulos legales.
- **Desarrollador:** entorno interno y aislado; no debe mezclarse con información ni permisos de clientes.

## 7. Principios de producto
- Conservar historia.
- Poder explicar qué ocurrió, cuándo, quién lo hizo y sobre qué empresa.
- No deducir el pasado desde el estado actual de tablas maestras.
- Próximos Vencimientos y Alertas son parte central del producto.
- La arquitectura actual no debe bloquear Agenda, Órdenes de Pago, autorizaciones, cartera de cheques, conciliaciones, contabilidad, legal, multimoneda, nuevos impuestos/medios de pago ni nuevos planes comerciales.
- Toda nueva función se evalúa por su aporte a la Beta y por su compatibilidad con el crecimiento futuro.
