let cuentaBancariaEditandoId = null;
let cuentaBancariaReactivandoId = null;
let ultimaCuentaBancariaCreada = null;


/* =========================================
   INICIALIZACIÓN
========================================= */

function iniciarABMCuentasBancarias(){

    const btnGuardar =
        document.getElementById(
            "btnGuardarCuentaBancaria"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarCuentaBancaria"
        );

    const btnVolver =
        document.getElementById(
            "btnVolverCuentaBancaria"
        );

    const btnAgregarBanco =
        document.getElementById(
            "btnAgregarBancoCuentaBancaria"
        );

    const buscador =
        document.getElementById(
            "buscarCuentaBancariaABM"
        );

    const inputCBU =
        document.getElementById(
            "cbuCuentaBancaria"
        );


    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarCuentaBancaria
        );

    }


    if(btnCancelar){

        btnCancelar.addEventListener(
            "click",
            cancelarEdicionCuentaBancaria
        );

    }


    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeABMCuentasBancarias
        );

    }


    if(btnAgregarBanco){

        btnAgregarBanco.addEventListener(
            "click",
            function(){

                mostrarABMBancos(
                    "cuenta_bancaria"
                );

            }
        );

    }


    if(buscador){

        buscador.addEventListener(
            "input",
            filtrarCuentasBancariasABM
        );

    }


    if(inputCBU){

        inputCBU.addEventListener(
            "input",
            function(){

                inputCBU.value =
                    inputCBU.value
                        .replace(
                            /\D/g,
                            ""
                        )
                        .slice(
                            0,
                            22
                        );

            }
        );

    }


    document
        .querySelectorAll(
            ".btn-modificar-cuenta-bancaria"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        const tarjeta =
                            boton.closest(
                                ".tarjeta-cuenta-bancaria-abm"
                            );


                        if(!tarjeta){

                            return;

                        }


                        modificarCuentaBancaria(
                            tarjeta.dataset.cuentaId,
                            tarjeta.dataset.cuentaNombre,
                            tarjeta.dataset.cuentaBanco,
                            tarjeta.dataset.cuentaTipo,
                            tarjeta.dataset.cuentaMoneda,
                            tarjeta.dataset.cuentaNumero,
                            tarjeta.dataset.cuentaCbu,
                            tarjeta.dataset.cuentaAlias
                        );

                    }
                );

            }
        );


    document
        .querySelectorAll(
            ".btn-eliminar-cuenta-bancaria"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        eliminarCuentaBancaria(
                            boton.dataset.cuentaId,
                            boton.dataset.cuentaNombre
                        );

                    }
                );

            }
        );

}

async function actualizarBancosCuentaBancaria(){

    const empresa =
        document.getElementById(
            "empresaActiva"
        );

    const selectBanco =
        document.getElementById(
            "bancoCuentaBancaria"
        );


    if(
        !empresa ||
        !empresa.value ||
        !selectBanco
    ){

        return;

    }


    const valorAnterior =
        selectBanco.value;


    try{

        const respuesta =
            await fetch(
                `/listar-bancos/?empresa=${encodeURIComponent(empresa.value)}`
            );


        const resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !Array.isArray(
                resultado.bancos
            )
        ){

            return;

        }


        selectBanco.innerHTML = `
            <option value="">
                Seleccione...
            </option>
        `;


        resultado.bancos.forEach(
            function(banco){

                const opcion =
                    document.createElement(
                        "option"
                    );


                opcion.value =
                    String(
                        banco.id
                    );


                opcion.textContent =
                    banco.nombre;


                selectBanco.appendChild(
                    opcion
                );

            }
        );


        if(
            valorAnterior &&
            selectBanco.querySelector(
                `option[value="${valorAnterior}"]`
            )
        ){

            selectBanco.value =
                valorAnterior;

        }

    if(
        typeof ultimoBancoCreado !==
            "undefined" &&
        ultimoBancoCreado
    ){

        const bancoId =
            String(
                ultimoBancoCreado.id
            );


        const opcionNueva =
            selectBanco.querySelector(
                `option[value="${bancoId}"]`
            );


        if(opcionNueva){

            selectBanco.value =
                bancoId;

        }


        ultimoBancoCreado =
            null;

    }

    }catch(error){

        console.error(
            "Error actualizando bancos de la cuenta bancaria:",
            error
        );

    }

}

/* =========================================
   AUXILIARES
========================================= */

function valorCuentaBancaria(id){

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

function filtrarCuentasBancariasABM(){

    const buscador =
        document.getElementById(
            "buscarCuentaBancariaABM"
        );

    const mensaje =
        document.getElementById(
            "sinResultadosCuentaBancariaABM"
        );

    const texto =
        buscador
            ? buscador.value
                .trim()
                .toLowerCase()
            : "";

    const tarjetas =
        document.querySelectorAll(
            ".tarjeta-cuenta-bancaria-abm"
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
   GUARDAR / MODIFICAR / REACTIVAR
========================================= */

async function guardarCuentaBancaria(){

    const empresa =
        valorCuentaBancaria(
            "empresaActiva"
        );

    const nombre =
        valorCuentaBancaria(
            "nombreCuentaBancaria"
        );

    const banco =
        valorCuentaBancaria(
            "bancoCuentaBancaria"
        );

    const tipoCuenta =
        valorCuentaBancaria(
            "tipoCuentaBancaria"
        );

    const moneda =
        valorCuentaBancaria(
            "monedaCuentaBancaria"
        );

    const numeroCuenta =
        valorCuentaBancaria(
            "numeroCuentaBancaria"
        );

    const cbu =
        valorCuentaBancaria(
            "cbuCuentaBancaria"
        );

    const alias =
        valorCuentaBancaria(
            "aliasCuentaBancaria"
        );


    if(!empresa){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }


    if(!nombre){

        alert(
            "Ingrese un nombre para la cuenta."
        );

        return;

    }


    if(!banco){

        alert(
            "Seleccione un banco."
        );

        return;

    }


    if(!tipoCuenta){

        alert(
            "Seleccione un tipo de cuenta."
        );

        return;

    }


    if(!moneda){

        alert(
            "Seleccione una moneda."
        );

        return;

    }


    if(
        cbu &&
        cbu.length !== 22
    ){

        alert(
            "El CBU debe tener 22 dígitos."
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
        "banco",
        banco
    );

    formulario.append(
        "tipo_cuenta",
        tipoCuenta
    );

    formulario.append(
        "moneda",
        moneda
    );

    formulario.append(
        "numero_cuenta",
        numeroCuenta
    );

    formulario.append(
        "cbu",
        cbu
    );

    formulario.append(
        "alias",
        alias
    );


    let url =
        "/cuentas-bancarias/guardar/";


    if(cuentaBancariaEditandoId){

        url =
            "/cuentas-bancarias/modificar/";


        formulario.append(
            "cuenta",
            cuentaBancariaEditandoId
        );

    }else if(cuentaBancariaReactivandoId){

        url =
            "/cuentas-bancarias/reactivar/";


        formulario.append(
            "cuenta",
            cuentaBancariaReactivandoId
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
            resultado.inactiva &&
            resultado.cuenta
        ){

            cargarCuentaBancariaParaReactivar(
                resultado.cuenta
            );


            alert(
                resultado.mensaje ||
                "La cuenta está inactiva."
            );


            return;

        }


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                "No se pudo guardar la cuenta bancaria."
            );


            return;

        }


        /*
         * Si fue un alta nueva, recordamos la cuenta
         * para seleccionarla cuando volvamos al formulario
         * que originó el ABM.
         */

        if(
            !cuentaBancariaEditandoId &&
            !cuentaBancariaReactivandoId &&
            resultado.cuenta &&
            resultado.cuenta.id
        ){

            /*
            * =========================================
            * CUENTA BANCARIA RECIÉN CREADA
            * =========================================
            *
            * Guardamos los datos mínimos necesarios
            * para poder incorporarla inmediatamente
            * al select que originó el ABM.
            */

            const selectBanco =
                document.getElementById(
                    "bancoCuentaBancaria"
                );


            const bancoNombre =
                selectBanco
                    ? selectBanco.options[
                        selectBanco.selectedIndex
                    ]?.textContent.trim() || ""
                    : "";


            ultimaCuentaBancariaCreada = {

                id:
                    String(
                        resultado.cuenta.id
                    ),

                nombre:
                    resultado.cuenta.nombre,

                banco:
                    bancoNombre

            };

        }


        cuentaBancariaEditandoId =
            null;


        cuentaBancariaReactivandoId =
            null;


        await mostrarABMCuentasBancarias(
            origenABM
        );

    }catch(error){

        console.error(
            "Error guardando cuenta bancaria:",
            error
        );


        alert(
            "Ocurrió un error al guardar la cuenta bancaria."
        );

    }

}


/* =========================================
   MODIFICAR
========================================= */

function modificarCuentaBancaria(
    cuentaId,
    nombre,
    banco,
    tipoCuenta,
    moneda,
    numeroCuenta,
    cbu,
    alias
){

    cuentaBancariaReactivandoId =
        null;

    cuentaBancariaEditandoId =
        String(
            cuentaId
        );


    const inputNombre =
        document.getElementById(
            "nombreCuentaBancaria"
        );

    const selectBanco =
        document.getElementById(
            "bancoCuentaBancaria"
        );

    const selectTipo =
        document.getElementById(
            "tipoCuentaBancaria"
        );

    const selectMoneda =
        document.getElementById(
            "monedaCuentaBancaria"
        );

    const inputNumero =
        document.getElementById(
            "numeroCuentaBancaria"
        );

    const inputCBU =
        document.getElementById(
            "cbuCuentaBancaria"
        );

    const inputAlias =
        document.getElementById(
            "aliasCuentaBancaria"
        );


    if(inputNombre){

        inputNombre.value =
            nombre || "";

    }


    if(selectBanco){

        selectBanco.value =
            banco || "";

    }


    if(selectTipo){

        selectTipo.value =
            tipoCuenta || "";

    }


    if(selectMoneda){

        selectMoneda.value =
            moneda || "";

    }


    if(inputNumero){

        inputNumero.value =
            numeroCuenta || "";

    }


    if(inputCBU){

        inputCBU.value =
            cbu || "";

    }


    if(inputAlias){

        inputAlias.value =
            alias || "";

    }


    configurarModoEdicionCuentaBancaria(
        "Actualizar"
    );

}


/* =========================================
   REACTIVAR
========================================= */

function cargarCuentaBancariaParaReactivar(
    cuenta
){

    cuentaBancariaEditandoId =
        null;

    cuentaBancariaReactivandoId =
        String(
            cuenta.id
        );


    const inputNombre =
        document.getElementById(
            "nombreCuentaBancaria"
        );

    const selectBanco =
        document.getElementById(
            "bancoCuentaBancaria"
        );

    const selectTipo =
        document.getElementById(
            "tipoCuentaBancaria"
        );

    const selectMoneda =
        document.getElementById(
            "monedaCuentaBancaria"
        );

    const inputNumero =
        document.getElementById(
            "numeroCuentaBancaria"
        );

    const inputCBU =
        document.getElementById(
            "cbuCuentaBancaria"
        );

    const inputAlias =
        document.getElementById(
            "aliasCuentaBancaria"
        );


    if(inputNombre){

        inputNombre.value =
            cuenta.nombre || "";

    }


    if(selectBanco){

        selectBanco.value =
            cuenta.banco_id || "";

    }


    if(selectTipo){

        selectTipo.value =
            cuenta.tipo_cuenta || "";

    }


    if(selectMoneda){

        selectMoneda.value =
            cuenta.moneda || "";

    }


    if(inputNumero){

        inputNumero.value =
            cuenta.numero_cuenta || "";

    }


    if(inputCBU){

        inputCBU.value =
            cuenta.cbu || "";

    }


    if(inputAlias){

        inputAlias.value =
            cuenta.alias || "";

    }


    configurarModoEdicionCuentaBancaria(
        "Reactivar"
    );

}


/* =========================================
   MODO EDICIÓN
========================================= */

function configurarModoEdicionCuentaBancaria(
    textoBoton
){

    const btnGuardar =
        document.getElementById(
            "btnGuardarCuentaBancaria"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarCuentaBancaria"
        );

    const inputNombre =
        document.getElementById(
            "nombreCuentaBancaria"
        );


    if(btnGuardar){

        btnGuardar.textContent =
            textoBoton;

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

function cancelarEdicionCuentaBancaria(){

    cuentaBancariaEditandoId =
        null;

    cuentaBancariaReactivandoId =
        null;


    limpiarFormularioCuentaBancaria();

}


function limpiarFormularioCuentaBancaria(){

    const ids = [

        "nombreCuentaBancaria",
        "bancoCuentaBancaria",
        "tipoCuentaBancaria",
        "monedaCuentaBancaria",
        "numeroCuentaBancaria",
        "cbuCuentaBancaria",
        "aliasCuentaBancaria"

    ];


    ids.forEach(
        function(id){

            const elemento =
                document.getElementById(
                    id
                );


            if(elemento){

                elemento.value = "";

            }

        }
    );


    const btnGuardar =
        document.getElementById(
            "btnGuardarCuentaBancaria"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarCuentaBancaria"
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

async function eliminarCuentaBancaria(
    cuentaId,
    nombreCuenta
){

    const confirmado =
        confirm(
            `¿Desactivar la cuenta bancaria "${nombreCuenta}"?\n\n` +
            "La información histórica seguirá conservándose."
        );


    if(!confirmado){

        return;

    }


    const empresa =
        valorCuentaBancaria(
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
        "cuenta",
        cuentaId
    );


    try{

        const respuesta =
            await fetch(
                "/cuentas-bancarias/eliminar/",
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
                "No se pudo desactivar la cuenta bancaria."
            );

            return;

        }


        await mostrarABMCuentasBancarias(
            origenABM
        );


    }catch(error){

        console.error(
            "Error eliminando cuenta bancaria:",
            error
        );


        alert(
            "Ocurrió un error al desactivar la cuenta bancaria."
        );

    }

}


/* =========================================
   VOLVER
========================================= */

async function volverDesdeABMCuentasBancarias(){

    cuentaBancariaEditandoId =
        null;

    cuentaBancariaReactivandoId =
        null;


    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );


    /*
     * =========================================
     * CUENTAS BANCARIAS ABIERTA DESDE REGISTRO
     * =========================================
     */

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


        /*
         * =====================================
         * ORIGEN DE TRANSFERENCIA
         * =====================================
         */

        if(
            typeof contextoRetornoABM !==
                "undefined" &&
            contextoRetornoABM &&
            contextoRetornoABM.tipo ===
                "operacion_bancaria" &&
            contextoRetornoABM.campo ===
                "origen"
        ){

            const pagoId =
                contextoRetornoABM.pagoId;


            if(
                typeof cargarCuentasOperacionBancaria ===
                    "function"
            ){

                await cargarCuentasOperacionBancaria(
                    pagoId
                );

            }


            if(
                ultimaCuentaBancariaCreada
            ){

                const tarjeta =
                    document.getElementById(
                        `pagoRegistro_${pagoId}`
                    );


                const selectCuenta =
                    tarjeta?.querySelector(
                        ".cuenta-origen-operacion-bancaria"
                    );


                if(selectCuenta){

                    const cuentaId =
                        String(
                            ultimaCuentaBancariaCreada.id
                        );


                    const opcion =
                        selectCuenta.querySelector(
                            `option[value="${cuentaId}"]`
                        );


                    if(opcion){

                        selectCuenta.value =
                            cuentaId;

                    }

                }

            }


            const tarjeta =
                document.getElementById(
                    `pagoRegistro_${pagoId}`
                );


            const bloque =
                tarjeta?.querySelector(
                    ".bloque-operaciones-bancarias"
                );


            if(bloque){

                bloque.style.display =
                    "block";

            }


            contextoRetornoABM =
                null;


            origenABM =
                "registro";


            return;

        }


        /*
         * =====================================
         * CHEQUE PROPIO DEL PAGO
         * =====================================
         */

        if(
            typeof contextoRetornoABM !==
                "undefined" &&
            contextoRetornoABM &&
            contextoRetornoABM.tipo ===
                "cheque_pago" &&
            contextoRetornoABM.origen ===
                "propio"
        ){

            const pagoId =
                contextoRetornoABM.pagoId;


            if(
                typeof cargarEntidadesChequePago ===
                    "function"
            ){

                await cargarEntidadesChequePago(
                    pagoId,
                    "propio"
                );

            }


            const tarjeta =
                document.getElementById(
                    `pagoRegistro_${pagoId}`
                );


            const bloque =
                tarjeta?.querySelector(
                    ".bloque-cheques-pago"
                );


            if(bloque){

                bloque.style.display =
                    "block";

            }


            ultimaCuentaBancariaCreada =
                null;


            contextoRetornoABM =
                null;


            origenABM =
                "registro";


            return;

        }

    }


    /*
     * =========================================
     * CUENTAS BANCARIAS ABIERTA DESDE TARJETAS
     * =========================================
     *
     * Flujo:
     *
     * Pago
     *   ↓
     * Tarjetas
     *   ↓
     * [+] Cuenta Bancaria
     *   ↓
     * Cuentas Bancarias
     *   ↓
     * Volver
     *   ↓
     * MISMO formulario de Tarjetas
     *
     * El DOM original de Tarjetas fue guardado
     * antes de abrir Cuentas Bancarias.
     * Por eso Nombre, Tipo y cualquier otro
     * estado del formulario se conserva.
     */

    if(
        origenABM === "tarjeta" &&
        typeof contenidoAnteriorABMCuentasBancariasDesdeTarjeta !==
            "undefined" &&
        contenidoAnteriorABMCuentasBancariasDesdeTarjeta &&
        contenidoOperativo
    ){

        contenidoOperativo.innerHTML =
            "";


        /*
         * Restauramos LOS MISMOS nodos del
         * formulario de Tarjetas.
         */
        contenidoOperativo.appendChild(
            contenidoAnteriorABMCuentasBancariasDesdeTarjeta
        );


        contenidoAnteriorABMCuentasBancariasDesdeTarjeta =
            null;


        /*
         * Recuperamos el origen que tenía
         * Tarjetas antes de entrar a Cuentas.
         *
         * Si Tarjetas había sido abierta desde
         * un Pago, seguirá teniendo origen
         * "registro".
         */
        origenABM =
            typeof origenABMTarjetas !==
                "undefined"
                ? origenABMTarjetas
                : "menu";


        /*
         * Recargamos solamente el select de
         * Cuenta Bancaria del formulario
         * restaurado.
         *
         * actualizarCuentasTarjeta() ya sabe
         * detectar ultimaCuentaBancariaCreada
         * y seleccionarla automáticamente.
         */
        if(
            typeof actualizarCuentasTarjeta ===
                "function"
        ){

            await actualizarCuentasTarjeta();

        }


        /*
         * La cuenta nueva ya fue utilizada.
         * Recién ahora limpiamos la referencia.
         */
        ultimaCuentaBancariaCreada =
            null;


        /*
         * Dejamos visualmente al usuario en
         * el formulario de Tarjetas, no arriba
         * del ABM.
         */
        requestAnimationFrame(
            function(){

                requestAnimationFrame(
                    function(){

                        const selectCuenta =
                            document.getElementById(
                                "cuentaBancariaTarjeta"
                            );


                        if(selectCuenta){

                            selectCuenta.scrollIntoView({

                                behavior:
                                    "smooth",

                                block:
                                    "center"

                            });

                        }

                    }
                );

            }
        );


        return;

    }


    /*
     * =========================================
     * CUENTAS BANCARIAS ABIERTA DESDE MENÚ
     * =========================================
     */

    ultimaCuentaBancariaCreada =
        null;


    if(
        typeof contextoRetornoABM !==
            "undefined"
    ){

        contextoRetornoABM =
            null;

    }


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