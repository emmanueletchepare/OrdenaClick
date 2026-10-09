let clienteEditandoId = null;

/**
 * Devuelve únicamente los dígitos de un CUIT,
 * limitados a los 11 caracteres válidos.
 */
function limpiarCuit(cuit){

    return String(cuit || "")
        .replace(/\D/g, "")
        .slice(0, 11);

}


/**
 * Formatea progresivamente un CUIT mientras
 * el usuario lo escribe.
 *
 * Ejemplo:
 * 20          -> 20-
 * 2012345678  -> 20-12345678-
 * 20123456783 -> 20-12345678-3
 */
function formatearCuit(cuit){

    const digitos =
        limpiarCuit(cuit);


    if(digitos.length === 0){

        return "";

    }


    if(digitos.length < 2){

        return digitos;

    }


    if(digitos.length === 2){

        return `${digitos}-`;

    }


    if(digitos.length < 10){

        return (
            `${digitos.slice(0, 2)}-` +
            digitos.slice(2)
        );

    }


    if(digitos.length === 10){

        return (
            `${digitos.slice(0, 2)}-` +
            `${digitos.slice(2, 10)}-`
        );

    }


    return (
        `${digitos.slice(0, 2)}-` +
        `${digitos.slice(2, 10)}-` +
        digitos.slice(10, 11)
    );

}

/**
 * Inicializa los eventos del ABM de Clientes después
 * de insertar su HTML en el panel.
 */
function iniciarABMClientes(){

    const btnGuardar =
        document.getElementById(
            "btnGuardarCliente"
        );

    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarCliente
        );

    }


    const btnCancelar =
        document.getElementById(
            "btnCancelarCliente"
        );

    if(btnCancelar){

        btnCancelar.addEventListener(
            "click",
            cancelarEdicionCliente
        );

    }


    const btnVolver =
        document.getElementById(
            "btnVolverCliente"
        );

    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeABMClientes
        );

    }


    const btnAgregarCentro =
        document.getElementById(
            "btnAgregarCentroOperativoCliente"
        );

    if(btnAgregarCentro){

        btnAgregarCentro.addEventListener(
            "click",
            abrirCentroOperativoDesdeCliente
        );

    }


    const inputCuit =
        document.getElementById(
            "clienteCuit"
        );

    if(inputCuit){

        inputCuit.addEventListener(
            "input",
            function(){

                inputCuit.value =
                    formatearCuit(
                        inputCuit.value
                    );

            }
        );

    }

    const btnAutocompletarArca =
        document.getElementById(
            "btnAutocompletarClienteArca"
        );

    if(btnAutocompletarArca){

        btnAutocompletarArca.addEventListener(
            "click",
            autocompletarClienteArca
        );

    }

    const buscador =
        document.getElementById(
            "buscarClienteABM"
        );

    if(buscador){

        buscador.addEventListener(
            "input",
            filtrarClientesABM
        );

    }


    document
        .querySelectorAll(
            ".btn-modificar-cliente"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        modificarCliente(
                            boton.dataset.clienteId,
                            boton.dataset.centroId,
                            boton.dataset.numero,
                            boton.dataset.cuit,
                            boton.dataset.razonSocial,
                            boton.dataset.direccion,
                            boton.dataset.celular,
                            boton.dataset.telefono
                        );

                    }
                );

            }
        );


    document
        .querySelectorAll(
            ".btn-eliminar-cliente"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        eliminarCliente(
                            boton.dataset.clienteId,
                            boton.dataset.clienteNombre
                        );

                    }
                );

            }
        );

}

/**
 * Consulta ARCA utilizando el CUIT cargado y completa únicamente
 * la razón social y la dirección del Cliente.
 *
 * La consulta no guarda el Cliente ni modifica ningún otro campo
 * del formulario.
 */
async function autocompletarClienteArca(){

    const inputCuit =
        document.getElementById(
            "clienteCuit"
        );

    const inputRazonSocial =
        document.getElementById(
            "clienteRazonSocial"
        );

    const inputDireccion =
        document.getElementById(
            "clienteDireccion"
        );

    const boton =
        document.getElementById(
            "btnAutocompletarClienteArca"
        );


    if(
        !inputCuit ||
        !inputRazonSocial ||
        !inputDireccion ||
        !boton
    ){

        console.error(
            "No se encontraron los elementos necesarios para consultar ARCA."
        );

        return;

    }


    const cuit =
        limpiarCuit(
            inputCuit.value
        );


    if(cuit.length !== 11){

        alert(
            "Ingresá un CUIT válido de 11 dígitos."
        );

        inputCuit.focus();

        return;

    }


    const url =
        boton.dataset.url;

    if(!url){

        console.error(
            "No se encontró la URL para consultar ARCA."
        );

        return;

    }


    const formulario =
        new FormData();

    const inputEmpresa = document.getElementById("empresaActiva");
    if(!inputEmpresa || !inputEmpresa.value){
        alert("No hay una empresa activa seleccionada.");
        return;
    }

    formulario.append(
        "cuit",
        cuit
    );
    formulario.append("empresa", inputEmpresa.value);


    const textoOriginal =
        boton.textContent;

    boton.disabled = true;
    boton.textContent =
        "Consultando ARCA...";


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


        if(!respuesta.ok || !resultado.ok){

            alert(
                resultado.mensaje ||
                "No se pudo consultar ARCA."
            );

            return;

        }


        inputRazonSocial.value =
            resultado.razon_social || "";

        inputDireccion.value =
            resultado.direccion || "";


    }catch(error){

        console.error(
            "Error consultando ARCA:",
            error
        );

        alert(
            "No se pudo consultar ARCA en este momento. " +
            "Podés continuar cargando el cliente manualmente."
        );


    }finally{

        boton.disabled = false;
        boton.textContent =
            textoOriginal;

    }

}

/**
 * Abre el ABM de Centros Operativos desde Clientes.
 *
 * El formulario de Cliente permanece en el DOM preservado
 * por la navegación contextual para poder restaurarlo sin
 * perder los datos cargados ni el estado de edición.
 */
function abrirCentroOperativoDesdeCliente(){

    mostrarABMCentrosOperativos(
        "cliente"
    );

}

/**
 * Actualiza el selector de Centro Operativo del formulario
 * de Cliente después de regresar desde su ABM contextual.
 *
 * Mantiene intacto el resto del formulario restaurado y,
 * si se creó un Centro Operativo, lo selecciona
 * automáticamente.
 */
async function actualizarCentroOperativoDelCliente(){

    const inputEmpresa =
        document.getElementById(
            "empresaActiva"
        );

    const selectCentro =
        document.getElementById(
            "clienteCentroOperativo"
        );


    if(
        !inputEmpresa ||
        !selectCentro
    ){

        ultimoCentroOperativoCreado =
            null;

        return;

    }


    const empresa =
        inputEmpresa.value;

    const seleccionAnterior =
        selectCentro.value;


    if(!empresa){

        ultimoCentroOperativoCreado =
            null;

        return;

    }


    try{

        const respuesta =
            await fetch(
                `/clientes/?empresa=${encodeURIComponent(empresa)}`
            );


        if(!respuesta.ok){

            console.error(
                "No se pudieron actualizar los Centros Operativos del Cliente."
            );

            return;

        }


        const datos =
            await respuesta.json();


        const contenedorTemporal =
            document.createElement(
                "div"
            );

        contenedorTemporal.innerHTML =
            datos.html;


        const selectActualizado =
            contenedorTemporal.querySelector(
                "#clienteCentroOperativo"
            );


        if(!selectActualizado){

            console.error(
                "La respuesta de Clientes no contiene el selector de Centro Operativo."
            );

            return;

        }


        selectCentro.innerHTML =
            selectActualizado.innerHTML;


        let centroASeleccionar =
            seleccionAnterior;


        if(ultimoCentroOperativoCreado){

            centroASeleccionar =
                typeof ultimoCentroOperativoCreado ===
                    "object"

                    ? String(
                        ultimoCentroOperativoCreado.id
                    )

                    : String(
                        ultimoCentroOperativoCreado
                    );

        }


        if(centroASeleccionar){

            const opcion =
                selectCentro.querySelector(
                    `option[value="${centroASeleccionar}"]`
                );


            if(opcion){

                selectCentro.value =
                    centroASeleccionar;

            }

        }


    }catch(error){

        console.error(
            "Error actualizando los Centros Operativos del Cliente:",
            error
        );


    }finally{

        ultimoCentroOperativoCreado =
            null;

    }

}

/**
 * Filtra visualmente los Clientes mostrados en el ABM.
 */
function filtrarClientesABM(){

    const buscador =
        document.getElementById(
            "buscarClienteABM"
        );

    const mensajeSinResultados =
        document.getElementById(
            "sinResultadosClienteABM"
        );

    const texto =
        buscador
            ? buscador.value
                .trim()
                .toLowerCase()
            : "";

    const tarjetas =
        document.querySelectorAll(
            ".tarjeta-cliente-abm"
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


/**
 * Crea un Cliente o guarda los cambios del Cliente
 * que se encuentra en edición.
 */
async function guardarCliente(){

    const inputEmpresa =
        document.getElementById(
            "empresaActiva"
        );

    const selectCentro =
        document.getElementById(
            "clienteCentroOperativo"
        );

    const inputNumero =
        document.getElementById(
            "clienteNumero"
        );

    const inputCuit =
        document.getElementById(
            "clienteCuit"
        );

    const inputRazonSocial =
        document.getElementById(
            "clienteRazonSocial"
        );

    const inputDireccion =
        document.getElementById(
            "clienteDireccion"
        );

    const inputCelular =
        document.getElementById(
            "clienteCelular"
        );

    const inputTelefono =
        document.getElementById(
            "clienteTelefono"
        );


    if(
        !inputEmpresa ||
        !selectCentro ||
        !inputNumero ||
        !inputCuit ||
        !inputRazonSocial ||
        !inputDireccion ||
        !inputCelular ||
        !inputTelefono
    ){

        console.error(
            "No se encontraron todos los elementos del formulario de clientes."
        );

        return;

    }


    const empresa =
        inputEmpresa.value;

    const centroOperativo =
        selectCentro.value;

    const numeroCliente =
        inputNumero.value.trim();

    const cuit =
        limpiarCuit(
            inputCuit.value
        );

    const razonSocial =
        inputRazonSocial.value.trim();

    const direccion =
        inputDireccion.value.trim();

    const celular =
        inputCelular.value.trim();

    const telefono =
        inputTelefono.value.trim();


    if(!empresa){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }


    if(!centroOperativo){

        alert(
            "Seleccione el Centro Operativo."
        );

        selectCentro.focus();

        return;

    }


    if(!numeroCliente){

        alert(
            "Ingrese el número de cliente."
        );

        inputNumero.focus();

        return;

    }


    if(!razonSocial){

        alert(
            "Ingrese el nombre o razón social."
        );

        inputRazonSocial.focus();

        return;

    }


    const formulario =
        new FormData();

    formulario.append(
        "empresa",
        empresa
    );

    formulario.append(
        "centro_operativo",
        centroOperativo
    );

    formulario.append(
        "numero_cliente",
        numeroCliente
    );

    formulario.append(
        "cuit",
        cuit
    );

    formulario.append(
        "razon_social",
        razonSocial
    );

    formulario.append(
        "direccion",
        direccion
    );

    formulario.append(
        "celular",
        celular
    );

    formulario.append(
        "telefono",
        telefono
    );


    const estaEditando =
        clienteEditandoId !== null;

    let url =
        "/clientes/guardar/";

    if(estaEditando){

        url =
            "/clientes/modificar/";

        formulario.append(
            "cliente",
            clienteEditandoId
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


        if(!respuesta.ok || !resultado.ok){

            if(
                resultado.requiere_reactivacion &&
                resultado.cliente
            ){

                const confirmar =
                    confirm(
                        resultado.mensaje ||
                        "El cliente ya existe pero está inactivo. ¿Desea reactivarlo?"
                    );

                if(confirmar){

                    await reactivarCliente(
                        resultado.cliente.id,
                        formulario
                    );

                }

                return;

            }


            alert(
                resultado.mensaje ||
                (
                    estaEditando
                        ? "No se pudo modificar el cliente."
                        : "No se pudo guardar el cliente."
                )
            );

            return;

        }


        clienteEditandoId = null;

        await mostrarABMClientes(
            origenABM
        );


    }catch(error){

        console.error(
            "Error guardando cliente:",
            error
        );

        alert(
            estaEditando
                ? "Ocurrió un error al modificar el cliente."
                : "Ocurrió un error al guardar el cliente."
        );

    }

}


/**
 * Carga un Cliente existente en el formulario para editarlo.
 */
function modificarCliente(
    clienteId,
    centroId,
    numeroCliente,
    cuit,
    razonSocial,
    direccion,
    celular,
    telefono
){

    clienteEditandoId =
        String(clienteId);


    const selectCentro =
        document.getElementById(
            "clienteCentroOperativo"
        );

    const inputNumero =
        document.getElementById(
            "clienteNumero"
        );

    const inputCuit =
        document.getElementById(
            "clienteCuit"
        );

    const inputRazonSocial =
        document.getElementById(
            "clienteRazonSocial"
        );

    const inputDireccion =
        document.getElementById(
            "clienteDireccion"
        );

    const inputCelular =
        document.getElementById(
            "clienteCelular"
        );

    const inputTelefono =
        document.getElementById(
            "clienteTelefono"
        );

    const btnGuardar =
        document.getElementById(
            "btnGuardarCliente"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarCliente"
        );


    if(selectCentro){

        selectCentro.value =
            centroId || "";

    }

    if(inputNumero){

        inputNumero.value =
            numeroCliente || "";

    }

    if(inputCuit){

        inputCuit.value =
            formatearCuit(
                cuit
            );

    }

    if(inputRazonSocial){

        inputRazonSocial.value =
            razonSocial || "";

    }

    if(inputDireccion){

        inputDireccion.value =
            direccion || "";

    }

    if(inputCelular){

        inputCelular.value =
            celular || "";

    }

    if(inputTelefono){

        inputTelefono.value =
            telefono || "";

    }


    if(btnGuardar){

        btnGuardar.textContent =
            "Actualizar";

    }

    if(btnCancelar){

        btnCancelar.style.display =
            "inline-block";

    }

    if(selectCentro){

        selectCentro.focus();

    }

}


/**
 * Cancela la edición y devuelve el formulario
 * al estado de alta de Cliente.
 */
function cancelarEdicionCliente(){

    clienteEditandoId = null;

    limpiarFormularioCliente();

}


/**
 * Limpia el formulario del ABM de Clientes.
 */
function limpiarFormularioCliente(){

    const selectCentro =
        document.getElementById(
            "clienteCentroOperativo"
        );

    const inputNumero =
        document.getElementById(
            "clienteNumero"
        );

    const inputCuit =
        document.getElementById(
            "clienteCuit"
        );

    const inputRazonSocial =
        document.getElementById(
            "clienteRazonSocial"
        );

    const inputDireccion =
        document.getElementById(
            "clienteDireccion"
        );

    const inputCelular =
        document.getElementById(
            "clienteCelular"
        );

    const inputTelefono =
        document.getElementById(
            "clienteTelefono"
        );

    const btnGuardar =
        document.getElementById(
            "btnGuardarCliente"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarCliente"
        );


    if(selectCentro){

        selectCentro.value = "";

    }

    if(inputNumero){

        inputNumero.value = "";

    }

    if(inputCuit){

        inputCuit.value = "";

    }

    if(inputRazonSocial){

        inputRazonSocial.value = "";

    }

    if(inputDireccion){

        inputDireccion.value = "";

    }

    if(inputCelular){

        inputCelular.value = "";

    }

    if(inputTelefono){

        inputTelefono.value = "";

    }


    if(btnGuardar){

        btnGuardar.textContent =
            "Guardar";

    }

    if(btnCancelar){

        btnCancelar.style.display =
            "none";

    }

    if(selectCentro){

        selectCentro.focus();

    }

}


/**
 * Desactiva lógicamente un Cliente.
 */
async function eliminarCliente(
    clienteId,
    nombreCliente
){

    const confirmado =
        confirm(
            `¿Eliminar el cliente "${nombreCliente}"?`
        );

    if(!confirmado){

        return;

    }


    const inputEmpresa =
        document.getElementById(
            "empresaActiva"
        );

    if(!inputEmpresa || !inputEmpresa.value){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }


    const formulario =
        new FormData();

    formulario.append(
        "empresa",
        inputEmpresa.value
    );

    formulario.append(
        "cliente",
        clienteId
    );


    try{

        const respuesta =
            await fetch(
                "/clientes/eliminar/",
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


        if(!respuesta.ok || !resultado.ok){

            alert(
                resultado.mensaje ||
                "No se pudo eliminar el cliente."
            );

            return;

        }


        if(
            clienteEditandoId ===
            String(clienteId)
        ){

            clienteEditandoId = null;

        }


        await mostrarABMClientes(
            origenABM
        );


    }catch(error){

        console.error(
            "Error eliminando cliente:",
            error
        );

        alert(
            "Ocurrió un error al eliminar el cliente."
        );

    }

}


/**
 * Reactiva un Cliente previamente desactivado utilizando
 * los datos actualmente cargados en el formulario.
 */
async function reactivarCliente(
    clienteId,
    datosFormulario
){

    const formulario =
        new FormData();

    for(
        const [clave, valor]
        of datosFormulario.entries()
    ){

        formulario.append(
            clave,
            valor
        );

    }

    formulario.append(
        "cliente",
        clienteId
    );


    try{

        const respuesta =
            await fetch(
                "/clientes/reactivar/",
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


        if(!respuesta.ok || !resultado.ok){

            alert(
                resultado.mensaje ||
                "No se pudo reactivar el cliente."
            );

            return;

        }


        clienteEditandoId = null;

        await mostrarABMClientes(
            origenABM
        );


    }catch(error){

        console.error(
            "Error reactivando cliente:",
            error
        );

        alert(
            "Ocurrió un error al reactivar el cliente."
        );

    }

}