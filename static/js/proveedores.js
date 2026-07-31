let ultimoProveedorCreado = null;
let proveedorEditandoId = null;
let proveedorReactivandoId = null;


/* =========================================
   INICIALIZACIÓN
========================================= */

function iniciarABMProveedores(){

    const btnGuardar =
        document.getElementById(
            "btnGuardarProveedor"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarProveedor"
        );

    const btnVolver =
        document.getElementById(
            "btnVolverProveedor"
        );

    const inputCuit =
        document.getElementById(
            "cuitProveedor"
        );


    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarProveedor
        );

    }


    if(btnCancelar){

        btnCancelar.addEventListener(
            "click",
            cancelarEdicionProveedor
        );

    }


    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeABMProveedores
        );

    }


    if(inputCuit){

        inputCuit.addEventListener(
            "input",
            function(){

                this.value =
                    formatearCuitProveedor(
                        this.value
                    );

            }
        );

    }

}


/* =========================================
   FUNCIONES AUXILIARES
========================================= */

function formatearCuitProveedor(valor){

    const numeros =
        String(valor || "")
        .replace(
            /\D/g,
            ""
        )
        .slice(
            0,
            11
        );


    if(numeros.length <= 2){

        return numeros;

    }


    if(numeros.length <= 10){

        return (
            numeros.slice(0, 2) +
            "-" +
            numeros.slice(2)
        );

    }


    return (
        numeros.slice(0, 2) +
        "-" +
        numeros.slice(2, 10) +
        "-" +
        numeros.slice(10)
    );

}


function valorProveedor(id){

    const elemento =
        document.getElementById(
            id
        );

    return elemento
        ? elemento.value.trim()
        : "";

}


/* =========================================
   GUARDAR / ACTUALIZAR
========================================= */

async function guardarProveedor(){

    const empresa =
        valorProveedor(
            "empresaActiva"
        );

    const razonSocial =
        valorProveedor(
            "razonSocialProveedor"
        );

    const cuit =
        valorProveedor(
            "cuitProveedor"
        );


    if(!empresa){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }


    if(!razonSocial){

        alert(
            "Ingrese la razón social del proveedor."
        );

        const input =
            document.getElementById(
                "razonSocialProveedor"
            );

        if(input){

            input.focus();

        }

        return;

    }


    if(
        !/^\d{2}-\d{8}-\d$/.test(
            cuit
        )
    ){

        alert(
            "El CUIT debe tener el formato 00-00000000-0."
        );

        const input =
            document.getElementById(
                "cuitProveedor"
            );

        if(input){

            input.focus();

        }

        return;

    }


    const formulario =
        new FormData();


    formulario.append(
        "empresa",
        empresa
    );

    formulario.append(
        "razon_social",
        razonSocial
    );

    formulario.append(
        "cuit",
        cuit
    );

    formulario.append(
        "direccion",
        valorProveedor(
            "direccionProveedor"
        )
    );

    formulario.append(
        "localidad",
        valorProveedor(
            "localidadProveedor"
        )
    );

    formulario.append(
        "contacto1_nombre",
        valorProveedor(
            "contacto1NombreProveedor"
        )
    );

    formulario.append(
        "contacto1_telefono",
        valorProveedor(
            "contacto1TelefonoProveedor"
        )
    );

    formulario.append(
        "contacto1_email",
        valorProveedor(
            "contacto1EmailProveedor"
        )
    );

    formulario.append(
        "contacto2_nombre",
        valorProveedor(
            "contacto2NombreProveedor"
        )
    );

    formulario.append(
        "contacto2_telefono",
        valorProveedor(
            "contacto2TelefonoProveedor"
        )
    );

    formulario.append(
        "contacto2_email",
        valorProveedor(
            "contacto2EmailProveedor"
        )
    );

    formulario.append(
        "email",
        valorProveedor(
            "emailProveedor"
        )
    );

    formulario.append(
        "observaciones",
        valorProveedor(
            "observacionesProveedor"
        )
    );


    const estaEditando =
        proveedorEditandoId !== null;

    const estaReactivando =
        proveedorReactivandoId !== null;


    let url =
        "/guardar-proveedor/";


    if(estaEditando){

        url =
            "/modificar-proveedor/";

        formulario.append(
            "proveedor",
            proveedorEditandoId
        );

    }else if(estaReactivando){

        url =
            "/reactivar-proveedor/";

        formulario.append(
            "proveedor",
            proveedorReactivandoId
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


        if(
            resultado.requiere_reactivacion &&
            resultado.proveedor
        ){

            cargarProveedorParaReactivar(
                resultado.proveedor
            );

            alert(
                resultado.mensaje ||
                "El proveedor está inactivo. Puede reactivarlo."
            );

            return;

        }


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            let mensajePredeterminado =
                "No se pudo guardar el proveedor.";


            if(estaEditando){

                mensajePredeterminado =
                    "No se pudo modificar el proveedor.";

            }else if(estaReactivando){

                mensajePredeterminado =
                    "No se pudo reactivar el proveedor.";

            }


            alert(
                resultado.mensaje ||
                mensajePredeterminado
            );

            return;

        }


        /*
         * Guardamos los datos del proveedor nuevo o reactivado.
         *
         * No se actualiza durante una modificación normal,
         * porque en ese caso no existe un proveedor nuevo
         * que deba seleccionarse automáticamente.
         */
        if(
            !estaEditando &&
            resultado.proveedor
        ){

            ultimoProveedorCreado = {

                id:
                    String(
                        resultado.proveedor.id
                    ),

                razon_social:
                    resultado.proveedor.razon_social ||
                    razonSocial,

                cuit:
                    resultado.proveedor.cuit ||
                    cuit

            };

        }


        proveedorEditandoId = null;
        proveedorReactivandoId = null;


        await mostrarABMProveedores(
            origenABM
        );


    }catch(error){

        console.error(
            "Error guardando proveedor:",
            error
        );


        alert(
            estaEditando
                ? "Ocurrió un error al modificar el proveedor."
                : "Ocurrió un error al guardar el proveedor."
        );

    }

}

function cargarProveedorParaReactivar(
    proveedor
){

    proveedorEditandoId = null;

    proveedorReactivandoId =
        String(
            proveedor.id
        );


    const valores = {

        razonSocialProveedor:
            proveedor.razon_social,

        cuitProveedor:
            proveedor.cuit,

        direccionProveedor:
            proveedor.direccion,

        localidadProveedor:
            proveedor.localidad,

        contacto1NombreProveedor:
            proveedor.contacto1_nombre,

        contacto1TelefonoProveedor:
            proveedor.contacto1_telefono,

        contacto1EmailProveedor:
            proveedor.contacto1_email,

        contacto2NombreProveedor:
            proveedor.contacto2_nombre,

        contacto2TelefonoProveedor:
            proveedor.contacto2_telefono,

        contacto2EmailProveedor:
            proveedor.contacto2_email,

        emailProveedor:
            proveedor.email,

        observacionesProveedor:
            proveedor.observaciones

    };


    Object.entries(
        valores
    ).forEach(
        function([id, valor]){

            const elemento =
                document.getElementById(
                    id
                );

            if(elemento){

                elemento.value =
                    valor || "";

            }

        }
    );


    const btnGuardar =
        document.getElementById(
            "btnGuardarProveedor"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarProveedor"
        );


    if(btnGuardar){

        btnGuardar.textContent =
            "Activar";

    }


    if(btnCancelar){

        btnCancelar.style.display =
            "inline-block";

    }


    const inputRazonSocial =
        document.getElementById(
            "razonSocialProveedor"
        );


    if(inputRazonSocial){

        inputRazonSocial.focus();
        inputRazonSocial.select();

    }

}

/* =========================================
   MODIFICAR
========================================= */

function modificarProveedor(
    proveedorId,
    razonSocial,
    cuit,
    direccion,
    localidad,
    contacto1Nombre,
    contacto1Telefono,
    contacto1Email,
    contacto2Nombre,
    contacto2Telefono,
    contacto2Email,
    email,
    observaciones
){
    proveedorReactivandoId = null;

    proveedorEditandoId =
        String(
            proveedorId
        );


    const valores = {

        razonSocialProveedor:
            razonSocial,

        cuitProveedor:
            cuit,

        direccionProveedor:
            direccion,

        localidadProveedor:
            localidad,

        contacto1NombreProveedor:
            contacto1Nombre,

        contacto1TelefonoProveedor:
            contacto1Telefono,

        contacto1EmailProveedor:
            contacto1Email,

        contacto2NombreProveedor:
            contacto2Nombre,

        contacto2TelefonoProveedor:
            contacto2Telefono,

        contacto2EmailProveedor:
            contacto2Email,

        emailProveedor:
            email,

        observacionesProveedor:
            observaciones

    };


    Object.entries(
        valores
    ).forEach(
        function([id, valor]){

            const elemento =
                document.getElementById(
                    id
                );

            if(elemento){

                elemento.value =
                    valor || "";

            }

        }
    );


    const btnGuardar =
        document.getElementById(
            "btnGuardarProveedor"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarProveedor"
        );


    if(btnGuardar){

        btnGuardar.textContent =
            "Actualizar";

    }


    if(btnCancelar){

        btnCancelar.style.display =
            "inline-block";

    }


    const inputRazonSocial =
        document.getElementById(
            "razonSocialProveedor"
        );


    if(inputRazonSocial){

        inputRazonSocial.focus();
        inputRazonSocial.select();

    }

}


/* =========================================
   CANCELAR / LIMPIAR
========================================= */

function cancelarEdicionProveedor(){

    proveedorEditandoId = null;
    proveedorReactivandoId = null;

    limpiarFormularioProveedor();

}


function limpiarFormularioProveedor(){

    proveedorEditandoId = null;
    proveedorReactivandoId = null;
    
    const campos = [

        "razonSocialProveedor",
        "cuitProveedor",
        "direccionProveedor",
        "localidadProveedor",
        "contacto1NombreProveedor",
        "contacto1TelefonoProveedor",
        "contacto1EmailProveedor",
        "contacto2NombreProveedor",
        "contacto2TelefonoProveedor",
        "contacto2EmailProveedor",
        "emailProveedor",
        "observacionesProveedor"

    ];


    campos.forEach(
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
            "btnGuardarProveedor"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarProveedor"
        );


    if(btnGuardar){

        btnGuardar.textContent =
            "Guardar";

    }


    if(btnCancelar){

        btnCancelar.style.display =
            "none";

    }


    const inputRazonSocial =
        document.getElementById(
            "razonSocialProveedor"
        );


    if(inputRazonSocial){

        inputRazonSocial.focus();

    }

}


/* =========================================
   DESACTIVAR
========================================= */

async function eliminarProveedor(
    proveedorId,
    razonSocial
){

    const confirmado =
        confirm(
            `¿Desactivar el proveedor "${razonSocial}"?\n\n` +
            "Los registros históricos conservarán el proveedor, " +
            "pero ya no podrá seleccionarse en operaciones nuevas."
        );


    if(!confirmado){

        return;

    }


    const empresa =
        valorProveedor(
            "empresaActiva"
        );


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
        "proveedor",
        proveedorId
    );


    try{

        const respuesta =
            await fetch(
                "/eliminar-proveedor/",
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
                "No se pudo desactivar el proveedor."
            );

            return;

        }


        if(
            proveedorEditandoId ===
            String(proveedorId)
        ){

            proveedorEditandoId = null;

        }


        await mostrarABMProveedores(
            origenABM
        );


    }catch(error){

        console.error(
            "Error desactivando proveedor:",
            error
        );


        alert(
            "Ocurrió un error al desactivar el proveedor."
        );

    }

}