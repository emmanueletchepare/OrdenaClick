/*
 * =========================================================
 * ABM TARJETAS
 * =========================================================
 *
 * Tarjetas propias de la empresa.
 *
 * Cada tarjeta contiene:
 *
 * - Nombre
 * - Tipo: Crédito / Débito
 * - Cuenta bancaria asociada
 * - Activa / Inactiva
 *
 * No representa necesariamente un plástico individual.
 * =========================================================
 */


let tarjetaEditandoId =
    null;

let tarjetaReactivandoId =
    null;

let ultimaTarjetaCreada =
    null;


/*
 * La cuenta bancaria que estaba seleccionada
 * antes de entrar al ABM de Cuentas Bancarias.
 */

let cuentaTarjetaSeleccionadaAntesABM =
    null;


/*
 * =========================================================
 * INICIALIZACIÓN
 * =========================================================
 */

function iniciarABMTarjetas(){

    const btnGuardar =
        document.getElementById(
            "btnGuardarTarjeta"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarTarjeta"
        );

    const btnVolver =
        document.getElementById(
            "btnVolverTarjetas"
        );

    const btnAgregarCuenta =
        document.getElementById(
            "btnAgregarCuentaTarjeta"
        );

    const buscador =
        document.getElementById(
            "buscarTarjetaABM"
        );


    /*
     * =========================================
     * GUARDAR
     * =========================================
     */

    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarTarjeta
        );

    }


    /*
     * =========================================
     * CANCELAR EDICIÓN / REACTIVACIÓN
     * =========================================
     */

    if(btnCancelar){

        btnCancelar.addEventListener(
            "click",
            cancelarEdicionTarjeta
        );

    }


    /*
     * =========================================
     * VOLVER
     * =========================================
     */

    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeABMTarjetas
        );

    }


    /*
     * =========================================
     * AGREGAR CUENTA BANCARIA
     * =========================================
     */

    if(btnAgregarCuenta){

        btnAgregarCuenta.addEventListener(
            "click",
            abrirABMCuentaDesdeTarjeta
        );

    }


    /*
     * =========================================
     * BUSCADOR
     * =========================================
     */

    if(buscador){

        buscador.addEventListener(
            "input",
            filtrarTarjetasABM
        );

    }


    /*
     * =========================================
     * MODIFICAR
     * =========================================
     */

    document
        .querySelectorAll(
            ".btn-modificar-tarjeta"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        const tarjeta =
                            boton.closest(
                                ".tarjeta-tarjeta-abm"
                            );


                        if(!tarjeta){

                            return;

                        }


                        modificarTarjeta(

                            tarjeta.dataset.tarjetaId,

                            tarjeta.dataset.tarjetaNombre,

                            tarjeta.dataset.tarjetaTipo,

                            tarjeta.dataset.tarjetaCuenta

                        );

                    }
                );

            }
        );


    /*
     * =========================================
     * ELIMINAR / DESACTIVAR
     * =========================================
     */

    document
        .querySelectorAll(
            ".btn-eliminar-tarjeta"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        eliminarTarjeta(

                            boton.dataset.tarjetaId,

                            boton.dataset.tarjetaNombre

                        );

                    }
                );

            }
        );


    /*
     * =========================================
     * CARGAR CUENTAS BANCARIAS
     * =========================================
     */

    actualizarCuentasTarjeta();

}


/*
 * =========================================================
 * HELPERS
 * =========================================================
 */

function valorTarjeta(
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


/*
 * =========================================================
 * CARGAR CUENTAS BANCARIAS
 * =========================================================
 */

async function actualizarCuentasTarjeta(){

    const empresa =
        document.getElementById(
            "empresaActiva"
        );

    const selectCuenta =
        document.getElementById(
            "cuentaBancariaTarjeta"
        );


    if(
        !empresa ||
        !empresa.value ||
        !selectCuenta
    ){

        return;

    }


    const valorAnterior =
        selectCuenta.value;


    try{

        const respuesta =
            await fetch(

                `/cuentas-bancarias/?empresa=${encodeURIComponent(
                    empresa.value
                )}`

            );


        const resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            console.error(
                "No se pudieron cargar las cuentas bancarias para Tarjetas.",
                resultado
            );

            return;

        }


        /*
         * =========================================
         * RECONSTRUIR SELECT
         * =========================================
         */

        selectCuenta.innerHTML = `

            <option value="">
                Seleccione...
            </option>

        `;


        const cuentas =
            Array.isArray(
                resultado.cuentas
            )
                ? resultado.cuentas
                : [];


        cuentas.forEach(
            function(cuenta){

                const opcion =
                    document.createElement(
                        "option"
                    );


                opcion.value =
                    String(
                        cuenta.id
                    );


                /*
                 * Priorizamos el nombre descriptivo
                 * de la Cuenta Bancaria.
                 */

                let texto =
                    cuenta.nombre ||
                    `Cuenta ${cuenta.id}`;


                if(
                    cuenta.banco_nombre &&
                    !texto.includes(
                        cuenta.banco_nombre
                    )
                ){

                    texto +=
                        ` · ${cuenta.banco_nombre}`;

                }


                opcion.textContent =
                    texto;


                selectCuenta.appendChild(
                    opcion
                );

            }
        );


        /*
         * =========================================
         * CONSERVAR VALOR ANTERIOR
         * =========================================
         */

        if(
            valorAnterior &&
            selectCuenta.querySelector(
                `option[value="${valorAnterior}"]`
            )
        ){

            selectCuenta.value =
                valorAnterior;

        }


        /*
         * =========================================
         * CUENTA RECIÉN CREADA
         * =========================================
         *
         * Si venimos del [+] de este ABM,
         * seleccionamos automáticamente la nueva.
         */

        if(
            typeof ultimaCuentaBancariaCreada !==
                "undefined" &&
            ultimaCuentaBancariaCreada
        ){

            const cuentaId =
                String(

                    typeof ultimaCuentaBancariaCreada ===
                    "object"

                        ? ultimaCuentaBancariaCreada.id

                        : ultimaCuentaBancariaCreada

                );


            const opcionNueva =
                selectCuenta.querySelector(
                    `option[value="${cuentaId}"]`
                );


            if(opcionNueva){

                selectCuenta.value =
                    cuentaId;

            }

        }


    }catch(error){

        console.error(
            "Error cargando cuentas bancarias para Tarjetas:",
            error
        );

    }

}


/*
 * =========================================================
 * ABRIR CUENTAS BANCARIAS DESDE TARJETAS
 * =========================================================
 */

function abrirABMCuentaDesdeTarjeta(){

    const selectCuenta =
        document.getElementById(
            "cuentaBancariaTarjeta"
        );


    cuentaTarjetaSeleccionadaAntesABM =
        selectCuenta
            ? selectCuenta.value
            : null;


    if(
        typeof mostrarABMCuentasBancarias !==
        "function"
    ){

        alert(
            "No se pudo abrir el ABM de Cuentas Bancarias."
        );

        return;

    }


    mostrarABMCuentasBancarias(
        "tarjeta"
    );

}


/*
 * =========================================================
 * GUARDAR
 * =========================================================
 */

async function guardarTarjeta(){

    const empresa =
        valorTarjeta(
            "empresaActiva"
        );

    const nombre =
        valorTarjeta(
            "nombreTarjeta"
        );

    const tipo =
        valorTarjeta(
            "tipoTarjeta"
        );

    const cuenta =
        valorTarjeta(
            "cuentaBancariaTarjeta"
        );


    /*
     * =========================================
     * VALIDACIONES
     * =========================================
     */

    if(!empresa){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }


    if(!nombre){

        alert(
            "Ingrese un nombre para la tarjeta."
        );


        const input =
            document.getElementById(
                "nombreTarjeta"
            );


        if(input){

            input.focus();

        }


        return;

    }


    if(!tipo){

        alert(
            "Seleccione si la tarjeta es de Crédito o Débito."
        );

        return;

    }


    if(!cuenta){

        alert(
            "Seleccione una cuenta bancaria."
        );

        return;

    }


    /*
     * =========================================
     * FORM DATA
     * =========================================
     */

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
        "tipo_tarjeta",
        tipo
    );


    formulario.append(
        "cuenta_bancaria",
        cuenta
    );


    /*
     * =========================================
     * URL SEGÚN ESTADO
     * =========================================
     */

    let url =
        "/tarjetas/guardar/";


    const estaEditando =
        tarjetaEditandoId !==
        null;


    const estaReactivando =
        tarjetaReactivandoId !==
        null;


    if(estaEditando){

        url =
            "/tarjetas/modificar/";


        formulario.append(
            "tarjeta",
            tarjetaEditandoId
        );

    }else if(estaReactivando){

        url =
            "/tarjetas/reactivar/";


        formulario.append(
            "tarjeta",
            tarjetaReactivandoId
        );

    }


    /*
     * =========================================
     * GUARDAR
     * =========================================
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
            resultado.inactiva &&
            resultado.tarjeta
        ){

            cargarTarjetaParaReactivar(
                resultado.tarjeta
            );


            alert(
                resultado.mensaje ||
                "La tarjeta existe pero está inactiva. Puede reactivarla."
            );


            return;

        }


        /*
         * =========================================
         * ERROR
         * =========================================
         */

        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            let mensaje =
                "No se pudo guardar la tarjeta.";


            if(estaEditando){

                mensaje =
                    "No se pudo modificar la tarjeta.";

            }else if(estaReactivando){

                mensaje =
                    "No se pudo reactivar la tarjeta.";

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
         */

        if(
            !estaEditando &&
            !estaReactivando &&
            resultado.tarjeta &&
            resultado.tarjeta.id
        ){

            ultimaTarjetaCreada = {

                id:
                    String(
                        resultado.tarjeta.id
                    ),

                nombre:
                    resultado.tarjeta.nombre ||
                    nombre,

                tipo_tarjeta:
                    resultado.tarjeta.tipo_tarjeta ||
                    tipo,

                cuenta_bancaria_id:
                    String(
                        resultado.tarjeta
                            .cuenta_bancaria_id ||
                        cuenta
                    )

            };

        }


        /*
         * =========================================
         * LIMPIAR ESTADO
         * =========================================
         */

        tarjetaEditandoId =
            null;


        tarjetaReactivandoId =
            null;


        /*
         * =========================================
         * RECARGAR ABM
         * =========================================
         */

        if(
            typeof mostrarABMTarjetas ===
            "function"
        ){

            await mostrarABMTarjetas(
                origenABM
            );

        }


    }catch(error){

        console.error(
            "Error guardando tarjeta:",
            error
        );


        alert(
            estaEditando
                ? "Ocurrió un error al modificar la tarjeta."
                : "Ocurrió un error al guardar la tarjeta."
        );

    }

}


/*
 * =========================================================
 * MODIFICAR
 * =========================================================
 */

function modificarTarjeta(
    tarjetaId,
    nombre,
    tipo,
    cuentaId
){

    tarjetaReactivandoId =
        null;


    tarjetaEditandoId =
        String(
            tarjetaId
        );


    const inputNombre =
        document.getElementById(
            "nombreTarjeta"
        );

    const selectTipo =
        document.getElementById(
            "tipoTarjeta"
        );

    const selectCuenta =
        document.getElementById(
            "cuentaBancariaTarjeta"
        );

    const btnGuardar =
        document.getElementById(
            "btnGuardarTarjeta"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarTarjeta"
        );


    /*
     * =========================================
     * CARGAR DATOS
     * =========================================
     */

    if(inputNombre){

        inputNombre.value =
            nombre || "";

    }


    if(selectTipo){

        selectTipo.value =
            tipo || "";

    }


    if(selectCuenta){

        selectCuenta.value =
            String(
                cuentaId || ""
            );

    }


    /*
     * =========================================
     * MODO EDICIÓN
     * =========================================
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
     * =========================================
     * LLEVAR AL FORMULARIO
     * =========================================
     */

    if(inputNombre){

        inputNombre.scrollIntoView({

            behavior:
                "smooth",

            block:
                "center"

        });


        inputNombre.focus();

        inputNombre.select();

    }

}


/*
 * =========================================================
 * CARGAR PARA REACTIVAR
 * =========================================================
 */

async function cargarTarjetaParaReactivar(
    tarjeta
){

    tarjetaEditandoId =
        null;


    tarjetaReactivandoId =
        String(
            tarjeta.id
        );


    const inputNombre =
        document.getElementById(
            "nombreTarjeta"
        );

    const selectTipo =
        document.getElementById(
            "tipoTarjeta"
        );

    const selectCuenta =
        document.getElementById(
            "cuentaBancariaTarjeta"
        );

    const btnGuardar =
        document.getElementById(
            "btnGuardarTarjeta"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarTarjeta"
        );


    /*
     * Si hace falta actualizar cuentas,
     * lo hacemos antes de seleccionarla.
     */

    await actualizarCuentasTarjeta();


    if(inputNombre){

        inputNombre.value =
            tarjeta.nombre ||
            "";

    }


    if(selectTipo){

        selectTipo.value =
            tarjeta.tipo_tarjeta ||
            "";

    }


    if(selectCuenta){

        selectCuenta.value =
            String(
                tarjeta.cuenta_bancaria_id ||
                ""
            );

    }


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


/*
 * =========================================================
 * CANCELAR EDICIÓN / REACTIVACIÓN
 * =========================================================
 */

function cancelarEdicionTarjeta(){

    tarjetaEditandoId =
        null;


    tarjetaReactivandoId =
        null;


    limpiarFormularioTarjeta();

}


/*
 * =========================================================
 * LIMPIAR FORMULARIO
 * =========================================================
 */

function limpiarFormularioTarjeta(){

    const inputNombre =
        document.getElementById(
            "nombreTarjeta"
        );

    const selectTipo =
        document.getElementById(
            "tipoTarjeta"
        );

    const selectCuenta =
        document.getElementById(
            "cuentaBancariaTarjeta"
        );

    const btnGuardar =
        document.getElementById(
            "btnGuardarTarjeta"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarTarjeta"
        );


    if(inputNombre){

        inputNombre.value =
            "";

    }


    if(selectTipo){

        selectTipo.value =
            "Credito";

    }


    if(selectCuenta){

        selectCuenta.value =
            "";

    }


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


/*
 * =========================================================
 * ELIMINAR / DESACTIVAR
 * =========================================================
 */

async function eliminarTarjeta(
    tarjetaId,
    nombreTarjeta
){

    const confirmado =
        confirm(

            `¿Desactivar la tarjeta "${nombreTarjeta}"?\n\n` +

            "La información histórica vinculada a pagos seguirá conservándose."

        );


    if(!confirmado){

        return;

    }


    const empresa =
        valorTarjeta(
            "empresaActiva"
        );


    if(!empresa){

        return;

    }


    const formulario =
        new FormData();


    formulario.append(
        "empresa",
        empresa
    );


    formulario.append(
        "tarjeta",
        tarjetaId
    );


    try{

        const respuesta =
            await fetch(
                "/tarjetas/eliminar/",
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
                "No se pudo desactivar la tarjeta."
            );


            return;

        }


        if(
            typeof mostrarABMTarjetas ===
            "function"
        ){

            await mostrarABMTarjetas(
                origenABM
            );

        }


    }catch(error){

        console.error(
            "Error eliminando tarjeta:",
            error
        );


        alert(
            "Ocurrió un error al desactivar la tarjeta."
        );

    }

}


/*
 * =========================================================
 * BUSCADOR
 * =========================================================
 */

function filtrarTarjetasABM(){

    const buscador =
        document.getElementById(
            "buscarTarjetaABM"
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
            ".tarjeta-tarjeta-abm"
        )
        .forEach(
            function(tarjeta){

                const nombre =
                    String(
                        tarjeta.dataset.tarjetaNombre ||
                        ""
                    ).toLowerCase();


                const tipo =
                    String(
                        tarjeta.dataset.tarjetaTipoLabel ||
                        tarjeta.dataset.tarjetaTipo ||
                        ""
                    ).toLowerCase();


                const cuenta =
                    String(
                        tarjeta.dataset.tarjetaCuentaNombre ||
                        ""
                    ).toLowerCase();


                const coincide =
                    !texto ||
                    nombre.includes(
                        texto
                    ) ||
                    tipo.includes(
                        texto
                    ) ||
                    cuenta.includes(
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

async function volverDesdeABMTarjetas(){

    tarjetaEditandoId =
        null;

    tarjetaReactivandoId =
        null;


    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );


    /*
     * =========================================
     * TARJETAS ABIERTA DESDE REGISTRO / PAGO
     * =========================================
     */
    if(
        origenABM === "registro" &&
        typeof contenidoAnteriorABMTarjetas !==
            "undefined" &&
        contenidoAnteriorABMTarjetas &&
        contenidoOperativo
    ){

        contenidoOperativo.innerHTML =
            "";


        contenidoOperativo.appendChild(
            contenidoAnteriorABMTarjetas
        );


        contenidoAnteriorABMTarjetas =
            null;


        /*
         * Si Tarjetas fue abierta desde el [+]
         * de un Pago, recuperamos exactamente
         * ese Pago y actualizamos solamente
         * su selector de Tarjetas.
         *
         * El resto del formulario se conserva
         * porque los nodos originales fueron
         * guardados y luego restaurados.
         */
        if(
            typeof actualizarTarjetaDelRegistro ===
            "function"
        ){

            await actualizarTarjetaDelRegistro();

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