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
                "btnProximosVencimientos"
            );

        if(!boton){
            return;
        }

        boton.addEventListener(
            "click",
            function(){

                mostrarProximosVencimientos();

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

    const botones =
        document.querySelectorAll(
            ".vencimientos-segmento"
        );

    botones.forEach(
        function(boton){

            boton.classList.remove(
                "activo"
            );

        }
    );

    if(botonActivo){

        botonActivo.classList.add(
            "activo"
        );

    }

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

    if(
        !botonera ||
        !btnAnterior ||
        !btnSiguiente
    ){
        return;
    }

    const botones =
        botonera.querySelectorAll(
            ".vencimientos-segmento"
        );

    const necesitaNavegacion =
        botones.length > 4 ||
        botonera.scrollWidth >
            botonera.clientWidth + 2;

    btnAnterior.classList.toggle(
        "visible",
        necesitaNavegacion
    );

    btnSiguiente.classList.toggle(
        "visible",
        necesitaNavegacion
    );

    if(!necesitaNavegacion){
        return;
    }

    const maximoScroll =
        botonera.scrollWidth -
        botonera.clientWidth;

    btnAnterior.disabled =
        botonera.scrollLeft <= 2;

    btnSiguiente.disabled =
        botonera.scrollLeft >=
        maximoScroll - 2;

}


function desplazarBotoneraVencimientos(
    direccion
){

    const botonera =
        document.getElementById(
            "botoneraVencimientos"
        );

    if(!botonera){
        return;
    }

    const desplazamiento =
        Math.max(
            180,
            botonera.clientWidth * 0.45
        );

    botonera.scrollBy({
        left:
            direccion *
            desplazamiento,
        behavior: "smooth"
    });

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

    await cargarProximosVencimientos(
        "alertas"
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

    estado.textContent =
        "Cargando vencimientos...";

    tabla.innerHTML = "";

    let url =
        `/proximos-vencimientos/?empresa=` +
        encodeURIComponent(empresa) +
        `&periodo=` +
        encodeURIComponent(periodo);

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
            datos.movimientos
        );

    }catch(error){

        console.error(
            "Error cargando próximos vencimientos:",
            error
        );

        estado.textContent =
            "No se pudo conectar con Próximos vencimientos.";

    }

}


function mostrarTablaProximosVencimientos(
    movimientos
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
            "block";

        estado.textContent =
            "No hay vencimientos pendientes para el período seleccionado.";

        tabla.innerHTML = "";

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

            let filas = "";

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

}