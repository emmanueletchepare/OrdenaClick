let ultimoRecursoOperativoCreado = null;

let recursoOperativoEditandoId = null;

let recursoOperativoReactivandoId = null;

/*
 * =========================================
 * CENTROS OPERATIVOS RELACIONADOS
 * =========================================
 */

let centrosRelacionadosRecursoOperativo = new Set();



/* =========================================
   INICIALIZACIÓN
========================================= */

function iniciarABMRecursosOperativos(){

    const btnGuardar =
        document.getElementById(
            "btnGuardarRecursoOperativo"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarRecursoOperativo"
        );

    const btnVolver =
        document.getElementById(
            "btnVolverRecursoOperativo"
        );

    const buscador =
        document.getElementById(
            "buscarRecursoOperativoABM"
        );


    /*
     * =========================================
     * CENTROS OPERATIVOS
     * =========================================
     */

    const btnAgregarCentro =
        document.getElementById(
            "btnAgregarCentroRecursoOperativo"
        );

    const btnCancelarModalCentro =
        document.getElementById(
            "btnCancelarModalCentrosRecursoOperativo"
        );

    const btnGuardarModalCentro =
        document.getElementById(
            "btnGuardarModalCentrosRecursoOperativo"
        );

    const buscadorCentro =
        document.getElementById(
            "buscarCentroRecursoOperativo"
        );


    /*
     * Cada vez que cargamos el ABM desde cero
     * empezamos sin centros seleccionados.
     */

    centrosRelacionadosRecursoOperativo =
        new Set();


    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarRecursoOperativo
        );

    }


    if(btnCancelar){

        btnCancelar.addEventListener(
            "click",
            cancelarEdicionRecursoOperativo
        );

    }


    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeABMRecursosOperativos
        );

    }


    if(buscador){

        buscador.addEventListener(
            "input",
            filtrarRecursosOperativosABM
        );

    }


    /*
     * =========================================
     * MODAL CENTROS OPERATIVOS
     * =========================================
     */

    if(btnAgregarCentro){

        btnAgregarCentro.addEventListener(
            "click",
            abrirModalCentrosRecursoOperativo
        );

    }


    if(btnCancelarModalCentro){

        btnCancelarModalCentro.addEventListener(
            "click",
            cerrarModalCentrosRecursoOperativo
        );

    }


    if(btnGuardarModalCentro){

        btnGuardarModalCentro.addEventListener(
            "click",
            guardarSeleccionCentrosRecursoOperativo
        );

    }


    if(buscadorCentro){

        buscadorCentro.addEventListener(
            "input",
            filtrarCentrosModalRecursoOperativo
        );

    }


    /*
     * =========================================
     * MODIFICAR
     * =========================================
     */

    document
        .querySelectorAll(
            ".btn-modificar-recurso-operativo"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        const tarjeta =
                            boton.closest(
                                ".tarjeta-recurso-operativo-abm"
                            );


                        if(!tarjeta){

                            return;

                        }


                        modificarRecursoOperativo(

                            tarjeta.dataset.recursoId,

                            tarjeta.dataset.recursoNombre,

                            tarjeta.dataset.recursoTipo,

                            tarjeta.dataset.recursoCentros,

                            tarjeta.dataset.recursoDescripcion

                        );

                    }
                );

            }
        );


    /*
     * =========================================
     * ELIMINAR
     * =========================================
     */

    document
        .querySelectorAll(
            ".btn-eliminar-recurso-operativo"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        const recursoId =
                            boton.dataset.recursoId;

                        const recursoNombre =
                            boton.dataset.recursoNombre;


                        if(!recursoId){

                            return;

                        }


                        eliminarRecursoOperativo(
                            recursoId,
                            recursoNombre
                        );

                    }
                );

            }
        );


    renderizarCentrosRelacionadosRecursoOperativo();

}


/* =========================================
   AUXILIARES
========================================= */

function valorRecursoOperativo(id){

    const elemento =
        document.getElementById(
            id
        );


    return elemento
        ? elemento.value.trim()
        : "";

}

/*
 * =========================================
 * CENTROS OPERATIVOS
 * =========================================
 */

function centrosSeleccionadosRecursoOperativo(){

    return Array.from(
        centrosRelacionadosRecursoOperativo
    );

}


function centrosMarcadosModalRecursoOperativo(){

    return Array
        .from(
            document.querySelectorAll(
                ".centro-modal-recurso-operativo:checked"
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


function abrirModalCentrosRecursoOperativo(){

    const modal =
        document.getElementById(
            "modalCentrosRecursoOperativo"
        );

    const buscador =
        document.getElementById(
            "buscarCentroRecursoOperativo"
        );


    if(!modal){

        return;

    }


    /*
     * Restauramos en los checks
     * la selección que tiene actualmente
     * el formulario.
     */

    document
        .querySelectorAll(
            ".centro-modal-recurso-operativo"
        )
        .forEach(
            function(check){

                check.checked =
                    centrosRelacionadosRecursoOperativo
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


    filtrarCentrosModalRecursoOperativo();


    modal.style.display =
        "flex";

}


function cerrarModalCentrosRecursoOperativo(){

    const modal =
        document.getElementById(
            "modalCentrosRecursoOperativo"
        );


    if(modal){

        modal.style.display =
            "none";

    }

}


function guardarSeleccionCentrosRecursoOperativo(){

    const seleccion =
        centrosMarcadosModalRecursoOperativo();


    centrosRelacionadosRecursoOperativo =
        new Set(
            seleccion
        );


    renderizarCentrosRelacionadosRecursoOperativo();

    cerrarModalCentrosRecursoOperativo();

}


function quitarCentroRelacionadoRecursoOperativo(
    centroId
){

    centrosRelacionadosRecursoOperativo.delete(
        String(
            centroId
        )
    );


    const check =
        document.querySelector(
            '.centro-modal-recurso-operativo[value="' +
            String(
                centroId
            ) +
            '"]'
        );


    if(check){

        check.checked =
            false;

    }


    renderizarCentrosRelacionadosRecursoOperativo();

}


function renderizarCentrosRelacionadosRecursoOperativo(){

    const contenedor =
        document.getElementById(
            "centrosRecursoOperativo"
        );


    if(!contenedor){

        return;

    }


    contenedor.innerHTML =
        "";


    if(
        centrosRelacionadosRecursoOperativo.size ===
        0
    ){

        const mensaje =
            document.createElement(
                "div"
            );


        mensaje.id =
            "mensajeSinCentrosRecursoOperativo";


        mensaje.style.color =
            "#8b93a7";

        mensaje.style.padding =
            "12px";

        mensaje.style.textAlign =
            "center";


        mensaje.textContent =
            "No hay Centros Operativos relacionados.";


        contenedor.appendChild(
            mensaje
        );


        return;

    }


    centrosRelacionadosRecursoOperativo
        .forEach(
            function(centroId){

                const tarjetaModal =
                    document.querySelector(
                        '.tarjeta-centro-modal-recurso-operativo' +
                        '[data-centro-id="' +
                        centroId +
                        '"]'
                    );


                if(!tarjetaModal){

                    return;

                }


                const nombre =
                    tarjetaModal.dataset
                        .centroNombre ||
                    "Centro Operativo";


                const fila =
                    document.createElement(
                        "div"
                    );


                fila.dataset.centroId =
                    centroId;


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


                texto.textContent =
                    nombre;


                const botonEliminar =
                    document.createElement(
                        "button"
                    );


                botonEliminar.type =
                    "button";

                botonEliminar.className =
                    "action-btn";

                botonEliminar.title =
                    "Quitar Centro Operativo relacionado";

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

                        quitarCentroRelacionadoRecursoOperativo(
                            centroId
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


function filtrarCentrosModalRecursoOperativo(){

    const buscador =
        document.getElementById(
            "buscarCentroRecursoOperativo"
        );

    const mensaje =
        document.getElementById(
            "sinResultadosCentrosRecursoOperativo"
        );


    const texto =
        buscador
            ? buscador.value
                .trim()
                .toLowerCase()
            : "";


    const tarjetas =
        document.querySelectorAll(
            ".tarjeta-centro-modal-recurso-operativo"
        );


    let visibles =
        0;


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


    if(mensaje){

        mensaje.style.display =
            (
                tarjetas.length > 0 &&
                visibles === 0
            )
                ? "block"
                : "none";

    }

}

/* =========================================
   BUSCADOR
========================================= */

function filtrarRecursosOperativosABM(){

    const buscador =
        document.getElementById(
            "buscarRecursoOperativoABM"
        );

    const mensajeSinResultados =
        document.getElementById(
            "sinResultadosRecursoOperativoABM"
        );


    const texto =
        buscador
            ? buscador.value
                .trim()
                .toLowerCase()
            : "";


    const tarjetas =
        document.querySelectorAll(
            ".tarjeta-recurso-operativo-abm"
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
   GUARDAR / MODIFICAR / REACTIVAR
========================================= */

async function guardarRecursoOperativo(){

    const empresa =
        valorRecursoOperativo(
            "empresaActiva"
        );

    const nombre =
        valorRecursoOperativo(
            "nombreRecursoOperativo"
        );

    const tipoRecurso =
        valorRecursoOperativo(
            "tipoRecursoOperativo"
        );

    const descripcion =
        valorRecursoOperativo(
            "descripcionRecursoOperativo"
        );


    const centros =
        centrosSeleccionadosRecursoOperativo();


    if(!empresa){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }


    if(!nombre){

        alert(
            "Ingrese el nombre del recurso operativo."
        );


        const input =
            document.getElementById(
                "nombreRecursoOperativo"
            );


        if(input){

            input.focus();

        }


        return;

    }


    if(!tipoRecurso){

        alert(
            "Seleccione el tipo de recurso."
        );


        const select =
            document.getElementById(
                "tipoRecursoOperativo"
            );


        if(select){

            select.focus();

        }


        return;

    }


    /*
     * =========================================
     * REGLA OBLIGATORIA
     * =========================================
     *
     * Todo Recurso Operativo debe pertenecer
     * al menos a un Centro Operativo.
     */

    if(
        centros.length ===
        0
    ){

        alert(
            "Seleccione al menos un Centro Operativo."
        );


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
        "tipo_recurso",
        tipoRecurso
    );

    formulario.append(
        "descripcion",
        descripcion
    );


    /*
     * Enviamos una entrada por cada Centro.
     *
     * Django la recibe mediante:
     *
     * request.POST.getlist("centros_operativos")
     */

    centros.forEach(
        function(centroId){

            formulario.append(
                "centros_operativos",
                centroId
            );

        }
    );


    const estaEditando =
        recursoOperativoEditandoId !== null;

    const estaReactivando =
        recursoOperativoReactivandoId !== null;


    let url =
        "/recursos-operativos/guardar/";


    if(estaEditando){

        url =
            "/recursos-operativos/modificar/";


        formulario.append(
            "recurso",
            recursoOperativoEditandoId
        );

    }else if(estaReactivando){

        url =
            "/recursos-operativos/reactivar/";


        formulario.append(
            "recurso",
            recursoOperativoReactivandoId
        );

    }


    try{

        const respuesta =
            await fetch(
                url,
                {
                    method:
                        "POST",

                    headers: {

                        "X-CSRFToken":
                            obtenerCookie(
                                "csrftoken"
                            )

                    },

                    body:
                        formulario
                }
            );


        const resultado =
            await respuesta.json();


        if(
            resultado.requiere_reactivacion &&
            resultado.recurso
        ){

            cargarRecursoOperativoParaReactivar(
                resultado.recurso
            );


            alert(
                resultado.mensaje ||
                "El recurso operativo está inactivo. Puede reactivarlo."
            );


            return;

        }


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            let mensaje =
                "No se pudo guardar el recurso operativo.";


            if(estaEditando){

                mensaje =
                    "No se pudo modificar el recurso operativo.";

            }else if(estaReactivando){

                mensaje =
                    "No se pudo reactivar el recurso operativo.";

            }


            alert(
                resultado.mensaje ||
                mensaje
            );


            return;

        }


        if(
            !estaEditando &&
            resultado.recurso
        ){

            ultimoRecursoOperativoCreado = {

                id:
                    String(
                        resultado.recurso.id
                    ),

                nombre:
                    resultado.recurso.nombre ||
                    nombre

            };

        }


        recursoOperativoEditandoId =
            null;

        recursoOperativoReactivandoId =
            null;

        centrosRelacionadosRecursoOperativo =
            new Set();


        await mostrarABMRecursosOperativos(
            origenABM
        );


    }catch(error){

        console.error(
            "Error guardando recurso operativo:",
            error
        );


        alert(
            estaEditando
                ? "Ocurrió un error al modificar el recurso operativo."
                : "Ocurrió un error al guardar el recurso operativo."
        );

    }

}


/* =========================================
   CARGAR PARA REACTIVAR
========================================= */

function cargarRecursoOperativoParaReactivar(
    recurso
){

    recursoOperativoEditandoId =
        null;

    recursoOperativoReactivandoId =
        String(
            recurso.id
        );


    const inputNombre =
        document.getElementById(
            "nombreRecursoOperativo"
        );


    if(inputNombre){

        inputNombre.value =
            recurso.nombre || "";

    }


    const btnGuardar =
        document.getElementById(
            "btnGuardarRecursoOperativo"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarRecursoOperativo"
        );


    if(btnGuardar){

        btnGuardar.textContent =
            "Activar";

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
   MODIFICAR
========================================= */

function modificarRecursoOperativo(
    recursoId,
    nombre,
    tipoRecurso,
    centrosOperativos,
    descripcion
){

    recursoOperativoReactivandoId =
        null;


    recursoOperativoEditandoId =
        String(
            recursoId
        );


    const inputNombre =
        document.getElementById(
            "nombreRecursoOperativo"
        );

    const selectTipo =
        document.getElementById(
            "tipoRecursoOperativo"
        );

    const inputDescripcion =
        document.getElementById(
            "descripcionRecursoOperativo"
        );


    if(inputNombre){

        inputNombre.value =
            nombre || "";

    }


    if(selectTipo){

        selectTipo.value =
            tipoRecurso || "";

    }


    if(inputDescripcion){

        inputDescripcion.value =
            descripcion || "";

    }


    /*
     * data-recurso-centros viene como:
     *
     * "1,3,5"
     */

    const centros =
        (
            centrosOperativos ||
            ""
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


    centrosRelacionadosRecursoOperativo =
        new Set(
            centros
        );


    document
        .querySelectorAll(
            ".centro-modal-recurso-operativo"
        )
        .forEach(
            function(check){

                check.checked =
                    centrosRelacionadosRecursoOperativo
                        .has(
                            String(
                                check.value
                            )
                        );

            }
        );


    renderizarCentrosRelacionadosRecursoOperativo();


    const btnGuardar =
        document.getElementById(
            "btnGuardarRecursoOperativo"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarRecursoOperativo"
        );


    if(btnGuardar){

        btnGuardar.textContent =
            "Actualizar";

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
   CANCELAR / LIMPIAR
========================================= */

function cancelarEdicionRecursoOperativo(){

    recursoOperativoEditandoId =
        null;

    recursoOperativoReactivandoId =
        null;


    limpiarFormularioRecursoOperativo();

}


function limpiarFormularioRecursoOperativo(){

    recursoOperativoEditandoId =
        null;

    recursoOperativoReactivandoId =
        null;


    const inputNombre =
        document.getElementById(
            "nombreRecursoOperativo"
        );

    const selectTipo =
        document.getElementById(
            "tipoRecursoOperativo"
        );


    const inputDescripcion =
        document.getElementById(
            "descripcionRecursoOperativo"
        );


    if(inputNombre){

        inputNombre.value = "";

    }


    if(selectTipo){

        selectTipo.value = "";

    }

/*
 * =========================================
 * LIMPIAR CENTROS OPERATIVOS RELACIONADOS
 * =========================================
 */

centrosRelacionadosRecursoOperativo =
    new Set();


document
    .querySelectorAll(
        ".centro-modal-recurso-operativo"
    )
    .forEach(
        function(check){

            check.checked =
                false;

        }
    );


renderizarCentrosRelacionadosRecursoOperativo();


    if(inputDescripcion){

        inputDescripcion.value = "";

    }


    const btnGuardar =
        document.getElementById(
            "btnGuardarRecursoOperativo"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarRecursoOperativo"
        );


    if(btnGuardar){

        btnGuardar.textContent =
            "Guardar";

    }


    if(btnCancelar){

        btnCancelar.style.display =
            "none";

    }


    if(inputNombre){

        inputNombre.focus();

    }

}


/* =========================================
   ELIMINAR
========================================= */

async function eliminarRecursoOperativo(
    recursoId,
    nombreRecurso
){

    const confirmado =
        confirm(
            `¿Desactivar el recurso operativo "${nombreRecurso}"?\n\n` +
            "Los movimientos históricos conservarán el recurso, " +
            "pero ya no podrá seleccionarse en operaciones nuevas."
        );


    if(!confirmado){

        return;

    }


    const empresa =
        valorRecursoOperativo(
            "empresaActiva"
        );


    if(!empresa){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }


    const formulario =
        new FormData();


    formulario.append(
        "empresa",
        empresa
    );

    formulario.append(
        "recurso",
        recursoId
    );


    try{

        const respuesta =
            await fetch(
                "/recursos-operativos/eliminar/",
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
                "No se pudo desactivar el recurso operativo."
            );

            return;

        }


        if(
            recursoOperativoEditandoId ===
            String(
                recursoId
            )
        ){

            recursoOperativoEditandoId =
                null;

        }


        await mostrarABMRecursosOperativos(
            origenABM
        );


    }catch(error){

        console.error(
            "Error desactivando recurso operativo:",
            error
        );


        alert(
            "Ocurrió un error al desactivar el recurso operativo."
        );

    }

}


/* =========================================
   VOLVER
========================================= */

async function volverDesdeABMRecursosOperativos(){

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


        contenidoAnteriorABM =
            null;


        if(
            typeof actualizarRecursoOperativoDelRegistro ===
            "function"
        ){

            await actualizarRecursoOperativoDelRegistro();

        }


        origenABM =
            "registro";


        return;

    }


    contenidoAnteriorABM =
        null;

    ultimoRecursoOperativoCreado =
        null;

    origenABM =
        "menu";


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

async function refrescarRecursosOperativos(){

    await mostrarABMRecursosOperativos(
        origenABM
    );

}