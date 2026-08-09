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