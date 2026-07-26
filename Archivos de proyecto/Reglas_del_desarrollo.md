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