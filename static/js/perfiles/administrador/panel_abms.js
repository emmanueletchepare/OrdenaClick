async function mostrarABMCentrosOperativos(origen = "menu"){

    origenABM = origen;

    if(origen === "menu"){

        contenidoAnteriorABM = null;

    }

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );

    if(
        (
            origen === "registro" ||
            origen === "cliente"
        ) &&
        contenidoAnteriorABM === null
    ){

        contenidoAnteriorABM =
            document.createDocumentFragment();

        while(contenidoOperativo.firstChild){

            contenidoAnteriorABM.appendChild(
                contenidoOperativo.firstChild
            );

        }

    }

    const empresa =
        document.getElementById(
            "empresaActiva"
        ).value;

    if(!empresa){

        alert(
            "No hay una empresa seleccionada."
        );

        return;

    }

    const respuesta = await fetch(
        `/listar-centros-operativos/?empresa=${empresa}`
    );

    if(!respuesta.ok){

        alert(
            "No se pudo cargar el módulo de centros operativos."
        );

        return;

    }

    const datos =
        await respuesta.json();

    document.getElementById(
        "bloque-alta-empresa"
    ).style.display = "none";

    contenidoOperativo.innerHTML =
        datos.html;

    iniciarABMCentrosOperativos();

}

/**
 * Carga el ABM de Clientes correspondiente a la Empresa
 * activa y conserva el origen de navegación para permitir
 * el futuro retorno contextual desde formularios.
 */
async function mostrarABMClientes(origen = "menu"){

    origenABM = origen;

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );

    const inputEmpresa =
        document.getElementById(
            "empresaActiva"
        );


    if(
        !contenidoOperativo ||
        !inputEmpresa
    ){

        console.error(
            "No se encontraron los elementos necesarios para abrir Clientes."
        );

        return;

    }


    const empresa =
        inputEmpresa.value;


    if(!empresa){

        alert(
            "No hay una empresa seleccionada."
        );

        return;

    }


    try{

        const respuesta =
            await fetch(
                `/clientes/?empresa=${empresa}`
            );


        if(!respuesta.ok){

            alert(
                "No se pudo cargar el módulo de clientes."
            );

            return;

        }


        const datos =
            await respuesta.json();


        const bloqueAlta =
            document.getElementById(
                "bloque-alta-empresa"
            );


        if(bloqueAlta){

            bloqueAlta.style.display =
                "none";

        }


        contenidoOperativo.innerHTML =
            datos.html;


        iniciarABMClientes();


    }catch(error){

        console.error(
            "Error cargando clientes:",
            error
        );

        alert(
            "Ocurrió un error al cargar el módulo de clientes."
        );

    }

}


/**
 * Regresa desde el ABM de Clientes al menú general de ABMs.
 *
 * El retorno contextual desde formularios se incorporará
 * cuando exista el primer selector de Cliente con botón [+].
 */
function volverDesdeABMClientes(){

    mostrarSubmenu(
        "abms"
    );

}

function volverDesdeABMCentrosOperativos(){

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );

    if(
        origenABM === "cliente" &&
        contenidoAnteriorABM
    ){

        contenidoOperativo.innerHTML = "";

        contenidoOperativo.appendChild(
            contenidoAnteriorABM
        );

        contenidoAnteriorABM = null;

        actualizarCentroOperativoDelCliente();

        return;

    }

    if(
        origenABM === "registro" &&
        contenidoAnteriorABM
    ){

        contenidoOperativo.innerHTML = "";

        contenidoOperativo.appendChild(
            contenidoAnteriorABM
        );

        contenidoAnteriorABM = null;

        actualizarCentroOperativoDelRegistro();

        return;

    }

    contenidoAnteriorABM = null;

    mostrarSubmenu("abms");

}

async function actualizarCentroOperativoDelRegistro(){

    if(
        typeof cargarSelectCentrosOperativos !==
            "function"
    ){

        return;

    }


    await cargarSelectCentrosOperativos();


    const select =
        document.getElementById(
            "centroOperativoRegistro"
        );


    if(!select){

        ultimoCentroOperativoCreado =
            null;

        return;

    }


    /*
     * =========================================
     * SELECCIONAR CENTRO RECIÉN CREADO
     * =========================================
     */

    if(
        ultimoCentroOperativoCreado
    ){

        const centroId =
            typeof ultimoCentroOperativoCreado ===
                "object"

                ? String(
                    ultimoCentroOperativoCreado.id
                )

                : String(
                    ultimoCentroOperativoCreado
                );


        const opcion =
            select.querySelector(
                `option[value="${centroId}"]`
            );


        if(opcion){

            select.value =
                centroId;

        }

    }


    ultimoCentroOperativoCreado =
        null;


    /*
     * El Recurso Operativo depende del Centro.
     * Actualizamos sus opciones después de
     * restaurar el Centro seleccionado.
     */

    if(
        typeof actualizarRecursosPorCentroOperativo ===
            "function"
    ){

        actualizarRecursosPorCentroOperativo();

    }


    /*
     * =========================================
     * POSICIÓN EXACTA
     * =========================================
     */

    posicionarCargaSimpleEnCampo(
        "centroOperativoRegistro"
    );

}

async function mostrarABMProveedores(
    origen = "menu"
){

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );

    const empresaActiva =
        document.getElementById(
            "empresaActiva"
        );

    if(
        !contenidoOperativo ||
        !empresaActiva
    ){

        alert(
            "No se pudo preparar el módulo de proveedores."
        );

        return;

    }


    const empresa =
        empresaActiva.value;


    if(!empresa){

        alert(
            "No hay una empresa seleccionada."
        );

        return;

    }


    let datos;


    try{

        const respuesta =
            await fetch(
                `/listar-proveedores/?empresa=${encodeURIComponent(empresa)}`
            );


        if(!respuesta.ok){

            alert(
                "No se pudo cargar el módulo de proveedores."
            );

            return;

        }


        datos =
            await respuesta.json();

    }
    catch(error){

        console.error(
            "Error al cargar el ABM de proveedores:",
            error
        );

        alert(
            "No se pudo conectar con el módulo de proveedores."
        );

        return;

    }


    origenABM =
        origen;

    origenABMTiposGasto =
        origen;


    if(origen === "menu"){

        contenidoAnteriorABMProveedores =
            null;

    }


    if(
        (
            origen === "registro" ||
            origen === "tipo_gasto"
        ) &&
        contenidoAnteriorABMProveedores ===
            null
    ){

        contenidoAnteriorABMProveedores =
            document.createDocumentFragment();


        while(
            contenidoOperativo.firstChild
        ){

            contenidoAnteriorABMProveedores
                .appendChild(
                    contenidoOperativo.firstChild
                );

        }

    }


    const bloqueAltaEmpresa =
        document.getElementById(
            "bloque-alta-empresa"
        );


    if(bloqueAltaEmpresa){

        bloqueAltaEmpresa.style.display =
            "none";

    }


    contenidoOperativo.innerHTML =
        datos.html;


    if(
        typeof iniciarABMProveedores ===
        "function"
    ){

        iniciarABMProveedores();

    }
    else{

        console.error(
            "No se encontró la función iniciarABMProveedores()."
        );

        alert(
            "El módulo de proveedores se cargó, pero no pudo iniciarse."
        );

    }

}

async function mostrarABMTiposGasto(
    origen = "menu"
){

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );

    const empresaActiva =
        document.getElementById(
            "empresaActiva"
        );


    if(
        !contenidoOperativo ||
        !empresaActiva
    ){

        alert(
            "No se pudo preparar el módulo de tipos de gasto."
        );

        return;

    }


    const empresa =
        empresaActiva.value;


    if(!empresa){

        alert(
            "No hay una empresa seleccionada."
        );

        return;

    }


    /*
     * Primero validamos y cargamos el ABM.
     * De esta forma no retiramos Carga Simple
     * si ocurre un error de conexión.
     */
    let datos;


    try{

        const respuesta =
            await fetch(

                `/tipos-gasto/?empresa=${encodeURIComponent(empresa)}`

            );


        if(!respuesta.ok){

            alert(
                "No se pudo cargar el módulo de tipos de gasto."
            );

            return;

        }


        datos =
            await respuesta.json();


    }catch(error){

        console.error(
            "Error cargando tipos de gasto:",
            error
        );

        alert(
            "No se pudo conectar con el módulo de tipos de gasto."
        );

        return;

    }


    origenABM = origen;


    if(origen === "menu"){

        contenidoAnteriorABM = null;

    }


    if(
        origen === "registro" &&
        contenidoAnteriorABM === null
    ){

        contenidoAnteriorABM =
            document.createDocumentFragment();


        while(
            contenidoOperativo.firstChild
        ){

            contenidoAnteriorABM.appendChild(
                contenidoOperativo.firstChild
            );

        }

    }


    const bloqueAltaEmpresa =
        document.getElementById(
            "bloque-alta-empresa"
        );


    if(bloqueAltaEmpresa){

        bloqueAltaEmpresa.style.display =
            "none";

    }


    contenidoOperativo.innerHTML =
        datos.html;


    if(
        typeof iniciarABMTiposGasto ===
        "function"
    ){

        iniciarABMTiposGasto();

    }else{

        console.error(
            "No se encontró iniciarABMTiposGasto()."
        );

        alert(
            "El módulo se cargó, pero no pudo iniciarse."
        );

    }

}

function actualizarTipoGastoDelRegistro(){

    const select =
        document.getElementById(
            "tipoGastoRegistro"
        );


    if(!select){

        ultimoTipoGastoCreado =
            null;

        return;

    }


    /*
     * Aunque no se haya creado un elemento,
     * si volvemos desde el ABM debemos quedar
     * exactamente en Tipo de Gasto.
     */

    if(!ultimoTipoGastoCreado){

        posicionarCargaSimpleEnCampo(
            "tipoGastoRegistro"
        );

        return;

    }


    const tipoGastoId =
        typeof ultimoTipoGastoCreado ===
            "object"

            ? String(
                ultimoTipoGastoCreado.id
            )

            : String(
                ultimoTipoGastoCreado
            );


    const tipoGastoNombre =
        typeof ultimoTipoGastoCreado ===
            "object"

            ? ultimoTipoGastoCreado.nombre

            : "Tipo de gasto creado";


    let opcion =
        select.querySelector(
            `option[value="${tipoGastoId}"]`
        );


    if(!opcion){

        opcion =
            document.createElement(
                "option"
            );


        opcion.value =
            tipoGastoId;


        opcion.textContent =
            tipoGastoNombre ||
            "Tipo de gasto creado";


        select.appendChild(
            opcion
        );

    }


    select.value =
        tipoGastoId;


    ultimoTipoGastoCreado =
        null;


    /*
     * =========================================
     * POSICIÓN EXACTA
     * =========================================
     */

    posicionarCargaSimpleEnCampo(
        "tipoGastoRegistro"
    );

}

async function volverDesdeABMProveedores(){

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );


    if(!contenidoOperativo){

        alert(
            "No se pudo recuperar el módulo anterior."
        );

        return;

    }


    /*
     * Proveedores abierto desde Carga Simple.
     */
    if(
        origenABM === "registro" &&
        contenidoAnteriorABMProveedores
    ){

        contenidoOperativo.innerHTML =
            "";


        contenidoOperativo.appendChild(
            contenidoAnteriorABMProveedores
        );


        contenidoAnteriorABMProveedores =
            null;


        if(
            typeof actualizarProveedorDelRegistro ===
            "function"
        ){

            await actualizarProveedorDelRegistro();

        }


        origenABM =
            "registro";


        return;

    }


    /*
     * Proveedores abierto desde Tipo de Gasto.
     */
    if(
        origenABM === "tipo_gasto" &&
        contenidoAnteriorABMProveedores
    ){

        contenidoOperativo.innerHTML =
            "";


        contenidoOperativo.appendChild(
            contenidoAnteriorABMProveedores
        );


        contenidoAnteriorABMProveedores =
            null;


        if(
            typeof actualizarProveedoresDelTipoGasto ===
            "function"
        ){

            await actualizarProveedoresDelTipoGasto();

        }


        /*
        * Volvemos a Tipo de Gasto, pero restauramos
        * también el origen REAL desde donde ese ABM
        * había sido abierto.
        *
        * Ejemplo:
        *
        * Carga Simple
        * → Tipo de Gasto
        * → Proveedor
        * → Tipo de Gasto
        * → Carga Simple
        */

        origenABM =
            origenABMTiposGasto;


        return;

    }


    /*
     * Proveedores abierto directamente desde el menú.
     */
    contenidoAnteriorABMProveedores =
        null;

    origenABM =
        "menu";


    mostrarSubmenu(
        "abms"
    );

}


async function actualizarProveedorDelRegistro(){

    await cargarSelectProveedores();


    const select =
        document.getElementById(
            "proveedorRegistro"
        );


    if(!select){

        ultimoProveedorCreado =
            null;

        return;

    }


    if(
        ultimoProveedorCreado
    ){

        const opcion =
            select.querySelector(
                `option[value="${ultimoProveedorCreado}"]`
            );


        if(opcion){

            select.value =
                ultimoProveedorCreado;

        }

    }


    ultimoProveedorCreado =
        null;


    /*
     * =========================================
     * POSICIÓN EXACTA
     * =========================================
     */

    posicionarCargaSimpleEnCampo(
        "proveedorRegistro"
    );

}

async function mostrarABMTarjetas(
    origen = "menu"
){

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );

    const empresa =
        document.getElementById(
            "empresaActiva"
        );


    if(
        !contenidoOperativo ||
        !empresa ||
        !empresa.value
    ){

        alert(
            "Seleccione una empresa."
        );

        return;

    }


    let resultado;


    try{

        const respuesta =
            await fetch(
                `/tarjetas/?empresa=${encodeURIComponent(empresa.value)}`
            );


        resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                "No se pudieron cargar las tarjetas."
            );

            return;

        }

    }catch(error){

        console.error(
            "Error cargando tarjetas:",
            error
        );


        alert(
            "Ocurrió un error al cargar las tarjetas."
        );

        return;

    }


    origenABM =
        origen;

    origenABMTarjetas =
        origen;


    if(origen === "menu"){

        contenidoAnteriorABMTarjetas =
            null;

    }


    if(
        origen === "registro" &&
        contenidoAnteriorABMTarjetas === null
    ){

        contenidoAnteriorABMTarjetas =
            document.createDocumentFragment();


        while(
            contenidoOperativo.firstChild
        ){

            contenidoAnteriorABMTarjetas.appendChild(
                contenidoOperativo.firstChild
            );

        }

    }


    const bloqueAlta =
        document.getElementById(
            "bloque-alta-empresa"
        );


    if(bloqueAlta){

        bloqueAlta.style.display =
            "none";

    }


    contenidoOperativo.innerHTML =
        resultado.html;


    if(
        typeof iniciarABMTarjetas ===
        "function"
    ){

        iniciarABMTarjetas();

    }else{

        console.error(
            "No se encontró iniciarABMTarjetas()."
        );

    }

}

async function mostrarABMRetenciones(
    origen = "menu"
){

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );

    const empresa =
        document.getElementById(
            "empresaActiva"
        );


    if(
        !contenidoOperativo ||
        !empresa ||
        !empresa.value
    ){

        alert(
            "Seleccione una empresa."
        );

        return;

    }


    let resultado;


    /*
     * =========================================
     * CARGAR ABM
     * =========================================
     */

    try{

        const respuesta =
            await fetch(

                `/retenciones/?empresa=${encodeURIComponent(
                    empresa.value
                )}`

            );


        resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                "No se pudieron cargar las retenciones."
            );

            return;

        }


    }catch(error){

        console.error(
            "Error cargando retenciones:",
            error
        );


        alert(
            "Ocurrió un error al cargar las retenciones."
        );

        return;

    }


    /*
     * =========================================
     * GUARDAR ORIGEN
     * =========================================
     */

    origenABM =
        origen;

    origenABMRetenciones =
        origen;


    /*
     * =========================================
     * APERTURA DESDE MENÚ
     * =========================================
     */

    if(origen === "menu"){

        contenidoAnteriorABMRetenciones =
            null;

    }


    /*
     * =========================================
     * APERTURA DESDE PAGO
     * =========================================
     *
     * Todavía no usamos esta rama.
     *
     * Queda preparada para:
     *
     * Carga Simple
     * → Pago determinado
     * → Retenciones
     * → [+]
     * → ABM Retenciones
     *
     * Guardamos LOS MISMOS nodos para no perder
     * importe, comprobante, otros pagos, etc.
     */

    if(
        origen === "registro" &&
        contenidoAnteriorABMRetenciones ===
            null
    ){

        contenidoAnteriorABMRetenciones =
            document.createDocumentFragment();


        while(
            contenidoOperativo.firstChild
        ){

            contenidoAnteriorABMRetenciones
                .appendChild(
                    contenidoOperativo.firstChild
                );

        }

    }


    /*
     * =========================================
     * OCULTAR ALTA DE EMPRESA
     * =========================================
     */

    const bloqueAlta =
        document.getElementById(
            "bloque-alta-empresa"
        );


    if(bloqueAlta){

        bloqueAlta.style.display =
            "none";

    }


    /*
     * =========================================
     * MOSTRAR ABM
     * =========================================
     */

    contenidoOperativo.innerHTML =
        resultado.html;


    /*
     * =========================================
     * INICIALIZAR JS EXTERNO
     * =========================================
     */

    if(
        typeof iniciarABMRetenciones ===
            "function"
    ){

        iniciarABMRetenciones();

    }else{

        console.error(
            "No se encontró iniciarABMRetenciones()."
        );

    }

}

async function mostrarABMCuentasBancarias(
    origen = "menu"
){

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );

    const empresa =
        document.getElementById(
            "empresaActiva"
        );


    if(
        !contenidoOperativo ||
        !empresa ||
        !empresa.value
    ){

        alert(
            "Seleccione una empresa."
        );

        return;

    }


    let resultado;


    try{

        const respuesta =
            await fetch(
                `/cuentas-bancarias/?empresa=${encodeURIComponent(empresa.value)}`
            );


        resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                "No se pudieron cargar las cuentas bancarias."
            );

            return;

        }

    }catch(error){

        console.error(
            "Error cargando cuentas bancarias:",
            error
        );


        alert(
            "Ocurrió un error al cargar las cuentas bancarias."
        );

        return;

    }


    origenABM =
        origen;

    origenABMCuentasBancarias =
        origen;


    if(origen === "menu"){

        contenidoAnteriorABM =
            null;

    }


    if(
        origen === "registro" &&
        contenidoAnteriorABM === null
    ){

        contenidoAnteriorABM =
            document.createDocumentFragment();


        while(
            contenidoOperativo.firstChild
        ){

            contenidoAnteriorABM.appendChild(
                contenidoOperativo.firstChild
            );

        }

    }


    /*
     * Tarjetas → Cuentas Bancarias.
     * Guardamos el DOM completo del ABM de Tarjetas para
     * poder restaurarlo exactamente al volver.
     */

    if(
        origen === "tarjeta" &&
        contenidoAnteriorABMCuentasBancariasDesdeTarjeta === null
    ){

        contenidoAnteriorABMCuentasBancariasDesdeTarjeta =
            document.createDocumentFragment();


        while(
            contenidoOperativo.firstChild
        ){

            contenidoAnteriorABMCuentasBancariasDesdeTarjeta.appendChild(
                contenidoOperativo.firstChild
            );

        }

    }


    const bloqueAlta =
        document.getElementById(
            "bloque-alta-empresa"
        );


    if(bloqueAlta){

        bloqueAlta.style.display =
            "none";

    }


    contenidoOperativo.innerHTML =
        resultado.html;


    if(
        typeof iniciarABMCuentasBancarias ===
        "function"
    ){

        iniciarABMCuentasBancarias();

    }

}

async function mostrarABMRecursosOperativos(
    origen = "menu"
){

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );

    const empresa =
        document.getElementById(
            "empresaActiva"
        );


    if(
        !contenidoOperativo ||
        !empresa ||
        !empresa.value
    ){

        alert(
            "Seleccione una empresa."
        );

        return;

    }


    let resultado;


    try{

        const respuesta =
            await fetch(
                `/recursos-operativos/?empresa=${encodeURIComponent(empresa.value)}`
            );


        resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                "No se pudieron cargar los recursos operativos."
            );

            return;

        }


    }catch(error){

        console.error(
            "Error cargando recursos operativos:",
            error
        );


        alert(
            "Ocurrió un error al cargar los recursos operativos."
        );

        return;

    }


    /*
     * Recién después de comprobar que el ABM cargó
     * guardamos el origen.
     */
    origenABM =
        origen;


    if(origen === "menu"){

        contenidoAnteriorABM =
            null;

    }


    /*
     * Si viene desde Carga Simple, retiramos físicamente
     * el formulario y lo guardamos completo.
     *
     * Así conserva inputs, selects y demás estado.
     */
    if(
        origen === "registro" &&
        contenidoAnteriorABM === null
    ){

        contenidoAnteriorABM =
            document.createDocumentFragment();


        while(
            contenidoOperativo.firstChild
        ){

            contenidoAnteriorABM.appendChild(
                contenidoOperativo.firstChild
            );

        }

    }


    const bloqueAlta =
        document.getElementById(
            "bloque-alta-empresa"
        );


    if(bloqueAlta){

        bloqueAlta.style.display =
            "none";

    }


    contenidoOperativo.innerHTML =
        resultado.html;


    if(
        typeof iniciarABMRecursosOperativos ===
        "function"
    ){

        iniciarABMRecursosOperativos();

    }else{

        console.error(
            "No se encontró iniciarABMRecursosOperativos()."
        );

        alert(
            "El módulo se cargó, pero no pudo iniciarse."
        );

    }

}

async function actualizarRecursoOperativoDelRegistro(){

    const empresa =
        document.getElementById(
            "empresaActiva"
        );


    const selectCentro =
        document.getElementById(
            "centroOperativoRegistro"
        );


    const selectRecurso =
        document.getElementById(
            "recursoOperativoRegistro"
        );


    if(
        !empresa ||
        !empresa.value ||
        !selectCentro ||
        !selectRecurso
    ){

        ultimoRecursoOperativoCreado =
            null;

        return;

    }


    try{

        const respuesta =
            await fetch(
                `/recursos-operativos/?empresa=${encodeURIComponent(empresa.value)}`
            );


        const resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !resultado.ok ||
            !Array.isArray(
                resultado.recursos
            )
        ){

            posicionarCargaSimpleEnCampo(
                "recursoOperativoRegistro"
            );

            return;

        }


        recursosCargaSimple =
            resultado.recursos;


        if(
            ultimoRecursoOperativoCreado
        ){

            const recursoId =
                typeof ultimoRecursoOperativoCreado ===
                    "object"

                    ? String(
                        ultimoRecursoOperativoCreado.id
                    )

                    : String(
                        ultimoRecursoOperativoCreado
                    );


            const recursoCreado =
                recursosCargaSimple.find(

                    function(recurso){

                        return String(
                            recurso.id
                        ) === recursoId;

                    }

                );


            if(recursoCreado){

                const centrosRecurso =
                    Array.isArray(
                        recursoCreado.centros_operativos_ids
                    )

                        ? recursoCreado.centros_operativos_ids

                        : [];


                /*
                 * Si el Centro Operativo actual pertenece
                 * al recurso nuevo, lo conservamos.
                 */

                const centroActual =
                    String(
                        selectCentro.value ||
                        ""
                    );


                const perteneceAlCentroActual =
                    centrosRecurso

                        .map(
                            function(centroId){

                                return String(
                                    centroId
                                );

                            }
                        )

                        .includes(
                            centroActual
                        );


                /*
                 * Si no pertenece al Centro actual,
                 * usamos el primero asociado al recurso.
                 */

                if(!perteneceAlCentroActual){

                    const primerCentroId =
                        centrosRecurso.length > 0

                            ? String(
                                centrosRecurso[0]
                            )

                            : "";


                    if(primerCentroId){

                        const opcionCentro =
                            selectCentro.querySelector(
                                `option[value="${primerCentroId}"]`
                            );


                        if(opcionCentro){

                            selectCentro.value =
                                primerCentroId;

                        }

                    }

                }


                /*
                 * Reconstruimos Recursos según
                 * el Centro Operativo seleccionado.
                 */

                actualizarRecursosPorCentroOperativo();


                const opcionRecurso =
                    selectRecurso.querySelector(
                        `option[value="${recursoId}"]`
                    );


                if(opcionRecurso){

                    selectRecurso.value =
                        recursoId;

                }

            }else{

                actualizarRecursosPorCentroOperativo();

            }

        }else{

            actualizarRecursosPorCentroOperativo();

        }


    }catch(error){

        console.error(
            "Error actualizando Recursos Operativos del registro:",
            error
        );

    }


    ultimoRecursoOperativoCreado =
        null;


    /*
     * =========================================
     * POSICIÓN EXACTA
     * =========================================
     */

    posicionarCargaSimpleEnCampo(
        "recursoOperativoRegistro"
    );

}

async function mostrarABMBancos(
    origen = "menu"
){

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );

    const empresaElemento =
        document.getElementById(
            "empresaActiva"
        );


    if(
        !contenidoOperativo ||
        !empresaElemento ||
        !empresaElemento.value
    ){

        alert(
            "No hay una empresa seleccionada."
        );

        return;

    }


    const empresa =
        empresaElemento.value;


    let datos;


    try{

        const respuesta =
            await fetch(
                `/listar-bancos/?empresa=${encodeURIComponent(empresa)}`
            );


        if(!respuesta.ok){

            alert(
                "No se pudo cargar el módulo de bancos."
            );

            return;

        }


        datos =
            await respuesta.json();

    }catch(error){

        console.error(
            "Error cargando bancos:",
            error
        );


        alert(
            "Ocurrió un error al cargar el módulo de bancos."
        );

        return;

    }


    /*
     * Guardamos el formulario anterior recién después
     * de comprobar que Bancos pudo cargarse.
     */

    if(origen === "menu"){

        contenidoAnteriorABM =
            null;

    }


    if(
        origen === "registro" &&
        contenidoAnteriorABM === null
    ){

        contenidoAnteriorABM =
            document.createDocumentFragment();


        while(
            contenidoOperativo.firstChild
        ){

            contenidoAnteriorABM.appendChild(
                contenidoOperativo.firstChild
            );

        }

    }


    /*
     * Segundo nivel:
     *
     * Formulario original
     * → Cuentas Bancarias
     * → Bancos
     *
     * Este fragmento guarda exclusivamente
     * el ABM de Cuentas Bancarias.
     */

    if(
        origen === "cuenta_bancaria" &&
        contenidoAnteriorABMBancosDesdeCuentaBancaria === null
    ){

        contenidoAnteriorABMBancosDesdeCuentaBancaria =
            document.createDocumentFragment();


        while(
            contenidoOperativo.firstChild
        ){

            contenidoAnteriorABMBancosDesdeCuentaBancaria.appendChild(
                contenidoOperativo.firstChild
            );

        }

    }


    origenABM =
        origen;


    const bloqueAlta =
        document.getElementById(
            "bloque-alta-empresa"
        );


    if(bloqueAlta){

        bloqueAlta.style.display =
            "none";

    }


    contenidoOperativo.innerHTML =
        datos.html;


    iniciarABMBancos();

}

async function volverDesdeABMBancos(){

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );


    /*
     * =========================================
     * BANCOS ABIERTO DESDE CUENTAS BANCARIAS
     * =========================================
     */

    if(
        origenABM === "cuenta_bancaria" &&
        contenidoAnteriorABMBancosDesdeCuentaBancaria &&
        contenidoOperativo
    ){

        contenidoOperativo.innerHTML =
            "";


        contenidoOperativo.appendChild(
            contenidoAnteriorABMBancosDesdeCuentaBancaria
        );


        contenidoAnteriorABMBancosDesdeCuentaBancaria =
            null;


        origenABM =
            origenABMCuentasBancarias;


        if(
            typeof actualizarBancosCuentaBancaria ===
                "function"
        ){

            await actualizarBancosCuentaBancaria();

        }


        return;

    }


    /*
     * =========================================
     * BANCOS ABIERTOS DESDE REGISTRO
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
         * DESTINO TRANSFERENCIA / DEPÓSITO
         * =====================================
         */

        if(
            contextoRetornoABM &&
            contextoRetornoABM.tipo ===
                "operacion_bancaria" &&
            contextoRetornoABM.campo ===
                "destino"
        ){

            const pagoId =
                Number(
                    contextoRetornoABM.pagoId
                );


            const tarjeta =
                document.getElementById(
                    `pagoRegistro_${pagoId}`
                );


            if(!tarjeta){

                contextoRetornoABM =
                    null;

                return;

            }


            /*
             * Recargar Bancos de ESTA transferencia.
             */

            await cargarBancosOperacionBancaria(
                pagoId
            );


            /*
             * Abrir Transferencias / Depósitos.
             */

            const bloque =
                tarjeta.querySelector(
                    ".bloque-operaciones-bancarias"
                );


            const boton =
                tarjeta.querySelector(
                    ".btn-toggle-operaciones-bancarias"
                );


            const total =
                tarjeta.querySelector(
                    ".total-operaciones-bancarias"
                );


            if(bloque){

                bloque.style.display =
                    "block";

            }


            if(boton){

                boton.innerHTML = `

                    <span>
                        ▼ Transferencias / Depósitos
                    </span>

                    <strong
                        class="total-operaciones-bancarias"
                    >
                        ${
                            total
                                ? total.textContent
                                : "$ 0,00"
                        }
                    </strong>

                `;

            }


            /*
             * Banco recién creado.
             *
             * cargarBancosOperacionBancaria()
             * ya maneja ultimoBancoCreado y selecciona
             * automáticamente el Banco nuevo.
             */


            contextoRetornoABM =
                null;


            origenABM =
                "registro";


            /*
             * =====================================
             * POSICIÓN EXACTA
             * =====================================
             *
             * El encabezado Transferencias queda
             * arriba, igual que con Cuenta Bancaria.
             */

            posicionarMainEnElemento(
                boton,
                15
            );


            return;

        }


        /*
         * =====================================
         * CHEQUE DE TERCERO DEL PAGO
         * =====================================
         */

        if(
            contextoRetornoABM &&
            contextoRetornoABM.tipo ===
                "cheque_pago" &&
            contextoRetornoABM.origen ===
                "tercero"
        ){

            const pagoId =
                Number(
                    contextoRetornoABM.pagoId
                );


            const tarjeta =
                document.getElementById(
                    `pagoRegistro_${pagoId}`
                );


            if(!tarjeta){

                contextoRetornoABM =
                    null;

                return;

            }


            await cargarEntidadesChequePago(
                pagoId,
                "tercero"
            );


            const bloque =
                tarjeta.querySelector(
                    ".bloque-cheques-pago"
                );


            const boton =
                tarjeta.querySelector(
                    ".btn-toggle-cheques-pago"
                );


            const total =
                tarjeta.querySelector(
                    ".total-cheques-pago"
                );


            if(bloque){

                bloque.style.display =
                    "block";

            }


            if(boton){

                boton.innerHTML = `

                    <span>
                        ▼ Cheques
                    </span>

                    <strong
                        class="total-cheques-pago"
                    >
                        ${
                            total
                                ? total.textContent
                                : "$ 0,00"
                        }
                    </strong>

                `;

            }


            /*
             * Mantener origen Tercero.
             */

            const selectOrigen =
                tarjeta.querySelector(
                    ".origen-cheque-pago"
                );


            if(selectOrigen){

                selectOrigen.value =
                    "tercero";

            }


            contextoRetornoABM =
                null;


            origenABM =
                "registro";


            posicionarMainEnElemento(
                boton,
                15
            );


            return;

        }

    }


    /*
     * =========================================
     * ABM ABIERTO DESDE MENÚ
     * =========================================
     */

    contenidoAnteriorABM =
        null;


    contextoRetornoABM =
        null;


    origenABM =
        "menu";


    mostrarSubmenu(
        "abms"
    );

}

function agregarBancoTemporal(){

    const input =
        document.getElementById(
            "nuevoBanco"
        );

    const nombre =
        input.value.trim();

    if(nombre===""){

        alert(
            "Ingrese el nombre del banco."
        );

        return;

    }

    const grilla =
        document.getElementById(
            "grillaBancos"
        );

    grilla.insertAdjacentHTML(
        "beforeend",
        `

<div
style="
display:flex;
justify-content:space-between;
align-items:center;
padding:14px 18px;
background:#1b2130;
border:1px solid #2b3447;
border-radius:14px;
">

<div>

${nombre}

</div>

<div
style="
display:flex;
gap:8px;
">

<button
class="action-btn">

Modificar

</button>

<button
class="action-btn"
style="
background:#7f1d1d;
border-color:#991b1b;
">

Eliminar

</button>

</div>

</div>

`
    );

    input.value="";

    input.focus();

}
