let gestionClaveEditandoId = null;

let gestionClaveReactivandoId = null;

let gestionClaveModoVer = false;


/* =========================================
   INICIALIZACIÓN
========================================= */

function iniciarABMGestionClaves(){

    const btnGuardar =
        document.getElementById(
            "btnGuardarGestionClave"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarGestionClave"
        );

    const btnVolver =
        document.getElementById(
            "btnVolverGestionClaves"
        );

    const btnVerContrasena =
        document.getElementById(
            "btnVerContrasenaGestionClave"
        );

    const btnCopiarContrasena =
        document.getElementById(
            "btnCopiarContrasenaGestionClave"
        );


    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarGestionClave
        );

    }


    if(btnCancelar){

        btnCancelar.addEventListener(
            "click",
            cancelarGestionClave
        );

    }


    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeGestionClaves
        );

    }


    if(btnVerContrasena){

        btnVerContrasena.addEventListener(
            "click",
            alternarVisibilidadContrasena
        );

    }


    if(btnCopiarContrasena){

        btnCopiarContrasena.addEventListener(
            "click",
            copiarContrasenaGestionClave
        );

    }


    document
        .querySelectorAll(
            ".btn-ver-gestion-clave"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        verGestionClave(
                            boton.dataset.claveId
                        );

                    }
                );

            }
        );


    document
        .querySelectorAll(
            ".btn-modificar-gestion-clave"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        modificarGestionClave(
                            boton.dataset.claveId
                        );

                    }
                );

            }
        );


    document
        .querySelectorAll(
            ".btn-eliminar-gestion-clave"
        )
        .forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        eliminarGestionClave(
                            boton.dataset.claveId
                        );

                    }
                );

            }
        );

}


/* =========================================
   AUXILIARES
========================================= */

function valorGestionClave(id){

    const elemento =
        document.getElementById(
            id
        );

    return elemento
        ? elemento.value
        : "";

}


function obtenerEmpresaGestionClave(){

    const empresa =
        document.getElementById(
            "empresaActiva"
        );

    return empresa
        ? empresa.value
        : "";

}


function obtenerCookieGestionClave(nombre){

    const cookies =
        document.cookie
            .split(";")
            .map(
                function(cookie){

                    return cookie.trim();

                }
            );

    for(
        const cookie of cookies
    ){

        if(
            cookie.startsWith(
                nombre + "="
            )
        ){

            return decodeURIComponent(
                cookie.substring(
                    nombre.length + 1
                )
            );

        }

    }

    return "";

}


/* =========================================
   GUARDAR / MODIFICAR / REACTIVAR
========================================= */

async function guardarGestionClave(){

    if(gestionClaveModoVer){

        return;

    }

    const empresa =
        obtenerEmpresaGestionClave();

    const nombre =
        valorGestionClave(
            "nombreGestionClave"
        ).trim();

    if(!empresa){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }

    if(!nombre){

        alert(
            "Ingrese el nombre de la credencial."
        );

        const input =
            document.getElementById(
                "nombreGestionClave"
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
        "nombre",
        nombre
    );

    formulario.append(
        "sitio",
        valorGestionClave(
            "sitioGestionClave"
        ).trim()
    );

    formulario.append(
        "usuario",
        valorGestionClave(
            "usuarioGestionClave"
        ).trim()
    );

    formulario.append(
        "correo",
        valorGestionClave(
            "correoGestionClave"
        ).trim()
    );

    formulario.append(
        "contrasena",
        valorGestionClave(
            "contrasenaGestionClave"
        )
    );

    formulario.append(
        "referencia_recuperacion_1",
        valorGestionClave(
            "referencia1GestionClave"
        ).trim()
    );

    formulario.append(
        "referencia_recuperacion_2",
        valorGestionClave(
            "referencia2GestionClave"
        ).trim()
    );

    formulario.append(
        "observaciones",
        valorGestionClave(
            "observacionesGestionClave"
        ).trim()
    );


    let url =
        "/gestion-claves/guardar/";


    if(
        gestionClaveEditandoId !== null
    ){

        url =
            "/gestion-claves/modificar/";

        formulario.append(
            "clave",
            gestionClaveEditandoId
        );

    }else if(
        gestionClaveReactivandoId !== null
    ){

        url =
            "/gestion-claves/reactivar/";

        formulario.append(
            "clave",
            gestionClaveReactivandoId
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
                            obtenerCookieGestionClave(
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
            resultado.clave
        ){

            gestionClaveReactivandoId =
                String(
                    resultado.clave.id
                );

            gestionClaveEditandoId =
                null;

            const btnGuardar =
                document.getElementById(
                    "btnGuardarGestionClave"
                );

            const btnCancelar =
                document.getElementById(
                    "btnCancelarGestionClave"
                );

            if(btnGuardar){

                btnGuardar.textContent =
                    "Reactivar";

            }

            if(btnCancelar){

                btnCancelar.style.display =
                    "inline-flex";

            }

            alert(
                resultado.mensaje ||
                "La credencial está inactiva. Puede reactivarla."
            );

            return;

        }


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                "No fue posible guardar la credencial."
            );

            return;

        }


        gestionClaveEditandoId =
            null;

        gestionClaveReactivandoId =
            null;


        await mostrarABMGestionClaves();

    }catch(error){

        console.error(
            "Error guardando credencial:",
            error
        );

        alert(
            "Ocurrió un error al guardar la credencial."
        );

    }

}


/* =========================================
   VER
========================================= */

async function verGestionClave(
    claveId
){

    const empresa =
        obtenerEmpresaGestionClave();

    if(
        !empresa ||
        !claveId
    ){

        return;

    }


    try{

        const respuesta =
            await fetch(
                `/gestion-claves/ver/?empresa=${encodeURIComponent(empresa)}&clave=${encodeURIComponent(claveId)}`
            );

        const resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                "No fue posible cargar la credencial."
            );

            return;

        }


        cargarDatosGestionClave(
            resultado.clave
        );

        gestionClaveModoVer =
            true;

        gestionClaveEditandoId =
            null;

        gestionClaveReactivandoId =
            null;

        establecerModoLecturaGestionClave(
            true
        );

    }catch(error){

        console.error(
            "Error cargando credencial:",
            error
        );

        alert(
            "Ocurrió un error al cargar la credencial."
        );

    }

}


/* =========================================
   MODIFICAR
========================================= */

async function modificarGestionClave(
    claveId
){

    const empresa =
        obtenerEmpresaGestionClave();

    if(
        !empresa ||
        !claveId
    ){

        return;

    }


    try{

        const respuesta =
            await fetch(
                `/gestion-claves/ver/?empresa=${encodeURIComponent(empresa)}&clave=${encodeURIComponent(claveId)}`
            );

        const resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                "No fue posible cargar la credencial."
            );

            return;

        }


        cargarDatosGestionClave(
            resultado.clave
        );


        gestionClaveModoVer =
            false;

        gestionClaveEditandoId =
            String(
                claveId
            );

        gestionClaveReactivandoId =
            null;


        establecerModoLecturaGestionClave(
            false
        );


        const btnGuardar =
            document.getElementById(
                "btnGuardarGestionClave"
            );

        const btnCancelar =
            document.getElementById(
                "btnCancelarGestionClave"
            );


        if(btnGuardar){

            btnGuardar.textContent =
                "Modificar";

        }


        if(btnCancelar){

            btnCancelar.style.display =
                "inline-flex";

        }


        const inputContrasena =
            document.getElementById(
                "contrasenaGestionClave"
            );

        if(inputContrasena){

            inputContrasena.type =
                "password";

        }


        const btnVerContrasena =
            document.getElementById(
                "btnVerContrasenaGestionClave"
            );

        if(btnVerContrasena){

            btnVerContrasena.textContent =
                "Ver";

        }


        const inputNombre =
            document.getElementById(
                "nombreGestionClave"
            );

        if(inputNombre){

            inputNombre.focus();
            inputNombre.select();

        }

    }catch(error){

        console.error(
            "Error cargando credencial para modificar:",
            error
        );

        alert(
            "Ocurrió un error al cargar la credencial."
        );

    }

}


/* =========================================
   CARGAR DATOS
========================================= */

function cargarDatosGestionClave(
    clave
){

    const valores = {

        nombreGestionClave:
            clave.nombre,

        sitioGestionClave:
            clave.sitio,

        usuarioGestionClave:
            clave.usuario,

        correoGestionClave:
            clave.correo,

        contrasenaGestionClave:
            clave.contrasena,

        referencia1GestionClave:
            clave.referencia_recuperacion_1,

        referencia2GestionClave:
            clave.referencia_recuperacion_2,

        observacionesGestionClave:
            clave.observaciones

    };


    Object.entries(
        valores
    ).forEach(
        function(
            [id, valor]
        ){

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


    const inputContrasena =
        document.getElementById(
            "contrasenaGestionClave"
        );

    const btnVer =
        document.getElementById(
            "btnVerContrasenaGestionClave"
        );


    if(inputContrasena){

        inputContrasena.type =
            "password";

    }


    if(btnVer){

        btnVer.textContent =
            "Ver";

    }

}


/* =========================================
   MODO VER
========================================= */

function establecerModoLecturaGestionClave(
    soloLectura
){

    const campos = [

        "nombreGestionClave",
        "sitioGestionClave",
        "usuarioGestionClave",
        "correoGestionClave",
        "contrasenaGestionClave",
        "referencia1GestionClave",
        "referencia2GestionClave",
        "observacionesGestionClave"

    ];


    campos.forEach(
        function(id){

            const elemento =
                document.getElementById(
                    id
                );

            if(elemento){

                elemento.readOnly =
                    soloLectura;

            }

        }
    );


    const btnGuardar =
        document.getElementById(
            "btnGuardarGestionClave"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarGestionClave"
        );


    if(btnGuardar){

        btnGuardar.style.display =
            soloLectura
                ? "none"
                : "block";

    }


    if(btnCancelar){

        btnCancelar.style.display =
            soloLectura
                ? "inline-flex"
                : (
                    gestionClaveEditandoId !== null ||
                    gestionClaveReactivandoId !== null

                        ? "inline-flex"
                        : "none"
                );

        if(soloLectura){

            btnCancelar.textContent =
                "Cerrar";

        }else{

            btnCancelar.textContent =
                "Cancelar";

        }

    }

}


/* =========================================
   CANCELAR / LIMPIAR
========================================= */

function cancelarGestionClave(){

    gestionClaveEditandoId =
        null;

    gestionClaveReactivandoId =
        null;

    gestionClaveModoVer =
        false;

    limpiarFormularioGestionClave();

}


function limpiarFormularioGestionClave(){

    const campos = [

        "nombreGestionClave",
        "sitioGestionClave",
        "usuarioGestionClave",
        "correoGestionClave",
        "contrasenaGestionClave",
        "referencia1GestionClave",
        "referencia2GestionClave",
        "observacionesGestionClave"

    ];


    campos.forEach(
        function(id){

            const elemento =
                document.getElementById(
                    id
                );

            if(elemento){

                elemento.value =
                    "";

                elemento.readOnly =
                    false;

            }

        }
    );


    const inputContrasena =
        document.getElementById(
            "contrasenaGestionClave"
        );

    if(inputContrasena){

        inputContrasena.type =
            "password";

    }


    const btnVer =
        document.getElementById(
            "btnVerContrasenaGestionClave"
        );

    if(btnVer){

        btnVer.textContent =
            "Ver";

    }


    const btnGuardar =
        document.getElementById(
            "btnGuardarGestionClave"
        );

    if(btnGuardar){

        btnGuardar.textContent =
            "Guardar";

        btnGuardar.style.display =
            "block";

    }


    const btnCancelar =
        document.getElementById(
            "btnCancelarGestionClave"
        );

    if(btnCancelar){

        btnCancelar.textContent =
            "Cancelar";

        btnCancelar.style.display =
            "none";

    }

}


/* =========================================
   ELIMINAR
========================================= */

async function eliminarGestionClave(
    claveId
){

    if(
        !confirm(
            "¿Desea eliminar esta credencial?"
        )
    ){

        return;

    }


    const empresa =
        obtenerEmpresaGestionClave();

    const formulario =
        new FormData();

    formulario.append(
        "empresa",
        empresa
    );

    formulario.append(
        "clave",
        claveId
    );


    try{

        const respuesta =
            await fetch(
                "/gestion-claves/eliminar/",
                {
                    method: "POST",

                    headers: {
                        "X-CSRFToken":
                            obtenerCookieGestionClave(
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
                "No fue posible eliminar la credencial."
            );

            return;

        }


        await mostrarABMGestionClaves();

    }catch(error){

        console.error(
            "Error eliminando credencial:",
            error
        );

        alert(
            "Ocurrió un error al eliminar la credencial."
        );

    }

}


/* =========================================
   CONTRASEÑA
========================================= */

function alternarVisibilidadContrasena(){

    const input =
        document.getElementById(
            "contrasenaGestionClave"
        );

    const boton =
        document.getElementById(
            "btnVerContrasenaGestionClave"
        );


    if(
        !input ||
        !boton
    ){

        return;

    }


    if(
        input.type === "password"
    ){

        input.type =
            "text";

        boton.textContent =
            "Ocultar";

    }else{

        input.type =
            "password";

        boton.textContent =
            "Ver";

    }

}


async function copiarContrasenaGestionClave(){

    const input =
        document.getElementById(
            "contrasenaGestionClave"
        );

    const boton =
        document.getElementById(
            "btnCopiarContrasenaGestionClave"
        );


    if(
        !input ||
        !input.value
    ){

        return;

    }


    try{

        await navigator.clipboard.writeText(
            input.value
        );


        if(boton){

            const textoAnterior =
                boton.textContent;

            boton.textContent =
                "Copiado ✓";

            window.setTimeout(
                function(){

                    boton.textContent =
                        textoAnterior;

                },
                1500
            );

        }

    }catch(error){

        console.error(
            "No se pudo copiar la contraseña:",
            error
        );

        alert(
            "No fue posible copiar la contraseña al portapapeles."
        );

    }

}


/* =========================================
   VOLVER
========================================= */

function volverDesdeGestionClaves(){

    gestionClaveEditandoId =
        null;

    gestionClaveReactivandoId =
        null;

    gestionClaveModoVer =
        false;

    mostrarSubmenu(
        "herramientas"
    );

}