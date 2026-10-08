async function iniciarEventosCargaSimple(){

    const selectTipoGasto =
        document.getElementById(
            "tipoGastoRegistro"
        );

    const selectProveedor =
        document.getElementById(
            "proveedorRegistro"
        );

    const selectCentroOperativo =
        document.getElementById(
            "centroOperativoRegistro"
        );

    const selectRecursoOperativo =
        document.getElementById(
            "recursoOperativoRegistro"
        );

    const botonAgregarTipoGasto =
        document.getElementById(
            "btnAgregarTipoGastoRegistro"
        );

    const botonAgregarProveedor =
        document.getElementById(
            "btnAgregarProveedorRegistro"
        );

    const botonAgregarRecurso =
        document.getElementById(
            "btnAgregarRecursoOperativoRegistro"
        );

    const empresaActiva =
        document.getElementById(
            "empresaActiva"
        );

    const selectOrigenCheque =
        document.getElementById(
            "origenCheque"
        );


    const selectTipoCheque =
        document.getElementById(
            "tipoCheque"
        );


    if(
        !selectTipoGasto ||
        !selectProveedor ||
        !selectCentroOperativo ||
        !selectRecursoOperativo ||
        !empresaActiva
    ){

        console.error(
            "No se encontraron todos los controles de Carga Simple."
        );

        return;

    }


    /*
     * Proveedor depende de Tipo de Gasto.
     */
    if(!selectTipoGasto.value){

        selectProveedor.disabled = true;

        selectProveedor.innerHTML = `
            <option value="">
                Seleccione primero un tipo de gasto...
            </option>
        `;


        if(botonAgregarProveedor){

            botonAgregarProveedor.disabled =
                true;

        }

    }


    /*
     * Recurso Operativo depende de Centro Operativo.
     */
    if(!selectCentroOperativo.value){

        selectRecursoOperativo.disabled =
            true;

        selectRecursoOperativo.innerHTML = `
            <option value="">
                Seleccione primero un Centro Operativo...
            </option>
        `;


        if(botonAgregarRecurso){

            botonAgregarRecurso.disabled =
                true;

        }

    }


    if(
        botonAgregarTipoGasto &&
        !botonAgregarTipoGasto.dataset.eventoAsignado
    ){

        botonAgregarTipoGasto.addEventListener(

            "click",

            function(){

                mostrarABMTiposGasto(
                    "registro"
                );

            }

        );


        botonAgregarTipoGasto.dataset.eventoAsignado =
            "true";

    }


    if(
        botonAgregarProveedor &&
        !botonAgregarProveedor.dataset.eventoAsignado
    ){

        botonAgregarProveedor.addEventListener(

            "click",

            function(){

                if(!selectTipoGasto.value){

                    return;

                }


                mostrarABMProveedores(
                    "registro"
                );

            }

        );


        botonAgregarProveedor.dataset.eventoAsignado =
            "true";

    }


    if(
        botonAgregarRecurso &&
        !botonAgregarRecurso.dataset.eventoAsignado
    ){

        botonAgregarRecurso.addEventListener(

            "click",

            function(){

                if(!selectCentroOperativo.value){

                    return;

                }


                mostrarABMRecursosOperativos(
                    "registro"
                );

            }

        );


        botonAgregarRecurso.dataset.eventoAsignado =
            "true";

    }


    if(
        !selectTipoGasto.dataset.eventoProveedorAsignado
    ){

        selectTipoGasto.addEventListener(

            "change",

            actualizarProveedoresPorTipoGasto

        );


        selectTipoGasto.dataset.eventoProveedorAsignado =
            "true";

    }


    if(
        !selectCentroOperativo.dataset.eventoRecursoAsignado
    ){

        selectCentroOperativo.addEventListener(

            "change",

            actualizarRecursosPorCentroOperativo

        );


        selectCentroOperativo.dataset.eventoRecursoAsignado =
            "true";

    }

    /*
     * Cheques:
     * Banco / Cuenta Bancaria depende del origen.
     */
    if(
        selectOrigenCheque &&
        !selectOrigenCheque.dataset.eventoChequeAsignado
    ){

        selectOrigenCheque.addEventListener(

            "change",

            cambiarOrigenCheque

        );


        selectOrigenCheque.dataset.eventoChequeAsignado =
            "true";

    }


    /*
     * Cheques:
     * Las fechas dependen de si es común o diferido.
     */
    if(
        selectTipoCheque &&
        !selectTipoCheque.dataset.eventoChequeAsignado
    ){

        selectTipoCheque.addEventListener(

            "change",

            cambiarTipoCheque

        );


        selectTipoCheque.dataset.eventoChequeAsignado =
            "true";

    }

    const empresa =
        empresaActiva.value;


    if(!empresa){

        return;

    }


    try{

        const respuestas =
            await Promise.all([

                fetch(
                    `/tipos-gasto/?empresa=${encodeURIComponent(empresa)}`
                ),

                fetch(
                    `/listar-proveedores/?empresa=${encodeURIComponent(empresa)}`
                ),

                fetch(
                    `/recursos-operativos/?empresa=${encodeURIComponent(empresa)}`
                )

            ]);


        const respuestaTipos =
            respuestas[0];

        const respuestaProveedores =
            respuestas[1];

        const respuestaRecursos =
            respuestas[2];


        const resultadoTipos =
            await respuestaTipos.json();

        const resultadoProveedores =
            await respuestaProveedores.json();

        const resultadoRecursos =
            await respuestaRecursos.json();


        if(
            !respuestaTipos.ok ||
            !resultadoTipos.ok
        ){

            console.error(
                resultadoTipos.mensaje ||
                "No se pudieron cargar los tipos de gasto."
            );

            return;

        }


        if(
            !respuestaProveedores.ok ||
            !Array.isArray(
                resultadoProveedores.proveedores
            )
        ){

            console.error(
                "No se pudieron cargar los proveedores."
            );

            return;

        }


        if(
            !respuestaRecursos.ok ||
            !resultadoRecursos.ok ||
            !Array.isArray(
                resultadoRecursos.recursos
            )
        ){

            console.error(
                resultadoRecursos.mensaje ||
                "No se pudieron cargar los recursos operativos."
            );

            return;

        }


        proveedoresCargaSimple =
            resultadoProveedores.proveedores;


        recursosCargaSimple =
            resultadoRecursos.recursos;


        selectTipoGasto.innerHTML = `
            <option value=""></option>
        `;


        const tiposGasto =
            Array.isArray(
                resultadoTipos.tipos_gasto
            )
                ? resultadoTipos.tipos_gasto
                : [];


        tiposGasto.forEach(

            function(tipoGasto){

                const opcion =
                    document.createElement(
                        "option"
                    );


                opcion.value =
                    String(
                        tipoGasto.id
                    );


                opcion.textContent =
                    tipoGasto.nombre;


                opcion.dataset.proveedores =
                    JSON.stringify(

                        Array.isArray(
                            tipoGasto.proveedores
                        )
                            ? tipoGasto.proveedores
                                .map(function(proveedor){

                                    if(
                                        proveedor &&
                                        typeof proveedor === "object"
                                    ){

                                        return String(
                                            proveedor.id ??
                                            proveedor.proveedor_id ??
                                            ""
                                        );

                                    }


                                    return String(
                                        proveedor
                                    );

                                })
                                .filter(function(id){

                                    return id !== "";

                                })

                            : []

                    );


                selectTipoGasto.appendChild(
                    opcion
                );

            }

        );


        if(ultimoTipoGastoCreado){

            actualizarTipoGastoDelRegistro();

        }


        /*
         * Si Carga Simple fue restaurada desde un ABM,
         * respetamos el Centro Operativo que ya tenía.
         */
        actualizarRecursosPorCentroOperativo();


    }catch(error){

        console.error(
            "Error cargando datos de Carga Simple:",
            error
        );

    }



}

function actualizarProveedoresPorTipoGasto(){

    const selectTipoGasto =
        document.getElementById(
            "tipoGastoRegistro"
        );

    const selectProveedor =
        document.getElementById(
            "proveedorRegistro"
        );

    const botonAgregarProveedor =
        document.getElementById(
            "btnAgregarProveedorRegistro"
        );


    if(
        !selectTipoGasto ||
        !selectProveedor
    ){

        return;

    }


    selectProveedor.value = "";

    selectProveedor.innerHTML = "";


    if(!selectTipoGasto.value){

        const opcion =
            document.createElement(
                "option"
            );


        opcion.value = "";

        opcion.textContent =
            "Seleccione primero un tipo de gasto...";


        selectProveedor.appendChild(
            opcion
        );


        selectProveedor.disabled = true;


        if(botonAgregarProveedor){

            botonAgregarProveedor.disabled = true;

        }


        return;

    }


    selectProveedor.disabled = false;


    if(botonAgregarProveedor){

        botonAgregarProveedor.disabled = false;

    }


    const opcionInicial =
        document.createElement(
            "option"
        );


    opcionInicial.value = "";

    opcionInicial.textContent =
        "Seleccione...";


    selectProveedor.appendChild(
        opcionInicial
    );


    const opcionTipoGasto =
        selectTipoGasto.options[
            selectTipoGasto.selectedIndex
        ];


    let proveedoresRelacionados = [];


    try{

        proveedoresRelacionados =
            JSON.parse(
                opcionTipoGasto.dataset.proveedores ||
                "[]"
            );

    }catch(error){

        console.error(
            "No se pudieron interpretar los proveedores asociados:",
            error
        );

    }


    proveedoresCargaSimple

        .filter(

            function(proveedor){

                return proveedoresRelacionados.includes(
                    String(
                        proveedor.id
                    )
                );

            }

        )

        .forEach(

            function(proveedor){

                const opcion =
                    document.createElement(
                        "option"
                    );


                opcion.value =
                    String(
                        proveedor.id
                    );


                opcion.textContent =
                    proveedor.cuit

                        ? `${proveedor.razon_social} · ${proveedor.cuit}`

                        : proveedor.razon_social;


                selectProveedor.appendChild(
                    opcion
                );

            }

        );

}

function actualizarRecursosPorCentroOperativo(){

    const selectCentro =
        document.getElementById(
            "centroOperativoRegistro"
        );

    const selectRecurso =
        document.getElementById(
            "recursoOperativoRegistro"
        );

    const botonAgregarRecurso =
        document.getElementById(
            "btnAgregarRecursoOperativoRegistro"
        );


    if(
        !selectCentro ||
        !selectRecurso
    ){

        return;

    }


    const valorAnterior =
        selectRecurso.value;


    selectRecurso.innerHTML =
        "";


    if(!selectCentro.value){

        const opcion =
            document.createElement(
                "option"
            );


        opcion.value =
            "";

        opcion.textContent =
            "Seleccione primero un Centro Operativo...";


        selectRecurso.appendChild(
            opcion
        );


        selectRecurso.disabled =
            true;


        if(botonAgregarRecurso){

            botonAgregarRecurso.disabled =
                true;

        }


        return;

    }


    selectRecurso.disabled =
        false;


    if(botonAgregarRecurso){

        botonAgregarRecurso.disabled =
            false;

    }


    const opcionInicial =
        document.createElement(
            "option"
        );


    opcionInicial.value =
        "";

    opcionInicial.textContent =
        "Seleccione...";


    selectRecurso.appendChild(
        opcionInicial
    );


    const centroSeleccionado =
        String(
            selectCentro.value
        );


    recursosCargaSimple

        .filter(

            function(recurso){

                const centrosRecurso =
                    Array.isArray(
                        recurso.centros_operativos_ids
                    )
                        ? recurso.centros_operativos_ids
                        : [];


                return centrosRecurso
                    .map(
                        function(centroId){

                            return String(
                                centroId
                            );

                        }
                    )
                    .includes(
                        centroSeleccionado
                    );

            }

        )

        .forEach(

            function(recurso){

                const opcion =
                    document.createElement(
                        "option"
                    );


                opcion.value =
                    String(
                        recurso.id
                    );


                opcion.textContent =
                    recurso.tipo_recurso_label
                        ? `${recurso.nombre} · ${recurso.tipo_recurso_label}`
                        : recurso.nombre;


                selectRecurso.appendChild(
                    opcion
                );

            }

        );


    /*
     * Si el recurso que estaba seleccionado
     * sigue perteneciendo al Centro Operativo
     * elegido, conservamos la selección.
     */

    if(
        valorAnterior &&
        selectRecurso.querySelector(
            `option[value="${valorAnterior}"]`
        )
    ){

        selectRecurso.value =
            valorAnterior;

    }

}

function mostrarCargaSimple(){

    document.getElementById(
        "bloque-alta-empresa"
    ).style.display = "none";

    document.getElementById(
        "contenido-operativo"
    ).innerHTML = `

<div class="card">

<div
style="
font-size:28px;
font-weight:700;
margin-bottom:8px;
">

Carga Simple

</div>

<div
style="
color:#8b93a7;
margin-bottom:30px;
">

Registro manual de un gasto.

</div>

<div class="form-grid">

<div class="field">

<label
class="label"
for="tipoGastoRegistro">

Tipo de gasto

</label>

<div
style="
display:flex;
gap:10px;
">

<select
id="tipoGastoRegistro"
class="input-box"
style="flex:1;">

<div
style="
display:flex;
gap:10px;
">

<select
id="tipoGastoRegistro"
class="input-box"
style="flex:1;">

<option value=""></option>

</select>

<button
type="button"
class="action-btn"
onclick="mostrarABMTiposGasto('registro')">

+

</button>

</div>
</div>

<div class="field">

<label
class="label"
for="proveedorRegistro">

Proveedor

</label>

<div
style="
display:flex;
gap:10px;
">

<select
id="proveedorRegistro"
class="input-box"
style="flex:1;"
disabled>

<option value="">

Seleccione primero un tipo de gasto...

</option>

</select>

<button
id="btnAgregarProveedorRegistro"
type="button"
class="action-btn"
disabled>

+

</button>

</div>

</div>

<div class="field">

<label class="label">

Centro Operativo

</label>

<div
style="
display:flex;
gap:10px;
">

<select
id="centroOperativoRegistro"
class="input-box"
style="flex:1;">

<option value="">

Seleccione...

</option>

</select>

<button
type="button"
class="action-btn"
onclick="mostrarABMCentrosOperativos('registro')">

+

</button>

</div>

</div>

<div class="field">

<label
class="label"
for="recursoOperativoRegistro">

Recurso operativo

</label>

<div
style="
display:flex;
gap:10px;
">

<select
id="recursoOperativoRegistro"
class="input-box"
style="flex:1;"
disabled>

<option value="">

Seleccione primero un Centro Operativo...

</option>

</select>

<button
id="btnAgregarRecursoOperativoRegistro"
type="button"
class="action-btn"
disabled>

+

</button>

</div>

</div>

<div class="field">

<label class="label">

Fecha

</label>

<input
id="fechaRegistro"
type="date"
class="input-box">

</div>

<div class="field">

<label class="label">

Fecha de Vencimiento

</label>

<input
id="fechaVencimientoRegistro"
type="date"
class="input-box">

</div>

<div class="field">

<label class="label">

Tipo de comprobante

</label>

<select
id="tipoComprobanteRegistro"
class="input-box">

<option>A</option>

<option>B</option>

<option>C</option>

<option>X</option>

</select>

</div>

<div class="field">

    <label class="label">
        Número
    </label>

    <div style="
        display:grid;
        grid-template-columns:110px 18px 1fr;
        gap:8px;
        align-items:center;
    ">

        <input
        id="puntoVentaComprobanteRegistro"
        type="text"
        inputmode="numeric"
        maxlength="4"
        class="input-box"
        placeholder="0000"
        onblur="normalizarComprobanteRegistro()">

        <div style="
            text-align:center;
            color:#98a2b3;
        ">
            -
        </div>

        <input
        id="numeroComprobanteRegistro"
        type="text"
        inputmode="numeric"
        maxlength="8"
        class="input-box"
        placeholder="00000000"
        onblur="normalizarComprobanteRegistro()">

    </div>

</div>

<div class="field">

<label class="label">

Neto Gravado

</label>

<input
id="neto"
type="text"
inputmode="decimal"
class="input-box"
oninput="calcularTotalRegistro()">

</div>

<div class="field">

<label class="label">

No Gravado / Exento

</label>

<input
id="exento"
type="text"
inputmode="decimal"
class="input-box"
oninput="calcularTotalRegistro()">

</div>

<div
style="
grid-column:1 / -1;
display:grid;
grid-template-columns:1fr 20px 1fr 20px 1fr;
align-items:end;
gap:12px;
margin-top:5px;
">

<!-- IVA 21 -->

<div class="field">

<label class="label">

IVA 21%

</label>

<div
style="
display:flex;
gap:8px;
">

<input
id="iva21"
type="text"
inputmode="decimal"
class="input-box"
style="flex:1"
oninput="calcularTotalRegistro()">

<button
type="button"
class="action-btn"
onclick="calcularIVA(0.21,'iva21')">

21%

</button>

</div>

</div>

<div
style="
text-align:center;
font-size:22px;
color:#64748b;
">

|

</div>

<!-- IVA 27 -->

<div class="field">

<label class="label">

IVA 27%

</label>

<div
style="
display:flex;
gap:8px;
">

<input
id="iva27"
type="text"
inputmode="decimal"
class="input-box"
style="flex:1"
oninput="calcularTotalRegistro()">

<button
type="button"
class="action-btn"
onclick="calcularIVA(0.27,'iva27')">

27%

</button>

</div>

</div>

<div
style="
text-align:center;
font-size:22px;
color:#64748b;
">

|

</div>

<!-- IVA 10.5 -->

<div class="field">

<label class="label">

IVA 10.5%

</label>

<div
style="
display:flex;
gap:8px;
">

<input
id="iva105"
type="text"
inputmode="decimal"
class="input-box"
style="flex:1"
oninput="calcularTotalRegistro()">

<button
type="button"
class="action-btn"
onclick="calcularIVA(0.105,'iva105')">

10.5%

</button>

</div>

</div>

</div>

<div class="field">

<label class="label">

Recargos / Intereses

</label>

<input
id="recargosIntereses"
type="text"
inputmode="decimal"
class="input-box"
oninput="calcularTotalRegistro()">

</div>

<div class="field">

<label class="label">

Ajuste por redondeo

</label>

<input
id="ajuste"
type="text"
inputmode="decimal"
class="input-box"
oninput="calcularTotalRegistro()">

</div>

<div
style="
grid-column:1/-1;
margin-top:10px;
">

<button
type="button"
class="sidebar-btn"
style="
justify-content:space-between;
padding-left:20px;
padding-right:20px;
"
onclick="togglePercepciones()"
id="btnPercepciones">

<span>
► Percepciones
</span>

<span id="totalPercepcionesBoton">
$ 0.00
</span>

</button>

</div>


<div
id="bloquePercepciones"
style="
display:none;
grid-column:1/-1;
">

<div class="form-grid">


<div class="field">

<label class="label">

Ingresos Brutos (IIBB)

</label>

<input
id="percepcionIIBB"
type="text"
inputmode="decimal"
class="input-box"
oninput="calcularTotalPercepciones()">

</div>


<div class="field">

<label class="label">

IVA (Impuesto al Valor Agregado)

</label>

<input
id="percepcionIVA"
type="text"
inputmode="decimal"
class="input-box"
oninput="calcularTotalPercepciones()">

</div>


<div class="field">

<label class="label">

Impuesto a las Ganancias

</label>

<input
id="percepcionGanancias"
type="text"
inputmode="decimal"
class="input-box"
oninput="calcularTotalPercepciones()">

</div>


<div class="field">

<label class="label">

Tasas Municipales

</label>

<input
id="percepcionTasasMunicipales"
type="text"
inputmode="decimal"
class="input-box"
oninput="calcularTotalPercepciones()">

</div>


</div>

</div>

<div
class="field"
style="grid-column:1 / -1;">

<label class="label">

Total del Registro

</label>

<div
style="
display:flex;
align-items:center;
gap:10px;
">

<input
id="total_registro"
type="text"
class="input-box"
style="
flex:1;
font-size:22px;
font-weight:700;
text-align:right;
background:#111827;
color:#60a5fa;"
readonly>

<button
id="btnAdjuntarFacturaRegistro"
type="button"
class="action-btn"
style="
flex-shrink:0;
padding:0 16px;
">

📎 Factura

</button>

<input
id="archivoFacturaRegistro"
type="file"
accept=".pdf,.jpg,.jpeg,.png,.webp"
hidden>

</div>

</div>

<!-- ===================================================== -->
<!-- PREVISIÓN DE PAGO -->
<!-- ===================================================== -->

<div
id="bloquePrevisionPagoRegistro"
style="
grid-column:1 / -1;
margin-top:6px;
padding-top:22px;
border-top:1px solid #252c3d;
"
>

<div
style="
display:grid;
grid-template-columns:1fr 1fr;
gap:18px;
"
>

<div class="field">

<label
class="label"
for="modalidadPagoRegistro">

Forma prevista de pago

</label>

<select
id="modalidadPagoRegistro"
class="input-box">

<option value="Manual">
Pago manual
</option>

<option value="DebitoAutomatico">
Débito automático
</option>

</select>

</div>


<div
id="campoCuentaDebitoRegistro"
class="field"
style="
visibility:hidden;
pointer-events:none;
"
>

<label
class="label"
for="cuentaDebitoRegistro">

Cuenta para débito

</label>

<select
id="cuentaDebitoRegistro"
class="input-box"
disabled>

<option value="">
Seleccione una cuenta...
</option>

</select>

</div>

</div>

</div>

<!-- ===================================================== -->
<!-- FIN DATOS DEL REGISTRO -->
<!-- ===================================================== -->

</div>

</div>

<!-- ===================================================== -->
<!-- PAGOS DEL REGISTRO -->
<!-- ===================================================== -->

<div
    id="listaPagosRegistro"
    style="
        display:flex;
        flex-direction:column;
        gap:18px;
        margin-top:24px;
    "
>
</div>

<!-- ===================================================== -->
<!-- ACCIONES DEL REGISTRO -->
<!-- ===================================================== -->

<div
style="
display:grid;
grid-template-columns:1fr 1fr 1fr;
gap:12px;
margin-top:22px;
"
>

    <button
        id="btnGuardarRegistro"
        type="button"
        class="guardar"
        style="
        margin-top:0;
        "
    >
        Guardar registro
    </button>


    <button
        id="btnAgregarPagoRegistro"
        type="button"
        class="action-btn"
        style="
        height:52px;
        "
    >
        + Agregar pago
    </button>


    <button
        id="btnPlanPagoRegistro"
        type="button"
        class="action-btn"
        style="
        height:52px;
        "
    >
        Plan de pago
    </button>

</div>

`;

cargarSelectCentrosOperativos();

iniciarEventosCargaSimple();

}

async function cargarSelectCentrosOperativos(){

    const empresaInput =
        document.getElementById(
            "empresaActiva"
        );

    const select =
        document.getElementById(
            "centroOperativoRegistro"
        );

    if(!empresaInput || !select){

        return;

    }

    const empresa =
        empresaInput.value;

    if(!empresa){

        return;

    }

    const valorAnterior =
        select.value;

    try{

        const respuesta = await fetch(
            `/listar-centros-operativos/?empresa=${encodeURIComponent(empresa)}`
        );

        if(!respuesta.ok){

            throw new Error(
                `Error HTTP ${respuesta.status}`
            );

        }

        const datos =
            await respuesta.json();

        select.innerHTML = `
            <option value="">
                Seleccione...
            </option>
        `;

        if(!Array.isArray(datos.centros)){

            console.error(
                "La respuesta no contiene datos.centros:",
                datos
            );

            return;

        }

        datos.centros.forEach(centro => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                String(centro.id);

            option.textContent =
                centro.nombre;

            select.appendChild(
                option
            );

        });

        if(
            valorAnterior &&
            select.querySelector(
                `option[value="${valorAnterior}"]`
            )
        ){

            select.value =
                valorAnterior;

        }

    }catch(error){

        console.error(
            "Error cargando centros operativos:",
            error
        );

    }

}

async function cargarSelectProveedores(){

    const empresaInput =
        document.getElementById(
            "empresaActiva"
        );

    const select =
        document.getElementById(
            "proveedorRegistro"
        );

    if(
        !empresaInput ||
        !select
    ){

        return;

    }

    const empresa =
        empresaInput.value;

    if(!empresa){

        return;

    }

    const valorAnterior =
        select.value;

    try{

        const respuesta = await fetch(
            `/listar-proveedores/?empresa=${encodeURIComponent(empresa)}`
        );

        if(!respuesta.ok){

            throw new Error(
                `Error HTTP ${respuesta.status}`
            );

        }

        const datos =
            await respuesta.json();

        select.innerHTML = `
            <option value="">
                Seleccione...
            </option>
        `;

        if(
            !Array.isArray(
                datos.proveedores
            )
        ){

            return;

        }

        datos.proveedores.forEach(
            proveedor => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    String(
                        proveedor.id
                    );

                option.textContent =
                    `${proveedor.razon_social} · ${proveedor.cuit}`;

                select.appendChild(
                    option
                );

            }
        );

        if(
            valorAnterior &&
            select.querySelector(
                `option[value="${valorAnterior}"]`
            )
        ){

            select.value =
                valorAnterior;

        }

    }catch(error){

        console.error(
            "Error cargando proveedores:",
            error
        );

    }

}

async function cargarSelectBancos(){

    const empresa =
        document.getElementById(
            "empresaActiva"
        ).value;

    const select =
        document.getElementById(
            "bancoCheque"
        );

    if(!empresa || !select){

        return;

    }

    const respuesta = await fetch(
        `/listar-bancos/?empresa=${empresa}`
    );

    if(!respuesta.ok){

        return;

    }

    const datos =
        await respuesta.json();

    select.innerHTML = `
        <option value="">
            Seleccione...
        </option>
    `;

    datos.bancos.forEach(banco => {

        const option =
            document.createElement(
                "option"
            );

        option.value = banco.id;

        option.textContent =
            banco.nombre;

        select.appendChild(option);

    });

}

function formatearImporte(
    valor
){

    const numero =
        Number(
            valor || 0
        );


    return numero.toLocaleString(
        "es-AR",
        {
            minimumFractionDigits:
                2,

            maximumFractionDigits:
                2
        }
    );

}

function leerImporte(
    valor
){

    if(
        valor === null ||
        valor === undefined ||
        valor === ""
    ){

        return 0;

    }


    if(
        typeof valor === "number"
    ){

        return valor;

    }


    let texto =
        String(
            valor
        )
        .trim()
        .replace(
            /\$/g,
            ""
        )
        .replace(
            /\s/g,
            ""
        );


    /*
     * Formato argentino:
     *
     * 1.234.567,89
     *
     * Eliminamos puntos de miles y
     * convertimos la coma decimal a punto.
     */

    texto =
        texto
            .replace(
                /\./g,
                ""
            )
            .replace(
                ",",
                "."
            );


    const numero =
        Number(
            texto
        );


    return Number.isFinite(
        numero
    )
        ? numero
        : 0;

}


function formatearCampoImporte(
    input
){

    if(!input){

        return;

    }


    const valor =
        leerImporte(
            input.value
        );


    if(
        input.value.trim() === ""
    ){

        return;

    }


    input.value =
        formatearImporte(
            valor
        );

}

function calcularTotalRegistro(){

    const neto =
        leerImporte(
            document.getElementById(
                "neto"
            )?.value
        );


    const exento =
        leerImporte(
            document.getElementById(
                "exento"
            )?.value
        );


    const iva21 =
        leerImporte(
            document.getElementById(
                "iva21"
            )?.value
        );


    const iva27 =
        leerImporte(
            document.getElementById(
                "iva27"
            )?.value
        );


    const iva105 =
        leerImporte(
            document.getElementById(
                "iva105"
            )?.value
        );


    const recargosIntereses =
        leerImporte(
            document.getElementById(
                "recargosIntereses"
            )?.value
        );


    const percepcionIIBB =
        leerImporte(
            document.getElementById(
                "percepcionIIBB"
            )?.value
        );


    const percepcionIVA =
        leerImporte(
            document.getElementById(
                "percepcionIVA"
            )?.value
        );


    const percepcionGanancias =
        leerImporte(
            document.getElementById(
                "percepcionGanancias"
            )?.value
        );


    const percepcionTasasMunicipales =
        leerImporte(
            document.getElementById(
                "percepcionTasasMunicipales"
            )?.value
        );


    const ajuste =
        leerImporte(
            document.getElementById(
                "ajuste"
            )?.value
        );


    const totalPercepciones =
        percepcionIIBB +
        percepcionIVA +
        percepcionGanancias +
        percepcionTasasMunicipales;


    const total =
        neto +
        exento +
        iva21 +
        iva27 +
        iva105 +
        recargosIntereses +
        totalPercepciones +
        ajuste;


    const inputTotal =
        document.getElementById(
            "total_registro"
        );


    if(inputTotal){

        inputTotal.dataset.valorNumerico =
            String(
                total
            );


        inputTotal.value =
            "$ " +
            formatearImporte(
                total
            );

    }


    actualizarResumenGeneralPagos();

}

function calcularIVA(
    porcentaje,
    idDestino
){

    const neto =
        leerImporte(
            document.getElementById(
                "neto"
            )?.value
        );


    const iva =
        neto *
        porcentaje;


    const destino =
        document.getElementById(
            idDestino
        );


    if(destino){

        destino.value =
            formatearImporte(
                iva
            );

    }


    calcularTotalRegistro();

}

function togglePercepciones(){

    const bloque =
        document.getElementById(
            "bloquePercepciones"
        );

    const boton =
        document.getElementById(
            "btnPercepciones"
        );

    const total =
        document.getElementById(
            "totalPercepcionesBoton"
        );


    if(
        !bloque ||
        !boton
    ){

        return;

    }


    const textoTotal =
        total
            ? total.textContent
            : "$ 0.00";


    if(
        bloque.style.display === "none"
    ){

        bloque.style.display =
            "block";


        boton.innerHTML = `

            <span>
                ▼ Percepciones
            </span>

            <span id="totalPercepcionesBoton">
                ${textoTotal}
            </span>

        `;

    }else{

        bloque.style.display =
            "none";


        boton.innerHTML = `

            <span>
                ► Percepciones
            </span>

            <span id="totalPercepcionesBoton">
                ${textoTotal}
            </span>

        `;

    }

}

function calcularTotalPercepciones(){

    const iibB =
        leerImporte(
            document.getElementById(
                "percepcionIIBB"
            )?.value
        );


    const iva =
        leerImporte(
            document.getElementById(
                "percepcionIVA"
            )?.value
        );


    const ganancias =
        leerImporte(
            document.getElementById(
                "percepcionGanancias"
            )?.value
        );


    const tasasMunicipales =
        leerImporte(
            document.getElementById(
                "percepcionTasasMunicipales"
            )?.value
        );


    const total =
        iibB +
        iva +
        ganancias +
        tasasMunicipales;


    const totalBoton =
        document.getElementById(
            "totalPercepcionesBoton"
        );


    if(totalBoton){

        totalBoton.textContent =
            "$ " +
            formatearImporte(
                total
            );

    }


    calcularTotalRegistro();

}
