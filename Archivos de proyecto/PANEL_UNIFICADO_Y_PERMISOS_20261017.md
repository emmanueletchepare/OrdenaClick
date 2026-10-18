# Administrar: panel unificado y autorizaciones (17/10/2026)

## Decisión aprobada

La pantalla de entrada tiene **Administrar**, **Contable** y **Legal**. "Colaborador" no es un panel separado: es una **jerarquía por Empresa** dentro de Administrar. Relaciones/solicitudes siguen accesibles por su enlace propio. Una persona puede administrar una Empresa y colaborar en otra.

Se reutiliza el mismo panel, sidebar, lenguaje visual y flujos `[+]` del Administrador, sin duplicar aplicaciones. Una relación activa permite **ver/seleccionar una Empresa**, pero no da acceso por sí sola a sus módulos. Las capacidades son específicas de Empresa, módulo, acción y, donde corresponda, Centro Operativo. Se comprueban en backend en todas las URLs, además de filtrar la interfaz. No se otorga jamás administración global para abrir un ABM aislado.

## Árbol único de Gestión de accesos (orden del sidebar)

- **Registros**: consultar, crear, editar, aprobar/anular (solo si existe endpoint autorizado).
- **Pendientes bancarios**: consultar, precargar, revisar, resolver, operar e-Cheqs. Alcance por Centro según regla vigente.
- **Herramientas**: Gestión de claves, *solo claves propias/asignadas* una vez modelada su titularidad. Administrador puede ver todas las autorizadas.
- **ABM**:
  - Estructura Operativa: Centros Operativos, Recursos Operativos, Proveedores, Tipos de gastos, Clientes.
  - Finanzas y estado de pagos: Bancos, Cuentas Bancarias, Tarjetas, Retenciones.

Cada título tiene casilla y despliegue. Las casillas de títulos agrupan las capacidades de sus hijos, con estado parcial. El orden reproduce el sidebar. Al desarrollar módulos (p. ej. Órdenes de Compra), registrar capacidades y permisos backend ANTES de exponer su casilla. Los `[+]` reutilizan el ABM autorizado con retorno LIFO y formularios intactos.

## Etapas y límites de seguridad

1. **Entrada unificada**: selección de Empresas propias y asignaciones operativas activas en Administrar. El propietario conserva su panel completo. Un colaborador ve el mismo contenedor visual, pero solo Pendientes bancarios si `alcance_pendientes` lo permite. Sin permisos, no hay módulos, aunque la Empresa sí aparece. No se incorporan datos sensibles ni scripts de administración al HTML restringido. No hay migraciones.
2. **Catálogo persistido y administración de permisos**: modelo de capacidades por Empresa/usuario/módulo/acción; auditoría, revocación efectiva e invariantes de Centro. UI acorde al árbol anterior. Sin conceder capacidades implícitas.
3. **Habilitación progresiva de módulos compartidos**: primero Registros, Pendientes, Gestión de claves, ABM (cada endpoint autorizado); después nuevas funciones. Gestión de claves **NO** se habilita hasta modelar dueño/asignación.
4. **Integración total**: unificar la navegación funcional de todos los módulos en el mismo contenedor, validando también Administradores generales/de Centro que no son propietarios. No eliminar rutas históricas hasta actualizar consumidores y pruebas.

## Prohibiciones

No copiar íntegramente paneles, no elevar permisos mediante rol visual, no presentar datos de otras Empresas, no esconder únicamente botones sin autorizar en servidor, no tocar Nómina ni Caja para esta etapa, no cambiar estética sin autorización, no instalar sobre hashes distintos, no incluir SQLite en commits.
