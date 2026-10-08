# Estado del documento — 08/10/2026

Backup Empresa v1 ya tiene una implementación base con servicios dedicados,
manifest, inspector, restaurador, wizard y round-trip. Este inventario se
mantiene como contrato técnico y checklist de cobertura.

Los puntos aún no marcados siguen siendo pruebas/cierres pre-Beta; no deben
interpretarse como que el subsistema completo todavía no existe.

---

# BACKUP EMPRESA V1 — INVENTARIO Y CONTRATO PRELIMINAR

**Fecha:** 04/10/2026
**Estado:** Diseño previo a implementación.
**Objetivo:** inventariar el ecosistema real de una Empresa y fijar las reglas que deberá cumplir el primer formato de backup portable de OrdenaClick.

> Este documento no reemplaza `ARQUITECTURA.md`, `REGLAS.md`, `DECISIONES.md`, `PRE_BETA.md` ni `MODELO_DATOS.md`. Los complementa para el bloque Exportar/Importar Empresa. Código, migraciones y reglas autoritativas vigentes mandan ante contradicción.

---

## 1. Decisiones ya cerradas para v1

1. No se dará compatibilidad a backups legacy anteriores a v1. El proyecto todavía no llegó a Beta ni existen clientes que dependan de esos formatos.
2. El formato nuevo comienza directamente como **Backup Empresa v1** y debe estar versionado mediante manifest.
3. El backup es entrada no confiable. Su contenido nunca acredita autorización ni concede privilegios por sí mismo.
4. El propietario/fundador de la Empresa restaurada no lo decide el ZIP. Lo determina el flujo autenticado y autorizado de la instalación destino.
5. La importación será un **proceso guiado (wizard)**: validar primero, permitir revisar/configurar información vigente y restaurar recién después de una confirmación final.
6. El wizard debe distinguir historia de configuración actual. Un dato histórico no se reescribe sólo porque una persona, Centro, cuenta u otra entidad haya dejado de estar activa.
7. Los usuarios que participaron históricamente no desaparecen de la auditoría. Su estado operativo actual se resuelve como activo/inactivo y su jerarquía vigente se confirma explícitamente durante la importación.
8. Un rol escrito en el backup es información de origen, no una orden para conceder ese rol en destino.
9. Si el CUIT ya existe, no se elimina primero la Empresa válida. La restauración debe planificarse y validarse antes de cualquier operación destructiva y utilizar atomicidad/rollback donde corresponda.
10. La futura precarga de catálogos básicos (por ejemplo bancos frecuentes) es un subsistema diferente del backup y no debe mezclarse con él.
11. Más adelante podrá existir un wizard de creación inicial de Empresa basado en una lógica de configuración progresiva semejante, pero eso queda fuera del alcance de este bloque.

---

## 2. Clasificación usada para el inventario

Para diseñar exportación, restauración y wizard se utilizarán estas categorías conceptuales:

- **Raíz:** identifica la Empresa restaurada.
- **Maestro:** dato operativo relativamente estable que puede activarse/inactivarse.
- **Histórico/transaccional:** forma parte de la historia económica, financiera o de auditoría y no debe reinterpretarse según la configuración actual.
- **Relación:** tabla que une entidades y cuya identidad depende de ellas.
- **Configuración revisable:** dato que puede requerir confirmación o actualización en el wizard.
- **Sensible:** dato que exige tratamiento especial por contener credenciales, información privada o archivos delicados.
- **Global/no propiedad de Empresa:** objeto de la instalación que puede estar relacionado con una Empresa pero no debe restaurarse como si fuese propiedad exclusiva de ella.

Estas categorías pueden coexistir para una misma entidad.

---

## 3. Inventario real de modelos

El inventario se obtuvo del `usuarios/models.py` vigente del baseline `da16e88` más el prototipo posterior de asignaciones.

### 3.1 Empresa

**Modelo:** `Empresa`
**Clasificación:** raíz + configuración revisable + sensible.
**Relaciones relevantes:** `propietario -> auth.User` (`PROTECT`, nullable).
**Archivos:** `estatuto`, `acta`, `designacion`.

**v1:** se exporta.
**Importación:** los datos de identidad empresarial forman parte del wizard. La categoría fiscal y documentación pueden haber cambiado desde el backup y deben poder confirmarse/actualizarse antes de finalizar.
**Propietario:** nunca se restaura desde el ZIP como privilegio.
**Identidad portable propuesta:** UUID interno del backup, no PK Django.

### 3.2 Ejercicio

**Modelo:** `Ejercicio`
**Clasificación:** maestro contable + histórico.
**Depende de:** Empresa.
**v1:** se exporta completo, incluidos ejercicios cerrados.
**Identidad portable:** UUID de backup.

### 3.3 TipoGasto

**Modelo:** `TipoGasto`
**Clasificación:** maestro.
**Depende de:** Empresa.
**Tiene activo/inactivo:** sí.
**v1:** exportar activos e inactivos.
**Identidad portable:** UUID de backup.

### 3.4 Proveedor

**Modelo:** `Proveedor`
**Clasificación:** maestro.
**Depende de:** Empresa.
**Tiene activo/inactivo:** sí.
**v1:** exportar activos e inactivos y todos los datos de contacto/observaciones.
**Identidad portable:** UUID de backup.

### 3.5 TipoGastoProveedor

**Modelo:** `TipoGastoProveedor`
**Clasificación:** relación.
**Depende de:** TipoGasto + Proveedor.
**v1:** exportar después de resolver ambos maestros.
**Identidad:** puede reconstruirse por la pareja de identidades portables de sus extremos; no requiere confiar en PK de origen.

### 3.6 CentroOperativo

**Modelo:** `CentroOperativo`
**Clasificación:** maestro estructural + configuración revisable.
**Depende de:** Empresa.
**Tiene activo/inactivo:** sí.
**v1:** exportar activos e inactivos.
**Wizard:** puede requerir confirmar cuáles continúan operativos.
**Identidad portable:** UUID de backup.

### 3.7 RecursoOperativo

**Modelo:** `RecursoOperativo`
**Clasificación:** maestro.
**Depende de:** Empresa.
**Tiene activo/inactivo:** sí.
**v1:** exportar activos e inactivos.
**Identidad portable:** UUID de backup.

### 3.8 RecursoOperativoCentro

**Modelo:** `RecursoOperativoCentro`
**Clasificación:** relación.
**Depende de:** RecursoOperativo + CentroOperativo.
**v1:** exportar y reconstruir después de ambos extremos.

### 3.9 Cliente

**Modelo:** `Cliente`
**Clasificación:** maestro con uso histórico.
**Depende de:** Empresa + CentroOperativo.
**Tiene activo/inactivo:** sí.
**v1:** exportar activos e inactivos.
**Identidad portable:** UUID de backup.
**Nota:** no usar CUIT como única identidad técnica; puede estar vacío, repetido históricamente o sujeto a reglas aún no cerradas.

### 3.10 Banco

**Modelo:** `Banco`
**Clasificación:** maestro.
**Depende de:** Empresa.
**Tiene activo/inactivo:** sí.
**v1:** exportar activos e inactivos.
**Identidad portable:** UUID de backup.
**Nota:** la futura precarga de bancos no reemplaza ni se mezcla con los bancos particulares restaurados desde una Empresa.

### 3.11 CuentaBancaria

**Modelo:** `CuentaBancaria`
**Clasificación:** maestro financiero + sensible.
**Depende de:** Empresa + Banco.
**Tiene activo/inactivo:** sí.
**v1:** exportar activos e inactivos.
**Identidad portable:** UUID de backup.
**Wizard:** puede ser revisable por cambios de cuentas activas, sin alterar la historia que las referencia.

### 3.12 Tarjeta

**Modelo:** `Tarjeta`
**Clasificación:** maestro financiero.
**Depende de:** Empresa + CuentaBancaria.
**Tiene activo/inactivo:** sí.
**v1:** exportar activos e inactivos.
**Identidad portable:** UUID de backup.

### 3.13 Retencion

**Modelo:** `Retencion`
**Clasificación:** maestro.
**Depende de:** Empresa.
**Tiene activo/inactivo:** sí.
**v1:** exportar activos e inactivos.
**Identidad portable:** UUID de backup.

### 3.14 Caja

**Modelo:** `Caja`
**Clasificación:** maestro financiero/operativo + configuración revisable.
**Depende de:** Empresa + CentroOperativo.
**Tiene activo/inactivo:** sí.
**v1:** exportar activos e inactivos.
**Identidad portable:** UUID de backup.

### 3.15 Movimiento

**Modelo:** `Movimiento`
**Clasificación:** histórico/transaccional.
**Depende directamente de:** Empresa y, opcionalmente, Ejercicio, TipoGasto, Proveedor, CentroOperativo, RecursoOperativo y CuentaBancaria.
**Archivo:** `archivo`.
**v1:** exportar todos los movimientos históricos y su archivo adjunto cuando exista.
**Identidad portable:** UUID de backup.
**Regla:** sus relaciones históricas deben reconstruirse contra los objetos restaurados correspondientes; no contra el estado maestro “actual” elegido por el wizard.

### 3.16 Pago

**Modelo:** `Pago`
**Clasificación:** histórico/transaccional.
**Depende de:** Empresa.
**v1:** exportar completo.
**Identidad portable:** UUID de backup.

### 3.17 AplicacionPago

**Modelo:** `AplicacionPago`
**Clasificación:** histórico/transaccional + relación.
**Depende de:** Pago y uno de los destinos previstos por el modelo (`Movimiento` y/o `CuotaPlan`, según reglas vigentes).
**v1:** exportar y reconstruir después de Pago, Movimiento, PlanPago y CuotaPlan.
**Identidad portable:** UUID de backup.

### 3.18 OperacionBancariaPago

**Modelo:** `OperacionBancariaPago`
**Clasificación:** histórico/transaccional.
**Depende de:** Pago, CuentaBancaria opcional y Banco destino.
**Archivo:** `comprobante`.
**v1:** exportar completo.
**Identidad portable:** UUID de backup.

### 3.19 DebitoAutomaticoPago

**Modelo:** `DebitoAutomaticoPago`
**Clasificación:** histórico/transaccional.
**Depende de:** Pago + CuentaBancaria.
**Archivo:** `comprobante`.
**v1:** exportar completo.
**Identidad portable:** UUID de backup.

### 3.20 TarjetaPago

**Modelo:** `TarjetaPago`
**Clasificación:** histórico/transaccional.
**Depende de:** Pago + Tarjeta.
**Archivo:** `comprobante`.
**v1:** exportar completo.
**Identidad portable:** UUID de backup.

### 3.21 RetencionPago

**Modelo:** `RetencionPago`
**Clasificación:** histórico/transaccional.
**Depende de:** Pago.
**Archivo:** `comprobante`.
**v1:** exportar completo.
**Identidad portable:** UUID de backup.

### 3.22 Cheque

**Modelo:** `Cheque`
**Clasificación:** histórico/transaccional + instrumento financiero.
**Depende de:** Empresa y, según origen/estado, puede referenciar Cobranza, Caja, Cliente, Pago, Banco y CuentaBancaria.
**Archivo:** `comprobante`.
**v1:** exportar todos los cheques/e-Cheqs relevantes, no sólo disponibles.
**Identidad portable:** UUID de backup.

### 3.23 PlanPago

**Modelo:** `PlanPago`
**Clasificación:** histórico/transaccional.
**Depende de:** Movimiento (1:1) y opcionalmente CuentaBancaria.
**v1:** exportar completo.
**Identidad portable:** UUID de backup.

### 3.24 CuotaPlan

**Modelo:** `CuotaPlan`
**Clasificación:** histórico/transaccional.
**Depende de:** PlanPago.
**v1:** exportar completo.
**Identidad portable:** UUID de backup.

### 3.25 Vencimiento

**Modelo:** `Vencimiento`
**Clasificación:** histórico/transaccional.
**Depende de:** Empresa y, según `tipo_origen`, puede referenciar Movimiento, CuotaPlan o Cheque; además Banco y CuentaBancaria opcionales.
**v1:** exportar completo.
**Identidad portable:** UUID de backup.

### 3.26 Alerta

**Modelo:** `Alerta`
**Clasificación:** histórico/operativo derivado.
**Depende de:** Vencimiento.
**v1:** inicialmente se considera exportable para preservar estado (`pendiente`, `atendida`, fechas y observaciones). Antes de cerrar contrato debe verificarse si alguna alerta futura será puramente regenerable y convendrá excluirla.

### 3.27 Cobranza

**Modelo:** `Cobranza`
**Clasificación:** histórico/transaccional + auditoría.
**Depende de:** Empresa + Caja + `auth.User` mediante `creado_por`.
**v1:** exportar completa.
**Identidad portable:** UUID de backup.
**BLOQUEANTE:** la referencia histórica a `auth.User` no es portable por sí sola. Debe definirse identidad histórica de actor antes de implementar restauración portable.

### 3.28 MovimientoCaja

**Modelo:** `MovimientoCaja`
**Clasificación:** histórico/transaccional + auditoría.
**Depende de:** Empresa + Caja + Cobranza opcional + `auth.User` mediante `creado_por`.
**v1:** exportar completo.
**Identidad portable:** UUID de backup.
**BLOQUEANTE:** mismo problema de identidad histórica de actor que Cobranza.

### 3.29 AsignacionUsuarioEmpresa

**Modelo:** `AsignacionUsuarioEmpresa`
**Clasificación:** configuración de acceso actual + relación con objeto global.
**Depende de:** Empresa + `auth.User` + CentroOperativo opcional según jerarquía.
**Tiene activo/inactivo:** sí.
**v1:** el estado de origen puede viajar como propuesta/configuración histórica, pero **no se aplica automáticamente**.
**Wizard:** el usuario autorizado que importa decide quién continúa activo, jerarquía actual y Centro cuando corresponda, pudiendo incorporar usuarios nuevos mediante el flujo seguro que se diseñe.
**Fundador:** no se duplica como asignación.

### 3.30 GestionClave

**Modelo:** `GestionClave`
**Clasificación:** maestro extremadamente sensible.
**Depende de:** Empresa.
**Tiene activo/inactivo:** sí.
**Dato sensible especial:** `contrasena_cifrada`, cifrada con una clave externa de la instalación (`GESTION_CLAVES_KEY`).

**Reglas ya vigentes:**
- nunca exportar contraseña en texto plano;
- nunca incluir la clave maestra dentro del backup;
- un ciphertext de una instalación no puede asumirse descifrable por otra.

**Decisión conservadora preliminar para v1:** exportar metadatos de la entrada (nombre, sitio, usuario, correo, referencias, observaciones, activo), pero **no considerar portable `contrasena_cifrada` tal como está hoy**. El wizard debe señalar esas credenciales para reingreso/reconfiguración, salvo que antes de implementar se diseñe un contenedor de secretos portable con cifrado independiente del servidor. No se debe improvisar ese mecanismo dentro del ZIP general.

### 3.31 PerfilUsuario

**Modelo:** `PerfilUsuario`
**Clasificación:** global/no propiedad de Empresa.
**Depende de:** `auth.User`, no de Empresa.
**v1:** no se restaura como entidad empresarial completa. Sus datos personales requieren una política separada vinculada a identidad de usuario y privacidad.

---

## 4. Problema estructural detectado: identidad histórica de usuarios

Actualmente la aplicación usa directamente `auth.User` en al menos:

- `Empresa.propietario`;
- `AsignacionUsuarioEmpresa.usuario`;
- `Cobranza.creado_por`;
- `MovimientoCaja.creado_por`.

Esto funciona dentro de una misma instalación, pero no garantiza portabilidad entre servidores: el usuario origen puede no existir en destino, su PK no es portable y tampoco corresponde crearle automáticamente una cuenta con privilegios a partir de un ZIP.

### Regla

El Backup Empresa v1 no puede usar `auth.User.pk` como identidad histórica portable.

### Requisito de diseño antes del restaurador

Definir una representación portable de **actor/identidad histórica** independiente de la autorización actual. Debe permitir conservar “quién realizó la operación” aunque esa persona:

- ya no trabaje en la Empresa;
- esté inactiva;
- no tenga cuenta activa en el servidor destino;
- haya cambiado de jerarquía;
- no deba recibir permisos al importar.

La solución exacta (snapshot histórico, entidad de persona/actor empresarial, vínculo posterior con `auth.User`, u otra) se definirá antes de cerrar el esquema v1. No crear usuarios Django automáticamente para resolver este problema.

---

## 5. Orden preliminar de restauración

Este orden es conceptual y deberá validarse con constraints y tests antes de implementarse:

1. Empresa (sin confiar en propietario del backup).
2. Ejercicios.
3. Centros Operativos.
4. Recursos Operativos.
5. Relación RecursoOperativoCentro.
6. Bancos.
7. Cuentas Bancarias.
8. Tarjetas.
9. Retenciones maestras.
10. Proveedores.
11. Tipos de Gasto.
12. TipoGastoProveedor.
13. Clientes.
14. Cajas.
15. Identidades históricas/participantes, cuando el diseño esté definido.
16. Configuración de asignaciones de usuario, sólo como datos para el wizard; privilegios definitivos se aplican mediante flujo autorizado.
17. Movimientos.
18. Planes de Pago.
19. Cuotas.
20. Pagos.
21. Medios/componentes de Pago.
22. Aplicaciones de Pago.
23. Cobranzas.
24. Cheques/e-Cheqs, ajustando el orden real según referencias Cobranza/Pago y estrategia de resolución diferida.
25. Movimientos de Caja.
26. Vencimientos.
27. Alertas.
28. Gestión de Claves: metadatos y reconfiguración segura de secretos según política definitiva.
29. Archivos adjuntos en ubicaciones controladas, coordinados con cada entidad y sin confiar en rutas del ZIP.

**Nota:** existen referencias cruzadas (especialmente Cheque ↔ Cobranza/Pago y Vencimiento ↔ Cheque/Cuota/Movimiento). El restaurador probablemente necesitará creación por etapas o resolución diferida de referencias, no un simple `create()` lineal.

---

## 6. Estructura conceptual del Backup Empresa v1

No es todavía el esquema JSON definitivo, pero el contenedor deberá tener como mínimo:

```text
backup_empresa.zip
├── manifest.json
├── data/
│   ├── empresa.json
│   ├── ejercicios.json
│   ├── centros_operativos.json
│   ├── recursos_operativos.json
│   ├── recursos_centros.json
│   ├── bancos.json
│   ├── cuentas_bancarias.json
│   ├── tarjetas.json
│   ├── retenciones.json
│   ├── proveedores.json
│   ├── tipos_gasto.json
│   ├── tipos_gasto_proveedores.json
│   ├── clientes.json
│   ├── cajas.json
│   ├── participantes.json
│   ├── asignaciones_origen.json
│   ├── movimientos.json
│   ├── pagos.json
│   ├── aplicaciones_pago.json
│   ├── operaciones_bancarias_pago.json
│   ├── debitos_automaticos_pago.json
│   ├── tarjetas_pago.json
│   ├── retenciones_pago.json
│   ├── cheques.json
│   ├── planes_pago.json
│   ├── cuotas_plan.json
│   ├── vencimientos.json
│   ├── alertas.json
│   ├── cobranzas.json
│   ├── movimientos_caja.json
│   └── gestion_claves.json
└── files/
    └── ... archivos con nombres controlados por el exportador ...
```

Los nombres definitivos pueden cambiar al cerrar el contrato. Ninguna relación interna debe depender de PK Django de origen.

---

## 7. Manifest v1 — contenido mínimo propuesto

```json
{
  "format": "ordenaclick_empresa",
  "format_version": 1,
  "exported_at": "ISO-8601",
  "application_version": null,
  "backup_id": "uuid",
  "company": {
    "backup_ref": "uuid",
    "cuit": "...",
    "display_name": "..."
  },
  "components": {},
  "files": {},
  "security": {
    "contains_plaintext_passwords": false,
    "contains_installation_secrets": false
  }
}
```

El manifest debe describir componentes y permitir validar que el ZIP contiene exactamente lo esperado para esa versión. Los campos definitivos y checksums se cerrarán en la etapa de contrato.

---

## 8. Reglas de identidad portable

1. Toda entidad que necesite ser referenciada por otra recibe una identidad portable interna del backup (preferentemente UUID).
2. La PK Django de origen no forma parte del contrato de identidad. Puede omitirse o conservarse únicamente como metadato diagnóstico no confiable.
3. Las referencias internas se expresan mediante las identidades portables.
4. Durante restauración se construyen mapas `backup_ref -> objeto destino`.
5. Ninguna referencia puede apuntar fuera del conjunto permitido para la Empresa restaurada.
6. Las claves naturales (CUIT, nombre, número de cuenta, etc.) sirven para validación o UX cuando corresponda, pero no se asumen universalmente seguras como identidad técnica.

---

## 9. Wizard de importación — alcance conceptual

El inspector debe terminar antes de abrir decisiones del wizard. El usuario no debe configurar sobre un ZIP todavía no validado.

Pasos conceptuales, sujetos al inventario final:

1. **Validación del backup**: formato, versión, estructura, tamaños, rutas, JSON, referencias y archivos.
2. **Empresa**: confirmar datos vigentes, incluida condición fiscal.
3. **Documentación societaria**: revisar/conservar/actualizar según política.
4. **Estructura operativa**: confirmar Centros y otros maestros que deban continuar activos.
5. **Usuarios y accesos**: elegir continuidades, inactivos, jerarquías actuales, Centros y altas nuevas mediante flujo seguro.
6. **Configuración financiera revisable**: cuentas, Cajas u otros elementos cuyo estado operativo actual pueda haber cambiado.
7. **Credenciales empresariales**: advertir/reconfigurar Gestión de Claves según política segura.
8. **Resumen del plan**: mostrar qué se restaura históricamente y qué configuración se modificará.
9. **Confirmación final**.
10. **Restauración controlada** con transacción/rollback y validación post-restauración.

El wizard no debe modificar hechos históricos para reflejar la configuración vigente elegida por el usuario.

---

## 10. Seguridad mínima del contenedor antes de persistir

El inspector de importación v1 deberá, como mínimo:

- exigir usuario autenticado y capacidad backend correspondiente;
- limitar tamaño de upload;
- limitar cantidad de entradas;
- limitar tamaño total descomprimido;
- limitar tamaño por entrada donde corresponda;
- rechazar rutas absolutas, `..`, enlaces o formas equivalentes de escape;
- rechazar archivos no declarados/permitidos por el esquema v1;
- validar que `manifest.json` exista y sea compatible;
- validar JSON, tipos, campos y referencias;
- validar duplicados de identidades portables;
- validar checksums si se incorporan al contrato;
- no extraer archivos a ubicaciones elegidas por nombres del ZIP;
- usar temporales privados y limpieza garantizada;
- no confiar en extensión ni MIME del upload;
- no devolver detalles internos sensibles al navegador;
- no ejecutar ninguna restauración hasta completar inspección y plan.

---

## 11. Pendientes que bloquean cerrar el contrato v1

- [ ] Definir identidad histórica portable de personas/actores y su relación con `auth.User`.
- [ ] Definir política definitiva de `GestionClave`: metadatos + reingreso, o contenedor de secretos portable diseñado específicamente.
- [ ] Revisar constraints/validaciones de cada modelo para fijar el orden real de restauración.
- [ ] Resolver referencias cruzadas de Cheque/Cobranza/Pago/Vencimiento.
- [ ] Definir esquema JSON exacto y validadores por componente.
- [ ] Definir checksums/integridad del manifest y archivos.
- [ ] Definir límites concretos de ZIP para producción mediante settings.
- [ ] Definir estrategia de restauración sobre CUIT existente sin destruir primero el estado válido.
- [ ] Definir qué estados/configuraciones entran al wizard y cuáles se restauran sin intervención.
- [ ] Crear tests de round-trip y adversariales antes de considerar el backup confiable.

---

## 12. Próximo paso recomendado

Antes de crear el servicio exportador, resolver primero el problema de **identidad histórica de usuario/actor**, porque afecta directamente la portabilidad de Cobranzas, Movimientos de Caja, asignaciones y futuras auditorías.

Después:

1. cerrar esquema de referencias portables;
2. cerrar política de Gestión de Claves;
3. definir `manifest.json` v1 exacto;
4. recién entonces crear servicios de exportación/inspección con tests.

---

## 10. Implementación realizada — Backup Empresa v1

**Fecha:** 04/10/2026

Se implementó el primer subsistema completo de Backup Empresa v1 con estas fronteras:

- `usuarios/services/backup_empresa/`: contrato, exportación, inspección/validación y restauración.
- `usuarios/empresa_backup_views.py`: coordinación HTTP del flujo.
- `templates/usuarios/empresa/importacion_wizard.html`: wizard de importación.
- `static/js/empresa/`: comportamiento del wizard y del lanzador de importación, sin JavaScript inline nuevo.
- `static/css/empresa/importacion_wizard.css`: estilos propios del wizard manteniendo la estética vigente.

### Cerrado en este bloque

- [x] `manifest.json` con formato `ordenaclick_empresa`, versión 1, componentes, tamaños y SHA-256.
- [x] No se acepta formato legacy sin manifest v1.
- [x] Exportación de todos los modelos de Empresa inventariados en este documento.
- [x] Archivos adjuntos empaquetados bajo rutas controladas.
- [x] Identificadores internos portables; la restauración no depende de conservar PK Django.
- [x] Límites de upload, cantidad de entradas, tamaño descomprimido, entrada individual y relación de compresión.
- [x] Rechazo de path traversal, rutas no válidas, symlinks y entradas ZIP cifradas.
- [x] Validación de hashes, tamaños, estructura JSON, conteos y referencias internas antes del wizard.
- [x] Propietario del backup ignorado como privilegio; el propietario destino es el usuario autorizado que restaura.
- [x] Wizard: datos actuales de Empresa/documentación -> usuarios/jerarquías -> resumen/confirmación.
- [x] Roles del ZIP no se conceden automáticamente.
- [x] El fundador actual no se duplica como `AsignacionUsuarioEmpresa`.
- [x] Identidades históricas se preservan aunque no exista cuenta de acceso equivalente.
- [x] Gestión de Claves viaja sin `contrasena_cifrada`; requiere reconfiguración en destino.
- [x] Si el CUIT ya existe, se restaura in-place dentro de `transaction.atomic()` después de validar y confirmar; un error revierte la base.
- [x] Archivos nuevos creados durante una restauración fallida se limpian explícitamente.
- [x] Señal automática de Recurso GENERAL contemplada para evitar duplicados durante round-trip.
- [x] Tests nuevos de formato, secretos, legacy, Zip Slip y round-trip.

### Deliberadamente fuera de este bloque

- [ ] Crear/invitar cuentas Django nuevas desde el wizard. Backup v1 sólo vincula cuentas existentes coincidentes; el alta nueva debe usar un flujo seguro propio y nunca importar contraseñas.
- [ ] Incorporar `admin_general` / `admin_centro` al servicio general de autorización de toda la aplicación. Sigue siendo el bloque posterior de Accesos.
- [ ] Limpieza programada adicional de archivos históricos de storage que queden huérfanos después de reemplazos exitosos.
- [ ] Wizard futuro de alta inicial de Empresa.


## Actualización 05/10/2026 — relaciones y roles funcionales

- `RolFuncionalUsuarioEmpresa` (Contable/Legal) forma parte del estado vigente de la Empresa y se serializa dentro de `data/usuarios.json`; nunca concede privilegios automáticamente al importar y debe confirmarse en el wizard.
- `SolicitudRelacionEmpresa` queda excluida deliberadamente del Backup Empresa v1: representa workflow transitorio de esta instalación (pendiente/aceptada/rechazada) ligado a cuentas globales de OrdenaClick, no historia financiera ni configuración portable de la Empresa.
- El origen futuro interno/externo, marketplace, ranking y contratación quedan fuera de Backup v1 hasta que existan modelos contractuales definidos.
