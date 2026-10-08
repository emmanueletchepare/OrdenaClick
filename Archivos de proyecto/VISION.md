# VISION.md — Qué es OrdenaClick y qué queremos que llegue a ser

## 1. Propósito

OrdenaClick es una aplicación web de gestión para ordenar registros económicos, pagos, compromisos, vencimientos, alertas e información operativa de una persona, actividad o Empresa.

Su valor no está solamente en almacenar hechos pasados. Debe ayudar a entender qué ocurrió, conservar una historia confiable y anticipar qué requiere atención.

La información operativa debe convertirse progresivamente en materia prima para:

- control de gastos y pagos;
- previsibilidad financiera;
- vencimientos y alertas;
- reportes;
- gestión por Centro/Recurso;
- Caja y Cartera;
- futura contabilidad.

## 2. Idea central

**Una sola arquitectura escalable.**

OrdenaClick debe poder servir a una operación simple y crecer junto con una Empresa sin obligar a migrar de producto ni reconstruir historia.

**Simplificar la interfaz, no simplificar ni destruir los datos.**

Los planes comerciales habilitarán capacidades. No crearán modelos incompatibles.

## 3. Primer objetivo: Beta

La prioridad inmediata es una **Beta usable, estable y segura**.

No se mide por cantidad de funciones sino por circuitos completos.

El eje Beta es **REGISTROS**:

```text
Comprobantes
Carga Planificada
Registrar Pago
Modificar / Eliminar
```

Los flujos deben incluir sus ABM, navegación `[+]`, pagos, saldos, vencimientos, alertas, permisos y pruebas.

La Beta también debe preservar la base ya construida de Caja/Cobranza y su arquitectura futura, sin permitir que esa etapa desplace el cierre de REGISTROS.

## 4. Núcleo económico

OrdenaClick separa hechos económicos de hechos financieros:

- Movimiento: documento/hecho económico.
- Pago: hecho financiero.
- AplicacionPago: cuánto de un Pago cancela un destino.
- Vencimiento: compromiso económico abierto.
- Alerta: aviso de atención.

La historia no se reescribe silenciosamente.

Un Movimiento puede existir sin Pago, con Pago parcial, total o múltiples Pagos.

Un Pago puede combinar medios y, en el circuito general Registrar Pago, distribuirse entre varios destinos.

## 5. Anticipación

OrdenaClick debe ayudar a responder no sólo “qué pasó”, sino también:

- qué vence;
- qué está vencido;
- cuánto queda pendiente;
- qué cuenta o recurso financiero deberá estar disponible;
- qué operación todavía necesita acción.

Próximos Vencimientos y Alertas son parte central del producto, no un agregado cosmético.

## 6. Personas, Empresas y colaboración

La cuenta de usuario es global a OrdenaClick.

Una persona puede:

- fundar una Empresa;
- administrar una Empresa;
- administrar un Centro;
- colaborar;
- actuar como Contable;
- actuar como Legal;
- relacionarse con varias Empresas con roles diferentes.

Jerarquía, rol funcional, origen contractual, reputación y suscripción son dimensiones distintas.

Ninguna de ellas sustituye la autorización backend.

## 7. Seguridad como producto

OrdenaClick manejará información empresarial, financiera, documentos y credenciales sensibles.

Por eso seguridad significa, como mínimo:

- autenticación;
- aislamiento entre Empresas;
- autorización por rol/capacidad;
- objetos hijos ligados a la Empresa autorizada;
- validación backend;
- secretos fuera del código;
- cifrado cuando corresponde;
- backups seguros;
- trazabilidad;
- despliegue seguro;
- concurrencia e idempotencia donde haya operaciones financieras.

Una pantalla que oculta un botón no constituye seguridad.

## 8. Caja, Cartera y Orden de Pago

Caja/Cartera representa dónde están los recursos y si pueden utilizarse.

Su dirección funcional es:

```text
Ingreso
→ Caja / Cartera
→ Disponibilidad
→ Gestión Administrativa
→ Traslados
→ Orden de Pago
```

No se modela complejidad innecesaria para reproducir sistemas externos. Se conserva sólo la información necesaria para disponibilidad, custodia, uso, historia y gestión.

## 9. Futuro preservado, no adelantado

La arquitectura no debe bloquear:

- Reportes;
- Estado de Resultados;
- Balance;
- Plan Contable;
- conciliaciones;
- Cartera;
- Orden de Pago;
- Agenda;
- autorizaciones;
- multimoneda;
- marketplace de perfiles;
- notificaciones móviles;
- nuevos impuestos y medios.

Pero preparar el futuro no significa implementarlo antes de cerrar la Beta.

## 10. Medida de éxito

OrdenaClick estará bien encaminado cuando una persona que nunca vio el sistema pueda:

```text
crear usuario
→ entrar
→ crear/configurar Empresa
→ relacionar colaboradores
→ registrar operaciones reales
→ registrar Pagos
→ consultar pendientes
→ recibir alertas
→ entender lo que cargó
```

y cuando cada usuario pueda hacer su trabajo sin obtener acceso a decisiones o datos que no le corresponden.
