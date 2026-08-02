let ultimoTipoGastoCreado = null;
let tipoGastoEditandoId = null;
let tipoGastoReactivandoId = null;
let estadoFormularioTipoGasto = null;

let proveedoresRelacionadosTipoGasto = new Set();


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

    const btnCancelarModal =
        document.getElementById(
            "btnCancelarModalProveedoresTipoGasto"
        );

    const btnGuardarModal =
        document.getElementById(
            "btnGuardarModalProveedoresTipoGasto"
        );

    const btnNuevoProveedorModal =
        document.getElementById(
            "btnNuevoProveedorDesdeModalTipoGasto"
        );

    const buscador =
        document.getElementById(
            "buscarProveedorTipoGasto"
        );

    const buscadorTiposGasto =
    document.getElementById(
        "buscarTipoGastoABM"
    );

    proveedoresRelacionadosTipoGasto =
        new Set();


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
            abrirModalProveedoresTipoGasto
        );

    }


    if(btnCancelarModal){

        btnCancelarModal.addEventListener(
            "click",
            cerrarModalProveedoresTipoGasto
        );

    }


    if(btnGuardarModal){

        btnGuardarModal.addEventListener(
            "click",
            guardarSeleccionProveedoresTipoGasto
        );

    }


    if(btnNuevoProveedorModal){

        btnNuevoProveedorModal.addEventListener(
            "click",
            abrirABMProveedoresDesdeTipoGasto
        );

    }


    if(buscador){

        buscador.addEventListener(
            "input",
            filtrarProveedoresModalTipoGasto
        );

    }

    if(buscadorTiposGasto){

        buscadorTiposGasto.addEventListener(
            "input",
            filtrarTiposGastoABM
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


    renderizarProveedoresRelacionadosTipoGasto();

}

function filtrarTiposGastoABM(){

    const buscador =
        document.getElementById(
            "buscarTipoGastoABM"
        );

    const mensajeSinResultados =
        document.getElementById(
            "sinResultadosTipoGastoABM"
        );


    const texto =
        buscador
            ? buscador.value
                .trim()
                .toLowerCase()
            : "";


    const tarjetas =
        document.querySelectorAll(
            ".fila-tipo-gasto"
        );


    let visibles = 0;


    tarjetas.forEach(
        function(tarjeta){

            const contenido =
                (
                    tarjeta.dataset.busqueda ||
                    ""
                )
                .toLowerCase();


            const coincide =
                contenido.includes(
                    texto
                );


            tarjeta.style.display =
                coincide
                    ? "flex"
                    : "none";


            if(coincide){

                visibles++;

            }

        }
    );


    if(mensajeSinResultados){

        mensajeSinResultados.style.display =
            (
                tarjetas.length > 0 &&
                visibles === 0
            )
                ? "block"
                : "none";

    }

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

    return Array.from(
        proveedoresRelacionadosTipoGasto
    );

}

function proveedoresMarcadosModalTipoGasto(){

    return Array
        .from(
            document.querySelectorAll(
                ".proveedor-modal-tipo-gasto:checked"
            )
        )
        .map(
            function(check){

                return String(
                    check.value
                );

            }
        );

}

function abrirModalProveedoresTipoGasto(){

    const modal =
        document.getElementById(
            "modalProveedoresTipoGasto"
        );

    const buscador =
        document.getElementById(
            "buscarProveedorTipoGasto"
        );


    if(!modal){

        return;

    }


    document
        .querySelectorAll(
            ".proveedor-modal-tipo-gasto"
        )
        .forEach(
            function(check){

                check.checked =
                    proveedoresRelacionadosTipoGasto
                        .has(
                            String(
                                check.value
                            )
                        );

            }
        );


    if(buscador){

        buscador.value = "";

    }


    filtrarProveedoresModalTipoGasto();


    modal.style.display =
        "flex";


    if(buscador){

        buscador.focus();

    }

}

function cerrarModalProveedoresTipoGasto(){

    const modal =
        document.getElementById(
            "modalProveedoresTipoGasto"
        );


    if(!modal){

        return;

    }


    modal.style.display =
        "none";

}

function filtrarProveedoresModalTipoGasto(){

    const buscador =
        document.getElementById(
            "buscarProveedorTipoGasto"
        );


    const texto =
        buscador
            ? buscador.value
                .trim()
                .toLowerCase()
            : "";


    document
        .querySelectorAll(
            ".tarjeta-proveedor-modal-tipo-gasto"
        )
        .forEach(
            function(tarjeta){

                const nombre =
                    (
                        tarjeta.dataset
                            .proveedorNombre ||
                        ""
                    )
                    .toLowerCase();

                const cuit =
                    (
                        tarjeta.dataset
                            .proveedorCuit ||
                        ""
                    )
                    .toLowerCase();


                const coincide =
                    nombre.includes(
                        texto
                    ) ||
                    cuit.includes(
                        texto
                    );


                tarjeta.style.display =
                    coincide
                        ? "flex"
                        : "none";

            }
        );

}

function guardarSeleccionProveedoresTipoGasto(){

    const seleccionados =
        document.querySelectorAll(
            ".proveedor-modal-tipo-gasto:checked"
        );


    proveedoresRelacionadosTipoGasto =
        new Set(
            Array
                .from(
                    seleccionados
                )
                .map(
                    function(check){

                        return String(
                            check.value
                        );

                    }
                )
        );


    renderizarProveedoresRelacionadosTipoGasto();

    cerrarModalProveedoresTipoGasto();

}

function renderizarProveedoresRelacionadosTipoGasto(){

    const contenedor =
        document.getElementById(
            "proveedoresTipoGasto"
        );


    if(!contenedor){

        return;

    }


    contenedor.innerHTML = "";


    if(
        proveedoresRelacionadosTipoGasto
            .size === 0
    ){

        const mensaje =
            document.createElement(
                "div"
            );


        mensaje.id =
            "mensajeSinProveedoresTipoGasto";


        mensaje.style.color =
            "#8b93a7";

        mensaje.style.padding =
            "12px";

        mensaje.style.textAlign =
            "center";


        mensaje.textContent =
            "No hay proveedores relacionados.";


        contenedor.appendChild(
            mensaje
        );


        return;

    }


    proveedoresRelacionadosTipoGasto
        .forEach(
            function(proveedorId){

                const tarjetaModal =
                    document.querySelector(
                        '.tarjeta-proveedor-modal-tipo-gasto' +
                        '[data-proveedor-id="' +
                        proveedorId +
                        '"]'
                    );


                if(!tarjetaModal){

                    return;

                }


                const nombre =
                    tarjetaModal.dataset
                        .proveedorNombre ||
                    "Proveedor";


                const cuit =
                    tarjetaModal.dataset
                        .proveedorCuit ||
                    "";


                const fila =
                    document.createElement(
                        "div"
                    );


                fila.dataset.proveedorId =
                    proveedorId;


                fila.style.display =
                    "flex";

                fila.style.alignItems =
                    "center";

                fila.style.justifyContent =
                    "space-between";

                fila.style.gap =
                    "12px";

                fila.style.padding =
                    "10px 12px";

                fila.style.background =
                    "#151a26";

                fila.style.border =
                    "1px solid #2b3447";

                fila.style.borderRadius =
                    "10px";


                const texto =
                    document.createElement(
                        "div"
                    );


                const nombreElemento =
                    document.createElement(
                        "span"
                    );


                nombreElemento.textContent =
                    nombre;


                texto.appendChild(
                    nombreElemento
                );


                if(cuit){

                    const cuitElemento =
                        document.createElement(
                            "span"
                        );


                    cuitElemento.style.color =
                        "#8b93a7";

                    cuitElemento.style.fontSize =
                        "13px";


                    cuitElemento.textContent =
                        ` · ${cuit}`;


                    texto.appendChild(
                        cuitElemento
                    );

                }


                const botonEliminar =
                    document.createElement(
                        "button"
                    );


                botonEliminar.type =
                    "button";

                botonEliminar.className =
                    "action-btn";

                botonEliminar.title =
                    "Quitar proveedor relacionado";

                botonEliminar.textContent =
                    "🗑";


                botonEliminar.style.width =
                    "38px";

                botonEliminar.style.minWidth =
                    "38px";

                botonEliminar.style.padding =
                    "6px";

                botonEliminar.style.margin =
                    "0";

                botonEliminar.style.background =
                    "#7f1d1d";

                botonEliminar.style.borderColor =
                    "#991b1b";


                botonEliminar.addEventListener(
                    "click",
                    function(){

                        quitarProveedorRelacionadoTipoGasto(
                            proveedorId
                        );

                    }
                );


                fila.appendChild(
                    texto
                );


                fila.appendChild(
                    botonEliminar
                );


                contenedor.appendChild(
                    fila
                );

            }
        );

}

function quitarProveedorRelacionadoTipoGasto(
    proveedorId
){

    proveedoresRelacionadosTipoGasto
        .delete(
            String(
                proveedorId
            )
        );


    const check =
        document.querySelector(
            '.proveedor-modal-tipo-gasto[value="' +
            proveedorId +
            '"]'
        );


    if(check){

        check.checked =
            false;

    }


    renderizarProveedoresRelacionadosTipoGasto();

}

function guardarEstadoFormularioTipoGasto(){

    const nombre =
        document.getElementById(
            "nombreTipoGasto"
        );

    const descripcion =
        document.getElementById(
            "descripcionTipoGasto"
        );


    estadoFormularioTipoGasto = {

        nombre:
            nombre
                ? nombre.value
                : "",

        descripcion:
            descripcion
                ? descripcion.value
                : "",

        proveedores:
            proveedoresSeleccionadosTipoGasto(),

        proveedoresModal:
            proveedoresMarcadosModalTipoGasto()

    };

}


function restaurarEstadoFormularioTipoGasto(){

    if(!estadoFormularioTipoGasto){

        return;

    }


    const nombre =
        document.getElementById(
            "nombreTipoGasto"
        );

    const descripcion =
        document.getElementById(
            "descripcionTipoGasto"
        );


    if(nombre){

        nombre.value =
            estadoFormularioTipoGasto.nombre || "";

    }


    if(descripcion){

        descripcion.value =
            estadoFormularioTipoGasto.descripcion || "";

    }


    proveedoresRelacionadosTipoGasto =
        new Set(
            (
                estadoFormularioTipoGasto
                    .proveedores ||
                []
            )
            .map(
                function(id){

                    return String(id);

                }
            )
        );


    document
        .querySelectorAll(
            ".proveedor-modal-tipo-gasto"
        )
        .forEach(
            function(check){

                check.checked = false;

            }
        );


    const seleccionModal =
        estadoFormularioTipoGasto
            .proveedoresModal ||
        [];


    seleccionModal.forEach(
        function(proveedorId){

            const check =
                document.querySelector(
                    '.proveedor-modal-tipo-gasto[value="' +
                    proveedorId +
                    '"]'
                );


            if(check){

                check.checked = true;

            }

        }
    );


    renderizarProveedoresRelacionadosTipoGasto();

}


async function actualizarProveedoresDelTipoGasto(){

    restaurarEstadoFormularioTipoGasto();


    if(
        typeof ultimoProveedorCreado ===
            "undefined" ||
        !ultimoProveedorCreado
    ){

        return;

    }


    const lista =
        document.getElementById(
            "listaProveedoresModalTipoGasto"
        );


    if(!lista){

        console.error(
            "No se encontró la lista del modal de proveedores."
        );

        ultimoProveedorCreado =
            null;

        return;

    }


    const proveedorId =
        String(
            ultimoProveedorCreado.id
        );


    let tarjeta =
        lista.querySelector(
            '.tarjeta-proveedor-modal-tipo-gasto' +
            '[data-proveedor-id="' +
            proveedorId +
            '"]'
        );


    if(!tarjeta){

        const mensaje =
            document.getElementById(
                "mensajeSinProveedoresModalTipoGasto"
            );


        if(mensaje){

            mensaje.remove();

        }


        tarjeta =
            document.createElement(
                "label"
            );


        tarjeta.className =
            "tarjeta-proveedor-modal-tipo-gasto";


        tarjeta.dataset.proveedorId =
            proveedorId;

        tarjeta.dataset.proveedorNombre =
            ultimoProveedorCreado.razon_social ||
            "";

        tarjeta.dataset.proveedorCuit =
            ultimoProveedorCreado.cuit ||
            "";


        tarjeta.style.display =
            "flex";

        tarjeta.style.alignItems =
            "center";

        tarjeta.style.gap =
            "12px";

        tarjeta.style.padding =
            "12px 14px";

        tarjeta.style.background =
            "#151a26";

        tarjeta.style.border =
            "1px solid #2b3447";

        tarjeta.style.borderRadius =
            "10px";

        tarjeta.style.cursor =
            "pointer";


        const check =
            document.createElement(
                "input"
            );


        check.type =
            "checkbox";

        check.className =
            "proveedor-modal-tipo-gasto";

        check.value =
            proveedorId;

        check.checked =
            true;


        const texto =
            document.createElement(
                "div"
            );


        const nombre =
            document.createElement(
                "div"
            );


        nombre.textContent =
            ultimoProveedorCreado.razon_social ||
            "Proveedor";


        texto.appendChild(
            nombre
        );


        if(
            ultimoProveedorCreado.cuit
        ){

            const cuit =
                document.createElement(
                    "div"
                );


            cuit.style.color =
                "#8b93a7";

            cuit.style.fontSize =
                "13px";

            cuit.style.marginTop =
                "3px";


            cuit.textContent =
                ultimoProveedorCreado.cuit;


            texto.appendChild(
                cuit
            );

        }


        tarjeta.appendChild(
            check
        );

        tarjeta.appendChild(
            texto
        );

        lista.appendChild(
            tarjeta
        );

    }else{

        const check =
            tarjeta.querySelector(
                ".proveedor-modal-tipo-gasto"
            );


        if(check){

            check.checked =
                true;

        }

    }


    /*
     * Lo incorporamos también al estado temporal
     * del modal para que no se pierda.
     */
    if(
        estadoFormularioTipoGasto
    ){

        if(
            !Array.isArray(
                estadoFormularioTipoGasto
                    .proveedoresModal
            )
        ){

            estadoFormularioTipoGasto
                .proveedoresModal = [];

        }


        if(
            !estadoFormularioTipoGasto
                .proveedoresModal
                .includes(
                    proveedorId
                )
        ){

            estadoFormularioTipoGasto
                .proveedoresModal
                .push(
                    proveedorId
                );

        }

    }


    ultimoProveedorCreado =
        null;


    filtrarProveedoresModalTipoGasto();

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

    tipoGastoEditandoId =
        null;

    tipoGastoReactivandoId =
        String(
            tipoGasto.id
        );


    const nombre =
        document.getElementById(
            "nombreTipoGasto"
        );

    const descripcion =
        document.getElementById(
            "descripcionTipoGasto"
        );


    if(nombre){

        nombre.value =
            tipoGasto.nombre || "";

    }


    if(descripcion){

        descripcion.value =
            tipoGasto.descripcion || "";

    }


    proveedoresRelacionadosTipoGasto =
        new Set(
            (
                tipoGasto.proveedores ||
                []
            )
            .map(
                function(id){

                    return String(id);

                }
            )
        );


    document
        .querySelectorAll(
            ".proveedor-modal-tipo-gasto"
        )
        .forEach(
            function(check){

                check.checked =
                    proveedoresRelacionadosTipoGasto
                        .has(
                            String(
                                check.value
                            )
                        );

            }
        );


    renderizarProveedoresRelacionadosTipoGasto();


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


    if(nombre){

        nombre.focus();
        nombre.select();

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

    tipoGastoReactivandoId =
        null;

    tipoGastoEditandoId =
        String(
            tipoGastoId
        );


    const inputNombre =
        document.getElementById(
            "nombreTipoGasto"
        );

    const inputDescripcion =
        document.getElementById(
            "descripcionTipoGasto"
        );


    if(inputNombre){

        inputNombre.value =
            nombre || "";

    }


    if(inputDescripcion){

        inputDescripcion.value =
            descripcion || "";

    }


    let idsProveedores = [];


    if(proveedores){

        idsProveedores =
            String(
                proveedores
            )
            .split(",")
            .map(
                function(valor){

                    return valor.trim();

                }
            )
            .filter(
                function(valor){

                    return valor !== "";

                }
            );

    }


    proveedoresRelacionadosTipoGasto =
        new Set(
            idsProveedores
        );


    document
        .querySelectorAll(
            ".proveedor-modal-tipo-gasto"
        )
        .forEach(
            function(check){

                check.checked =
                    proveedoresRelacionadosTipoGasto
                        .has(
                            String(
                                check.value
                            )
                        );

            }
        );


    renderizarProveedoresRelacionadosTipoGasto();


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

    const nombre =
        document.getElementById(
            "nombreTipoGasto"
        );

    const descripcion =
        document.getElementById(
            "descripcionTipoGasto"
        );


    if(nombre){

        nombre.value = "";

    }


    if(descripcion){

        descripcion.value = "";

    }


    proveedoresRelacionadosTipoGasto =
        new Set();


    document
        .querySelectorAll(
            ".proveedor-modal-tipo-gasto"
        )
        .forEach(
            function(check){

                check.checked =
                    false;

            }
        );


    const buscador =
        document.getElementById(
            "buscarProveedorTipoGasto"
        );


    if(buscador){

        buscador.value = "";

    }


    renderizarProveedoresRelacionadosTipoGasto();

    filtrarProveedoresModalTipoGasto();

    cerrarModalProveedoresTipoGasto();


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

