/*
 * =========================================================
 * ABM RETENCIONES
 * =========================================================
 *
 * Tabla maestra de tipos de retención por Empresa.
 *
 * Cada retención contiene:
 *
 * - Tipo
 * - Descripción
 * - Cuenta contable (pendiente de Plan Contable)
 * - Activa / Inactiva
 *
 * Las eliminaciones son lógicas.
 * =========================================================
 */


let retencionEditandoId =
    null;

let retencionReactivandoId =
    null;

let ultimaRetencionCreada =
    null;


/*
 * =========================================================
 * INICIALIZACIÓN
 * =========================================================
 */

function iniciarABMRetenciones(){

    const btnGuardar =
        document.getElementById(
            "btnGuardarRetencion"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarRetencion"
        );

    const btnVolver =
        document.getElementById(
            "btnVolverRetenciones"
        );

    const buscador =
        document.getElementById(
            "buscarRetencionABM"
        );


    /*
     * GUARDAR
     */

    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarRetencion
        );

    }


    /*
     * CANCELAR
     */

    if(btnCancelar){

        btnCancelar.addEventListener(
            "click",
            cancelarEdicionRetencion
        );

    }


    /*
     * VOLVER
     */

    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeABMRetenciones
        );

    }


    /*
     * BUSCADOR
     */

    if(buscador){

        buscador.addEventListener(
            "input",
            filtrarRetencionesABM
        );

    }


    /*
     * MODIFICAR
     */

    document
        .querySelectorAll(
            ".btn-modificar-retencion"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        const tarjeta =
                            boton.closest(
                                ".tarjeta-retencion-abm"
                            );


                        if(!tarjeta){

                            return;

                        }


                        modificarRetencion(

                            tarjeta.dataset.retencionId,

                            tarjeta.dataset.retencionTipo,

                            tarjeta.dataset.retencionDescripcion

                        );

                    }
                );

            }
        );


    /*
     * ELIMINAR / DESACTIVAR
     */

    document
        .querySelectorAll(
            ".btn-eliminar-retencion"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        eliminarRetencion(

                            boton.dataset.retencionId,

                            boton.dataset.retencionTipo

                        );

                    }
                );

            }
        );

}


/*
 * =========================================================
 * HELPERS
 * =========================================================
 */

function valorRetencion(
    id
){

    const elemento =
        document.getElementById(
            id
        );


    if(!elemento){

        return "";

    }


    return String(
        elemento.value || ""
    ).trim();

}


function obtenerEmpresaRetencion(){

    const empresa =
        document.getElementById(
            "empresaActiva"
        );


    if(
        !empresa ||
        !empresa.value
    ){

        return "";

    }


    return String(
        empresa.value
    );

}


/*
 * =========================================================
 * GUARDAR / MODIFICAR / REACTIVAR
 * =========================================================
 */

async function guardarRetencion(){

    const empresa =
        obtenerEmpresaRetencion();

    const tipo =
        valorRetencion(
            "tipoRetencion"
        );

    const descripcion =
        valorRetencion(
            "descripcionRetencion"
        );


    /*
     * VALIDACIONES
     */

    if(!empresa){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }


    if(!tipo){

        alert(
            "Ingrese un tipo de retención."
        );


        const input =
            document.getElementById(
                "tipoRetencion"
            );


        if(input){

            input.focus();

        }


        return;

    }


    /*
     * FORM DATA
     */

    const formulario =
        new FormData();


    formulario.append(
        "empresa",
        empresa
    );


    formulario.append(
        "tipo",
        tipo
    );


    formulario.append(
        "descripcion",
        descripcion
    );


    /*
     * ENDPOINT SEGÚN ESTADO
     */

    let url =
        "/retenciones/guardar/";


    const estaEditando =
        retencionEditandoId !==
        null;

    const estaReactivando =
        retencionReactivandoId !==
        null;


    if(estaEditando){

        url =
            "/retenciones/modificar/";


        formulario.append(
            "retencion",
            retencionEditandoId
        );

    }else if(estaReactivando){

        url =
            "/retenciones/reactivar/";


        formulario.append(
            "retencion",
            retencionReactivandoId
        );

    }


    /*
     * GUARDAR
     */

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


        /*
         * =========================================
         * EXISTE PERO ESTÁ INACTIVA
         * =========================================
         */

        if(
            resultado.requiere_reactivacion &&
            resultado.retencion
        ){

            cargarRetencionParaReactivar(
                resultado.retencion
            );


            alert(
                resultado.mensaje ||
                "La retención existe pero está inactiva. Puede reactivarla."
            );


            return;

        }


        /*
         * ERROR
         */

        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            let mensaje =
                "No se pudo guardar la retención.";


            if(estaEditando){

                mensaje =
                    "No se pudo modificar la retención.";

            }else if(estaReactivando){

                mensaje =
                    "No se pudo reactivar la retención.";

            }


            alert(
                resultado.mensaje ||
                mensaje
            );


            return;

        }


        /*
         * =========================================
         * RECORDAR ALTA NUEVA
         * =========================================
         *
         * Después se usará para que el [+] del Pago
         * seleccione automáticamente la retención
         * recién creada al volver.
         */

        if(
            !estaEditando &&
            !estaReactivando &&
            resultado.retencion &&
            resultado.retencion.id
        ){

            ultimaRetencionCreada = {

                id:
                    String(
                        resultado.retencion.id
                    ),

                tipo:
                    resultado.retencion.tipo ||
                    tipo,

                descripcion:
                    resultado.retencion.descripcion ||
                    descripcion

            };

        }


        /*
         * LIMPIAR ESTADO
         */

        retencionEditandoId =
            null;

        retencionReactivandoId =
            null;


        /*
         * RECARGAR ABM
         */

        if(
            typeof mostrarABMRetenciones ===
            "function"
        ){

            await mostrarABMRetenciones(
                origenABM
            );

        }


    }catch(error){

        console.error(
            "Error guardando retención:",
            error
        );


        alert(
            estaEditando
                ? "Ocurrió un error al modificar la retención."
                : "Ocurrió un error al guardar la retención."
        );

    }

}


/*
 * =========================================================
 * MODIFICAR
 * =========================================================
 */

function modificarRetencion(
    retencionId,
    tipo,
    descripcion
){

    /*
     * Si ya estamos modificando otra retención,
     * primero debe guardarse o cancelarse.
     */

    if(
        retencionEditandoId !== null &&
        String(
            retencionEditandoId
        ) !== String(
            retencionId
        )
    ){

        alert(
            "Ya hay una retención en edición.\n\n" +
            "Guarde o cancele los cambios antes de modificar otra."
        );

        return;

    }


    retencionReactivandoId =
        null;


    retencionEditandoId =
        String(
            retencionId
        );


    const inputTipo =
        document.getElementById(
            "tipoRetencion"
        );

    const inputDescripcion =
        document.getElementById(
            "descripcionRetencion"
        );

    const btnGuardar =
        document.getElementById(
            "btnGuardarRetencion"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarRetencion"
        );


    /*
     * CARGAR DATOS
     */

    if(inputTipo){

        inputTipo.value =
            tipo || "";

    }


    if(inputDescripcion){

        inputDescripcion.value =
            descripcion || "";

    }


    /*
     * MODO EDICIÓN
     */

    if(btnGuardar){

        btnGuardar.textContent =
            "Guardar cambios";

    }


    if(btnCancelar){

        btnCancelar.style.display =
            "inline-block";

    }


    /*
     * LLEVAR AL FORMULARIO
     */

    if(inputTipo){

        inputTipo.scrollIntoView({

            behavior:
                "smooth",

            block:
                "center"

        });


        inputTipo.focus();
        inputTipo.select();

    }

}


/*
 * =========================================================
 * REACTIVAR
 * =========================================================
 */

function cargarRetencionParaReactivar(
    retencion
){

    if(
        !retencion ||
        !retencion.id
    ){

        return;

    }


    retencionEditandoId =
        null;


    retencionReactivandoId =
        String(
            retencion.id
        );


    const inputTipo =
        document.getElementById(
            "tipoRetencion"
        );

    const inputDescripcion =
        document.getElementById(
            "descripcionRetencion"
        );

    const btnGuardar =
        document.getElementById(
            "btnGuardarRetencion"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarRetencion"
        );


    if(inputTipo){

        inputTipo.value =
            retencion.tipo || "";

    }


    if(inputDescripcion){

        inputDescripcion.value =
            retencion.descripcion || "";

    }


    if(btnGuardar){

        btnGuardar.textContent =
            "Reactivar retención";

    }


    if(btnCancelar){

        btnCancelar.style.display =
            "inline-block";

    }


    if(inputTipo){

        inputTipo.scrollIntoView({

            behavior:
                "smooth",

            block:
                "center"

        });


        inputTipo.focus();

    }

}


/*
 * =========================================================
 * CANCELAR EDICIÓN / REACTIVACIÓN
 * =========================================================
 */

function cancelarEdicionRetencion(){

    retencionEditandoId =
        null;

    retencionReactivandoId =
        null;


    const inputTipo =
        document.getElementById(
            "tipoRetencion"
        );

    const inputDescripcion =
        document.getElementById(
            "descripcionRetencion"
        );

    const btnGuardar =
        document.getElementById(
            "btnGuardarRetencion"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarRetencion"
        );


    if(inputTipo){

        inputTipo.value =
            "";

    }


    if(inputDescripcion){

        inputDescripcion.value =
            "";

    }


    if(btnGuardar){

        btnGuardar.textContent =
            "Guardar retención";

    }


    if(btnCancelar){

        btnCancelar.style.display =
            "none";

    }


    if(inputTipo){

        inputTipo.focus();

    }

}


/*
 * =========================================================
 * ELIMINAR / DESACTIVAR
 * =========================================================
 */

async function eliminarRetencion(
    retencionId,
    tipo
){

    /*
     * No permitimos eliminar mientras existe una
     * retención en edición o reactivación.
     */

    if(
        retencionEditandoId !== null ||
        retencionReactivandoId !== null
    ){

        alert(
            "Hay una retención en edición.\n\n" +
            "Guarde o cancele los cambios antes de eliminar."
        );

        return;

    }


    const confirmar =
        window.confirm(
            `¿Desactivar la retención "${tipo}"?\n\n` +
            "Los pagos históricos conservarán la referencia."
        );


    if(!confirmar){

        return;

    }


    const empresa =
        obtenerEmpresaRetencion();


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
        "retencion",
        retencionId
    );


    try{

        const respuesta =
            await fetch(
                "/retenciones/eliminar/",
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
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                "No se pudo desactivar la retención."
            );


            return;

        }


        if(
            typeof mostrarABMRetenciones ===
            "function"
        ){

            await mostrarABMRetenciones(
                origenABM
            );

        }


    }catch(error){

        console.error(
            "Error eliminando retención:",
            error
        );


        alert(
            "Ocurrió un error al desactivar la retención."
        );

    }

}


/*
 * =========================================================
 * BUSCADOR
 * =========================================================
 */

function filtrarRetencionesABM(){

    const buscador =
        document.getElementById(
            "buscarRetencionABM"
        );


    if(!buscador){

        return;

    }


    const texto =
        buscador.value
            .trim()
            .toLowerCase();


    document
        .querySelectorAll(
            ".tarjeta-retencion-abm"
        )
        .forEach(
            function(tarjeta){

                const tipo =
                    String(
                        tarjeta.dataset.retencionTipo ||
                        ""
                    ).toLowerCase();


                const descripcion =
                    String(
                        tarjeta.dataset.retencionDescripcion ||
                        ""
                    ).toLowerCase();


                const coincide =
                    !texto ||
                    tipo.includes(
                        texto
                    ) ||
                    descripcion.includes(
                        texto
                    );


                tarjeta.style.display =
                    coincide
                        ? ""
                        : "none";

            }
        );

}


/*
 * =========================================================
 * VOLVER
 * =========================================================
 */

async function volverDesdeABMRetenciones(){

    retencionEditandoId =
        null;

    retencionReactivandoId =
        null;


    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );


    /*
     * =========================================
     * RETENCIONES ABIERTA DESDE PAGO
     * =========================================
     *
     * Este flujo se terminará de conectar
     * cuando agreguemos el acordeón Retenciones
     * al Pago.
     */

    if(
        origenABM === "registro" &&
        typeof contenidoAnteriorABMRetenciones !==
            "undefined" &&
        contenidoAnteriorABMRetenciones &&
        contenidoOperativo
    ){

        contenidoOperativo.innerHTML =
            "";


        contenidoOperativo.appendChild(
            contenidoAnteriorABMRetenciones
        );


        contenidoAnteriorABMRetenciones =
            null;


        if(
            typeof actualizarRetencionDelRegistro ===
            "function"
        ){

            await actualizarRetencionDelRegistro();

        }


        origenABM =
            "registro";


        return;

    }


    /*
     * =========================================
     * APERTURA NORMAL DESDE MENÚ
     * =========================================
     */

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