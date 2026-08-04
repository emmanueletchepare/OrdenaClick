let ultimoRecursoOperativoCreado = null;

let recursoOperativoEditandoId = null;

let recursoOperativoReactivandoId = null;


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

                            tarjeta.dataset.recursoCentro,

                            tarjeta.dataset.recursoDescripcion

                        );

                    }
                );

            }
        );


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

    const centroOperativo =
        valorRecursoOperativo(
            "centroRecursoOperativo"
        );

    const descripcion =
        valorRecursoOperativo(
            "descripcionRecursoOperativo"
        );


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


    if(!centroOperativo){

        alert(
            "Seleccione el centro operativo."
        );

        const select =
            document.getElementById(
                "centroRecursoOperativo"
            );

        if(select){

            select.focus();

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
        "tipo_recurso",
        tipoRecurso
    );

    formulario.append(
        "centro_operativo",
        centroOperativo
    );

    formulario.append(
        "descripcion",
        descripcion
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
    centroOperativo,
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

    const selectCentro =
        document.getElementById(
            "centroRecursoOperativo"
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


    if(selectCentro){

        selectCentro.value =
            centroOperativo || "";

    }


    if(inputDescripcion){

        inputDescripcion.value =
            descripcion || "";

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

    const selectCentro =
        document.getElementById(
            "centroRecursoOperativo"
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


    if(selectCentro){

        selectCentro.value = "";

    }


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