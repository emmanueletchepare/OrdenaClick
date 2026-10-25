/*
 * =========================================
 * PRÓXIMOS VENCIMIENTOS
 * =========================================
 *
 * Interfaz del módulo de obligaciones
 * financieras pendientes.
 *
 * Las reglas de cálculo pertenecen al
 * servicio financiero del backend.
 */


document.addEventListener(
    "DOMContentLoaded",
    function(){

        const boton =
            document.getElementById(
                "btnSidebarAlertas"
            );

        if(!boton){
            return;
        }

        boton.addEventListener(
            "click",
            function(){

                mostrarAlertasIndependientes();

            }
        );

    }
);


function obtenerEmpresaActivaVencimientos(){

    const empresaActiva =
        document.getElementById(
            "empresaActiva"
        );

    if(
        !empresaActiva ||
        !empresaActiva.value
    ){
        return null;
    }

    return empresaActiva.value;

}


function formatearImporteVencimiento(valor){

    const numero =
        Number(valor || 0);

    return new Intl.NumberFormat(
        "es-AR",
        {
            style: "currency",
            currency: "ARS",
            minimumFractionDigits: 2,
        }
    ).format(numero);

}


function formatearFechaVencimiento(fecha){

    if(!fecha){
        return "-";
    }

    const partes =
        fecha.split("-");

    if(partes.length !== 3){
        return fecha;
    }

    return (
        `${partes[2]}/${partes[1]}/${partes[0]}`
    );

}


function construirEstructuraProximosVencimientos(){

    const contenido =
        document.getElementById(
            "contenido-operativo"
        );

    if(!contenido){
        return;
    }

    const bloqueAlta =
        document.getElementById(
            "bloque-alta-empresa"
        );

    if(bloqueAlta){
        bloqueAlta.style.display =
            "none";
    }

    const submenu =
        document.getElementById(
            "submenu-dinamico"
        );

    if(submenu){
        submenu.innerHTML = "";
    }

    contenido.innerHTML = `
        <div class="vencimientos-contenedor">

            <div class="vencimientos-navegacion">

                <button
                    type="button"
                    class="vencimientos-flecha vencimientos-flecha-izquierda"
                    id="btnVencimientosAnterior"
                    aria-label="Opciones anteriores"
                    title="Opciones anteriores"
                >
                    ‹
                </button>

                <div
                    class="vencimientos-botonera"
                    id="botoneraVencimientos"
                >

                    <button
                        type="button"
                        class="vencimientos-segmento activo"
                        id="btnVencimientosAlertas"
                    >
                        Alertas
                    </button>

                    <button
                        type="button"
                        class="vencimientos-segmento"
                        id="btnVencimientosHoy"
                    >
                        Hoy
                    </button>

                    <button
                        type="button"
                        class="vencimientos-segmento"
                        id="btnVencimientosSemana"
                    >
                        Esta semana
                    </button>

                    <button
                        type="button"
                        class="vencimientos-segmento"
                        id="btnVencimientosRango"
                    >
                        Rango de fechas
                    </button>

                </div>

                <button
                    type="button"
                    class="vencimientos-flecha vencimientos-flecha-derecha"
                    id="btnVencimientosSiguiente"
                    aria-label="Opciones siguientes"
                    title="Opciones siguientes"
                >
                    ›
                </button>

            </div>

            <div
                id="rangoFechasVencimientos"
                class="vencimientos-rango"
            >

                <div class="field">

                    <label
                        class="label"
                        for="fechaDesdeVencimientos"
                    >
                        Desde
                    </label>

                    <input
                        type="date"
                        id="fechaDesdeVencimientos"
                        class="input-box"
                    >

                </div>

                <div class="field">

                    <label
                        class="label"
                        for="fechaHastaVencimientos"
                    >
                        Hasta
                    </label>

                    <input
                        type="date"
                        id="fechaHastaVencimientos"
                        class="input-box"
                    >

                </div>

                <button
                    type="button"
                    class="sidebar-btn vencimientos-aplicar"
                    id="btnAplicarRangoVencimientos"
                >
                    Aplicar
                </button>

            </div>

            <div
                id="estadoProximosVencimientos"
                class="empty-state"
                style="display:none;"
            >
            </div>

            <div
                id="tablaProximosVencimientos"
            >
            </div>

        </div>
    `;

}

function marcarSegmentoVencimientosActivo(
    botonActivo
){

    const botonera =
        document.getElementById(
            "botoneraVencimientos"
        );


    marcarSegmentoNavegacionActivo(
        botonera,
        botonActivo
    );

}

function actualizarFlechasVencimientos(){

    const botonera =
        document.getElementById(
            "botoneraVencimientos"
        );

    const btnAnterior =
        document.getElementById(
            "btnVencimientosAnterior"
        );

    const btnSiguiente =
        document.getElementById(
            "btnVencimientosSiguiente"
        );


    actualizarFlechasNavegacion(
        botonera,
        btnAnterior,
        btnSiguiente
    );

}


function desplazarBotoneraVencimientos(
    direccion
){

    const botonera =
        document.getElementById(
            "botoneraVencimientos"
        );


    desplazarBotoneraNavegacion(
        botonera,
        direccion
    );

}

function conectarControlesProximosVencimientos(){

    const btnAlertas =
        document.getElementById(
            "btnVencimientosAlertas"
        );

    const btnHoy =
        document.getElementById(
            "btnVencimientosHoy"
        );

    const btnSemana =
        document.getElementById(
            "btnVencimientosSemana"
        );

    const btnRango =
        document.getElementById(
            "btnVencimientosRango"
        );

    const btnAplicarRango =
        document.getElementById(
            "btnAplicarRangoVencimientos"
        );

    const btnAnterior =
        document.getElementById(
            "btnVencimientosAnterior"
        );

    const btnSiguiente =
        document.getElementById(
            "btnVencimientosSiguiente"
        );

    const botonera =
        document.getElementById(
            "botoneraVencimientos"
        );

    const rango =
        document.getElementById(
            "rangoFechasVencimientos"
        );

    if(btnAlertas){

        btnAlertas.addEventListener(
            "click",
            function(){

                rango.style.display =
                    "none";

                marcarSegmentoVencimientosActivo(
                    btnAlertas
                );

                cargarProximosVencimientos(
                    "alertas"
                );

            }
        );

    }

    if(btnHoy){

        btnHoy.addEventListener(
            "click",
            function(){

                rango.style.display =
                    "none";

                marcarSegmentoVencimientosActivo(
                    btnHoy
                );

                cargarProximosVencimientos(
                    "hoy"
                );

            }
        );

    }

    if(btnSemana){

        btnSemana.addEventListener(
            "click",
            function(){

                rango.style.display =
                    "none";

                marcarSegmentoVencimientosActivo(
                    btnSemana
                );

                cargarProximosVencimientos(
                    "semana"
                );

            }
        );

    }

    if(btnRango){

        btnRango.addEventListener(
            "click",
            function(){

                rango.style.display =
                    "grid";

                marcarSegmentoVencimientosActivo(
                    btnRango
                );

                const fechaHasta =
                    document.getElementById(
                        "fechaHastaVencimientos"
                    );

                if(
                    fechaHasta &&
                    !fechaHasta.value
                ){

                    const hoy =
                        new Date();

                    const anio =
                        hoy.getFullYear();

                    const mes =
                        String(
                            hoy.getMonth() + 1
                        ).padStart(
                            2,
                            "0"
                        );

                    const dia =
                        String(
                            hoy.getDate()
                        ).padStart(
                            2,
                            "0"
                        );

                    fechaHasta.value =
                        `${anio}-${mes}-${dia}`;

                }

            }
        );

    }

    if(btnAplicarRango){

        btnAplicarRango.addEventListener(
            "click",
            function(){

                const fechaDesde =
                    document.getElementById(
                        "fechaDesdeVencimientos"
                    ).value;

                const fechaHasta =
                    document.getElementById(
                        "fechaHastaVencimientos"
                    ).value;

                if(
                    !fechaDesde ||
                    !fechaHasta
                ){

                    alert(
                        "Ingrese las fechas desde y hasta."
                    );

                    return;

                }

                cargarProximosVencimientos(
                    "rango",
                    fechaDesde,
                    fechaHasta
                );

            }
        );

    }

    if(btnAnterior){

        btnAnterior.addEventListener(
            "click",
            function(){

                desplazarBotoneraVencimientos(
                    -1
                );

            }
        );

    }

    if(btnSiguiente){

        btnSiguiente.addEventListener(
            "click",
            function(){

                desplazarBotoneraVencimientos(
                    1
                );

            }
        );

    }

    if(botonera){

        botonera.addEventListener(
            "scroll",
            actualizarFlechasVencimientos
        );

    }

    window.setTimeout(
        actualizarFlechasVencimientos,
        0
    );

}


// Constructor reutilizado al ingresar desde el sidebar y al volver de editar.
function construirEstructuraAlertas(){
    construirEstructuraProximosVencimientos();
    conectarControlesProximosVencimientos();
    const raiz = document.querySelector('#contenido-operativo .vencimientos-contenedor');
    if(raiz){
        raiz.dataset.ocVista = 'alertas';
        const cabecera = document.createElement('div');
        cabecera.className = 'caja-encabezado';
        const titulo = document.createElement('h2');
        titulo.textContent = 'Alertas';
        cabecera.appendChild(titulo);
        raiz.prepend(cabecera);
        configurarSonidoPersonalAlertas(cabecera);
    }
}

async function mostrarAlertasIndependientes(){
    const empresa = obtenerEmpresaActivaVencimientos();
    if(!empresa) return;
    construirEstructuraAlertas();
    await cargarProximosVencimientos('alertas');
}


async function mostrarProximosVencimientos(){

    const empresa =
        obtenerEmpresaActivaVencimientos();

    if(!empresa){

        alert(
            "No hay una empresa seleccionada."
        );

        return;

    }

    construirEstructuraProximosVencimientos();

    conectarControlesProximosVencimientos();

    marcarSegmentoVencimientosActivo(document.getElementById('btnVencimientosHoy'));
    await cargarProximosVencimientos(
        "hoy"
    );

}


async function cargarProximosVencimientos(
    periodo,
    fechaDesde = "",
    fechaHasta = ""
){

    const empresa =
        obtenerEmpresaActivaVencimientos();

    if(!empresa){
        return;
    }

    const estado =
        document.getElementById(
            "estadoProximosVencimientos"
        );

    const tabla =
        document.getElementById(
            "tablaProximosVencimientos"
        );

    if(
        !estado ||
        !tabla
    ){
        return;
    }

    estado.style.display =
        "block";

    estado.textContent = periodo === 'alertas'
        ? "Cargando alertas..." : "Cargando vencimientos...";

    tabla.innerHTML = "";

    window.__ocSolicitudVencimientos = (window.__ocSolicitudVencimientos || 0) + 1;
    const solicitud = window.__ocSolicitudVencimientos;
    let url = periodo === 'alertas'
        ? `/alertas/listado/?empresa=` + encodeURIComponent(empresa)
        : `/proximos-vencimientos/?empresa=` + encodeURIComponent(empresa) +
          `&periodo=` + encodeURIComponent(periodo);

    if(periodo === "rango"){

        url +=
            `&fecha_desde=` +
            encodeURIComponent(fechaDesde) +
            `&fecha_hasta=` +
            encodeURIComponent(fechaHasta);

    }

    try{

        const respuesta =
            await fetch(url);

        const datos =
            await respuesta.json();

        if(solicitud !== window.__ocSolicitudVencimientos || !tabla.isConnected) return;

        if(
            !respuesta.ok ||
            !datos.ok
        ){

            estado.textContent =
                datos.mensaje ||
                "No se pudieron cargar los vencimientos.";

            return;

        }

        mostrarTablaProximosVencimientos(
            datos.movimientos,
            periodo === 'alertas',
            (datos.licencias_nomina || []).concat(datos.alertas_instrumentos || [])
        );
        if(periodo === 'alertas'){
            construirPanelAlertasSegmentado(datos);
        }

    }catch(error){
        if(solicitud !== window.__ocSolicitudVencimientos || !tabla.isConnected) return;

        console.error(
            "Error cargando próximos vencimientos:",
            error
        );

        estado.textContent =
            "No se pudo conectar con Próximos vencimientos.";

    }

}

/**
 * Abre un Movimiento desde Próximos Vencimientos
 * conservando el contexto de navegación actual.
 *
 * El estado financiero no se conserva localmente:
 * cuando se regrese a Vencimientos se volverá a
 * consultar el backend.
 */
async function editarMovimientoDesdeVencimientos(
    movimientoId
){

    const botonActivo =
        document.querySelector(
            ".vencimientos-segmento.activo"
        );


    let periodo =
        "alertas";


    if(botonActivo){

        const periodosPorBoton = {
            btnVencimientosAlertas:
                "alertas",

            btnVencimientosHoy:
                "hoy",

            btnVencimientosSemana:
                "semana",

            btnVencimientosRango:
                "rango"
        };


        periodo =
            periodosPorBoton[
                botonActivo.id
            ] || "alertas";

    }


    const fechaDesde =
        document.getElementById(
            "fechaDesdeVencimientos"
        );


    const fechaHasta =
        document.getElementById(
            "fechaHastaVencimientos"
        );


    const btnToggleVencidos =
        document.getElementById(
            "btnToggleVencidos"
        );


    /*
     * Solamente guardamos contexto de navegación.
     *
     * Los Movimientos y saldos NO se guardan porque
     * deberán recalcularse desde backend al regresar.
     */
    window.contextoRetornoProximosVencimientos = {

        periodo:
            periodo,

        fechaDesde:
            fechaDesde?.value || "",

        fechaHasta:
            fechaHasta?.value || "",

        vencidosExpandido:
            btnToggleVencidos
                ? (
                    btnToggleVencidos.getAttribute(
                        "aria-expanded"
                    ) === "true"
                )
                : true

    };


    if(
        typeof abrirCargaSimpleEdicionMovimiento !==
        "function"
    ){

        console.error(
            "No está disponible la apertura de Carga Simple en modo edición."
        );

        alert(
            "No se pudo abrir el Movimiento."
        );

        return;

    }


    await abrirCargaSimpleEdicionMovimiento(
        movimientoId
    );

}

function mostrarTablaProximosVencimientos(
    movimientos,
    esAlertas = false,
    licenciasNomina = []
){

    const estado =
        document.getElementById(
            "estadoProximosVencimientos"
        );


    const tabla =
        document.getElementById(
            "tablaProximosVencimientos"
        );


    if(
        !estado ||
        !tabla
    ){

        return;

    }


    if(
        !Array.isArray(movimientos) ||
        movimientos.length === 0
    ){

        estado.style.display =
            (esAlertas && licenciasNomina.length) ? "none" : "block";

        estado.textContent = esAlertas
            ? "No hay alertas que requieran atención."
            : "No hay vencimientos pendientes para el período seleccionado.";


        tabla.innerHTML =
            "";


        return;

    }


    estado.style.display =
        "none";


    const proximos =
        movimientos.filter(
            function(movimiento){

                return (
                    movimiento.estado_vencimiento ===
                        "Hoy" ||
                    movimiento.estado_vencimiento ===
                        "Futuro"
                );

            }
        );


    const vencidos =
        movimientos.filter(
            function(movimiento){

                return (
                    movimiento.estado_vencimiento ===
                    "Vencido"
                );

            }
        );


    const calcularSubtotal =
        function(lista){

            return lista.reduce(
                function(total, movimiento){

                    const importe =
                        Number(
                            movimiento.saldo_pendiente
                        );


                    if(
                        Number.isNaN(importe)
                    ){

                        return total;

                    }


                    return total + importe;

                },
                0
            );

        };


    const construirFilas =
        function(lista){

            let filas =
                "";


            lista.forEach(
                function(movimiento){

                    const comprobante =
                        [
                            movimiento.tipo_comprobante,
                            movimiento.numero_comprobante
                        ]
                        .filter(Boolean)
                        .join(" ");


                    const modalidad =
                        movimiento.modalidad_pago ===
                        "DebitoAutomatico"
                            ? "Débito automático"
                            : (
                                movimiento.modalidad_pago ||
                                "Manual"
                            );


                    filas += `

                        <tr>

                            <td>
                                ${formatearFechaVencimiento(
                                    movimiento.fecha_vencimiento
                                )}
                            </td>

                            <td>
                                ${movimiento.proveedor || "-"}
                            </td>

                            <td>
                                ${comprobante || "-"}
                            </td>

                            <td class="importe">

                                ${formatearImporteVencimiento(
                                    movimiento.total
                                )}

                            </td>

                            <td class="importe">

                                ${formatearImporteVencimiento(
                                    movimiento.total_aplicado
                                )}

                            </td>

                            <td class="importe pendiente">

                                ${formatearImporteVencimiento(
                                    movimiento.saldo_pendiente
                                )}

                            </td>

                            <td class="modalidad">
                                ${modalidad}
                            </td>

                            <td class="vencimientos-col-acciones">

                                <button
                                    type="button"
                                    class="vencimientos-btn-editar"
                                    data-movimiento-id="${movimiento.id}"
                                    title="Editar movimiento"
                                    aria-label="Editar movimiento"
                                >

                                    <svg
                                        viewBox="0 0 24 24"
                                        aria-hidden="true"
                                    >
                                        <path
                                            d="
                                                M12 20
                                                h9
                                                M16.5 3.5
                                                a2.12 2.12 0 0 1 3 3
                                                L8 18
                                                l-4 1
                                                l1-4
                                                Z
                                            "
                                        ></path>
                                    </svg>

                                </button>

                            </td>

                        </tr>

                    `;

                }
            );


            return filas;

        };


    const construirTabla =
        function(lista){

            if(lista.length === 0){

                return `

                    <div class="vencimientos-sin-items">
                        Sin movimientos en este grupo.
                    </div>

                `;

            }


            return `

                <div class="vencimientos-tabla-contenedor">

                    <table class="vencimientos-tabla">

                        <thead>

                            <tr>

                                <th class="col-vencimiento">
                                    Vencimiento
                                </th>

                                <th class="col-proveedor">
                                    Proveedor
                                </th>

                                <th class="col-comprobante">
                                    Comprobante
                                </th>

                                <th class="col-total">
                                    Total
                                </th>

                                <th class="col-aplicado">
                                    Aplicado
                                </th>

                                <th class="col-pendiente">
                                    Pendiente
                                </th>

                                <th class="col-modalidad">
                                    Modalidad
                                </th>

                                <th class="vencimientos-col-acciones"></th>

                            </tr>

                        </thead>

                        <tbody>
                            ${construirFilas(lista)}
                        </tbody>

                    </table>

                </div>

            `;

        };


    const subtotalProximos =
        calcularSubtotal(
            proximos
        );


    const subtotalVencidos =
        calcularSubtotal(
            vencidos
        );


    const totalGeneral =
        subtotalProximos +
        subtotalVencidos;


    tabla.innerHTML = `

        <section
            class="vencimientos-grupo vencimientos-grupo-proximos"
        >

            <div class="vencimientos-grupo-cabecera">

                <div class="vencimientos-grupo-identidad">

                    <span
                        class="vencimientos-grupo-icono"
                        aria-hidden="true"
                    >
                        ◫
                    </span>

                    <span class="vencimientos-grupo-titulo">
                        Próximos a vencer
                    </span>

                    <span class="vencimientos-contador">
                        ${proximos.length}
                    </span>

                </div>


                <div class="vencimientos-subtotal">

                    <span>
                        Subtotal próximos
                    </span>

                    <strong>

                        ${formatearImporteVencimiento(
                            subtotalProximos
                        )}

                    </strong>

                </div>

            </div>


            ${construirTabla(proximos)}

        </section>


        <section
            class="vencimientos-grupo vencimientos-grupo-vencidos"
        >

            <button
                type="button"
                class="vencimientos-grupo-cabecera vencimientos-grupo-toggle"
                id="btnToggleVencidos"
                aria-expanded="true"
            >

                <span class="vencimientos-grupo-identidad">

                    <span
                        class="vencimientos-grupo-icono"
                        aria-hidden="true"
                    >
                        ◴
                    </span>

                    <span class="vencimientos-grupo-titulo">
                        Vencidos
                    </span>

                    <span class="vencimientos-contador">
                        ${vencidos.length}
                    </span>

                </span>


                <span class="vencimientos-subtotal">

                    <span>
                        Subtotal vencidos
                    </span>

                    <strong>

                        ${formatearImporteVencimiento(
                            subtotalVencidos
                        )}

                    </strong>

                    <span
                        class="vencimientos-chevron"
                        id="iconoToggleVencidos"
                        aria-hidden="true"
                    >
                       ⌃
                    </span>

                </span>

            </button>


            <div id="contenidoVencidos">

                ${construirTabla(vencidos)}

            </div>

        </section>


        <div class="vencimientos-total-general">

            <span class="vencimientos-total-etiqueta">

                <span
                    class="vencimientos-total-icono"
                    aria-hidden="true"
                >
                    ◎
                </span>

                Total general

            </span>

            <strong>

                ${formatearImporteVencimiento(
                    totalGeneral
                )}

            </strong>

        </div>

    `;


    const btnToggleVencidos =
        document.getElementById(
            "btnToggleVencidos"
        );


    const contenidoVencidos =
        document.getElementById(
            "contenidoVencidos"
        );


    const iconoToggleVencidos =
        document.getElementById(
            "iconoToggleVencidos"
        );


    if(
        btnToggleVencidos &&
        contenidoVencidos
    ){

        btnToggleVencidos.addEventListener(
            "click",
            function(){

                const expandido =
                    btnToggleVencidos.getAttribute(
                        "aria-expanded"
                    ) === "true";


                btnToggleVencidos.setAttribute(
                    "aria-expanded",
                    String(!expandido)
                );


                contenidoVencidos.classList.toggle(
                    "oculto",
                    expandido
                );


                if(iconoToggleVencidos){

                    iconoToggleVencidos.textContent =
                        expandido
                            ? "⌄"
                            : "⌃";

                }

            }
        );

    }


    const botonesEditar =
        tabla.querySelectorAll(
            ".vencimientos-btn-editar"
        );


    botonesEditar.forEach(
        function(boton){

            boton.addEventListener(
                "click",
                function(){

                    const movimientoId =
                        boton.dataset.movimientoId;


                    if(!movimientoId){

                        return;

                    }


                    editarMovimientoDesdeVencimientos(
                        movimientoId
                    );

                }
            );

        }
    );

}


/* Segmentacion SOLO visual: datos ya filtrados por el servidor.
 * No cambia destinatarios, fechas, permisos ni reglas de cada fuente.
 * La tabla de compromisos existente se mueve sin recrear sus eventos.
 */
function construirPanelAlertasSegmentado(datos) {
    const contenedor = document.getElementById('tablaProximosVencimientos');
    const raiz = contenedor?.closest('[data-oc-vista="alertas"]');
    if (!contenedor || !raiz) return;

    const movimientos = Array.isArray(datos.movimientos) ? datos.movimientos : [];
    const instrumentos = Array.isArray(datos.alertas_instrumentos) ? datos.alertas_instrumentos : [];
    const documentos = Array.isArray(datos.licencias_nomina) ? datos.licencias_nomina : [];

    // Retenemos los nodos y sus listeners (ej. editar Movimiento).
    const tablaCompromisos = document.createDocumentFragment();
    while (contenedor.firstChild) tablaCompromisos.appendChild(contenedor.firstChild);

    const capa = document.createElement('div');
    capa.className = 'oc-alertas-segmentadas';
    const introduccion = document.createElement('p');
    introduccion.className = 'oc-alertas-introduccion';
    introduccion.textContent = 'Avisos que podés consultar según tus permisos actuales.';
    capa.appendChild(introduccion);

    const navegacion = document.createElement('div');
    navegacion.className = 'oc-alertas-categorias';
    navegacion.setAttribute('role', 'tablist');
    navegacion.setAttribute('aria-label', 'Categorías de alertas');
    capa.appendChild(navegacion);

    const secciones = [
        {clave: 'compromisos', nombre: 'Compromisos', cantidad: movimientos.length,
         explicacion: 'Compromisos económicos con saldo pendiente.'},
        {clave: 'instrumentos', nombre: 'Cheques y e-Cheqs', cantidad: instrumentos.length,
         explicacion: 'Cartera física, cartera electrónica e instrumentos propios emitidos.'},
        {clave: 'documentacion', nombre: 'Documentación', cantidad: documentos.length,
         explicacion: 'Licencias y documentación con vencimiento.'}
    ];
    const botones = [];
    const paneles = [];

    for (const segmento of secciones) {
        const boton = document.createElement('button');
        boton.type = 'button';
        boton.className = 'oc-alertas-categoria';
        boton.id = 'oc-alertas-tab-' + segmento.clave;
        boton.setAttribute('role', 'tab');
        boton.setAttribute('aria-controls', 'oc-alertas-panel-' + segmento.clave);
        const nombre = document.createElement('span');
        nombre.textContent = segmento.nombre;
        const cantidad = document.createElement('span');
        cantidad.className = 'oc-alertas-cantidad';
        cantidad.textContent = String(segmento.cantidad);
        boton.append(nombre, cantidad);
        navegacion.appendChild(boton);
        botones.push(boton);

        const panel = document.createElement('section');
        panel.className = 'oc-alertas-panel';
        panel.id = 'oc-alertas-panel-' + segmento.clave;
        panel.setAttribute('role', 'tabpanel');
        panel.setAttribute('aria-labelledby', boton.id);
        panel.tabIndex = 0;
        const descripcion = document.createElement('p');
        descripcion.className = 'oc-alertas-descripcion';
        descripcion.textContent = segmento.explicacion;
        panel.appendChild(descripcion);
        capa.appendChild(panel);
        paneles.push(panel);
    }

    function vacio(panel, mensaje) {
        const parrafo = document.createElement('p');
        parrafo.className = 'oc-alertas-vacio';
        parrafo.textContent = mensaje;
        panel.appendChild(parrafo);
    }

    if (movimientos.length) {
        paneles[0].appendChild(tablaCompromisos);
    } else {
        vacio(paneles[0], 'No hay compromisos que requieran atención.');
    }
    if (instrumentos.length) {
        mostrarAlertasInstrumentos(instrumentos, paneles[1]);
    } else {
        vacio(paneles[1], 'No hay cheques ni e-Cheqs que requieran atención.');
    }
    if (documentos.length) {
        mostrarAlertasLicenciasNomina(documentos, paneles[2]);
    } else {
        vacio(paneles[2], 'No hay vencimientos de documentación que requieran atención.');
    }
    const pendientes = document.createElement('p');
    pendientes.className = 'oc-alertas-fuentes-futuras';
    pendientes.textContent = 'Habilitaciones y renovaciones de autoridades: fuentes todavía no operativas; no generan avisos.';
    paneles[2].appendChild(pendientes);

    function activar(indice, moverFoco = false) {
        botones.forEach((boton, i) => {
            const elegido = i === indice;
            boton.setAttribute('aria-selected', String(elegido));
            boton.tabIndex = elegido ? 0 : -1;
            paneles[i].hidden = !elegido;
        });
        if (moverFoco) botones[indice].focus();
    }
    botones.forEach((boton, indice) => {
        boton.addEventListener('click', () => activar(indice));
        boton.addEventListener('keydown', evento => {
            let siguiente = indice;
            if (evento.key === 'ArrowRight') siguiente = (indice + 1) % botones.length;
            else if (evento.key === 'ArrowLeft') siguiente = (indice + botones.length - 1) % botones.length;
            else if (evento.key === 'Home') siguiente = 0;
            else if (evento.key === 'End') siguiente = botones.length - 1;
            else return;
            evento.preventDefault();
            activar(siguiente, true);
        });
    });
    const inicial = Math.max(0, secciones.findIndex(s => s.cantidad > 0));
    activar(inicial);
    contenedor.appendChild(capa);
    const estado = document.getElementById('estadoProximosVencimientos');
    if (estado) estado.style.display = 'none';
}

/* Alertas de Cartera y propios: lectura informativa, sin acciones financieras. */
function mostrarAlertasInstrumentos(avisos, contenedorDestino = null) {
    if (!Array.isArray(avisos) || !avisos.length) return;
    const contenedor = contenedorDestino || document.getElementById('tablaProximosVencimientos');
    if (!contenedor) return;
    const grupos = [
        ['cartera_fisica', 'Cheques físicos recibidos · Cartera'],
        ['cartera_electronica', 'e-Cheqs recibidos · Cartera electrónica'],
        ['propio_fisico', 'Cheques propios emitidos'],
        ['propio_electronico', 'e-Cheqs propios emitidos']
    ];
    const seccion = document.createElement('section');
    seccion.className = 'nm-licencias-pendientes';
    const titulo = document.createElement('h3');
    titulo.textContent = 'Cheques y e-Cheqs que requieren atención';
    seccion.appendChild(titulo);
    grupos.forEach(([clave, nombre]) => {
        const items = avisos.filter(a => a.grupo === clave);
        if (!items.length) return;
        const subtitulo = document.createElement('h4');
        subtitulo.textContent = nombre;
        seccion.appendChild(subtitulo);
        items.forEach(a => {
            const fila = document.createElement('p');
            const proxima = a.estado_alerta === 'Vencido' ? 'Vencido' :
                a.estado_alerta === 'En atencion' ? 'En atención' :
                a.estado_alerta === 'Hoy' ? 'Hoy' : 'Próximo';
            fila.textContent = 'N.º ' + String(a.numero || '') +
                ' · ' + proxima + ' · acreditación ' +
                formatearFechaVencimiento(String(a.fecha_acreditacion || '')) +
                (clave.startsWith('cartera_') ?
                  ' · límite ' + formatearFechaVencimiento(String(a.fecha_limite || '')) : '');
            seccion.appendChild(fila);
        });
    });
    contenedor.appendChild(seccion);
}

/* Alertas laborales: sin mezclar documentos con importes financieros. */
function mostrarAlertasLicenciasNomina(alertas, contenedorDestino = null) {
    if (!Array.isArray(alertas) || !alertas.length) return;
    const contenedor = contenedorDestino || document.getElementById('tablaProximosVencimientos');
    if (!contenedor) return;
    const seccion = document.createElement('section');
    seccion.className = 'nm-licencias-pendientes';
    const titulo = document.createElement('h3');
    titulo.textContent = 'Licencias de conducir que requieren atención';
    seccion.appendChild(titulo);
    for (const dato of alertas) {
        const linea = document.createElement('p');
        linea.textContent = String(dato.nombre || '') + ' · vence ' +
            formatearFechaVencimiento(String(dato.vence || ''));
        seccion.appendChild(linea);
    }
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = 'Abrir Nómina de Empleados';
    btn.className = 'nm-abrir-desde-alertas';
    btn.addEventListener('click', () => {
        if (typeof mostrarSubmenu === 'function') mostrarSubmenu('herramientas');
        document.getElementById('btnNominaEmpleados')?.click();
    });
    seccion.appendChild(btn);
    contenedor.appendChild(seccion);
}

// Preferencia individual: el gestor asigna avisos; el receptor controla su audio.
async function configurarSonidoPersonalAlertas(cabecera){
    const empresa = obtenerEmpresaActivaVencimientos();
    if(!empresa || !cabecera) return;
    const etiqueta = document.createElement('label');
    etiqueta.className = 'oc-alertas-sonido-opcion';
    const casilla = document.createElement('input');
    casilla.type = 'checkbox';
    casilla.disabled = true;
    casilla.checked = true; // Preferencia inicial del servidor, hasta que llegue GET.
    etiqueta.append(casilla, document.createTextNode(' Sonido de alertas'));
    const estado = document.createElement('span');
    estado.className = 'oc-alertas-sonido-estado';
    estado.setAttribute('role', 'status');
    cabecera.append(etiqueta, estado);
    const url = '/alertas/sonido/?empresa=' + encodeURIComponent(empresa);
    try {
        const respuesta = await fetch(url, {credentials:'same-origin', cache:'no-store'});
        if(!respuesta.ok) throw new Error('No autorizado.');
        const datos = await respuesta.json();
        if(datos.ok !== true || typeof datos.habilitado !== 'boolean') throw new Error('Respuesta inválida.');
        if(!casilla.isConnected) return;
        casilla.checked = datos.habilitado;
        casilla.disabled = false;
        if(typeof sonidoLlamadorPermitido !== 'undefined') sonidoLlamadorPermitido = datos.habilitado;
    } catch (_) {
        if(casilla.isConnected) estado.textContent = 'No se pudo consultar el sonido.';
        return;
    }
    casilla.addEventListener('change', async () => {
        const anterior = !casilla.checked;
        const deseado = casilla.checked;
        casilla.disabled = true;
        estado.textContent = 'Guardando…';
        const cookieCsrf = document.cookie.split('; ').find(c => c.startsWith('csrftoken='));
        const token = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value ||
            (cookieCsrf ? decodeURIComponent(cookieCsrf.slice('csrftoken='.length)) : '');
        try {
            if(!token) throw new Error('No se encontró token CSRF.');
            const respuesta = await fetch(url, {
                method:'POST', credentials:'same-origin',
                headers:{'X-CSRFToken':token, 'Content-Type':'application/x-www-form-urlencoded'},
                body:'habilitado=' + (deseado ? '1' : '0') + '&empresa=' + encodeURIComponent(empresa)
            });
            if(!respuesta.ok) throw new Error('No autorizado.');
            const datos = await respuesta.json();
            if(datos.ok !== true || datos.habilitado !== deseado) throw new Error('Respuesta inválida.');
            if(!casilla.isConnected) return;
            if(typeof sonidoLlamadorPermitido !== 'undefined') sonidoLlamadorPermitido = deseado;
            estado.textContent = deseado ? 'Sonido activado' : 'Sonido silenciado';
        } catch (_) {
            if(casilla.isConnected) {
                casilla.checked = anterior;
                estado.textContent = 'No se pudo guardar el sonido.';
            }
        } finally {
            if(casilla.isConnected) casilla.disabled = false;
        }
    });
}
