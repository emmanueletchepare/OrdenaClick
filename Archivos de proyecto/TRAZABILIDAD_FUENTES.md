# TRAZABILIDAD_FUENTES.md

Este archivo no forma parte de los siete documentos operativos. Es un resguardo de trazabilidad para garantizar que la reorganización no haga desaparecer contenido fuente.
Los siete documentos normalizados son la referencia de trabajo; ante una duda histórica, este anexo permite volver al texto recibido.


## FUENTE: Reglas_del_desarrollo.md

```text
-no JavaScripts inline
-no eliminar comentarios importantes
-cada funcion debe tener docstrings
-la arquitectura se respeta de la navegacion se respeta siempre (Estructuras del menu.txt)
-mantener el mismo estilo de codigo del proyecto
-Siempre que un abm es llamado desde el centro de ABMs como de un Boton [+] de algun formulario debe volver al lugar desde donde fue llamado en el estado en el que estaba.
---------------------------------------------------
Para ABMS: 
El estándar para todos los ABM de OrdenaClick

Cada ABM (Proveedores, Clientes, Rubros, etc.) debería cumplir exactamente esto:

Apertura
✅ Desde el menú lateral.
✅ Desde el botón [+] de otro formulario.
Cierre
✅ Si se abrió desde el menú → vuelve al menú.
✅ Si se abrió desde un [+] → vuelve exactamente al formulario que lo llamó y deja seleccionado el registro recién creado.
Edición
✅ Sin prompt().
✅ La tarjeta carga los datos en el formulario.
✅ El botón Guardar cambia a Actualizar.
✅ Aparece Cancelar.
✅ Al cancelar se limpia el formulario y vuelve a modo Alta.
Eliminación
✅ Confirmación antes de borrar.
✅ Baja logica, pero no fisica para no romper la base en consultas. ( Usar PROTECT y nunca CASCADE)
✅ Validaciones de negocio cuando correspondan.
✅ Refresca la lista sin salir del ABM.
Estilo
✅ Mismo CSS.
✅ Mismos botones.
✅ Mismo comportamiento que Bancos y Centros Operativos.
✅ Toda tabla maestra usa baja lógica.
✅ Si existe un registro inactivo no se crea otro: se reactiva.
✅ Todos los ABM deben permitir edición integrada.
✅ Todo ABM debe funcionar desde el menú y desde [+].
✅ Todo ABM debe volver al origen.
✅ Si se abrió desde Registro, debe quedar seleccionado automáticamente.
✅ Las bajas físicas sólo se permiten en casos excepcionales (como Empresa, por decisión explícita).

Decisiones que considero cerradas para cargas simples

A partir de ahora tomaría estas reglas como definitivas:

Tipo de Gasto reemplaza conceptualmente al Rubro simple.
Tipo de Gasto y Proveedor tienen relación muchos a muchos.
Relacionado con pasa a llamarse Recurso Operativo.
Todo Recurso Operativo debe estar vinculado a un Centro Operativo mediante una asignación.
El movimiento conserva el recurso y el centro imputado históricamente.
Usuario y Recurso Operativo son entidades independientes, vinculables en el futuro.
Los archivos de movimientos serán registros independientes y múltiples.
Cuenta contable quedará visible pero deshabilitada hasta desarrollar el Plan Contable.
No vamos a implementar todavía Giras/Rendiciones, pero el modelo no debe impedirlas.

VISUAL
La pantalla nueva debe parecer parte de OrdenaClick:
mismos colores, radios, tamaños, botones, acordeones y espaciados.

FLUJO
Si desde un formulario se entra a un ABM con [+]:
crear → volver → conservar formulario → seleccionar nuevo elemento.

JERARQUÍA
Registro, Pago y Plan son etapas relacionadas,
pero no deben confundirse visualmente entre sí.
```


## FUENTE: Reglas_Exportacion_Empresa.txt

```text
EXPORTACIÓN / IMPORTACIÓN DE EMPRESA - REGLAS DE ARQUITECTURA

OBJETIVO

La opción Exportar Empresa debe generar una copia completa y portable
de toda la información perteneciente a una empresa.

La exportación no debe limitarse a los datos visibles del formulario
Modificar Empresa.

Toda nueva entidad que dependa funcionalmente de Empresa debe evaluarse
para su inclusión en Exportar/Importar Empresa.


REGLA PRINCIPAL

Si un dato se perdería al eliminar la empresa y volver a importarla,
ese dato debe formar parte del backup, salvo que exista una razón
explícita y documentada para excluirlo.


DATOS QUE DEBEN FORMAR PARTE DE LA EXPORTACIÓN

1. EMPRESA
- Datos generales.
- Datos fiscales.
- Datos de contacto.
- Autoridades.
- Configuraciones propias de la empresa.

2. DOCUMENTACIÓN SOCIETARIA
- Estatuto.
- Actas.
- Designaciones.
- Otros documentos societarios que se agreguen en el futuro.

3. EJERCICIOS
- Todos los ejercicios de la empresa.
- Estado.
- Fechas.
- Autoridades asociadas si corresponde.

4. CENTROS OPERATIVOS
- Activos e inactivos.
- Deben conservar sus identificadores lógicos para reconstruir relaciones.

5. RECURSOS OPERATIVOS
- Activos e inactivos.
- Tipo de recurso.
- Centro Operativo relacionado.
- Descripción.

6. BANCOS
- Activos e inactivos.

7. PROVEEDORES
- Activos e inactivos.
- Todos sus datos de contacto y observaciones.

8. TIPOS DE GASTO
- Activos e inactivos.
- Descripción.
- Relaciones con proveedores.

9. GESTIÓN DE CLAVES
- Debe incluirse solo mediante un mecanismo seguro.
- Nunca exportar contraseñas en texto plano.
- Definir cómo se trasladará el contenido cifrado entre instalaciones.
- La clave de cifrado de la aplicación NO debe incluirse dentro del backup.

10. MOVIMIENTOS
- Todos los movimientos históricos.
- Tipo de gasto.
- Proveedor.
- Centro Operativo.
- Recurso Operativo.
- Importes.
- Fechas.
- Estados.
- Datos fiscales.
- Archivos/facturas adjuntas.

11. PAGOS
- Todos los pagos asociados a movimientos.
- Medios de pago.
- Importes.
- Fechas.
- Bancos.
- Comprobantes.
- Cheques/e-Cheqs relacionados.

12. PLANES DE PAGO
- Condiciones del plan.
- Saldo financiado.
- Tasas.
- Cantidad de cuotas.

13. CUOTAS
- Capital.
- Interés.
- Impuestos.
- Vencimiento.
- Punitorios.
- Estado.
- Pagos y comprobantes relacionados.

14. VENCIMIENTOS
- Pendientes y finalizados.
- Origen.
- Fecha.
- Importe.
- Estado.

15. ALERTAS
- Configuración de anticipación.
- Estado de alertas cuando corresponda.
- Configuración general de la empresa.

16. ARCHIVOS ADJUNTOS
- Facturas.
- Comprobantes.
- Documentación.
- Todo archivo relacionado con entidades exportadas.


RELACIONES

Al importar una empresa deben reconstruirse correctamente todas las relaciones.

No se debe depender de que los IDs de la base original coincidan con los
IDs de la nueva base.

La importación debe crear mapas entre IDs originales y nuevos IDs.

Ejemplo:

Centro original ID 16
        ↓
Centro nuevo ID 4

Todo Recurso Operativo que apuntaba al Centro 16 debe pasar a apuntar
al Centro 4.


DATOS INACTIVOS

Los registros dados de baja lógicamente también forman parte del backup.

Ejemplos:
- Centro Operativo cerrado.
- Recurso Operativo inactivo.
- Proveedor inactivo.
- Tipo de gasto inactivo.

Se conservan porque pueden participar en información histórica.


SEGURIDAD

Nunca incluir:
- SECRET_KEY de Django.
- Claves maestras de cifrado.
- Variables de entorno del servidor.
- Credenciales de infraestructura.
- Contraseñas en texto plano.

Los backups deben considerarse información sensible.


COMPATIBILIDAD

La exportación debe incluir un número de versión del formato.

Ejemplo:

{
    "formato": "ordenaclick_empresa",
    "version": 1
}

Si el formato cambia en el futuro, Importar Empresa debe poder detectar
la versión y actuar en consecuencia.


REGLA PARA DESARROLLO FUTURO

Cada vez que se cree o modifique un modelo relacionado con Empresa,
se debe revisar este documento y responder:

1. ¿Debe exportarse?
2. ¿Debe importarse?
3. ¿Tiene archivos?
4. ¿Tiene relaciones que deban reconstruirse?
5. ¿Contiene información sensible?
6. ¿Hay que mantener registros inactivos?
7. ¿Afecta compatibilidad con backups anteriores?

La funcionalidad Exportar/Importar Empresa no se considera completa
hasta que todas las entidades definidas en este documento estén cubiertas.


RETENCIONES DE PAGO
- Tipo de retención.
- Importe.
- Comprobante/certificado.
- Pago relacionado.

CHEQUES / E-CHEQS
- Todos los datos del instrumento.
- Pago relacionado.
- Banco.
- Fechas.
- Estado.
- Vencimiento relacionado.

ORDENES DE PAGO (futuro)
- Cabecera.
- Documentos cancelados.
- Pagos relacionados.
- Retenciones.
- Comprobantes.

CUENTAS BANCARIAS

- Empresa.
- Banco.
- Nombre de la cuenta.
- Tipo de cuenta.
- Moneda.
- Número de cuenta.
- CBU.
- Alias.
- Estado activo/inactivo.

Las Cuentas Bancarias forman parte del entorno Empresa.

Al importar deben reconstruirse correctamente sus relaciones con:

- Transferencias.
- Cheques/e-Cheqs propios.
- Planes con débito automático.
- Vencimientos relacionados.
- Futuras operaciones bancarias.


APLICACIONES DE PAGO

- Pago relacionado.
- Movimiento o Cuota cancelada.
- Importe aplicado.

Las aplicaciones deben exportarse e importarse preservando las relaciones.

Al importar deben reconstruirse después de haber reconstruido:
- Pagos.
- Movimientos.
- Planes.
- Cuotas.
```


## FUENTE: TODO.md

```text



Futuras funciones de Ordenaclick:
Listado de cheques en cartera
Agenda
Generar Orden de pago
Autorizacion de operaciones
Agenda de Claves ( Habia un nombre )
Funcion VER INACTIVOS para Abms Borrados ( Que en realidad fueron desactivados para no romper nada) y Poder volver a Activar


Mejoras esteticas: 

---
Que el sidebar y el menu operativo tengan un scroll distinto. No es escencial, pero estaria bueno que si elijo algo de la botonera del sidebar el menu operativo se muestre desde arriba o a la inversa si estoy bajando en el menu operativo  hasta muy abajo no me desaparesca la botonera del sidebar porque quedo arriba
---

Buscador dinámico en listados de tarjetas de todos los ABM.

---
```


## FUENTE: Arquitectura Panel_admin.txt

```text

ORDENACLICK
│
├── Login
│		├── Selección de Rol
│		│		├ADMINISTRADOR
│		│		│	├Alta nueva empresa
│		│		│	├Seleccionar Empresa
│		│		│	│	├Empresa Seleccionada
│		│		│	│	│	├ Registros
│		│		│ 	│  	│	│	├ Carga Simple
│		│		│	│	│	│	├ Carga Planificada
│		│		│	│	│	│	├ Registrar Pago
│		│		│	│	│	│	└ Modificar / Eliminar
│		│		│	│	│	├ Dashboard
│		│		│	│	│	├ Próximos Vencimientos
│		│		│	│	│	├ Reportes
│		│		│	│	│	├ Estado de Resultados
│		│		│	│	│	├ Balance
│		│		│	│	│	├ ABMs
│		│		│	│	│	│	├ Centros Operativos
│		│		│	│	│	│	├ Recursos Operativos
│		│		│	│	│	│	│	├ Personas
│		│		│	│	│	│	│	├ Vehiculos
│		│		│	│	│	│	│	├ Inmuebles
│		│		│	│	│	│	│	├ Equipos
│		│		│	│	│	│	│	└  Otros
│		│		│	│	│	│	├ Tipos de Gastos
│		│		│	│	│	│	│	├ Proveedores relacionados
│		│		│	│	│	│	│	└  Cuenta Contable (futuro)
│		│		│	│	│	│	├ Proveedores
│		│		│	│	│	│	└ Plan Contable (antes Cuentas)
│		│		│	│	│	├ Configuración
│		│		│	│	│	│	├ Modificar Empresa
│		│		│	│	│	│	└ Designar Colaboradores
│		│		│	│	│	├ Cambiar Empresa
│		│		│	│	│	└ Volver a inicio
│		│		│	│	└Volver
│		│		│	├ Volver a roles (Este vuelve a la selección de roles)
│		│		│	└ CERRAR SESION (Este cierra hasta el Loguin y carga la primer pantalla de Ordenaclick)
│		│		├COLABORADOR
│		│		│	├Submenu a desarrollar (Se postula o acepta solicitudes para trabajar con empresas)
│		│		│	├Seleccionar Empresa (El listado sale de empresas que acepto o lo aceptaron del submenú anterior)
│		│		│	│	├Empresa Seleccionada
│		│		│	│	│	├ Registros
│		│		│ 	│  	│	│	├ Carga Simple
│		│		│	│	│	│	├ Carga Planificada
│		│		│	│	│	│	├ Registrar Pago
│		│		│	│	│	│	└ Modificar / Eliminar
│		│		│	│	│	├ Dashboard (Admin decide si oculta en permisos)
│		│		│	│	│	├ Próximos Vencimientos (Admin decide si oculta en permisos)
│		│		│	│	│	├ Reportes (Admin decide si oculta en permisos)
│		│		│	│	│	├ Estado de Resultados (Admin decide si oculta en permisos)
│		│		│	│	│	├ Balance (Admin decide si oculta en permisos)
│		│		│	│	│	├ ABMs (Admin decide si oculta en permisos)
│		│		│	│	│	│	├ Centros Operativos
│		│		│	│	│	│	├ Recursos Operativos
│		│		│	│	│	│	│	├ Personas
│		│		│	│	│	│	│	├ Vehiculos
│		│		│	│	│	│	│	├ Inmuebles
│		│		│	│	│	│	│	├ Equipos
│		│		│	│	│	│	│	└  Otros
│		│		│	│	│	│	├ Tipos de Gastos
│		│		│	│	│	│	│	├ Proveedores relacionados
│		│		│	│	│	│	│	└  Cuenta Contable (futuro)
│		│		│	│	│	│	├ Proveedores
│		│		│	│	│	│	└ Plan Contable (antes Cuentas)
│		│		│	│	│	├ Configuración (si o si oculto)
│		│		│	│	│	│	├ Modificar Empresa
│		│		│	│	│	│	└ Designar Colaboradores
│		│		│	│	│	├ Cambiar Empresa
│		│		│	│	│	└ Volver a inicio
│		│		│	│	└Volver
│		│		│	├ Volver a roles (Este vuelve a la selección de roles)
│		│		│	└ CERRAR SESION (Este cierra hasta el Loguin y carga la primer pantalla de Ordenaclick)
│		│		├CONTADOR/ES
│		│		│	├Submenu a desarrollar (Donde se postula o acepta solicitudes para trabajar con empresas)
│		│		│	│
│		│		│	├Seleccionar Empresa (El listado no sale de empresas que creo el sino de las que acepto o lo aceptaron del submenú anterior)
│		│		│	│	├Empresa Seleccionada
│		│		│	│	│	├ Registros
│		│		│ 	│  	│	│	├ Carga Simple
│		│		│	│	│	│	├ Carga Planificada
│		│		│	│	│	│	├ Registrar Pago
│		│		│	│	│	│	└ Modificar / Eliminar
│		│		│	│	│	├ Dashboard (Admin decide si oculta en permisos)
│		│		│	│	│	├ Próximos Vencimientos (Admin decide si oculta en permisos)
│		│		│	│	│	├ Reportes (Admin decide si oculta en permisos)
│		│		│	│	│	├ Estado de Resultados (Admin decide si oculta en permisos)
│		│		│	│	│	├ Balance (Admin decide si oculta en permisos)
│		│		│	│	│	├ ABMs (Admin decide si oculta en permisos)
│		│		│	│	│	│	├ Centros Operativos
│		│		│	│	│	│	├ Recursos Operativos
│		│		│	│	│	│	│	├ Personas
│		│		│	│	│	│	│	├ Vehiculos
│		│		│	│	│	│	│	├ Inmuebles
│		│		│	│	│	│	│	├ Equipos
│		│		│	│	│	│	│	└  Otros
│		│		│	│	│	│	├ Tipos de Gastos
│		│		│	│	│	│	│	├ Proveedores relacionados
│		│		│	│	│	│	│	└  Cuenta Contable (futuro)
│		│		│	│	│	│	├ Proveedores
│		│		│	│	│	│	└ Plan Contable (antes Cuentas)
│		│		│	│	│	├ Configuración (Admin decide si oculta en permisos)
│		│		│	│	│	│	├ Modificar Empresa
│		│		│	│	│	│	└ Designar Colaboradores
│		│		│	│	│	├ Cambiar Empresa
│		│		│	│	│	└ Volver a inicio
│		│		│	│	└Volver
│		│		│	├ Volver a roles (Este vuelve a la selección de roles)
│		│		│	└ CERRAR SESION (Este cierra hasta el Loguin y carga la primer pantalla de Ordenaclick)
│		│		├ABOGADO/S (Vera casos y posiblemente algo de lo contable... por ahora a desarrollar)
│		│		├MODIFICAR DATOS PERSONALES
│		│		└CERRAR SESION
x	└Registrarse
```


## FUENTE: Arquitectura_Movimientos_Pagos_Vencimientos_Alertas.txt

```text
=========================================================
ORDENACLICK
ARQUITECTURA DE MOVIMIENTOS, PAGOS,
VENCIMIENTOS Y ALERTAS
=========================================================


=========================================================
1. OBJETIVO CENTRAL DE ORDENACLICK
=========================================================

OrdenaClick debe ayudar a que el dueño de la empresa no pierda control
sobre pagos, cuotas, cheques y vencimientos, y al mismo tiempo generar
información ordenada y útil para la gestión y la contabilidad.

El sistema no debe limitarse a registrar lo que ya ocurrió.

Debe ayudar activamente a impedir que el usuario olvide obligaciones
económicas futuras.

Especialmente:

- Facturas pendientes.
- Cuotas.
- Cheques propios.
- e-Cheqs propios.
- Valores en cartera.
- Cualquier compromiso económico con fecha futura.

"Próximos vencimientos" y "Alertas" NO son agregados posteriores.

Deben nacer como una parte central de la arquitectura porque distintos
módulos del sistema alimentarán el mismo motor.

Conceptualmente:

MOVIMIENTOS / PAGOS / PLANES / CHEQUES
                    │
                    ▼
              VENCIMIENTOS
                    │
                    ▼
                 ALERTAS


La parte contable constituye otra pata central de OrdenaClick.

Pero Vencimientos y Alertas representan una de las funcionalidades
principales del producto desde el punto de vista del dueño de la empresa.


=========================================================
2. PRINCIPIOS GENERALES DE DISEÑO
=========================================================

1. Registrar un Movimiento y registrar su Pago son hechos diferentes.

2. Un Movimiento puede existir:
   - Sin pago.
   - Con pago parcial.
   - Con pago total.
   - Convertido a Plan de Pago.
   - Con pagos previos antes de convertirse en Plan.

3. Los Pagos deben ser entidades independientes.

4. Un Movimiento puede tener múltiples Pagos.

5. Un Pago puede estar compuesto simultáneamente por diferentes formas
   de cancelación.

6. Vencimiento y Alerta son conceptos diferentes.

7. El Vencimiento representa el compromiso real.

8. La Alerta representa cuándo y cómo se avisa al usuario.

9. Una Alerta nunca debe modificar ni eliminar el Vencimiento.

10. La información económica debe conservar histórico.

11. Pagar, cancelar o vencer una obligación no debe borrar su historia.

12. Los registros con impacto histórico, contable o financiero no deben
    borrarse físicamente durante el funcionamiento normal del sistema.

13. Próximos Vencimientos debe trabajar sobre una fuente común de
    Vencimientos y no implementar una lógica diferente para cada módulo.

14. Todo evento que tenga una fecha futura económicamente relevante debe
    poder generar un Vencimiento.

15. Toda nueva funcionalidad relacionada con obligaciones futuras debe
    evaluarse respecto del sistema común de Vencimientos y Alertas.

16. Toda nueva entidad perteneciente al entorno Empresa debe evaluarse
    respecto de Exportación / Importación de Empresa.


=========================================================
3. PAGO
=========================================================

Para la estructura funcional, interfaz, medios de pago disponibles
y comportamiento general del bloque Pagos:

VER:
Arquitectura Panel_admin.txt


ACLARACIONES DE ARQUITECTURA DE PAGOS

1. Un Pago representa un acto de cancelación total o parcial
   de un Movimiento.

2. Un Movimiento puede recibir uno o múltiples Pagos.

3. Un mismo Pago puede estar compuesto simultáneamente por
   diferentes medios de pago según lo definido en
   Arquitectura Panel_admin.txt.

4. La suma de los importes APLICADOS de todos los componentes
   determina el importe total aplicado por ese Pago.

5. El saldo del Movimiento se calcula sobre los importes
   efectivamente aplicados:

   Saldo nuevo =
   Saldo anterior - Pago aplicado.

6. Los costos financieros asociados a un medio de pago
   no deben confundirse con el importe aplicado al Movimiento.

   Ejemplos:

   - Intereses de financiación de Tarjeta de Crédito.
   - Intereses por mora.
   - Otros intereses o costos financieros que se incorporen.

   Estos importes incrementan el costo económico para la Empresa,
   pero NO incrementan el importe cancelado del Movimiento.

7. Registrar un Movimiento y registrar un Pago son eventos
   independientes.

   Un Movimiento puede existir:

   - Sin pagos.
   - Con pago parcial.
   - Con pago total.
   - Con múltiples pagos.
   - Con diferentes medios dentro de un mismo Pago.

8. Los Pagos deben conservar histórico y relación con el
   Movimiento al que fueron aplicados.

9. La información específica de cada medio de pago se desarrolla
   en las secciones siguientes de este documento únicamente cuando
   exista una regla económica, histórica, de vencimientos o de
   arquitectura que sea necesario preservar.

   La definición de interfaz y funcionamiento visual corresponde a:

   Arquitectura Panel_admin.txt


=========================================================
4. MOVIMIENTO
=========================================================

El Movimiento representa el gasto o documento original.

Debe conservar como mínimo:

- Empresa.
- Ejercicio.
- Tipo de gasto.
- Proveedor.
- Centro Operativo.
- Recurso Operativo.
- Fecha de registro.
- Fecha de vencimiento original cuando corresponda.
- Datos del comprobante.
- Descripción.
- Importes.
- Impuestos.
- Percepciones.
- Total.
- Factura / archivo adjunto.
- Estado.
- Observaciones.


CENTRO OPERATIVO Y RECURSO OPERATIVO

Ambos deben quedar guardados históricamente dentro del Movimiento.

No deben deducirse posteriormente desde el estado actual del Recurso.

Ejemplo:

Si CAMIONETA 01 pertenecía a CASA CENTRAL cuando ocurrió un gasto y
posteriormente se traslada a SUCURSAL AZUL, el Movimiento histórico debe
seguir indicando CASA CENTRAL.


El backend debe validar que:

- El Centro Operativo pertenece a la Empresa activa.
- El Recurso Operativo pertenece a la Empresa activa.
- El Recurso pertenece al Centro seleccionado.


ESTADOS PREVISTOS DEL MOVIMIENTO

- Pendiente.
- Parcial.
- Pagado.
- Vencido.
- Cancelado.


=========================================================
5. FLUJO DE CARGA SIMPLE
=========================================================

La sección principal de Datos del Gasto debe permanecer estable.

Una vez finalizada esta etapa del desarrollo debe evitarse modificarla
salvo necesidad funcional real.


Debe contener, entre otros:

- Tipo de gasto.
- Proveedor.
- Centro Operativo.
- Recurso Operativo.
- Datos del comprobante.
- Fecha.
- Descripción.
- Importes.
- Impuestos.
- Percepciones.
- Total del Registro.
- Factura / archivo adjunto.


Al lado de Total del Registro existe:

[ 📎 Factura ]


La Factura pertenece al Movimiento, NO al Pago.


Debajo de los Datos del Gasto debe existir la botonera:

[ Guardar ] [ Cargar pago ] [ Convertir a plan ] [ Cancelar ]


---------------------------------------------------------
GUARDAR
---------------------------------------------------------

Permite registrar el Movimiento sin necesidad de registrar ningún Pago.

Ejemplo:

Movimiento: $100.000
Pagado:     $0
Saldo:      $100.000
Estado:     Pendiente


---------------------------------------------------------
CARGAR PAGO
---------------------------------------------------------

Muestra el bloque de carga de Pago.

La botonera principal continúa disponible debajo del bloque.

El Movimiento puede recibir un Pago total o parcial.


---------------------------------------------------------
CONVERTIR A PLAN
---------------------------------------------------------

Muestra el bloque de Plan de Pago.

Si el bloque de Pago estuviera desplegado, visualmente puede ocultarse.

Los Pagos ya registrados o cargados NO se pierden.

El saldo a financiar será:

Saldo a financiar =
Total del Movimiento - Pagos aplicados previamente.


Si no existen Pagos:

Saldo a financiar =
Total del Movimiento.


---------------------------------------------------------
CANCELAR
---------------------------------------------------------

Cancela la operación de carga actual según las reglas de interfaz
definidas para el sistema.


=========================================================
6. TARJETAS DE CRÉDITO / DÉBITO
=========================================================

Las Tarjetas constituyen componentes independientes del Pago.

No se modelará inicialmente el plástico individual, titular,
fecha de vencimiento ni asignación a una persona/recurso operativo.

El objetivo de esta etapa es identificar el medio financiero utilizado
para luego poder controlar movimientos y conciliarlos contra los
resúmenes o cuentas correspondientes.


ABM DE TARJETAS

Debe existir un ABM de Tarjetas perteneciente a la Empresa.

Cada Tarjeta debe contener como mínimo:

- Nombre.
  Ejemplos:
  VISA GALICIA
  MASTERCARD NACIÓN
  CABAL CREDICOOP

- Tipo:
  - Crédito.
  - Débito.

- Cuenta bancaria propia asociada.

- Estado:
  - Activa.
  - Inactiva.


La Cuenta Bancaria asociada debe provenir del mismo ABM de
Cuentas Bancarias propias utilizado por otros medios de pago.

No se registrarán inicialmente:

- Titular.
- Número completo del plástico.
- Últimos cuatro dígitos.
- Fecha de vencimiento del plástico.
- Recurso Operativo asignado.

Estas relaciones podrán incorporarse posteriormente si el nivel
de control requerido lo justifica.


REGISTRO DENTRO DE UN PAGO

Un Pago puede contener una o varias operaciones realizadas con Tarjeta.

Cada operación debe registrar como mínimo:

- Tarjeta.
- Fecha.
- Importe aplicado al Movimiento.

Cuando la Tarjeta sea de Crédito deberá permitir además:

- Cantidad de cuotas.
- Intereses de financiación, cuando existan.


IMPORTE APLICADO E INTERESES

El importe aplicado mediante Tarjeta cancela total o parcialmente
el saldo del Movimiento.

Los intereses de financiación NO aumentan el importe aplicado
al Movimiento.

Ejemplo:

Movimiento / gasto:           $ 100.000
Pago aplicado con tarjeta:    $ 100.000
Intereses financiación:        $ 18.000
Costo financiero adicional:    $ 18.000

Saldo pendiente Movimiento:         $ 0

Los intereses representan un costo financiero adicional para
la Empresa y deberán conservarse diferenciados del importe aplicado.

Conceptualmente:

Importe aplicado al Movimiento
+
Intereses de financiación
=
Costo total de la operación financiera.


TARJETA DE DÉBITO

La Tarjeta de Débito se relaciona igualmente con una Cuenta Bancaria propia.

No requiere cuotas ni intereses de financiación como parte normal
del registro.

El importe registrado se considera importe aplicado al Movimiento.


TARJETA DE CRÉDITO

La Tarjeta de Crédito se relaciona con una Cuenta Bancaria propia.

Debe permitir registrar:

- Importe aplicado.
- Cantidad de cuotas.
- Intereses de financiación.

La cantidad de cuotas es un dato propio de la operación realizada
con Tarjeta y no debe confundirse con las Cuotas de un Plan de Pago
del Movimiento.


CONTROL Y REPORTES

La relación entre Tarjeta y Cuenta Bancaria permitirá posteriormente:

- Consultar movimientos registrados por Tarjeta.
- Obtener un detalle por período.
- Comparar movimientos cargados contra un resumen de Tarjeta.
- Controlar que los gastos incluidos en un resumen hayan sido registrados.
- Obtener totales de financiación e intereses asociados.

El Recurso Operativo que originó el gasto no debe confundirse con
la persona que eventualmente utilizó una Tarjeta para cancelarlo.

Ejemplo:

Un empleado puede originar un gasto en cuenta corriente y posteriormente
otra persona puede cancelarlo mediante una Tarjeta corporativa.

Por ese motivo, en esta etapa no existe una relación obligatoria
entre Tarjeta y Recurso Operativo.


INTERESES Y COSTOS FINANCIEROS

Los intereses derivados del uso de Tarjetas deben tratarse como
costos financieros adicionales.

Este criterio deberá ser compatible en el futuro con otros costos
financieros, por ejemplo:

- Intereses de financiación.
- Intereses por mora.
- Intereses punitorios cuando corresponda.

Estos importes deben poder identificarse separadamente para no alterar
incorrectamente el saldo cancelado del Movimiento.


HISTÓRICO

Las operaciones realizadas con Tarjetas forman parte de la historia
del Pago y no deben perderse por modificaciones posteriores del ABM.

El registro debe conservar la información necesaria para reconstruir
qué Tarjeta fue utilizada y bajo qué condiciones se realizó la operación.


EXPORTACIÓN / IMPORTACIÓN

El ABM de Tarjetas y las operaciones de Tarjeta vinculadas a Pagos
deben incluirse en Exportar/Importar Empresa.


=========================================================
7. EFECTIVO
=========================================================

El Efectivo constituye un componente propio del Pago.

Debe registrar su importe independientemente de los demás componentes.

No debe agruparse conceptualmente con Transferencias, Tarjetas,
Cheques ni Retenciones.


=========================================================
8. TRANSFERENCIAS
=========================================================

Un Pago puede contener UNA O VARIAS Transferencias.

Esto es obligatorio porque una empresa puede completar un mismo Pago
utilizando dinero disponible en distintas cuentas bancarias.


Cada Transferencia debe contemplar como mínimo:

- Banco / cuenta de origen.
- Importe.
- Fecha.
- Referencia / número de operación.
- Comprobante.
- Observaciones cuando corresponda.


Ejemplo:

Pago $500.000

Transferencia Galicia    $300.000
Transferencia Nación     $200.000


Ambas forman parte del mismo Pago.


=========================================================
9. TARJETA
=========================================================

Tarjeta constituye otro componente independiente del Pago.

Inicialmente se prevé una Tarjeta por Pago.

Debe poder registrar como mínimo:

- Importe.
- Identificación / referencia.
- Comprobante.
- Información adicional que se defina durante su implementación.


No debe agruparse en una entidad genérica junto con Efectivo o
Transferencias.


=========================================================
10. RETENCIONES
=========================================================

Las Retenciones forman parte del importe aplicado al Pago.

Un Pago puede contener múltiples Retenciones.


La interfaz debe utilizar un sistema similar al desplegable de
Percepciones existente en Datos del Gasto.


Cada Retención debe registrar:

- Tipo de Retención.
- Importe.
- Comprobante / certificado.
- Archivo relacionado.


Al lado de cada Retención debe existir un botón para adjuntar
su comprobante.


Ejemplo:

Retención Ganancias    $50.000   [ 📎 Comprobante ]
Retención IIBB         $20.000   [ 📎 Comprobante ]


Los tipos exactos de Retenciones se definirán durante la implementación.


=========================================================
11. CHEQUES / E-CHEQS
=========================================================

Un Pago puede contener múltiples Cheques y/o e-Cheqs.

Cada instrumento debe existir como entidad independiente.


Debe contemplar como mínimo:

- Tipo: Cheque / e-Cheq.
- Propio / tercero.
- Banco.
- Número.
- Importe.
- Fecha de emisión.
- Fecha de acreditación / débito / vencimiento según corresponda.
- Origen.
- Persona o empresa que lo entregó cuando corresponda.
- Estado.
- Pago relacionado.
- Información adicional necesaria.


---------------------------------------------------------
CHEQUE / E-CHEQ PROPIO
---------------------------------------------------------

Cuando un Cheque propio se utiliza como forma de Pago ocurren DOS hechos
diferentes.


HECHO 1

El importe se aplica inmediatamente a la cancelación total o parcial
del Movimiento.


HECHO 2

Se genera una obligación futura para la Empresa.

Por lo tanto, el Cheque debe generar automáticamente un Vencimiento.


Ejemplo:

Factura proveedor: $300.000

Se paga con:

Cheque propio: $300.000


El Movimiento puede quedar:

PAGADO


Pero simultáneamente debe existir:

Vencimiento
Tipo: Cheque propio
Importe: $300.000
Banco: correspondiente
Fecha: fecha de débito/presentación


Esto permitirá generar:

🔔 En 3 días se debita cheque de $300.000
   Banco Galicia


El objetivo es que el usuario recuerde disponer del dinero necesario
en la cuenta.


---------------------------------------------------------
CHEQUES / E-CHEQS DE TERCEROS
---------------------------------------------------------

También deben existir como entidades independientes.

Inicialmente podrán participar de Pagos.

En una etapa futura formarán parte de:

CARTERA DE VALORES


Los Cheques/e-Cheqs en cartera deberán utilizar el MISMO motor de
Vencimientos y Alertas.


Ejemplo futuro:

Cheque de tercero
Importe: $150.000
Fecha: 25/09/2026

        ↓

Vencimiento

        ↓

🔔 Cheque en cartera próximo a depositar/cobrar

=========================================================
VENCIMIENTO DE CHEQUES / E-CHEQS
=========================================================
Los Cheques y e-Cheqs pueden alcanzar estado VENCIDO.

Esto aplica tanto a instrumentos propios como de terceros.

Ejemplos:

- Cheque de tercero que permaneció en cartera y no fue
  depositado/cobrado dentro del plazo correspondiente.

- Cheque propio cuya fecha llegó pero cuyo débito/presentación
  todavía no fue confirmado.

La llegada de la fecha NO implica automáticamente:

- Debitado.
- Cobrado.
- Depositado.

El estado financiero real del instrumento debe conservarse
separado del hecho de haber alcanzado su vencimiento.

El sistema de Vencimientos y Alertas debe advertir previamente
estas situaciones para intentar evitar que ocurran.
=========================================================
12. PLAN DE PAGO
=========================================================

Un Movimiento puede convertirse total o parcialmente en Plan de Pago.


El capital inicial del Plan será:

Saldo pendiente del Movimiento.


Por lo tanto:

Capital a financiar =
Total Movimiento - Pagos previamente aplicados.


El Plan debe permitir definir como mínimo:

- Cantidad de cuotas.
- Fecha del primer vencimiento.
- Periodicidad.
- Interés.
- Impuestos.
- Condiciones adicionales que se definan durante la implementación.


A partir de estos datos debe generarse automáticamente la grilla de Cuotas.


=========================================================
13. CUOTAS
=========================================================

Cada Cuota es una entidad independiente.

NO es simplemente una fila dibujada en pantalla.


Debe contener como mínimo:

- Número de cuota.
- Capital.
- Interés.
- Impuesto.
- Fecha de vencimiento.
- Intereses punitorios.
- Total.
- Estado.
- Pago/s relacionados.
- Comprobante cuando corresponda.


Ejemplo:

Cuota | Capital | Interés | Impuesto | Vencimiento | Punitorios | Total
1     | 1000    | 100     | 21       | 01/09/2026  | 0          | 1121
2     | 1000    | 100     | 21       | 01/10/2026  | 0          | 1121


Cada Cuota debe generar automáticamente un Vencimiento.


---------------------------------------------------------
PUNITORIOS
---------------------------------------------------------

Los Intereses Punitorios NO deben fijarse definitivamente cuando se
crea el Plan.

Al crear una Cuota:

Punitorios = 0


Se calcularán cuando corresponda según:

- Fecha de vencimiento.
- Fecha real de Pago.
- Días de atraso.
- Reglas de punitorios definidas.


Debe preservarse la posibilidad futura de distinguir:

- Capital.
- Interés financiero.
- Impuesto sobre interés.
- Interés punitorio.
- Impuesto sobre punitorio.


=========================================================
14. PAGO DE CUOTAS
=========================================================

Una Cuota debe poder recibir Pagos.

El Pago de una Cuota utilizará la misma arquitectura general de Pagos.

Esto evita construir dos sistemas diferentes:

- Pago normal de Movimiento.
- Pago de Cuota.


Debe reutilizarse la misma lógica siempre que sea posible.


Inicialmente una Cuota pendiente puede mostrar:

[ Registrar pago ]


Una vez pagada:

[ Ver comprobante ]


Los pagos parciales de Cuotas deberán conservarse históricamente.


=========================================================
15. VENCIMIENTOS
=========================================================

Vencimientos constituye una CAPA CENTRAL del sistema.


Un Vencimiento representa un compromiso económico u operativo real.


Debe contener conceptualmente:

- Empresa.
- Origen.
- Entidad relacionada.
- Fecha real de vencimiento.
- Importe original.
- Importe pendiente.
- Estado.
- Información necesaria para identificar el compromiso.


Pueden generar Vencimientos:

- Movimientos pendientes.
- Cuotas de Planes.
- Cheques propios.
- e-Cheqs propios.
- Futuros Cheques/e-Cheqs en cartera.
- Otros compromisos económicos futuros.


ESTADOS MÍNIMOS:

- Pendiente.
- Pagado.
- Cancelado.
- Vencido.


Los Vencimientos deben conservar histórico.


---------------------------------------------------------
PAGO PARCIAL
---------------------------------------------------------

Si una obligación recibe un Pago parcial:

- NO desaparece.
- Continúa pendiente.
- Se actualiza su importe pendiente.
- El Movimiento relacionado puede pasar a PARCIAL.
- Continúa formando parte del sistema de Vencimientos.


Ejemplo:

Vencimiento original: $100.000
Pago:                  $ 40.000

Nuevo pendiente:       $ 60.000


Las Alertas futuras deberán reflejar:

$60.000 pendientes


y no el importe original de $100.000.


---------------------------------------------------------
PAGO TOTAL
---------------------------------------------------------

Cuando:

Importe pendiente = 0


el Vencimiento pasa a:

PAGADO


Deja de formar parte de las Alertas activas.

NO desaparece del histórico.


=========================================================
16. ALERTAS
=========================================================

Una Alerta NO es un Vencimiento.


VENCIMIENTO

Representa:

"Esto debe pagarse / cobrarse / atenderse en esta fecha."


ALERTA

Representa:

"Recordarle al usuario este compromiso en determinada fecha."


La anticipación inicial prevista será:

3 días antes.


Ejemplo:

Vencimiento: 15/08/2026
Anticipación: 3 días

Alerta desde: 12/08/2026


En el futuro la anticipación deberá poder configurarse:

- 3 días.
- 5 días.
- 7 días.
- El mismo día.
- Otros valores.


Debe contemplarse configuración general por Empresa y eventualmente
configuración particular por Vencimiento.


ESTADOS / COMPORTAMIENTOS PREVISTOS:

- Activa.
- Atendida.
- Reprogramada.
- Cancelada.


=========================================================
17. ALERTAS VENCIDAS
=========================================================

Si llega la fecha real del Vencimiento y la obligación continúa pendiente,
el registro NO desaparece.

El Vencimiento pasa a:

VENCIDO


Debe continuar disponible para el usuario.


Ejemplo:

🔴 Cuota vencida

Proveedor: X
Pendiente: $125.000
Venció: 01/09/2026

[ Registrar pago ]
[ Reprogramar alerta ]
[ Cancelar alerta ]


---------------------------------------------------------
REPROGRAMAR ALERTA
---------------------------------------------------------

Reprogramar una Alerta NO modifica la fecha real del Vencimiento.


Ejemplo:

Vencimiento real: 01/09/2026

El usuario solicita:

Recordar nuevamente: 05/09/2026


El sistema debe conservar:

Vencimiento real: 01/09/2026
Estado: VENCIDO
Nueva alerta: 05/09/2026


Por lo tanto podrá determinar que el compromiso lleva cuatro días vencido.


---------------------------------------------------------
CANCELAR ALERTA
---------------------------------------------------------

Cancelar una Alerta significa:

"No volver a avisarme sobre este compromiso."


NO significa:

"Eliminar o cancelar automáticamente el Vencimiento."


Es perfectamente válido:

Vencimiento = VENCIDO
Alerta = CANCELADA


El compromiso debe seguir apareciendo en históricos e informes.


=========================================================
18. PRÓXIMOS VENCIMIENTOS
=========================================================

Próximos Vencimientos constituye una funcionalidad central de OrdenaClick.


Debe existir como opción del Sidebar:

[ Próximos vencimientos ]


NO debe consultar por separado:

- Cuotas.
- Cheques.
- Facturas.
- Planes.
- etc.


Debe consultar la capa común:

VENCIMIENTOS


Conceptualmente:

"Dame los vencimientos de esta Empresa dentro del período seleccionado."


Debe permitir filtros como mínimo por:

- Próximos.
- Pendientes.
- Vencidos.
- Pagados.
- Cancelados.


En Informes deberá existir específicamente el filtro:

VENCIDAS


Una obligación vencida debe poder encontrarse allí aunque su Alerta
haya sido reprogramada o cancelada.


=========================================================
19. CAMPANITA / CENTRO DE ALERTAS
=========================================================

Debe existir una notificación visible en la interfaz.


Ejemplo:

🔔 3


El número representa:

ALERTAS ACTIVAS / RELEVANTES


NO representa todos los Vencimientos históricos.


Ejemplo de contenido:

Vence mañana
Cuota 2 - Proveedor X
$125.000


En 2 días
Cheque propio - Banco Nación
$500.000


En 3 días
Cuota 4 - Leasing camioneta
$80.000


Desde cada Alerta debe poder accederse al registro relacionado.


La Campanita representa el aviso inmediato.

Próximos Vencimientos representa la vista completa de gestión.


=========================================================
20. HISTÓRICO
=========================================================

La información económica debe conservarse.


No deben borrarse físicamente como parte del funcionamiento normal:

- Movimientos.
- Pagos.
- Transferencias.
- Retenciones.
- Cheques.
- e-Cheqs.
- Planes.
- Cuotas.
- Vencimientos.
- Alertas.
- Comprobantes relacionados.


Cuando corresponda deben utilizarse:

- Estados.
- Baja lógica.
- Cancelación.


Esto permitirá posteriormente obtener información como:

- Pagos realizados a término.
- Pagos vencidos.
- Días promedio de atraso.
- Historial de pagos parciales.
- Historial de Vencimientos.
- Obligaciones canceladas.
- Alertas reprogramadas.


=========================================================
21. CENTROS Y RECURSOS OPERATIVOS
=========================================================

Los Centros Operativos y Recursos Operativos deben conservar relaciones
históricas con los Movimientos.


Si tienen historia asociada debe preferirse:

INACTIVAR

en lugar de:

BORRAR


El cierre de una sucursal o la baja de un Recurso no debe romper
Movimientos históricos.


=========================================================
22. VERSIONES BÁSICA / MEDIA / FULL
=========================================================

La arquitectura interna NO debe depender de qué campos ve el usuario.


En una futura versión Básica puede ocultarse al usuario:

- Centro Operativo.
- Recurso Operativo.


Pero internamente deben continuar existiendo valores válidos.


Al crear una Empresa se prevé:

Centro Operativo:
CASA CENTRAL


Recurso Operativo:
GENERAL

Tipo:
INMUEBLE

Centro:
CASA CENTRAL


De esta forma todos los Movimientos conservan la misma arquitectura
independientemente de la versión comercial utilizada.


=========================================================
23. ORDEN DE PAGO - FUNCIONALIDAD FUTURA
=========================================================

NO implementar todavía.

Debe quedar prevista arquitectónicamente.


Luego de guardar un Pago podrá mostrarse un modal:

Pago registrado correctamente.

¿Desea generar Orden de Pago?

[ Generar ] [ Ahora no ]


La Orden de Pago deberá poder mostrar como mínimo:

- Empresa.
- Proveedor.
- Documento/s cancelado/s.
- Referencia de qué se está pagando.
- Efectivo.
- Transferencias.
- Tarjeta.
- Cheques/e-Cheqs.
- Retenciones.
- Comprobantes.
- Totales.


En una etapa posterior deberá agregarse como opción independiente
del módulo Registros.


Desde allí deberá ser posible:

- Seleccionar múltiples documentos pendientes.
- Crear una Orden de Pago.
- Aplicar un conjunto de medios de cancelación.
- Cancelar total o parcialmente dichos documentos.


Esta funcionalidad debe reutilizar la arquitectura de Pago existente
y NO crear un segundo sistema independiente.


=========================================================
24. CARTERA DE CHEQUES / E-CHEQS - FUTURO
=========================================================

NO implementar todavía.


En el futuro OrdenaClick deberá poder administrar:

- Cheques de terceros.
- e-Cheqs recibidos.
- Valores disponibles.
- Valores depositados.
- Valores entregados.
- Valores vencidos.


La cartera deberá utilizar el mismo motor de:

VENCIMIENTOS
        ↓
ALERTAS


Ejemplo:

Cheque en cartera
Fecha: 20/09/2026

        ↓

Alerta previa

        ↓

"Recordar depositar/cobrar cheque"


=========================================================
25. EXPORTACIÓN / IMPORTACIÓN DE EMPRESA
=========================================================

Todas las entidades pertenecientes al entorno Empresa definidas en esta
arquitectura deben contemplarse en:

Archivos de proyecto/Reglas_Exportacion_Empresa.txt


Como mínimo:

- Movimientos.
- Facturas adjuntas.
- Pagos.
- Datos de Efectivo cuando corresponda.
- Transferencias.
- Comprobantes de Transferencias.
- Tarjetas.
- Comprobantes de Tarjeta.
- Retenciones.
- Certificados de Retención.
- Cheques.
- e-Cheqs.
- Planes de Pago.
- Cuotas.
- Vencimientos.
- Alertas.
- Futuras Órdenes de Pago.
- Futura cartera de valores.


REGLA OBLIGATORIA:

Cada vez que durante el desarrollo se agregue una nueva entidad
relacionada con Empresa se debe revisar inmediatamente:

Reglas_Exportacion_Empresa.txt


y determinar:

1. Si debe exportarse.
2. Si debe importarse.
3. Qué relaciones deben reconstruirse.
4. Qué archivos deben incluirse.
5. Si contiene información sensible.
6. Si deben conservarse registros inactivos.
7. Cómo afecta backups anteriores.


=========================================================
26. REGLAS PARA DESARROLLO FUTURO
=========================================================

Antes de crear una funcionalidad nueva relacionada con Movimientos,
Pagos o compromisos económicos se debe responder:


1. ¿Genera una obligación futura?

Si la respuesta es sí:

Debe evaluarse si genera VENCIMIENTO.


2. ¿El usuario necesita ser avisado?

Si la respuesta es sí:

Debe utilizar ALERTAS.


3. ¿Tiene fecha económicamente relevante?

Debe evaluarse su integración con Próximos Vencimientos.


4. ¿Puede recibir Pagos parciales?

Debe utilizar la arquitectura común de Pagos y saldos.


5. ¿Tiene archivos o comprobantes?

Deben quedar relacionados con la entidad correcta y contemplarse
en Exportación / Importación.


6. ¿Tiene impacto histórico?

Debe evitarse el borrado físico durante el funcionamiento normal.


7. ¿Pertenece al entorno Empresa?

Debe actualizarse la documentación de Exportación / Importación.


8. ¿Ya existe una entidad que resuelve el mismo problema?

Debe reutilizarse antes de crear un sistema paralelo.


=========================================================
27. REGLA FUNDAMENTAL PARA NO DESVIARSE
=========================================================

El objetivo no es simplemente construir un sistema donde el usuario pueda
cargar gastos.


OrdenaClick debe transformar esos datos en información útil para administrar
la empresa y, principalmente, ayudar a evitar pérdidas y olvidos.


Por eso el diseño debe priorizar:

- No olvidar obligaciones.
- Dar visibilidad de próximos Vencimientos.
- Detectar obligaciones vencidas.
- Evitar cuotas impagas por olvido.
- Evitar Cheques/e-Cheqs propios sin fondos disponibles.
- Recordar valores en cartera que deban depositarse o cobrarse.
- Conservar histórico.
- Facilitar la gestión cotidiana del dueño de la Empresa.
- Generar información ordenada para administración y contabilidad.


Cuando exista una decisión de arquitectura entre resolver algo únicamente
para una pantalla o construirlo de manera reutilizable para el sistema,
debe preferirse la solución reutilizable cuando afecte:

- Movimientos.
- Pagos.
- Saldos.
- Cuotas.
- Cheques/e-Cheqs.
- Vencimientos.
- Alertas.
- Histórico.


ORIGEN FINANCIERO DE LOS VENCIMIENTOS

Los Vencimientos relacionados con movimientos bancarios deben permitir
identificar el Banco y, cuando corresponda, la Cuenta Bancaria afectada.

Esto permitirá filtrar Próximos Vencimientos por:

- Banco.
- Cuenta Bancaria.

Ejemplo:

Banco Galicia

→ Cheques/e-Cheqs propios pendientes.
→ Débitos automáticos pendientes.
→ Otros compromisos futuros asociados a cuentas de Galicia.

HISTÓRICO DE REPROGRAMACIONES

Un Vencimiento puede tener múltiples Alertas.

Cuando una Alerta se reprograma:

- La Alerta anterior no se elimina.
- Pasa a estado REPROGRAMADA.
- Se crea una nueva Alerta ACTIVA para la nueva fecha.

Esto permite conservar histórico de los avisos realizados y de las
decisiones del usuario.

=========================================================
PENDIENTES FUNCIONALES YA DEFINIDOS
=========================================================

1. MÚLTIPLES PAGOS POR MOVIMIENTO

Un Movimiento puede contener cero, uno o múltiples Pagos.

En Carga Simple:

- El Registro constituye la primera etapa visual.
- Debajo del Registro existe una botonera:
  [Guardar registro] [Agregar Pago] [Plan de Pago]

- No debe mostrarse una tarjeta de Pago vacía por defecto.
- Cada vez que se seleccione Agregar Pago se crea una nueva tarjeta:

  Pago 1
  Pago 2
  Pago 3
  ...

- Cada tarjeta de Pago debe:
  - poder plegarse/desplegarse;
  - mostrar su importe total en la cabecera;
  - permitir eliminar/cancelar el Pago;
  - contener sus propios medios de pago;
  - conservar independencia respecto de los demás Pagos.

- Guardar registro guarda el Movimiento y todos los Pagos
  agregados o modificados en la pantalla.


2. PLAN DE PAGO Y PAGOS PREVIOS

Un Movimiento puede convertirse en Plan de Pago después de
haber recibido uno o más Pagos.

El capital inicial del Plan será:

Total del Movimiento
- suma de Pagos previos
= saldo a financiar.

Al convertir a Plan:

- los Pagos anteriores NO se eliminan;
- continúan formando parte del histórico;
- dejan de mostrarse como etapa activa de carga;
- se muestra la tarjeta Plan de Pago;
- Agregar Pago deja de estar disponible para pagos libres sobre
  el Movimiento;
- los pagos posteriores deberán aplicarse a las Cuotas del Plan.


3. ELIMINACIÓN / REVERSIÓN DE PAGOS

Eliminar un Pago existente no debe considerarse solamente una
operación visual.

Debe sincronizar todas las consecuencias que produjo ese Pago.

Como mínimo deberá revisar:

- aplicaciones del Pago;
- saldo del Movimiento;
- Cheques/e-Cheqs relacionados;
- Vencimientos relacionados;
- Alertas relacionadas;
- estados de Plan/Cuotas si correspondiera.

Los registros históricos no deberán desaparecer físicamente salvo
correcciones controladas.


4. FUTURA CARTERA DE CHEQUES / E-CHEQS

Cuando exista el módulo Cartera:

- Un cheque/e-Cheq de tercero recibido deberá poder ingresar a Cartera.
- Si se utiliza para realizar un Pago, deberá quedar relacionado con
  ese Pago.
- Si posteriormente ese Pago se revierte/cancela y el cheque vuelve
  a estar disponible, deberá regresar a Cartera.
- Al volver a Cartera deberán reactivarse o regenerarse, según la
  política que se defina, los Vencimientos y Alertas correspondientes.
- Nunca se deberá crear un segundo motor de alertas para Cartera:
  utilizará Vencimiento + Alerta ya existentes.


5. FUTURO ABM DE CLIENTES

Se incorporará un ABM de Clientes.

En Cheques/e-Cheqs de terceros:

- el campo actual "Quién lo entregó" es temporalmente texto libre;
- cuando exista ABM Clientes deberá reemplazarse o complementarse
  por selección/autocompletado de Cliente;
- debe conservarse el flujo [+] para crear el Cliente sin perder
  el formulario que se estaba completando.


6. SALDO A FAVOR

Debe quedar previsto el caso:

Total del Movimiento < Total de Pagos.

No se resolverá todavía.

El excedente no deberá considerarse simplemente un error.
En el futuro podrá transformarse en saldo a favor/crédito aplicable
a otros documentos u Órdenes de Pago.


7. MODIFICACIÓN DE MOVIMIENTOS Y PAGOS

Cuando se implemente Modificar:

- agregar, modificar o quitar un Pago debe recalcular el saldo;
- modificar/quitar cheques debe sincronizar Vencimientos y Alertas;
- las relaciones históricas deben preservarse;
- toda consecuencia derivada deberá actualizarse de forma coherente.


=========================================================
FLUJO VISUAL Y FUNCIONAL DE PAGO
=========================================================

IMPORTANTE:

La implementación inicial contenía un único bloque fijo
"Datos del Pago".

Ese bloque se reemplaza por tarjetas dinámicas de Pago,
pero SU FLUJO FUNCIONAL NO DEBE PERDERSE.

Un Movimiento puede tener:

- cero Pagos;
- un Pago;
- múltiples Pagos;
- Pagos parciales previos y posteriormente un Plan de Pago.


---------------------------------------------------------
ESTRUCTURA VISUAL
---------------------------------------------------------

La tarjeta principal corresponde exclusivamente al Registro.

Termina en:

Total del Registro + Archivo de Factura

Debajo, fuera de esa tarjeta, se encuentra siempre la botonera:

[Guardar registro] [+ Agregar Pago] [Plan de Pago]

No debe existir una tarjeta Pago vacía por defecto.


Al seleccionar:

[+ Agregar Pago]

se crea una tarjeta independiente:

Pago 1        $ TOTAL        ▼        [Eliminar]

Cada nuevo Pago genera otra tarjeta:

Pago 2
Pago 3
etc.

Cada tarjeta debe poder plegarse/desplegarse individualmente.

El importe mostrado en la cabecera corresponde exclusivamente
a la suma de los medios contenidos en ESE Pago.


---------------------------------------------------------
CONTENIDO DE CADA PAGO
---------------------------------------------------------

Cada Pago es independiente de los demás.

Debe poder contener simultáneamente:

- Efectivo.
- Una o más Transferencias.
- Tarjeta.
- Varios Cheques / e-Cheqs.
- Varias Retenciones.

La suma de esos componentes constituye el importe total del Pago.

Los valores y formularios de un Pago NO deben mezclarse con
los de otro Pago.


---------------------------------------------------------
CHEQUES / E-CHEQS DENTRO DE CADA PAGO
---------------------------------------------------------

Debe conservarse el flujo funcional ya desarrollado.

TIPO DE INSTRUMENTO:

- Cheque físico.
- e-Cheq.


TIPO DE CHEQUE:

- Común.
- Diferido.


CHEQUE COMÚN:

- Fecha de emisión visible.
- Fecha de acreditación oculta.
- Internamente:
  fecha_acreditacion = fecha_emision.
- La regla acreditación > emisión NO aplica.


CHEQUE DIFERIDO:

- Fecha de emisión visible.
- Fecha de acreditación visible.
- Acreditación debe ser posterior a emisión.
- No puede superar 360 días desde emisión.


ORIGEN PROPIO:

- Selector muestra Cuenta Bancaria.
- [+] abre ABM Cuentas Bancarias.
- Al volver:
  - se conserva todo el formulario;
  - la nueva cuenta queda seleccionada.


ORIGEN TERCERO:

- Selector muestra Banco.
- [+] abre ABM Bancos.
- Al volver:
  - se conserva todo el formulario;
  - el nuevo banco queda seleccionado.
- Se muestra "Quién lo entregó".


QUIÉN LO ENTREGÓ:

Actualmente es texto libre.

En el futuro deberá integrarse con ABM Clientes.


LISTA DE CHEQUES:

Cada cheque agregado debe:

- pertenecer solamente al Pago correspondiente;
- aparecer en la lista de ese Pago;
- poder eliminarse;
- sumar al total Cheques de ese Pago;
- sumar al total general de ese Pago.

Después de agregar un cheque:

TODO el formulario de carga de cheque debe volver a su estado
inicial, ya que no se presume ninguna relación entre un cheque
y el siguiente.


---------------------------------------------------------
EFECTOS DE CHEQUES PROPIOS
---------------------------------------------------------

Los cheques propios NO deben generar Alertas al agregarlos
visualmente a la tarjeta.

Al guardar el Registro/Pago:

- se revisan los cheques propios;
- se generan sus Vencimientos;
- se generan las Alertas según la configuración de la
  Cuenta Bancaria correspondiente.

Al modificar posteriormente un Pago:

- cheques agregados deben generar sus efectos;
- cheques modificados deben actualizar Vencimientos/Alertas;
- cheques quitados deben sincronizar o cancelar sus efectos.


---------------------------------------------------------
ELIMINACIÓN / REVERSIÓN DE UN PAGO
---------------------------------------------------------

Eliminar una tarjeta antes de guardar solamente elimina
el Pago en preparación.

Eliminar/revertir un Pago YA GUARDADO requiere sincronización.

En el futuro, cuando exista Cartera:

Si un cheque de tercero perteneciente a Cartera fue utilizado
en un Pago y posteriormente ese Pago se revierte:

- el cheque debe volver a Cartera;
- debe recuperar el estado que corresponda;
- deben reactivarse/regenerarse sus Vencimientos y Alertas
  cuando corresponda.

No implementar todavía Cartera, pero la arquitectura actual
no debe impedir este comportamiento futuro.


---------------------------------------------------------
RESUMEN DEL MOVIMIENTO
---------------------------------------------------------

Debe poder calcularse:

Total del Registro
Total de Pagos
Saldo pendiente

Si:

Total Pagos < Total Registro

existe saldo pendiente.

Si:

Total Pagos = Total Registro

el Movimiento queda totalmente cancelado.

Si:

Total Pagos > Total Registro

existe un saldo a favor.

La utilización contable/operativa del saldo a favor queda
pendiente de definición.


---------------------------------------------------------
PLAN DE PAGO
---------------------------------------------------------

Puede existir después de uno o más Pagos parciales.

Capital a financiar:

Total Registro
- Pagos previos
= Saldo pendiente

Los Pagos previos NO se eliminan.

Al convertir el saldo pendiente en Plan:

- los Pagos anteriores permanecen en el histórico;
- dejan de mostrarse como etapa activa;
- aparece la tarjeta Plan de Pago;
- se deshabilita/oculta Agregar Pago libre;
- los pagos futuros se aplicarán a Cuotas del Plan.


---------------------------------------------------------
REGLA DE IMPLEMENTACIÓN
---------------------------------------------------------

La conversión del antiguo bloque fijo "Datos del Pago"
a tarjetas dinámicas NO autoriza a simplificar ni eliminar
funcionalidades que ya estaban resueltas.

La nueva implementación debe reproducir el flujo anterior,
pero haciendo que cada dato, medio de pago, cheque y total
pertenezca explícitamente a su Pago.

PENDIENTE / DEFINIDO

- Crear ABM Tipos de Retención.
- Cada Tipo de Retención podrá asociarse a una cuenta del Plan Contable.
- Tipos de Retención forman parte de Exportar/Importar Empresa.
- Retenciones dentro de Pago usan selector + [+] + retorno conservando formulario.
- Si un Pago supera el saldo pendiente, mostrar modal de advertencia.
- El exceso NO se bloquea: puede continuar y generar saldo a favor.
- Revalidar el exceso también al Guardar Registro.

=========================================================
FIN DEL DOCUMENTO
=========================================================

=========================================================
28. PREVISIÓN DE PAGO, PRÓXIMOS VENCIMIENTOS Y LLAMADOR
=========================================================

PREVISIÓN DE PAGO DEL MOVIMIENTO

Antes de cerrar un gasto debe indicarse:

- Pago Manual.
- Débito automático + Cuenta Bancaria propia.

Durante la Beta solamente se ofrecerán cuentas activas, ARS y de la
Empresa.

Elegir Débito automático NO crea un Pago. Es una previsión de
cancelación y de necesidad futura de fondos. El hecho financiero existe
recién cuando el débito ocurre o se confirma.

La previsión debe conservar modalidad, cuenta cuando corresponda y fecha
de vencimiento.


REGLA DE SALDO

Saldo pendiente =
Total Movimiento - Aplicaciones de Pago válidas.

Un Movimiento parcialmente pagado muestra solamente su saldo pendiente.
Uno totalmente pagado no aparece como obligación pendiente.
Un compromiso vencido continúa visible mientras siga abierto.

Los Cheques/e-Cheqs propios también generan previsibilidad por su Cuenta
Bancaria, importe, fecha de acreditación/débito y estado real. Aunque
Cheques propios y Débitos automáticos puedan agruparse visualmente por
Cuenta, conservan naturaleza e histórico independientes.


PRÓXIMOS VENCIMIENTOS - MENÚ OPERATIVO

[ Alerta ] [ Hoy ] [ Esta semana ] [ Rango de fechas ]

Listar:
[ Todos / Tipo de gasto / Proveedor / Centro Operativo /
  Recurso Operativo / Débitos por cuenta ]

Si Listar es distinto de Todos, debe seleccionarse el valor concreto.

Hoy muestra compromisos del día + TOTAL HOY.

Esta semana y Rango de fechas agrupan por día, muestran subtotal de cada
día y finalizan con TOTAL GENERAL.

Todos reutilizan una misma lógica financiera.


VISTA ESPECIAL ALERTA

Alerta NO es solamente otro rango de fechas.

Es una vista inmediata de previsión de tesorería para CUATRO DÍAS
CORRIDOS:

- Hoy.
- Hoy + 1.
- Hoy + 2.
- Hoy + 3.

Dentro de cada día, los compromisos se agrupan cuando corresponda por
Cuenta Bancaria.

Ejemplo:

HOY · fecha                                      $ TOTAL DÍA

Caja de ahorro Banco Provincia                   $ subtotal cuenta
Cheque 0002545 | Gasto | Proveedor               $ importe
Débito        | Gasto | Proveedor                $ importe

Cuenta Corriente Banco Comafi                     $ subtotal cuenta
Débito        | Gasto | Proveedor                $ importe

Otros / Pagos manuales                            $ subtotal manual
Gasto | Proveedor                                 $ importe

Cada subtotal debe ser la suma real de sus renglones.

La vista debe ser clara, resumida y concreta y permitir prever cuánto
dinero deberá estar disponible y en qué Cuenta Bancaria.


FUENTE COMÚN

Alerta, Hoy, Esta semana y Rango de fechas deben utilizar una misma
lógica capaz de devolver:

- Empresa.
- Fecha.
- Tipo/origen del compromiso.
- Importe pendiente o comprometido.
- Cuenta Bancaria cuando corresponda.
- Tipo de gasto.
- Proveedor.
- Centro Operativo.
- Recurso Operativo.
- Observaciones relevantes.

La misma fuente deberá reutilizarse por Reportes, Llamador y futuras
notificaciones móviles.


LLAMADOR DE ORDENACLICK

Se define un componente visual genérico denominado conceptualmente
LLAMADOR DE ORDENACLICK.

No debe quedar acoplado visualmente a Vencimientos.

Primera implementación:

1. Al seleccionar Empresa, consultar silenciosamente si existen
   compromisos para la vista Alerta.
2. Si no existen, NO mostrar el Llamador.
3. Si existen, esperar aproximadamente 60 segundos.
4. Si cambia la Empresa, cancelar el temporizador anterior.
5. Emerger con animación breve y un sonido corto de campana.
6. Quedar quieto.

El Llamador NO muestra:

- mensaje;
- texto;
- importe;
- cantidad;
- Empresa;
- motivo.

Su función es llamar la atención sin anticipar la información.

Debe permitir drag & drop y permanecer dentro del área visible. No es
necesario guardar inicialmente su posición en la base.

Si sigue pendiente, aproximadamente cada 20 minutos podrá realizar un
pequeño movimiento de campana y un sonido corto.

No debe mantener animación ni sonido constantes. Las restricciones del
navegador implican que el funcionamiento crítico no puede depender sólo
del audio.

Al hacer clic:

Operativo
→ Próximos Vencimientos
→ Alerta

Debe abrir directamente esa vista y desaparecer el Llamador.


SEPARACIÓN CONCEPTUAL

VENCIMIENTO / COMPROMISO
= fuente de verdad.

VISTA ALERTA
= presentación inmediata y resumida.

LLAMADOR DE ORDENACLICK
= componente de interfaz que reclama atención.

Ni Alerta ni el Llamador crean obligaciones.


USOS FUTUROS DEL LLAMADOR

NO implementar todavía un sistema genérico completo.

El componente debe poder evolucionar para llamar la atención por otros
motivos, por ejemplo:

- proximidad de cierre contable;
- vencimiento de acta de designación de autoridades;
- documentación que requiera atención;
- otros compromisos administrativos u operativos;
- necesidades futuras surgidas de usuarios reales.


NOTIFICACIONES MÓVILES FUTURAS

La futura versión móvil deberá permitir que el usuario elija si desea
recibir una notificación cuando exista una Alerta aunque no haya abierto
OrdenaClick.

Debe reutilizar la misma fuente común de compromisos. Configuración,
horarios, anticipación y tecnología push quedan pendientes.


ORDEN DE IMPLEMENTACIÓN ACORDADO

1. Previsión de pago:
   Pago Manual / Débito automático + Cuenta Bancaria.

2. Próximos Vencimientos:
   Alerta / Hoy / Esta semana / Rango de fechas / Listar.

3. Llamador de OrdenaClick:
   condición + delay + animación + sonido + drag & drop +
   recordatorio + navegación directa a Alerta.

4. Reportes:
   reutilizando la lógica financiera común.


=========================================================
36. REGISTRAR PAGO REAL DE UN DÉBITO AUTOMÁTICO
=========================================================

Cuando un Movimiento tenga modalidad prevista:

DÉBITO AUTOMÁTICO

OrdenaClick ya conoce:

- el medio previsto;
- la Cuenta Bancaria;
- el compromiso;
- su fecha de vencimiento.

Por lo tanto, el botón habitual:

[ + Agregar pago ]

debe cambiar a:

[ Registrar Pago ]


---------------------------------------------------------
ACORDEÓN SIMPLIFICADO
---------------------------------------------------------

Al utilizar Registrar Pago NO debe mostrarse el formulario completo de
medios de pago.

Debe mostrarse únicamente:

▼ Pago 1                                      $ 0,00

Fecha de Pago                     Importe
[ dd/mm/aaaa ]                    [          ]


En este flujo el campo que en el formulario general aparece como
"Efectivo" debe llamarse:

IMPORTE

No deben volver a solicitarse:

- Banco.
- Cuenta Bancaria.
- Forma de pago.

Esos datos ya pertenecen a la previsión de Débito automático del
Movimiento.

El Importe representa el débito real observado.


---------------------------------------------------------
IMPORTE IGUAL AL SALDO
---------------------------------------------------------

Si:

Importe debitado = saldo pendiente

se registra una cancelación total normal.


---------------------------------------------------------
IMPORTE MENOR AL SALDO
---------------------------------------------------------

Si:

Importe debitado < saldo pendiente

se registra un Pago parcial.

El compromiso continúa abierto por el saldo restante.


---------------------------------------------------------
IMPORTE MAYOR AL SALDO
---------------------------------------------------------

Si:

Importe debitado > saldo pendiente

la diferencia NO debe aplicarse automáticamente al Movimiento.

Si además la Fecha de Pago es posterior al vencimiento, OrdenaClick debe
solicitar confirmación antes de guardar.

Ejemplo:

Saldo pendiente:                 $100.000
Importe debitado:                $107.500
Diferencia:                        $7.500


Modal conceptual:

El débito se produjo después del vencimiento y el importe ingresado
supera en $7.500 el saldo pendiente.

¿Los $7.500 corresponden a intereses por mora?

[ Sí ] [ No ]


SI EL USUARIO ELIGE SÍ:

- Se aplica al Movimiento solamente el importe necesario para cancelar
  el saldo pendiente.
- La diferencia se registra separadamente como interés/costo financiero.
- El interés NO aumenta el importe aplicado al Movimiento.
- Se conserva la fecha real del Pago.
- Se actualizan saldo, estado y compromiso correspondientes.


SI EL USUARIO ELIGE NO:

- NO se guarda el Pago.
- NO se modifica el Movimiento.
- NO se modifica el compromiso.
- Se vuelve al acordeón simplificado.
- Se conservan Fecha e Importe para que el usuario pueda corregirlos.


OrdenaClick NO debe asumir automáticamente que un excedente corresponde
a intereses.

Si el importe supera el saldo pero la Fecha de Pago NO es posterior al
vencimiento, la diferencia NO debe clasificarse automáticamente como
interés por mora.

La clasificación definitiva de otros excedentes queda pendiente de
definición.


REGLA FINANCIERA:

Los intereses y costos financieros son económicamente reales, pero NO
incrementan el importe aplicado a la cancelación del Movimiento.
```


## FUENTE: ARQUITECTURA_NUCLEO_FINANCIERO_v2.md

```text
# Arquitectura del Núcleo Financiero --- OrdenaClick

## 1. Propósito

Este documento registra las decisiones conceptuales tomadas para el
núcleo financiero de OrdenaClick antes de implementar el guardado
definitivo de movimientos.

Su objetivo es servir como referencia para futuras etapas de desarrollo,
otros colaboradores y nuevas conversaciones de trabajo, evitando
reconstruir decisiones importantes únicamente a partir del código.

Este documento describe arquitectura y reglas de negocio. No implica que
todas las funcionalidades aquí mencionadas estén implementadas en la
versión Beta.

------------------------------------------------------------------------

## 2. Objetivo funcional de OrdenaClick

OrdenaClick debe ayudar a una empresa en dos frentes principales:

1.  Registrar y conservar información completa de gastos, comprobantes y
    pagos para su posterior consulta y explotación mediante Reportes.
2.  Evitar que el empresario pierda de vista compromisos financieros
    pendientes o próximos a vencer.

Por este motivo, el sistema no debe tratar un gasto únicamente como una
factura almacenada. Debe poder representar también su estado financiero,
sus pagos y las obligaciones futuras que genere.

------------------------------------------------------------------------

## 3. Núcleo conceptual

La estructura conceptual definida es:

``` text
EMPRESA
   │
   └── EJERCICIO
          │
          └── MOVIMIENTO
                │
                ├── PAGOS / APLICACIONES DE PAGO
                │
                └── OBLIGACIONES
                       │
                       ├── Pendientes
                       ├── Próximas a vencer
                       └── Vencidas

MOVIMIENTO
   │
   └── puede convertirse en
       PLAN DE PAGOS
          │
          └── CUOTAS
                 │
                 └── OBLIGACIONES

CHEQUE PROPIO EMITIDO
   └── genera una obligación por su fecha correspondiente

DÉBITO AUTOMÁTICO
   └── genera una obligación por su fecha prevista

REGISTRO / RENDICIÓN DEL VENDEDOR
   │
   └── REGISTRO PENDIENTE
          │
          └── revisión y completado por Admin / Colaborador
                 │
                 └── MOVIMIENTO definitivo
```

------------------------------------------------------------------------

## 4. Empresa y Ejercicio

Cada empresa abre y cierra ejercicios contables.

Los movimientos deben quedar asociados a:

-   una Empresa;
-   un Ejercicio.

Conceptualmente:

``` text
Empresa
 ├── Ejercicio 2026
 │    ├── Movimiento
 │    ├── Movimiento
 │    └── Movimiento
 │
 └── Ejercicio 2027
      ├── Movimiento
      └── Movimiento
```

El cierre de un ejercicio no debe eliminar su información histórica.

Las reglas exactas sobre qué operaciones podrán realizarse sobre un
ejercicio cerrado quedan pendientes de definición.

------------------------------------------------------------------------

## 5. Movimiento

El Movimiento representa el hecho económico y documental.

Debe conservar la información necesaria para reconstruir históricamente
el gasto y permitir posteriormente filtros e informes.

Como mínimo se prevé conservar:

-   Empresa.
-   Ejercicio.
-   Tipo de gasto.
-   Proveedor.
-   Centro Operativo.
-   Recurso Operativo.
-   Fecha de registro.
-   Fecha de vencimiento.
-   Tipo de comprobante.
-   Número de comprobante.
-   Descripción.
-   Neto gravado.
-   No gravado / exento.
-   IVA 21%.
-   IVA 27%.
-   IVA 10,5%.
-   Recargos / intereses propios del comprobante.
-   Ajuste por redondeo.
-   Percepción de Ingresos Brutos.
-   Percepción de IVA.
-   Percepción de Ganancias.
-   Percepción de Tasas Municipales.
-   Total.
-   Factura / archivo adjunto.
-   Estado.
-   Observaciones.
-   Moneda.
-   Datos de auditoría que correspondan.

El Total debe conservarse, pero también deben persistirse sus
componentes fiscales. No debe almacenarse únicamente un importe final
que impida reconstruir posteriormente la composición del gasto.

------------------------------------------------------------------------

## 6. Moneda

### Beta

La primera versión Beta operará exclusivamente en pesos argentinos
(ARS).

Los medios de pago disponibles durante esta etapa deben impedir
introducir importes en monedas incompatibles.

En particular, las cuentas bancarias en USD pueden continuar existiendo
en su ABM, pero no deben utilizarse como medio de pago de movimientos
ARS durante la Beta.

### Preparación para multimoneda

El modelo debe quedar preparado para identificar la moneda del
Movimiento aunque inicialmente todos los movimientos sean ARS.

Cuando se implemente multimoneda:

``` text
Movimiento ARS
→ habilita medios de pago compatibles con ARS

Movimiento USD
→ habilita medios de pago compatibles con USD
```

No se implementan todavía:

-   conversiones cambiarias;
-   tipos de cambio;
-   pagos cruzados entre monedas;
-   reglas definitivas para resúmenes de tarjetas en escenarios
    multimoneda.

Estas cuestiones se resolverán como una funcionalidad específica
posterior.

------------------------------------------------------------------------

## 7. Pago

El Pago representa el hecho financiero.

Un Movimiento puede tener:

-   cero pagos;
-   un pago;
-   múltiples pagos.

Los medios actualmente contemplados incluyen:

-   Efectivo.
-   Transferencias / Depósitos.
-   Tarjetas.
-   Cheques.
-   Retenciones.

Las Retenciones forman parte del importe aplicado al Pago.

El Pago y sus aplicaciones deben permanecer conceptualmente separados
del Movimiento para permitir pagos parciales, múltiples pagos y futuras
relaciones más complejas.

------------------------------------------------------------------------

## 8. Saldo pendiente

El sistema debe poder determinar cuánto del Movimiento permanece
pendiente.

Ejemplo:

``` text
Movimiento:       $100.000
Pagos aplicados:   $30.000
Saldo pendiente:   $70.000
```

El saldo pendiente es el que puede originar obligaciones futuras y
alertas.

------------------------------------------------------------------------

## 9. Obligación

La Obligación representa un compromiso financiero que todavía debe ser
atendido.

No debe confundirse con el Movimiento ni con la alerta visual.

Ejemplo:

``` text
Movimiento:
Factura proveedor X
Total: $100.000

Pago:
$30.000

Obligación:
Saldo pendiente: $70.000
Vencimiento: 15/09
```

La obligación permanece abierta mientras el compromiso continúe
pendiente.

### Vencimiento

El paso de la fecha NO elimina una obligación.

Una obligación abierta puede clasificarse como:

``` text
Fecha futura cercana  → Próxima a vencer
Fecha actual           → Vence hoy
Fecha pasada           → Vencida
```

Si el usuario no ingresa a OrdenaClick durante varios días y una
obligación vence durante ese período, al volver a ingresar debe
mostrarse como VENCIDA y continuar visible mientras siga pendiente.

Una obligación deja de formar parte de los compromisos abiertos cuando
corresponda por una acción real de negocio, por ejemplo:

-   pago/cancelación;
-   reemplazo por nuevas obligaciones derivadas de una conversión a Plan
    de Pagos;
-   otra acción futura expresamente definida.

------------------------------------------------------------------------


### Correspondencia con los modelos Django actuales

En la implementación actual de OrdenaClick, la entidad conceptual **Obligación** se encuentra representada técnicamente por el modelo `Vencimiento`.

Por lo tanto:

```text
OBLIGACIÓN conceptual
        =
Vencimiento en models.py
```

`Vencimiento` es la fuente de verdad del compromiso financiero abierto: conserva origen, fecha de vencimiento, importe original, importe pendiente y estado.

**Alerta no es sinónimo de Obligación.**

El modelo `Alerta` representa el aviso asociado a un `Vencimiento`, por ejemplo la fecha desde la cual corresponde llamar la atención del usuario y sus datos de anticipación/atención.

Conceptualmente:

```text
Movimiento / Cuota / Cheque
          ↓
     Vencimiento
     (Obligación)
          ↓
       Alerta
       (Aviso)
```

Una obligación vencida no desaparece por el paso del tiempo. Mientras `Vencimiento.importe_pendiente` continúe abierto y su estado no sea Pagado o Cancelado, debe seguir formando parte de los compromisos de la Empresa aunque su fecha ya haya pasado.

La campanita y la futura sección [Próximos vencimientos] deben tomar como fuente principal los `Vencimiento` abiertos. Las `Alerta` pueden utilizarse para programación, anticipación, atención o reprogramación del aviso, pero no deben reemplazar al `Vencimiento` como fuente de verdad del compromiso.


## 10. Campanita y Próximos vencimientos

La campanita no es la fuente de verdad de los vencimientos.

La fuente de verdad son las obligaciones abiertas.

Cuando el usuario selecciona una Empresa, OrdenaClick debe consultar las
obligaciones abiertas correspondientes a esa Empresa.

La campanita podrá informar:

-   compromisos próximos;
-   compromisos que vencen hoy;
-   compromisos vencidos que continúan pendientes.

La campanita direccionará al usuario a la futura sección:

``` text
[Próximos vencimientos]
```

del sidebar.

La versión móvil prevista deberá poder utilizar esta misma información
para generar notificaciones.

La estrategia técnica definitiva para notificaciones móviles queda
pendiente de definición.

------------------------------------------------------------------------

## 11. Fuentes de obligaciones

Una obligación puede originarse desde diferentes partes del sistema.

Entre las fuentes previstas se encuentran:

### Movimiento parcialmente o totalmente impago

El saldo pendiente genera una obligación según su vencimiento.

### Cheque propio emitido

Un cheque propio representa un compromiso de disponer de fondos en la
fecha correspondiente.

Debe poder generar una obligación futura.

### Débito automático

Un débito automático próximo representa un compromiso financiero futuro.

Debe poder generar una obligación según su fecha prevista.

### Plan de Pagos

Cada cuota pendiente del plan constituye una obligación con su propio
vencimiento.

El sistema de alertas no debería necesitar conocer internamente todas
las particularidades de cada origen para determinar que existe un
compromiso pendiente.

------------------------------------------------------------------------

## 12. Plan de Pagos

Carga Simple podrá convertirse posteriormente en Plan de Pagos.

La conversión debe heredar los datos necesarios del Movimiento original
y trabajar sobre el saldo restante.

Ejemplo:

``` text
Movimiento original: $1.000.000
Pagado:                 $200.000
Saldo:                  $800.000
```

Si el saldo se convierte en un plan:

``` text
Plan de Pagos
 ├── Cuota 1 → importe + vencimiento
 ├── Cuota 2 → importe + vencimiento
 ├── Cuota 3 → importe + vencimiento
 └── Cuota 4 → importe + vencimiento
```

Las cuotas podrán incorporar los intereses correspondientes al plan.

Al producirse la conversión:

1.  el Movimiento original conserva su historia;
2.  la obligación pendiente que estaba siendo reemplazada deja de formar
    parte de los compromisos abiertos;
3.  el Plan genera nuevas obligaciones correspondientes a sus cuotas;
4.  cada cuota será alertada según su propio vencimiento.

No debe destruirse ni reescribirse el valor documental histórico del
Movimiento original para representar el Plan.

------------------------------------------------------------------------

## 13. Intereses por mora

Un registro vencido podrá generar intereses al momento del pago.

Los intereses generados posteriormente al comprobante no deberían
modificar retroactivamente el importe documental original.

Ejemplo:

``` text
Factura original: $100.000
Interés por mora:    $5.000
Pago realizado:    $105.000
```

Debe ser posible distinguir posteriormente:

-   importe original;
-   interés generado por mora;
-   importe efectivamente pagado.

Esto permitirá además futuros Reportes sobre costos financieros e
intereses.

La fórmula, configuración y reglas definitivas de cálculo de mora quedan
pendientes de definición.

------------------------------------------------------------------------

## 14. Reportes

La sección \[Reportes\] utilizará la información persistida en los
Movimientos y demás entidades relacionadas.

Por ese motivo debe conservarse la información discriminada y no
solamente totales.

Se prevé que los usuarios puedan filtrar datos por diferentes
dimensiones, entre ellas las que posteriormente se definan sobre:

-   Empresa.
-   Ejercicio.
-   Proveedor.
-   Tipo de gasto.
-   Centro Operativo.
-   Recurso Operativo.
-   Fechas.
-   Estado.
-   Componentes fiscales.
-   Pagos.
-   Otras dimensiones futuras.

------------------------------------------------------------------------

## 15. Registro / Rendición del Vendedor

El futuro módulo del Vendedor estará orientado principalmente a la
rendición de viáticos y gastos producidos durante sus giras.

El vendedor realizará una carga simplificada con poca información.

Inicialmente se prevé:

-   Proveedor.
-   Importe.
-   Factura adjunta.
-   Comprobante de pago, cuando corresponda.
-   Otros datos mínimos que se definan al diseñar el módulo.

Esta información tiene valor para evitar una segunda carga manual
completa.

Sin embargo:

> Un Registro del Vendedor no debe convertirse automáticamente en un
> Movimiento contable definitivo.

El flujo conceptual será:

``` text
Vendedor
   ↓
Rendición / Registro preliminar
   ↓
Registros pendientes
   ↓
Admin / Colaborador
   ↓
Carga Simple precargada con la información disponible
   ↓
Completar / validar información restante
   ↓
Movimiento definitivo
```

El módulo concreto del Vendedor se diseñará e implementará
posteriormente, pero el núcleo financiero debe evitar decisiones que
impidan esta integración futura.

------------------------------------------------------------------------

## 16. Estados del Movimiento

Se prevén conceptualmente los siguientes estados:

-   Pendiente.
-   Parcial.
-   Pagado.
-   Vencido.
-   Cancelado.

Las reglas exactas de transición deberán definirse al implementar el
registro efectivo y la lógica de pagos.

El estado visual del Movimiento no debe reemplazar la existencia de
Obligaciones como fuente de verdad para compromisos financieros
abiertos.

------------------------------------------------------------------------

## 17. Seguridad

OrdenaClick funcionará como aplicación web y deberá contemplar seguridad
desde el backend.

No debe confiarse únicamente en restricciones de interfaz o JavaScript.

La autorización conceptual debe considerar:

``` text
Usuario
   ↓
permiso sobre Empresa
   ↓
Ejercicio
   ↓
Movimiento / Pago / Obligación / demás entidades
```

Cada operación sensible deberá validar del lado servidor que:

-   el usuario está autenticado;
-   tiene autorización sobre la Empresa;
-   el objeto pertenece a esa Empresa;
-   el Ejercicio corresponde;
-   su rol permite la operación;
-   las demás reglas de negocio aplicables se cumplen.

Los identificadores enviados por el navegador no deben considerarse
prueba suficiente de autorización.

La implementación debe mantener un equilibrio: seguridad correcta desde
el diseño sin agregar complejidad innecesaria antes de que sea
requerida.

------------------------------------------------------------------------

## 18. Planes, proveedor de pagos y webhooks

OrdenaClick tendrá planes de servicio.

En una etapa posterior se integrará un proveedor de pagos que permitirá
verificar el estado del plan contratado.

Se prevé el uso de webhooks.

Deben mantenerse separados dos conceptos:

``` text
1. ¿El usuario tiene permiso para operar sobre esta Empresa?

2. ¿El plan/suscripción de esa Empresa habilita esta funcionalidad?
```

La interfaz podrá ocultar o deshabilitar funcionalidades según el plan,
pero esa restricción visual no reemplaza la validación del backend.

El estado válido de la suscripción no debe depender exclusivamente de
información enviada por el navegador.

La integración concreta con el proveedor, validación de webhooks,
almacenamiento del estado de suscripción y políticas ante fallos se
diseñarán cuando se implemente el sistema comercial.

------------------------------------------------------------------------

## 19. Auditoría y trazabilidad

Por tratarse de información financiera y una aplicación web
multiusuario, los modelos principales deberían quedar preparados para
conservar trazabilidad suficiente.

Como mínimo debe evaluarse durante la implementación la necesidad de
registrar:

-   fecha de creación;
-   fecha de última modificación;
-   usuario creador;
-   usuario que realizó modificaciones relevantes;
-   estados y cambios que requieran trazabilidad.

El alcance definitivo se decidirá al diseñar los modelos concretos.

------------------------------------------------------------------------

## 20. Principios para la implementación

Las siguientes reglas deben guiar el desarrollo:

1.  El Movimiento conserva la historia documental.
2.  El Pago representa hechos financieros y no debe reescribir
    arbitrariamente el documento original.
3.  Las Obligaciones representan compromisos abiertos.
4.  Una obligación vencida permanece pendiente hasta que una acción real
    la cierre o reemplace.
5.  Las alertas se derivan de obligaciones abiertas.
6.  Los Planes de Pago reemplazan obligaciones pendientes por
    obligaciones correspondientes a sus cuotas, sin destruir el
    Movimiento original.
7.  La Beta trabaja exclusivamente en ARS.
8.  La arquitectura debe permitir multimoneda futura sin implementarla
    prematuramente.
9.  Los registros preliminares del Vendedor no son Movimientos
    definitivos.
10. Los datos discriminados deben conservarse para permitir Reportes
    futuros.
11. La seguridad y autorización reales pertenecen al backend.
12. Los permisos de usuario y la habilitación comercial por plan son
    controles diferentes.
13. Debe evitarse agregar complejidad futura que todavía no sea
    necesaria, pero también evitar decisiones que bloqueen
    funcionalidades ya previstas.

------------------------------------------------------------------------

## 21. Decisiones todavía no tomadas

Los siguientes temas están deliberadamente pendientes y NO deben
interpretarse como resueltos:

-   Modelo definitivo para resúmenes y pagos de tarjetas de crédito.
-   Reglas definitivas de multimoneda.
-   Conversión ARS/USD y tipos de cambio.
-   Pagos cruzados entre monedas.
-   Fórmula y política de intereses por mora.
-   Reglas definitivas de apertura y cierre de ejercicios.
-   Implementación técnica definitiva de alertas.
-   Implementación de notificaciones móviles.
-   Configuración de anticipación de alertas.
-   Diseño definitivo de Planes de Pago.
-   Diseño definitivo del módulo del Vendedor.
-   Flujo definitivo de aprobación de Registros Pendientes.
-   Integración concreta con proveedor de pagos.
-   Política de webhooks y contingencias.
-   Alcance definitivo de auditoría y trazabilidad.
-   Reglas completas de transición entre estados del Movimiento.

------------------------------------------------------------------------

## 22. Estado de la Beta al momento de esta decisión

La Beta se está construyendo inicialmente alrededor de Carga Simple y
Pagos.

Se ha definido que:

-   los pagos de la Beta operan en ARS;
-   Transferencias / Depósitos no deben permitir utilizar cuentas USD;
-   Retenciones forman parte del importe aplicado al Pago;
-   posteriormente se implementará el registro persistente de
    Movimientos con y sin Pago;
-   luego se desarrollarán las operaciones de Registrar Pago y Modificar
    / Eliminar;
-   posteriormente se incorporará Carga Planificada / Convertir a Plan;
-   Reportes, Pendientes y Alertas recorrerán la información persistida
    en el núcleo financiero.

Antes de implementar el guardado definitivo de Carga Simple debe
diseñarse el modelo de datos concreto respetando las decisiones de este
documento.

------------------------------------------------------------------------

## 23. Próximo paso de desarrollo

El próximo paso recomendado es diseñar los modelos Django concretos que
representarán este núcleo, comenzando por Movimiento y sus relaciones
inmediatas.

Antes de crear migraciones debe verificarse el código existente para:

-   detectar referencias al modelo Movimiento actual;
-   determinar compatibilidad con campos existentes;
-   confirmar las relaciones reales con Empresa, Ejercicio, Proveedor,
    Tipo de Gasto, Centro Operativo y Recurso Operativo;
-   evitar eliminar campos todavía utilizados;
-   diseñar una migración segura.

Una vez definido y migrado el modelo, podrá conectarse \[Guardar
registro\] comenzando por el flujo sin Pago y posteriormente el flujo
con Pago.

------------------------------------------------------------------------

## 24. Previsión de pago, Próximos Vencimientos y Llamador de OrdenaClick

### 24.1 Previsión de pago del Movimiento

Antes de cerrar la carga de un gasto, el Movimiento debe indicar cómo se prevé atender su saldo pendiente:

- **Pago Manual**.
- **Débito automático**, asociado a una Cuenta Bancaria propia.

Durante la Beta, las cuentas ofrecidas para débito automático deben estar activas, pertenecer a la Empresa y operar en ARS.

Elegir Débito automático **NO crea un Pago**. Representa una previsión de cancelación y una futura necesidad de fondos. El hecho financiero se registra recién cuando el débito ocurre o se confirma.

La previsión debe conservar conceptualmente:

- modalidad prevista de pago;
- Cuenta Bancaria prevista, cuando corresponda;
- fecha de vencimiento del Movimiento.

### 24.2 Regla común de saldo y compromisos

Para Movimientos pendientes:

```text
Saldo pendiente =
Total del Movimiento - Aplicaciones de Pago válidas
```

Un Movimiento parcialmente pagado muestra únicamente su saldo pendiente. Uno totalmente pagado no aparece como obligación pendiente del Movimiento. Una obligación vencida continúa visible mientras siga abierta.

Los Cheques/e-Cheqs propios también generan previsibilidad: aunque ya hayan aplicado su importe a un Pago, representan una salida futura de fondos según su cuenta y fecha de acreditación/débito. Débitos automáticos y Cheques propios pueden agruparse visualmente por Cuenta Bancaria, pero conservan entidades, estados e histórico independientes.

### 24.3 Próximos Vencimientos

Dentro del menú Operativo, Próximos Vencimientos tendrá:

```text
[ Alerta ] [ Hoy ] [ Esta semana ] [ Rango de fechas ]

Listar:
[ Todos / Tipo de gasto / Proveedor / Centro Operativo /
  Recurso Operativo / Débitos por cuenta ]
```

Si `Listar` es distinto de `Todos`, deberá permitirse seleccionar el valor concreto del criterio elegido.

**Hoy** muestra los compromisos del día, sus importes pendientes y un total del día.

**Esta semana** y **Rango de fechas** agrupan por día, muestran subtotal por día y finalizan con un **TOTAL GENERAL**.

Los filtros modifican el conjunto mostrado, pero no deben implementar motores financieros diferentes.

### 24.4 Vista especial Alerta

`Alerta` no es simplemente otro rango. Es una vista inmediata de previsión de tesorería.

La ventana inicial comprende cuatro días corridos:

```text
HOY
HOY + 1
HOY + 2
HOY + 3
```

Dentro de cada día, los compromisos se agrupan cuando corresponda por Cuenta Bancaria:

```text
HOY · fecha                                      $ TOTAL DÍA

Caja de ahorro Banco Provincia                   $ subtotal cuenta
Cheque 0002545 | Gasto | Proveedor               $ importe
Débito        | Gasto | Proveedor                $ importe

Cuenta Corriente Banco Comafi                     $ subtotal cuenta
Débito        | Gasto | Proveedor                $ importe

Otros / Pagos manuales                            $ subtotal manual
Gasto | Proveedor                                 $ importe
```

Cada subtotal debe ser la suma real de sus renglones. La vista debe ser clara, resumida y concreta, orientada a responder cuánto debe preverse y en qué Cuenta Bancaria.

### 24.5 Fuente común

Alerta, Hoy, Esta semana y Rango de fechas deben reutilizar una única lógica capaz de proporcionar como mínimo:

- Empresa;
- fecha;
- tipo y origen del compromiso;
- importe pendiente o comprometido;
- Cuenta Bancaria, cuando corresponda;
- Tipo de gasto;
- Proveedor;
- Centro Operativo;
- Recurso Operativo;
- observaciones relevantes.

La misma fuente deberá poder reutilizarse posteriormente por Reportes, el Llamador y notificaciones móviles.

### 24.6 Llamador de OrdenaClick

Se define un componente visual genérico denominado conceptualmente **Llamador de OrdenaClick**. No debe quedar acoplado visualmente a Vencimientos porque en el futuro podrá utilizarse para otros motivos que requieran atención.

Para su primera implementación:

1. Al seleccionar una Empresa se consulta silenciosamente si existen compromisos para la vista Alerta.
2. Si no existen, el Llamador no aparece.
3. Si existen, espera aproximadamente 60 segundos.
4. Si cambia la Empresa durante la espera, se cancela el temporizador anterior.
5. Luego emerge mediante una animación breve y una campana produce un sonido corto.
6. Después permanece quieto.

El Llamador **no muestra texto, importes, cantidad, Empresa ni motivo**. Su función es llamar la atención y despertar la consulta.

Debe permitir **drag & drop**, permanecer dentro del área visible y conservar su posición durante la interacción. No es necesario persistir inicialmente esa posición en la base.

Si continúa pendiente, aproximadamente cada **20 minutos** puede realizar un pequeño movimiento de campana y reproducir un sonido corto. No debe mantener animaciones o sonidos constantes. El funcionamiento crítico no dependerá exclusivamente del audio debido a posibles restricciones del navegador.

Al hacer clic:

```text
Operativo
→ Próximos Vencimientos
→ Alerta
```

La vista debe abrirse directamente configurada como Alerta y el Llamador desaparece.

### 24.7 Separación conceptual

```text
VENCIMIENTO / COMPROMISO
= fuente de verdad.

VISTA ALERTA
= presentación inmediata y resumida.

LLAMADOR DE ORDENACLICK
= componente de interfaz que reclama atención.
```

Ni la vista Alerta ni el Llamador crean obligaciones.

### 24.8 Reutilización futura

No se implementará ahora un sistema genérico completo, pero el Llamador no debe quedar limitado a compromisos financieros.

Posibles usos futuros:

- proximidad de cierre contable;
- vencimiento de acta de designación de autoridades;
- documentación que requiera atención;
- otros compromisos administrativos u operativos;
- nuevas necesidades surgidas de usuarios reales.

### 24.9 Notificaciones móviles futuras

La futura versión móvil deberá permitir que el usuario elija si desea recibir una notificación cuando exista una Alerta aunque no haya abierto OrdenaClick.

Debe reutilizarse la misma fuente común de compromisos. Configuración, horarios, anticipación y tecnología push quedan para una etapa posterior.

### 24.10 Orden de implementación acordado

```text
1. Previsión de pago:
   Pago Manual / Débito automático + Cuenta Bancaria.

2. Próximos Vencimientos:
   Alerta / Hoy / Esta semana / Rango de fechas / Listar.

3. Llamador de OrdenaClick:
   condición + delay + animación + sonido + drag & drop +
   recordatorio + navegación a Alerta.

4. Reportes:
   reutilizando la lógica financiera común.
```

El objetivo es que OrdenaClick no se limite a registrar hechos pasados, sino que transforme esos datos en previsibilidad concreta de compromisos futuros.


### 24.11 Registro del Pago real de un Débito automático

Cuando un Movimiento tenga como modalidad prevista **Débito automático**, la interfaz de carga del Pago debe simplificarse porque OrdenaClick ya conoce el medio previsto y la Cuenta Bancaria asociada.

En este caso el botón habitual:

```text
[ + Agregar pago ]
```

debe presentarse como:

```text
[ Registrar Pago ]
```

Al utilizarlo no debe mostrarse el conjunto completo de medios de pago. El acordeón debe contener únicamente:

```text
▼ Pago 1                                      $ 0,00

Fecha de Pago                     Importe
[ dd/mm/aaaa ]                    [          ]
```

El campo que en el formulario general corresponde visualmente a `Efectivo` debe denominarse **Importe** en este flujo.

No deben volver a solicitarse Banco, Cuenta Bancaria ni forma de pago, porque esos datos provienen de la previsión de Débito automático del Movimiento.

El importe ingresado representa el débito real observado en la Cuenta Bancaria.

#### Importe igual, menor o mayor al compromiso

Si:

```text
Importe debitado = saldo pendiente
```

se registra una cancelación total normal.

Si:

```text
Importe debitado < saldo pendiente
```

se registra un Pago parcial y el compromiso continúa abierto por el saldo restante.

Si:

```text
Importe debitado > saldo pendiente
```

la diferencia NO debe aplicarse automáticamente al Movimiento.

Cuando además la fecha real del Pago sea posterior al vencimiento, OrdenaClick debe solicitar confirmación antes de guardar.

Ejemplo:

```text
Saldo pendiente:                 $100.000
Importe debitado:                $107.500
Diferencia:                        $7.500
```

Modal conceptual:

```text
El débito se produjo después del vencimiento y el importe ingresado
supera en $7.500 el saldo pendiente.

¿Los $7.500 corresponden a intereses por mora?

[ Sí ] [ No ]
```

Si el usuario selecciona **Sí**:

- se registra como importe aplicado únicamente el saldo que corresponde cancelar;
- la diferencia se conserva separadamente como interés/costo financiero;
- el interés NO incrementa el importe aplicado al Movimiento;
- se registra la fecha real del Pago;
- se actualiza el saldo y estado del compromiso.

Si selecciona **No**:

- no se guarda el Pago;
- no se modifica el Movimiento ni el compromiso;
- se vuelve al acordeón;
- deben conservarse Fecha e Importe ingresados para permitir su corrección.

La confirmación del usuario es necesaria: OrdenaClick no debe asumir automáticamente que todo excedente corresponde a intereses.

Si el importe es superior al saldo pero la fecha NO es posterior al vencimiento, no debe clasificarse automáticamente la diferencia como interés por mora. La clasificación definitiva de otros excedentes queda pendiente de definición.

Este flujo debe respetar la regla general del núcleo financiero:

> Los intereses y costos financieros son económicamente reales, pero no aumentan el importe aplicado a la cancelación del Movimiento.
```


## FUENTE: Para no perder el tiempo cuando reinicio.txt

```text
============================================================
ORDENACLICK 2.0 - DOCUMENTO DE INICIO / CONTEXTO DE PROYECTO
============================================================

OBJETIVO DE ESTE ARCHIVO
------------------------
Este archivo debe leerse al comenzar un nuevo chat, incorporar una nueva persona al proyecto o retomar el desarrollo después de una pausa.

Su finalidad es evitar perder contexto, decisiones ya tomadas, reglas de arquitectura y prioridades del producto.

NO reemplaza los documentos técnicos existentes del proyecto. Los complementa.
Antes de modificar código también deben revisarse, como mínimo:

- Reglas_del_desarrollo.md
- Arquitectura Panel_admin.txt
- Arquitectura_Movimientos_Pagos_Vencimientos_Alertas.txt
- Reglas_Exportacion_Empresa.txt
- TODO.md


============================================================
1. QUE ES ORDENACLICK
============================================================

OrdenaClick es una aplicación web de gestión empresarial orientada a ordenar gastos, registros, pagos, vencimientos, alertas e información de gestión, conservando una arquitectura preparada para incorporar contabilidad, aspectos legales y otras funciones futuras.

El sistema no debe limitarse a registrar lo que ya ocurrió. También debe ayudar al dueño de una empresa a anticipar obligaciones económicas y evitar olvidos o pérdidas de control.

La información histórica debe conservarse. El diseño debe permitir que una empresa crezca sin tener que migrar a otra estructura de datos.

Principio general:

UNA SOLA ARQUITECTURA ESCALABLE
+ funciones visibles/ocultas o automáticas según necesidad y plan
+ sin migraciones destructivas cuando una empresa crece.


============================================================
2. VISION DE ESCALABILIDAD
============================================================

OrdenaClick debe asumir que:

- Las empresas cambian y crecen.
- Una empresa hoy simple puede necesitar mañana sucursales, depósitos, vehículos, más empleados, varias cuentas bancarias, tarjetas, contabilidad completa, etc.
- Aparecen nuevos impuestos.
- Aparecen nuevas formas de pago.
- Formas de pago antiguas pueden digitalizarse.
- Cambian necesidades regulatorias, contables y operativas.

Por eso NO deben existir arquitecturas separadas para "empresa simple" y "empresa compleja".

La estructura de datos debe ser común y completa.
Lo que cambia según empresa o plan es:

- qué módulos están habilitados;
- qué configuraciones son manuales;
- qué valores se resuelven automáticamente;
- qué partes se muestran al usuario.

Ejemplo:
Una empresa simple puede no usar Sucursales explícitamente.
Sin embargo, el sistema puede registrar internamente todas sus operaciones sobre una ubicación/base creada automáticamente con el domicilio real de la empresa.
Si la empresa crece, se habilita la administración de sucursales sin migrar ni perder datos anteriores.

Regla de diseño:

NO BORRAR ESTRUCTURA PARA SIMPLIFICAR LA EXPERIENCIA.
SIMPLIFICAR LA INTERFAZ, NO LOS DATOS.


============================================================
3. PERFILES DE USUARIO PREVISTOS
============================================================

Un usuario de OrdenaClick puede actuar con cuatro perfiles:

1. ADMINISTRADOR
2. COLABORADOR
3. CONTABLE / CONTADOR
4. LEGAL / ABOGADO

Actualmente el desarrollo principal está centrado en ADMINISTRADOR.
El siguiente perfil prioritario para la primera versión testeable es COLABORADOR.


ADMINISTRADOR
-------------
Puede, entre otras funciones:

- Crear empresas.
- Administrar sus empresas.
- Configurar estructura y ABMs.
- Designar colaboradores.
- Contratar/asignar contadores.
- Contratar/asignar abogados.
- Cargar registros y pagos.
- Acceder a reportes, vencimientos, alertas y demás módulos habilitados.
- Definir permisos o visibilidad de determinadas funciones para colaboradores y otros perfiles cuando corresponda.


COLABORADOR
-----------
No toma decisiones estructurales sobre la empresa y no crea empresas.

Su función principal es operativa.
Puede:

- Trabajar sobre empresas para las que fue aceptado/asignado.
- Cargar registros.
- Cargar pagos.
- Usar los ABMs necesarios para esas cargas.

El Administrador podrá definir permisos sobre módulos adicionales cuando esa parte del sistema esté desarrollada.


CONTABLE / CONTADOR
-------------------
Perfil futuro.
Debe poder trabajar sobre empresas que lo hayan contratado/asignado.
La arquitectura actual debe mantenerse compatible con:

- Plan de Cuentas.
- Estado de Resultados.
- Balance.
- Imputaciones contables.
- Configuraciones contables realizadas por Administrador o Contador.


LEGAL / ABOGADO
---------------
Perfil futuro.
Trabajará sobre empresas asignadas y funcionalidades legales que se desarrollen posteriormente.


============================================================
4. OBJETIVO PRIORITARIO: VERSION TESTEABLE EN SEPTIEMBRE
============================================================

Para septiembre se busca tener OrdenaClick en la nube, usable y preparado para pruebas reales.

NO significa que OrdenaClick esté terminado.
Significa que debe existir un circuito funcional completo y estable para comenzar testing.

Alcance prioritario esperado:

- Login.
- Perfil Administrador.
- Perfil Colaborador.
- Creación y administración de empresas.
- Asignación/uso básico de colaboradores.
- Carga de Registros.
- Carga de Pagos.
- ABMs necesarios para Registros y Pagos.
- Posiblemente Plan de Pagos, si llega con estabilidad suficiente.
- Informes mediante filtros sobre la información cargada.
- Deudas pendientes.
- Próximos vencimientos.
- Alertas de pagos pendientes.
- Alertas/control de débitos pendientes.

Los informes deberían permitir responder, entre otras preguntas:

- ¿Quién realizó/cargó el gasto?
- ¿Qué empresa gastó?
- ¿Qué Centro/Recurso estuvo relacionado?
- ¿En qué se gastó?
- ¿Cómo se pagó?
- ¿Cuánto se pagó?
- ¿Cuánto queda pendiente?
- ¿Qué obligaciones vencen próximamente?
- ¿Qué débitos todavía no impactaron?

CRITERIO DE PRIORIDAD HASTA SEPTIEMBRE:

Primero cerrar flujos utilizables de punta a punta.
Después estabilizarlos y testearlos.
Las mejoras secundarias o refactors no bloqueantes quedan para más adelante.

Toda tarea nueva debe evaluarse con esta pregunta:

"¿Esto acerca la versión de septiembre a ser usable o nos desvía?"


============================================================
5. FUTURO QUE LA ARQUITECTURA ACTUAL NO DEBE BLOQUEAR
============================================================

Aunque no sea prioridad para septiembre, lo trabajado hoy debe permitir incorporar sin rehacer la base:

- Estado de Resultados.
- Balance.
- Plan de Cuentas Contables.
- Perfil Contable.
- Perfil Legal.
- Calificación de colaboradores.
- Calificación de contadores.
- Calificación de abogados.
- Órdenes de Pago.
- Autorizaciones de operaciones.
- Agenda.
- Cheques en cartera.
- Nuevos medios de pago.
- Nuevos impuestos y retenciones.
- Nuevas formas digitales de instrumentos existentes.
- Diferentes niveles de permisos.
- Diferentes planes comerciales de OrdenaClick.

El desarrollo actual NO debe implementar estas funciones antes de tiempo si no son necesarias para septiembre, pero tampoco debe tomar decisiones que las vuelvan imposibles.


============================================================
6. MODELO COMERCIAL / HABILITACION DE USO
============================================================

El acceso a OrdenaClick NO debe considerarse libre e ilimitado solamente porque un usuario consiguió registrarse.

Conceptualmente deben existir dos niveles diferentes:

1. AUTENTICACION
   El usuario crea su login e inicia sesión.

2. HABILITACION COMERCIAL / DE USO
   El propietario/administrador de la plataforma OrdenaClick debe poder decidir si ese usuario puede utilizar el sistema y bajo qué condiciones.

Debe quedar prevista la posibilidad de:

- Usuario pendiente de aprobación.
- Usuario habilitado.
- Usuario bloqueado/suspendido.
- Usuario con suscripción activa.
- Usuario sin pago / suscripción vencida.
- Versión demo o período de prueba.

La implementación exacta se definirá más adelante.

IMPORTANTE:
No confundir este nivel con los perfiles Administrador/Colaborador/Contable/Legal.

Una cosa es QUIÉN ES el usuario dentro de una empresa.
Otra cosa es SI PUEDE USAR OrdenaClick comercialmente.


============================================================
7. PLANES DE SUSCRIPCION Y CAPACIDADES
============================================================

OrdenaClick debe poder ofrecer distintos planes según complejidad y necesidad de cada empresa.

Ejemplos conceptuales:

- Empresa simple: menos módulos/configuración visibles.
- Empresa compleja: estructura completa habilitada.

Pero todos deben usar la misma base arquitectónica.

La suscripción debe habilitar o limitar CAPACIDADES, no obligar a migrar datos entre modelos distintos.

Ejemplo:
Una empresa puede comenzar sin administrar Sucursales manualmente.
El sistema conserva de todos modos una estructura coherente.
Más adelante, al cambiar de plan o necesidad, se habilita el módulo y se continúa sobre los mismos datos.

Regla:

CRECIMIENTO = HABILITAR FUNCIONES
NO = MIGRAR O RECONSTRUIR HISTORIA


============================================================
8. ALTA Y CONFIGURACION INICIAL DE EMPRESA
============================================================

La pantalla actual de Alta de Empresa debe conservarse como base funcional.

Para una versión futura orientada a usuarios reales, después de cargar los datos básicos de una empresa debería ofrecerse un recorrido opcional de configuración guiada.

Concepto de experiencia:

PASO 1
Datos básicos de la empresa.

PASO 2
Mensaje similar a:
"¿Te ayudo a configurar tu empresa?"

El usuario puede:

- Iniciar configuración guiada.
- Omitirla y configurar después.

La configuración guiada puede presentarse por pasos, preguntas o modales.

Objetivo:
Dejar precargados los principales selects y estructuras que el usuario necesitará para comenzar a registrar movimientos sin tener que descubrir todos los ABMs uno por uno.

Preguntas/configuraciones posibles:

- ¿Tenés sucursales?
- ¿Tenés depósitos?
- ¿Tenés empleados/personas que quieras registrar como recursos?
- ¿Tenés vehículos?
- ¿Qué Cuentas Bancarias utilizás?
- ¿Qué Tarjetas están asociadas?
- Otros Recursos Operativos necesarios.

La información obtenida también puede servir para sugerir qué plan comercial de OrdenaClick resulta más adecuado para esa empresa.

Esta configuración debe ser OPCIONAL.

El usuario debe poder omitirla y continuar.


CONFIGURACION CONTABLE
----------------------
También deberá existir una configuración contable inicial cuando el Plan Contable esté desarrollado.

Podrá:

- realizarla el Administrador;
- dejarla para después;
- asignarla al Contador contratado/asignado.

La experiencia inicial no debe obligar a una empresa pequeña a conocer o completar configuraciones que no necesita inmediatamente.


============================================================
9. PRINCIPIOS DE MOVIMIENTOS, PAGOS Y VENCIMIENTOS
============================================================

Según la arquitectura vigente:

- Registrar un Movimiento y registrar su Pago son hechos diferentes.
- Un Movimiento puede existir sin pago, con pago parcial, total o múltiples pagos.
- Los Pagos son entidades independientes.
- Un Movimiento puede tener múltiples Pagos.
- Un Pago puede componerse simultáneamente de diferentes medios de cancelación.
- La suma de importes APLICADOS determina cuánto cancela ese Pago.
- Costos financieros no deben confundirse con importe aplicado.
- Vencimiento y Alerta son entidades/conceptos diferentes.
- Los pagos y vencimientos deben conservar historia.
- Los registros con impacto histórico/financiero/contable no se borran físicamente en funcionamiento normal.

Flujo conceptual central:

MOVIMIENTOS / PAGOS / PLANES / CHEQUES
                 |
                 v
            VENCIMIENTOS
                 |
                 v
              ALERTAS

Próximos Vencimientos y Alertas son parte central del producto, no agregados decorativos posteriores.


============================================================
10. INFORMACION HISTORICA Y CONTABILIDAD FUTURA
============================================================

La información necesaria para reportes y contabilidad debe guardarse en el momento del hecho.

No debe deducirse la historia desde el estado actual de tablas maestras.

Ejemplo ya definido:
Si un vehículo estaba asignado a CASA CENTRAL cuando ocurrió un gasto y luego se mueve a SUCURSAL AZUL, el Movimiento histórico debe seguir indicando CASA CENTRAL.

Esto aplica conceptualmente a toda información histórica relevante.

El desarrollo de hoy debe permitir que mañana se pueda reconstruir:

- qué se gastó;
- quién lo cargó;
- qué empresa lo hizo;
- qué centro/recurso estaba involucrado;
- a qué proveedor;
- cómo se pagó;
- con qué instrumento;
- qué importe canceló deuda;
- qué importe fue interés/costo financiero;
- qué saldo quedó pendiente;
- qué vencimientos se generaron.


============================================================
11. ABMs - ESTANDAR OBLIGATORIO
============================================================

Todos los ABMs de OrdenaClick deben seguir el estándar documentado.

APERTURA
- Desde menú lateral.
- Desde botón [+] de otro formulario.

CIERRE
- Si se abrió desde menú: vuelve al menú.
- Si se abrió desde [+]: vuelve exactamente al formulario que lo llamó.
- Debe conservar el estado previo.
- El registro recién creado debe quedar seleccionado automáticamente cuando corresponda.

EDICION
- Sin prompt().
- Carga datos en formulario.
- Guardar cambia a Actualizar.
- Aparece Cancelar.
- Cancelar limpia y vuelve a modo Alta.

ELIMINACION
- Confirmación.
- Baja lógica como regla general.
- PROTECT y no CASCADE para proteger historia, salvo excepciones explícitas.
- Validaciones de negocio.
- Refrescar listado sin salir del ABM.

REACTIVACION
- Si un registro equivalente está inactivo, no crear otro duplicado: reactivar.

VISUAL
- Mismo CSS.
- Mismos colores.
- Mismos radios.
- Mismos tamaños.
- Mismos botones.
- Mismos espaciados.
- Misma lógica visual que Bancos y Centros Operativos.


============================================================
12. REGLAS DE DESARROLLO QUE NO SE NEGOCIAN
============================================================

Reglas actuales del proyecto:

- NO JavaScript inline nuevo.
- NO eliminar comentarios importantes.
- Cada función debe tener docstrings/documentación siguiendo el criterio vigente del proyecto.
- Respetar la arquitectura de navegación.
- Mantener el estilo de código del proyecto.
- Todo ABM abierto desde [+] debe volver al origen, conservar estado y seleccionar lo recién creado cuando corresponda.
- Mantener baja lógica en tablas maestras.
- Evitar cambios amplios/refactors innecesarios durante el cierre de la versión testeable.

IMPORTANTE SOBRE CODIGO HISTORICO:
panel_admin.html puede contener JavaScript inline heredado.
Eso NO debe tomarse como autorización para seguir agregando JavaScript inline.
El código NUEVO debe ubicarse en archivos .js externos.
No refactorizar de golpe todo el JavaScript antiguo solamente para cumplir esta regla, salvo que exista una necesidad concreta y controlada.


============================================================
13. METODO DE TRABAJO ACORDADO PARA MODIFICACIONES
============================================================

No reemplazar archivos completos como práctica habitual.
Puede entregarse un archivo completo como respaldo, pero no como método principal.

Cuando se modifica código se debe indicar:

1. ARCHIVO exacto.
2. QUÉ BUSCAR.
3. QUÉ REEMPLAZAR o DÓNDE AGREGAR.
4. Si cambia una función: entregar la FUNCIÓN COMPLETA modificada.
5. Explicar brevemente qué hace el cambio y por qué.

Si se agrega una función nueva:
- indicar después de qué función debe colocarse;
- entregar la función completa.

Antes de modificar:
- revisar reglas;
- revisar arquitectura;
- revisar el patrón existente equivalente;
- evitar inventar comportamientos nuevos si ya existe un patrón funcional en OrdenaClick.

Principio:

TOMAR PATRON QUE YA FUNCIONA
-> REPLICAR
-> TOCAR SOLO LO NECESARIO
-> VERIFICAR QUE NO SE ROMPA LO DEMAS


============================================================
14. EXPORTACION / IMPORTACION DE EMPRESA
============================================================

Toda entidad que pertenezca funcionalmente al entorno Empresa debe evaluarse respecto de Exportar/Importar Empresa.

Regla principal existente:

Si un dato se perdería al eliminar la empresa y volver a importarla,
debe formar parte del backup salvo exclusión explícita documentada.

Debe preservarse:

- información activa e inactiva;
- movimientos históricos;
- pagos;
- planes;
- cuotas;
- vencimientos;
- alertas;
- cuentas bancarias;
- tarjetas;
- cheques/e-Cheqs;
- archivos relacionados;
- relaciones entre entidades.

Nunca depender de que los IDs originales coincidan con los IDs de una importación nueva.

Cada nueva entidad relacionada con Empresa obliga a revisar las reglas de Exportación/Importación.


============================================================
15. DECISIONES FUNCIONALES YA CERRADAS PARA CARGA SIMPLE
============================================================

Según Reglas_del_desarrollo.md:

- Tipo de Gasto reemplaza conceptualmente al Rubro simple.
- Tipo de Gasto y Proveedor tienen relación muchos a muchos.
- "Relacionado con" pasa a llamarse Recurso Operativo.
- Todo Recurso Operativo debe vincularse a un Centro Operativo mediante asignación.
- El Movimiento conserva históricamente Recurso y Centro imputados.
- Usuario y Recurso Operativo son entidades independientes, vinculables en el futuro.
- Los archivos de movimientos serán registros independientes y múltiples.
- Cuenta Contable quedará visible pero deshabilitada hasta desarrollar Plan Contable.
- No implementar todavía Giras/Rendiciones, pero el modelo no debe impedirlas.

Jerarquía visual:
REGISTRO, PAGO y PLAN son etapas relacionadas, pero no deben confundirse visualmente.


============================================================
16. ESTADO ACTUAL DEL DESARROLLO AL CREAR ESTE DOCUMENTO
============================================================

Fecha de referencia: agosto de 2026.

Se está desarrollando principalmente el perfil ADMINISTRADOR.

El foco actual está en CARGA SIMPLE y especialmente en PAGOS.

Se terminó/avanzó el ABM de TARJETAS y se comenzó a integrar TARJETAS como medio de pago dentro de una tarjeta de Pago.

IMPORTANTE PARA RETOMAR:

La versión actualmente colocada en VS Code proviene de una modificación reciente de panel_admin.html en la que se agregó lógica de Tarjeta dentro del propio panel.
Posteriormente se recordó/reforzó la regla:

"NO JavaScript inline nuevo".

Por lo tanto, NO DESCARTAR DE GOLPE lo ya hecho ni volver arbitrariamente a una versión anterior.

El próximo trabajo debe tomar el estado actual de VS Code y llevarlo de forma controlada a la arquitectura correcta:

- conservar el HTML útil del acordeón Tarjetas;
- ajustar su estética para que replique exactamente otros acordeones;
- mover la lógica nueva de Tarjetas de Pago a un archivo .js externo;
- no refactorizar JavaScript histórico que no sea necesario;
- verificar cada cambio de forma localizada.

Ajustes pendientes ya conversados para el acordeón Tarjetas:

- Debe respetar exactamente el formato visual de los otros acordeones.
- Debe tener botón "REGISTRAR PAGO CON TARJETA".
- Debe permitir registrar múltiples operaciones con tarjeta dentro de un mismo Pago si la arquitectura lo requiere.
- Debe permitir modificar la operación registrada.
- Debe permitir cancelar la modificación.
- "CANCELAR CAMBIOS" debe usar el mismo estilo rojo que los otros acordeones.
- Debe impedir eliminar la operación que se está editando y respetar las mismas protecciones de edición existentes en otros medios de pago.
- Debe evitar comenzar otra edición incompatible mientras exista una operación en edición, según el patrón existente.
- El orden del formulario debe ser lógico: primero campos de datos, luego comprobante/archivo, luego botones.
- Se decidió QUITAR "Observaciones" del bloque de Pago con Tarjeta.
- No dejar referencias JavaScript muertas a Observaciones luego de quitar el campo.
- La tarjeta maestra del ABM y la operación de Pago con Tarjeta son conceptos diferentes.

El ABM Tarjetas debe seguir permitiendo alta, modificación, baja lógica/reactivación y regreso al origen según las reglas de los demás ABMs.


============================================================
17. TARJETAS - CRITERIOS ARQUITECTONICOS EXISTENTES
============================================================

El ABM Tarjetas pertenece a Empresa.

Las Tarjetas deben poder relacionarse con una Cuenta Bancaria propia.

Una operación de Pago con Tarjeta debe conservar, según corresponda:

- Tarjeta utilizada.
- Fecha.
- Importe aplicado al Movimiento.
- Para crédito: cuotas e intereses de financiación.
- Referencia/comprobante cuando corresponda.

Regla económica importante:

El importe aplicado con Tarjeta cancela deuda del Movimiento.
Los intereses de financiación son costo económico adicional y NO aumentan el importe aplicado al Movimiento.

La relación Tarjeta -> Cuenta Bancaria debe permitir en el futuro:

- consultar movimientos por Tarjeta;
- comparar contra resumen;
- controlar gastos incluidos en resumen;
- conciliaciones y controles posteriores.

Tarjetas y sus operaciones relacionadas con Pagos forman parte del entorno Empresa y deben contemplarse en Exportar/Importar Empresa.


============================================================
18. EXPERIENCIA DE USUARIO - PRINCIPIO GENERAL
============================================================

OrdenaClick puede tener una arquitectura interna completa sin obligar al usuario inicial a configurarla toda manualmente.

Objetivo UX:

- Entrada simple.
- Configuración progresiva.
- Defaults inteligentes.
- Posibilidad de omitir configuración avanzada.
- Poder comenzar a registrar movimientos rápidamente.
- No perder capacidad de crecimiento posterior.

La simplicidad debe resolverse mediante experiencia y automatización, no eliminando estructura de datos.


============================================================
19. CRITERIO PARA NUEVAS FUNCIONALIDADES
============================================================

Antes de agregar cualquier funcionalidad relevante, preguntar:

1. ¿Pertenece al entorno Empresa?
2. ¿Debe conservar historia?
3. ¿Puede generar un Vencimiento?
4. ¿Puede generar una Alerta?
5. ¿Tiene impacto contable futuro?
6. ¿Debe incluirse en Exportar/Importar Empresa?
7. ¿Debe usar baja lógica?
8. ¿Cómo se comporta si la empresa crece?
9. ¿Debe estar siempre visible o puede habilitarse según plan?
10. ¿Qué perfil puede verla/usarla/modificarla?
11. ¿Acerca o desvía la versión usable de septiembre?


============================================================
20. PRINCIPIO FINAL
============================================================

OrdenaClick debe ser fácil para una empresa pequeña sin quedar chico para una empresa que crece.

El sistema debe permitir comenzar simple y habilitar complejidad gradualmente SIN PERDER DATOS, SIN MIGRAR HISTORIA y SIN CAMBIAR DE ARQUITECTURA.

Hasta la versión testeable de septiembre, priorizar:

FUNCIONAR -> CONSERVAR DATOS -> RESPETAR FLUJOS -> SER TESTEABLE -> LUEGO MEJORAR.

============================================================
ESTO ES ESPECIALMENTE PARA LA IA: ACA TU RESPUESTA CUANDO TE PLENTEE ORDENACLICK
============================================================
Ahora que tengo el panorama bastante más completo, creo que la idea de OrdenaClick es más ambiciosa que un sistema de carga de gastos, pero también tiene una lógica bastante coherente detrás. Lo importante va a ser no intentar construir toda esa ambición al mismo tiempo.

Lo que entiendo que realmente es OrdenaClick

OrdenaClick no apunta solamente a registrar facturas y decir cuánto se pagó.

El núcleo que estás construyendo es una especie de historia operativa y económica estructurada de una empresa.

Cuando alguien registra un movimiento, no querés guardar solamente:

“Se gastaron $100.000.”

Querés poder reconstruir:

Qué empresa gastó → quién realizó/cargó el gasto → para qué → asociado a qué recurso/sector/sucursal → a qué proveedor → cuándo → cuándo vence → cómo se pagó → desde qué cuenta/tarjeta/cheque → cuánto quedó pendiente → qué ocurrió después.

Ese nivel de información es el que después permite que aparezcan naturalmente los informes, las alertas y, bastante más adelante, la contabilidad.

Y me parece una decisión acertada que la información operativa sea la fuente, en vez de pedirle al usuario que cargue después otra vez los mismos datos para obtener informes.

La decisión arquitectónica que más me gusta

Hay una idea tuya que me parece especialmente importante:

una empresa simple y una empresa compleja no deberían vivir en arquitecturas diferentes.

Eso evita un problema enorme a futuro.

Imaginemos:

2026: un profesional tiene una empresa, una cuenta bancaria y ningún empleado.

OrdenaClick puede esconderle sucursales, depósitos, centros operativos, estructuras contables avanzadas, etc.

Pero internamente sus movimientos siguen entrando en una estructura compatible con esas cosas.

Después:

2028: tiene 3 sucursales, 25 empleados, vehículos, depósitos y varias cuentas.

No debería escuchar:

“Ahora tenés que pasar al sistema empresarial y migrar tus datos.”

Simplemente se habilitan nuevas capacidades y empieza a clasificar con mayor profundidad sin destruir los años anteriores.

Eso es muy valioso.

La frase que usamos antes lo resume bien:

simplificar la interfaz, no simplificar los datos.

Y esto encaja muy bien con los planes

También veo coherencia entre arquitectura y modelo comercial.

No necesariamente necesitás fabricar:

OrdenaClick Simple
OrdenaClick PyME
OrdenaClick Enterprise

como tres productos técnicamente diferentes.

Puede existir un OrdenaClick y habilitar capacidades.

Una empresa chica podría tener muchas cosas resueltas automáticamente. Una más compleja puede empezar a configurarlas manualmente.

Eso permite incluso que el sistema recomiende:

“Por cómo está organizada tu empresa, probablemente te convenga este plan.”

En lugar de obligar al usuario nuevo a entender una tabla de 40 características antes de haber utilizado el producto.

La configuración inicial que planteaste me parece especialmente importante

Porque hay un problema típico en los sistemas administrativos: para poder usarlos primero hay que configurarlos durante horas.

Y eso mata la experiencia inicial.

Vos ya construiste muchos ABM porque son necesarios para que después los selects tengan información. Pero imaginemos un usuario nuevo.

Crea su empresa.

Entra a Carga Simple.

Y encuentra:

Cuenta bancaria: vacío
Tarjeta: vacío
Empleado: vacío
Vehículo: vacío
Sucursal: vacío

Técnicamente el sistema funciona.

Para el usuario, no funciona.

Tu idea del asistente inicial soluciona justamente eso.

Podría ser algo como:

1. Datos de tu empresa

Ya tenemos buena parte de esto.

2. ¿Querés que te ayudemos a configurarla?

Configurar ahora / Lo haré después

Y recién ahí empieza un recorrido amigable.

¿Tu empresa tiene sucursales?

No → OrdenaClick utiliza automáticamente la estructura base.

Sí → carguemos las sucursales.

Después:

¿Tenés empleados?

¿Utilizan vehículos?

¿Con qué bancos trabajás?

¿Qué cuentas bancarias utilizás?

¿Utilizás tarjetas de débito o crédito?

Y cuando termina, la persona entra a Carga Simple y los selects ya tienen sentido.

Eso convierte todos los ABM que estamos haciendo ahora en algo más interesante: no solamente sirven desde Administración; también pueden reutilizarse dentro del onboarding.

Incluso veo una segunda utilidad

Ese recorrido puede funcionar simultáneamente como configurador y diagnóstico.

Por ejemplo, si responde:

5 sucursales
3 depósitos
40 empleados
12 vehículos
6 cuentas bancarias
varias tarjetas
necesita permisos diferenciados
quiere contabilidad

OrdenaClick ya sabe que probablemente no estamos frente a una empresa “simple”.

Por eso tu onboarding podría terminar diciendo algo como:

Tu empresa ya está configurada para comenzar.

Por la estructura que cargaste, estas son las funcionalidades que podrían resultarte útiles.

Ahí aparece la recomendación comercial después de aportar valor, no antes.

Me parece mucho mejor que diseñar el sistema alrededor de planes rígidos desde el comienzo.

Contabilidad

También me parece correcta tu idea de no forzarla ahora pero preparar el terreno.

El Administrador podría eventualmente elegir:

Configurar contabilidad ahora.

o:

Dejar configuración contable al contador.

Eso encaja perfectamente con que posteriormente exista el perfil Contable.

Y hay una consecuencia arquitectónica importante: cuando desarrollemos el plan de cuentas, no deberíamos obligar a reconstruir todos los movimientos anteriores.

Por eso tenemos que seguir teniendo cuidado ahora con cosas aparentemente pequeñas como:

capital vs. intereses, fechas, medios de pago, categorías, proveedores, recursos, empresas, usuarios que realizaron acciones, etc.

Hoy parecen detalles de Carga Simple.

Mañana son materia prima para:

Estado de Resultados y Balance.

Administrador y Colaborador

También me queda mucho más claro el límite.

El Administrador administra la organización.

El Colaborador opera dentro de la organización que le fue habilitada.

Eso significa que Colaborador no es simplemente “Administrador con botones ocultos”.

Conceptualmente tiene otra responsabilidad.

Puede:

registrar movimientos, cargar pagos y utilizar los maestros necesarios para completar esas operaciones.

Pero no debería poder decidir unilateralmente cuestiones estructurales como crear empresas o administrar quién tiene acceso a ellas.

Más adelante tendremos que convertir esto en permisos concretos, pero el concepto está bien definido.

Hay otro sistema por encima de las empresas

Lo que mencionaste sobre el acceso me parece muy importante y hasta ahora no lo teníamos suficientemente presente.

Hay realmente dos niveles administrativos.

Uno es:

Administrador de una empresa dentro de OrdenaClick.

Y otro completamente diferente:

Administrador/propietario de OrdenaClick.

Este último necesita eventualmente poder controlar:

usuarios;
estado de suscripción;
demos;
habilitación;
suspensión/bloqueo;
posiblemente planes;
posiblemente límites y capacidades.

Eso significa que:

Tener login válido ≠ tener derecho indefinido a utilizar OrdenaClick.

La autenticación responde:

“¿Quién sos?”

La autorización empresarial responde:

“¿Qué podés hacer?”

Y la habilitación comercial de OrdenaClick responde:

“¿Tu cuenta puede utilizar actualmente el servicio y con qué capacidades?”

Conviene mantener esas tres cosas separadas conceptualmente desde el principio.

Donde sí pondría muchísimo cuidado

La escalabilidad que estás pensando es buena, pero tiene un riesgo: sobrearquitectura.

Es muy fácil empezar a pensar:

“Esto algún día podría necesitar…”

y terminar desarrollando durante meses infraestructura para casos que todavía no existen.

Por eso el objetivo de septiembre que marcaste es fundamental.

Yo usaría una regla:

Preparar para el futuro no significa desarrollar hoy el futuro.

Ejemplo.

Necesitamos que un Pago tenga información suficientemente estructurada para que mañana pueda contabilizarse.

Sí.

Necesitamos desarrollar ahora el motor completo de asientos contables porque algún día tendremos Balance.

No.

Necesitamos que los permisos Admin/Colaborador estén bien pensados.

Sí.

Necesitamos desarrollar ahora Legal, Contable, calificaciones y marketplace de profesionales.

No.

Necesitamos pensar el concepto de planes y capacidades.

Sí.

Necesitamos ahora construir todo el sistema de billing y cinco niveles comerciales.

Probablemente no para septiembre.

Esa separación nos puede ahorrar muchísimo tiempo.

Y septiembre me parece un objetivo muy bueno

Porque obliga a dejar de medir progreso por cantidad de código o cantidad de ABM.

El verdadero examen debería ser que una persona que nunca vio OrdenaClick pueda:

crear su usuario → obtener acceso → crear/configurar una empresa → invitar/asignar un colaborador → cargar operaciones reales durante varios días → registrar cómo se pagaron → consultar pendientes → recibir alertas → obtener información útil de lo que cargó.

Y que el Colaborador pueda entrar y hacer su trabajo sin tener acceso a decisiones que corresponden al Administrador.

Si conseguimos eso funcionando en la nube, aunque todavía no haya Balance, perfil Legal, calificaciones ni diez planes comerciales, ya existe un producto testeable.

Y ahí las personas reales nos van a empezar a mostrar qué cosas que hoy creemos importantes realmente lo son.

Finalmente, algo que ahora entiendo mejor de cómo venís construyendo

Al principio podía parecer que estábamos haciendo muchos ABM independientes: Bancos, Cuentas Bancarias, Tarjetas, Recursos, etc.

Ahora entiendo por qué estás siendo tan insistente con cosas como los [+], volver exactamente al lugar anterior y no perder lo cargado.

No es solamente estética.

Estás intentando que la carga administrativa no obligue al usuario a pensar en la estructura interna del sistema.

Si estoy registrando un pago y descubro que falta una tarjeta:

[+] Tarjeta → la creo → vuelvo → continúa mi pago.

No:

salir → Administración → ABM → Tarjetas → crear → volver a Carga Simple → encontrar nuevamente el registro → volver al pago → completar.

Ese principio debería mantenerse en todo OrdenaClick.

Y ahora que conozco el objetivo de septiembre y el horizonte posterior, entiendo mucho mejor por qué varias decisiones que pueden parecer pequeñas son en realidad reglas de producto.

Tenemos una dirección bastante definida. Lo que necesitamos ahora es volver a lo concreto y avanzar con disciplina: terminar bien Tarjetas en Pago, sin romper lo anterior, y seguir cerrando el circuito operativo que necesitamos probar en septiembre.
============================================================
FIN DEL DOCUMENTO
============================================================
```
