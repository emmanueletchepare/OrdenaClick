let origenABM = "menu";

let origenABMTiposGasto = "menu";

let contenidoAnteriorABM = null;

let contextoRetornoABM = null;

let contenidoAnteriorABMProveedores = null;

let proveedoresCargaSimple = [];

let recursosCargaSimple = [];

let contenidoAnteriorABMBancosDesdeCuentaBancaria = null;

let origenABMCuentasBancarias = "menu";

let origenABMTarjetas = "menu";

let contenidoAnteriorABMTarjetas = null;

let contenidoAnteriorABMCuentasBancariasDesdeTarjeta = null;


/*
 * =========================================
 * RETENCIONES
 * =========================================
 */

let origenABMRetenciones = "menu";

let contenidoAnteriorABMRetenciones = null;


let ultimoBancoCreado = null;

function confirmarEliminarEmpresa(){

    document.getElementById(
        "modal-eliminar-empresa"
    ).style.display = "flex";

}

function cerrarModalEliminarEmpresa(){

    document.getElementById(
        "modal-eliminar-empresa"
    ).style.display = "none";

}

function abrirSelectorFacturaRegistro(){

    const input =
        document.getElementById(
            "archivoFacturaRegistro"
        );


    if(!input){

        return;

    }


    input.click();

}


function actualizarFacturaSeleccionada(){

    const input =
        document.getElementById(
            "archivoFacturaRegistro"
        );

    const boton =
        document.getElementById(
            "btnAdjuntarFacturaRegistro"
        );


    if(
        !input ||
        !boton
    ){

        return;

    }


    if(
        !input.files ||
        input.files.length === 0
    ){

        boton.textContent =
            "📎 Factura";

        boton.removeAttribute(
            "title"
        );

        return;

    }


    const archivo =
        input.files[0];


    boton.textContent =
        "📎 Factura ✓";


    boton.title =
        archivo.name;

}

document.addEventListener(
    "change",
    function(event){

        if(
            event.target.id !==
            "archivoFacturaRegistro"
        ){

            return;

        }


        actualizarFacturaSeleccionada();

    }
);
