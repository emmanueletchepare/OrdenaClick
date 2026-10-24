# OrdenaClick — continuidad después de permisos operativos (22/10/2026)

Proyecto: Django multempresa, Argentina. Casa `D:\Programacion\Proyectos\Ordenaclick`; rama `main`, remoto e5a520f antes de commit del bloque. Migraciones instaladas 0054 (administración multicientro/auditoría) y 0055 (Nómina por Centro). Regresiones históricas: 111/111; corrección posterior de UX de casillas Nómina informada como probada por el usuario.

**Instalador de cierre propuesto:** `instalar_permisos_registros_bancarios_y_docs.py`. Incluye acceso por acción para Registros y Pendientes bancarios, pruebas nuevas y actualización de MD. Instalación de código y pruebas focalizadas completadas por el helper. AÚN NO implica aprobación visual ni commit/push efectuado.

## Reglas que no deben modificarse

- Un panel Administrar, un sidebar, mismo acordeón, mismas vistas y retornos; no duplicar botoneras ni abrir pestañas paralelas. No reescribir CSS/layout aceptados.
- Propietario, superusuario y Administrador general pueden administrar; Administrador de Centro tiene Centros de Designar perfiles y permisos ON/OFF; Colaborador no Caja ni Configuración; Contable/Legal solo Nómina delegada; RRHH futuro (no creado).
- Caja requiere permiso explícito y solo permite cajas de Centros asignados; Nómina integral por Centro, descarga privada siempre protegida; Claves propias para operativos y todas para administradores generales.
- **Bandeja PENDIENTES es GLOBAL por Empresa** hasta resolver; el usuario con permiso ve todos los pendientes de esa Empresa, sin importar Centro. Solo al resolver se asigna un Centro autorizado y los resueltos se filtran por Centro. Carga de banco, cambio de estado y salidas e-Cheq no generan movimientos de Caja ni pagos de sistema externo.
- Registros y Pendientes se conceden POR ACCIÓN. Lecturas auxiliares de maestros no permiten modificarlos. Registrar/modificar comprobantes NO concede Pagos ni débito automático. La jerarquía Administrador general no eleva automáticamente el permiso histórico para escribir Movimientos. Obligaciones sigue pantalla informativa, no persistente; no abrir placeholder de Registrar Pago, Carga Planificada ni Modificar/Eliminar.
- Guardar/revocar permisos es auditado; prohibido conceder privilegios por ocultar/mostrar botones solamente: cada endpoint debe validar usuario, Empresa, acción y Centro correspondiente.

## Validación y commit

Tras `--plan` y `--apply`, confirmar `manage.py check`, `makemigrations usuarios --check --dry-run`, regresiones automáticas de seguridad/menú/Caja/Nómina/Bancos/Registros y validación visual en OLAFI. Consultar `git status --short` y revisar diff; hacer `git add` SELECTIVO de los archivos del cambio más docs y migraciones 0054/0055 pendientes, NO DB ni helper/respaldos/credenciales. Hacer commit/push solo con aceptación explícita y después de pruebas reales.

## Próximo bloque

Elegir con el usuario: (1) Gestor de alertas por usuario/acción (incluida OP lista para imprimir y aplicar), (2) Mensajes al desarrollador, (3) Caja. No iniciar nuevos trabajos antes del commit aprobado.


## Relevo de Alertas — Bloque A (23/10/2026, propuesto)

El cierre anterior de permisos se publicó en GitHub `main` como `0c09140`.
El bloque A autorizado incorpora un módulo Alertas separado de Próximos vencimientos,
reutilizando campanita/sonido y renderizadores existentes, sin tocar Caja, Nómina,
SQLite, migraciones ni reglas financieras. El permiso explícito `alertas.ver` autoriza
abrir Alertas, **no** concede acceso a los datos de cada módulo; cada fuente conserva
su permiso propio. Próximos vencimientos queda con Hoy/Semana/Rango y su ruta
no acepta el periodo `alertas`. La campanita consulta un endpoint protegido por
`alertas.ver` y abre Alertas dentro del área operativa, manteniendo sidebar visible.
El helper no declara el desarrollo validado: comprobar HTTP, regresiones, permisos,
visual y navegación en Casa y obtener aprobación antes del commit selectivo.
Gestión de destinatarios, avisos opcionales por usuario y nuevos eventos corresponden
a un bloque futuro no implementado en este helper.
