let ultimoTipoGastoCreado = null;
let tipoGastoEditandoId = null;
let tipoGastoReactivandoId = null;
let estadoFormularioTipoGasto = null;


/* =========================================
   INICIALIZACIÓN
========================================= */

function iniciarABMTiposGasto(){

    const btnGuardar =
        document.getElementById(
            "btnGuardarTipoGasto"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarTipoGasto"
        );

    const btnVolver =
        document.getElementById(
            "btnVolverTipoGasto"
        );

    const btnAgregarProveedor =
        document.getElementById(
            "btnAgregarProveedorTipoGasto"
        );


    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarTipoGasto
        );

    }


    if(btnCancelar){

        btnCancelar.addEventListener(
            "click",
            cancelarEdicionTipoGasto
        );

    }


    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeABMTiposGasto
        );

    }


    if(btnAgregarProveedor){

        btnAgregarProveedor.addEventListener(
            "click",
            abrirABMProveedoresDesdeTipoGasto
        );

    }


    document

        .querySelectorAll(
            ".btn-modificar-tipo-gasto"
        )

        .forEach(

            function(boton){

                boton.addEventListener(

                    "click",

                    function(){

                        const fila =
                            boton.closest(
                                ".fila-tipo-gasto"
                            );

                        if(!fila){

                            return;

                        }

                        modificarTipoGasto(

                            fila.dataset.tipoGastoId,

                            fila.dataset.tipoGastoNombre,

                            fila.dataset.tipoGastoDescripcion,

                            fila.dataset.proveedores

                        );

                    }

                );

            }

        );


    document

        .querySelectorAll(
            ".btn-eliminar-tipo-gasto"
        )

        .forEach(

            function(boton){

                boton.addEventListener(

                    "click",

                    function(){

                        const tipoGastoId =
                            boton.dataset.tipoGastoId;

                        if(!tipoGastoId){

                            return;

                        }

                        eliminarTipoGasto(
                            tipoGastoId
                        );

                    }

                );

            }

        );

}


/* =========================================
   FUNCIONES AUXILIARES
========================================= */

function valorTipoGasto(id){

    const elemento =
        document.getElementById(
            id
        );

    return elemento
        ? elemento.value.trim()
        : "";

}


function proveedoresSeleccionadosTipoGasto(){

    return Array

        .from(

            document.querySelectorAll(
                ".proveedor-tipo-gasto:checked"
            )

        )

        .map(

            checkbox => checkbox.value

        );

}

function guardarEstadoFormularioTipoGasto(){

    estadoFormularioTipoGasto = {

        nombre:

            document
                .getElementById(
                    "nombreTipoGasto"
                ).value,

        descripcion:

            document
                .getElementById(
                    "descripcionTipoGasto"
                ).value,

        proveedores:

            proveedoresSeleccionadosTipoGasto()

    };

}


function restaurarEstadoFormularioTipoGasto(){

    if(!estadoFormularioTipoGasto){

        return;

    }

    document
        .getElementById(
            "nombreTipoGasto"
        ).value =
        estadoFormularioTipoGasto.nombre;

    document
        .getElementById(
            "descripcionTipoGasto"
        ).value =
        estadoFormularioTipoGasto.descripcion;

    document

        .querySelectorAll(
            ".proveedor-tipo-gasto"
        )

        .forEach(

            function(check){

                check.checked =

                    estadoFormularioTipoGasto
                        .proveedores

                        .includes(
                            check.value
                        );

            }

        );

}


function actualizarProveedoresDelTipoGasto(){

    restaurarEstadoFormularioTipoGasto();


    if(
        typeof ultimoProveedorCreado === "undefined" ||
        !ultimoProveedorCreado
    ){

        return;

    }


    const contenedor =
        document.getElementById(
            "proveedoresTipoGasto"
        );


    if(!contenedor){

        console.error(
            "No se encontró el contenedor de proveedores del tipo de gasto."
        );

        ultimoProveedorCreado = null;

        return;

    }


    const proveedorId =
        String(
            ultimoProveedorCreado.id
        );


    let checkbox =
        contenedor.querySelector(
            `.proveedor-tipo-gasto[value="${proveedorId}"]`
        );


    /*
     * El formulario restaurado contiene la lista anterior.
     * Si el proveedor recién creado todavía no aparece,
     * lo incorporamos al listado sin recargar todo el ABM.
     */
    if(!checkbox){

        const mensajeSinProveedores =
            contenedor.querySelector(
                ".mensaje-sin-proveedores"
            );


        if(mensajeSinProveedores){

            mensajeSinProveedores.remove();

        }


        const etiqueta =
            document.createElement(
                "label"
            );


        etiqueta.style.display =
            "flex";

        etiqueta.style.alignItems =
            "center";

        etiqueta.style.gap =
            "10px";

        etiqueta.style.padding =
            "10px 12px";

        etiqueta.style.background =
            "#151a26";

        etiqueta.style.border =
            "1px solid #2b3447";

        etiqueta.style.borderRadius =
            "10px";

        etiqueta.style.cursor =
            "pointer";


        checkbox =
            document.createElement(
                "input"
            );


        checkbox.type =
            "checkbox";

        checkbox.className =
            "proveedor-tipo-gasto";

        checkbox.value =
            proveedorId;


        const texto =
            document.createElement(
                "span"
            );


        texto.appendChild(
            document.createTextNode(
                ultimoProveedorCreado.razon_social ||
                "Proveedor"
            )
        );


        if(ultimoProveedorCreado.cuit){

            const cuit =
                document.createElement(
                    "span"
                );


            cuit.style.color =
                "#8b93a7";

            cuit.style.fontSize =
                "13px";


            cuit.textContent =
                ` · ${ultimoProveedorCreado.cuit}`;


            texto.appendChild(
                cuit
            );

        }


        etiqueta.appendChild(
            checkbox
        );


        etiqueta.appendChild(
            texto
        );


        contenedor.appendChild(
            etiqueta
        );

    }


    checkbox.checked = true;


    if(
        estadoFormularioTipoGasto &&
        !estadoFormularioTipoGasto
            .proveedores
            .includes(proveedorId)
    ){

        estadoFormularioTipoGasto
            .proveedores
            .push(proveedorId);

    }


    ultimoProveedorCreado = null;

}

/* =========================================
   ABM ANIDADO DE PROVEEDORES
========================================= */

function abrirABMProveedoresDesdeTipoGasto(){

    guardarEstadoFormularioTipoGasto();

    mostrarABMProveedores(
        "tipo_gasto"
    );

}
/* =========================================
   GUARDAR / ACTUALIZAR
========================================= */

async function guardarTipoGasto(){

    const empresa =
        valorTipoGasto(
            "empresaActiva"
        );

    const nombre =
        valorTipoGasto(
            "nombreTipoGasto"
        );

    const descripcion =
        valorTipoGasto(
            "descripcionTipoGasto"
        );


    if(!empresa){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }


    if(!nombre){

        alert(
            "Ingrese el nombre del tipo de gasto."
        );

        const input =
            document.getElementById(
                "nombreTipoGasto"
            );

        if(input){

            input.focus();

        }

        return;

    }


    const formulario =
        new FormData();


    formulario.append(
        "empresa",
        empresa
    );

    formulario.append(
        "nombre",
        nombre
    );

    formulario.append(
        "descripcion",
        descripcion
    );


    proveedoresSeleccionadosTipoGasto()

        .forEach(

            function(proveedor){

                formulario.append(
                    "proveedores",
                    proveedor
                );

            }

        );


    const estaEditando =
        tipoGastoEditandoId !== null;

    const estaReactivando =
        tipoGastoReactivandoId !== null;


    let url =
        "/tipos-gasto/guardar/";


    if(estaEditando){

        url =
            "/tipos-gasto/modificar/";

        formulario.append(
            "tipo_gasto",
            tipoGastoEditandoId
        );

    }else if(estaReactivando){

        url =
            "/tipos-gasto/reactivar/";

        formulario.append(
            "tipo_gasto",
            tipoGastoReactivandoId
        );

    }


    try{

        const respuesta =
            await fetch(
                url,
                {
                    method: "POST",

                    headers: {

                        "X-CSRFToken":
                            obtenerCookie(
                                "csrftoken"
                            )

                    },

                    body: formulario
                }
            );


        const resultado =
            await respuesta.json();


        if(
            resultado.requiere_reactivacion &&
            resultado.tipo_gasto
        ){

            cargarTipoGastoParaReactivar(
                resultado.tipo_gasto
            );

            alert(
                resultado.mensaje ||
                "El tipo de gasto está inactivo. Puede reactivarlo."
            );

            return;

        }


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            let mensaje =
                "No se pudo guardar el tipo de gasto.";


            if(estaEditando){

                mensaje =
                    "No se pudo modificar el tipo de gasto.";

            }else if(estaReactivando){

                mensaje =
                    "No se pudo reactivar el tipo de gasto.";

            }


            alert(
                resultado.mensaje ||
                mensaje
            );

            return;

        }


        if(
            !estaEditando &&
            resultado.tipo_gasto
        ){

            ultimoTipoGastoCreado = {

                id:
                    String(
                        resultado.tipo_gasto.id
                    ),

                nombre:
                    resultado.tipo_gasto.nombre ||
                    nombre

            };

        }


        tipoGastoEditandoId = null;
        tipoGastoReactivandoId = null;
        estadoFormularioTipoGasto = null;

        await mostrarABMTiposGasto(
            origenABM
        );


    }catch(error){

        console.error(
            "Error guardando tipo de gasto:",
            error
        );

        alert(

            estaEditando

                ? "Ocurrió un error al modificar el tipo de gasto."

                : "Ocurrió un error al guardar el tipo de gasto."

        );

    }

}
function cargarTipoGastoParaReactivar(
    tipoGasto
){

    tipoGastoEditandoId = null;

    tipoGastoReactivandoId =
        String(
            tipoGasto.id
        );


    const valores = {

        nombreTipoGasto:
            tipoGasto.nombre,

        descripcionTipoGasto:
            tipoGasto.descripcion

    };


    Object.entries(
        valores
    ).forEach(
        function([id, valor]){

            const elemento =
                document.getElementById(
                    id
                );

            if(elemento){

                elemento.value =
                    valor || "";

            }

        }
    );


    document

        .querySelectorAll(
            ".proveedor-tipo-gasto"
        )

        .forEach(
            function(checkbox){

                checkbox.checked = false;

            }
        );


    if(
        tipoGasto.proveedores
    ){

        tipoGasto.proveedores.forEach(

            function(idProveedor){

                const checkbox =
                    document.querySelector(
                        '.proveedor-tipo-gasto[value="' +
                        idProveedor +
                        '"]'
                    );

                if(checkbox){

                    checkbox.checked = true;

                }

            }

        );

    }


    const btnGuardar =
        document.getElementById(
            "btnGuardarTipoGasto"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarTipoGasto"
        );


    if(btnGuardar){

        btnGuardar.textContent =
            "Activar";

    }


    if(btnCancelar){

        btnCancelar.style.display =
            "inline-block";

    }


    const inputNombre =
        document.getElementById(
            "nombreTipoGasto"
        );


    if(inputNombre){

        inputNombre.focus();
        inputNombre.select();

    }

}


/* =========================================
   MODIFICAR
========================================= */

function modificarTipoGasto(
    tipoGastoId,
    nombre,
    descripcion,
    proveedores
){

    tipoGastoReactivandoId = null;

    tipoGastoEditandoId =
        String(
            tipoGastoId
        );


    document.getElementById(
        "nombreTipoGasto"
    ).value =
        nombre || "";


    document.getElementById(
        "descripcionTipoGasto"
    ).value =
        descripcion || "";


    document

        .querySelectorAll(
            ".proveedor-tipo-gasto"
        )

        .forEach(
            function(checkbox){

                checkbox.checked = false;

            }
        );


    if(proveedores){

        proveedores
            .split(",")

            .filter(
                valor => valor !== ""
            )

            .forEach(

                function(idProveedor){

                    const checkbox =
                        document.querySelector(
                            '.proveedor-tipo-gasto[value="' +
                            idProveedor +
                            '"]'
                        );

                    if(checkbox){

                        checkbox.checked = true;

                    }

                }

            );

    }


    const btnGuardar =
        document.getElementById(
            "btnGuardarTipoGasto"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarTipoGasto"
        );


    if(btnGuardar){

        btnGuardar.textContent =
            "Modificar";

    }


    if(btnCancelar){

        btnCancelar.style.display =
            "inline-block";

    }


    const inputNombre =
        document.getElementById(
            "nombreTipoGasto"
        );


    if(inputNombre){

        inputNombre.focus();
        inputNombre.select();

    }

}


/* =========================================
   CANCELAR
========================================= */

function cancelarEdicionTipoGasto(){

    tipoGastoEditandoId = null;

    tipoGastoReactivandoId = null;

    estadoFormularioTipoGasto = null;


    limpiarFormularioTipoGasto();

}

/* =========================================
   LIMPIEZA DEL FORMULARIO
========================================= */

function limpiarFormularioTipoGasto(){

    document.getElementById(
        "nombreTipoGasto"
    ).value = "";

    document.getElementById(
        "descripcionTipoGasto"
    ).value = "";

    document

        .querySelectorAll(
            ".proveedor-tipo-gasto"
        )

        .forEach(

            function(checkbox){

                checkbox.checked = false;

            }

        );

    const btnGuardar =
        document.getElementById(
            "btnGuardarTipoGasto"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarTipoGasto"
        );


    if(btnGuardar){

        btnGuardar.textContent =
            "Guardar";

    }


    if(btnCancelar){

        btnCancelar.style.display =
            "none";

    }

}


/* =========================================
   ELIMINAR
========================================= */

async function eliminarTipoGasto(
    idTipoGasto
){

    if(

        !confirm(
            "¿Desea eliminar el tipo de gasto?"
        )

    ){

        return;

    }


    const formulario =
        new FormData();

    const empresa =
        valorTipoGasto(
            "empresaActiva"
        );

    formulario.append(
        "empresa",
        empresa
    );

    formulario.append(
        "tipo_gasto",
        idTipoGasto
    );


    try{

        const respuesta =
            await fetch(

                "/tipos-gasto/eliminar/",

                {

                    method: "POST",

                    headers: {

                        "X-CSRFToken":
                            obtenerCookie(
                                "csrftoken"
                            )

                    },

                    body: formulario

                }

            );


        const resultado =
            await respuesta.json();


        if(

            !respuesta.ok ||
            !resultado.ok

        ){

            alert(

                resultado.mensaje ||

                "No fue posible eliminar el tipo de gasto."

            );

            return;

        }


        await mostrarABMTiposGasto(
            origenABM
        );


    }catch(error){

        console.error(error);

        alert(
            "Ocurrió un error al eliminar el tipo de gasto."
        );

    }

}


/* =========================================
   VOLVER
========================================= */

function volverDesdeABMTiposGasto(){

    tipoGastoEditandoId = null;

    tipoGastoReactivandoId = null;


    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );


    if(
        origenABM === "registro" &&
        contenidoAnteriorABM &&
        contenidoOperativo
    ){

        contenidoOperativo.innerHTML =
            "";


        contenidoOperativo.appendChild(
            contenidoAnteriorABM
        );


        contenidoAnteriorABM = null;


        actualizarTipoGastoDelRegistro();


        return;

    }


    ultimoTipoGastoCreado = null;

    estadoFormularioTipoGasto = null;

    contenidoAnteriorABM = null;


    if(
        typeof mostrarSubmenu ===
        "function"
    ){

        mostrarSubmenu(
            "abms"
        );

    }

}


/* =========================================
   REFRESCO
========================================= */

async function refrescarTiposGasto(){

    await mostrarABMTiposGasto(
        origenABM
    );

}


/* =========================================
   INICIO
========================================= */

document.addEventListener(

    "DOMContentLoaded",

    function(){

        iniciarABMTiposGasto();

    }

);

