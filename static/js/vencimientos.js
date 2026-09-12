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

            <h2 class="vencimientos-titulo">
                Próximos vencimientos
            </h2>

            <div class="vencimientos-botonera">

                <button
                    type="button"
                    class="module-card"
                    id="btnVencimientosHoy"
                >
                    Hoy
                </button>

                <button
                    type="button"
                    class="module-card"
                    id="btnVencimientosSemana"
                >
                    Esta semana
                </button>

                <button
                    type="button"
                    class="module-card"
                    id="btnVencimientosRango"
                >
                    Rango de fechas
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


function conectarControlesProximosVencimientos(){

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

    const rango =
        document.getElementById(
            "rangoFechasVencimientos"
        );

    if(btnHoy){

        btnHoy.addEventListener(
            "click",
            function(){

                rango.style.display =
                    "none";

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

    let filas = "";

    movimientos.forEach(
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
                    : "Manual";

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

    tabla.innerHTML = `
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
                    ${filas}
                </tbody>

            </table>

        </div>
    `;

}