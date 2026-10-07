let bancoEditandoId = null;


function iniciarABMBancos(){

    const btnGuardar =
        document.getElementById(
            "btnGuardarBanco"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarBanco"
        );

    const btnVolver =
        document.getElementById(
            "btnVolverBanco"
        );

    const buscador =
        document.getElementById(
            "buscarBancoABM"
        );


    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarBanco
        );

    }


    if(btnCancelar){

        btnCancelar.addEventListener(
            "click",
            cancelarEdicionBanco
        );

    }


    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeABMBancos
        );

    }


    if(buscador){

        buscador.addEventListener(
            "input",
            filtrarBancosABM
        );

    }

}

function filtrarBancosABM(){

    const buscador =
        document.getElementById(
            "buscarBancoABM"
        );

    const mensajeSinResultados =
        document.getElementById(
            "sinResultadosBancoABM"
        );


    const texto =
        buscador
            ? buscador.value
                .trim()
                .toLowerCase()
            : "";


    const tarjetas =
        document.querySelectorAll(
            ".tarjeta-banco-abm"
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

async function guardarBanco(){

    const input =
        document.getElementById(
            "nuevoBanco"
        );

    const empresa =
        document.getElementById(
            "empresaActiva"
        ).value;

    const nombre =
        input.value.trim();


    if(!nombre){

        alert(
            "Ingrese el nombre del banco."
        );

        input.focus();

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


    let url =
        "/guardar-banco/";


    const estaEditando =
        Boolean(
            bancoEditandoId
        );


    if(estaEditando){

        url =
            "/modificar-banco/";


        formulario.append(
            "banco",
            bancoEditandoId
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
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                (
                    estaEditando
                        ? "No se pudo modificar el banco."
                        : "No se pudo guardar el banco."
                )
            );

            return;

        }


        /*
         * Si fue un alta nueva guardamos cuál fue
         * el Banco recién creado.
         */
        if(
            !estaEditando &&
            resultado.banco &&
            resultado.banco.id
        ){

            ultimoBancoCreado = {

                id:
                    String(
                        resultado.banco.id
                    ),

                nombre:
                    resultado.banco.nombre

            };

        }


        const origenActual =
            origenABM;


        bancoEditandoId =
            null;


        /*
         * Si Bancos fue abierto desde Cuentas Bancarias
         * para resolver una dependencia, al crear el Banco
         * volvemos automáticamente.
         *
         * volverDesdeABMBancos() restaurará el formulario
         * de Cuenta Bancaria y actualizará su select.
         */
        if(
            origenActual === "cuenta_bancaria" &&
            ultimoBancoCreado
        ){

            await volverDesdeABMBancos();

            return;

        }


        /*
         * En el resto de los casos mantenemos
         * el comportamiento normal del ABM.
         */
        await mostrarABMBancos(
            origenActual
        );


    }catch(error){

        console.error(
            "Error guardando banco:",
            error
        );


        alert(
            estaEditando
                ? "Ocurrió un error al modificar el banco."
                : "Ocurrió un error al guardar el banco."
        );

    }

}


function modificarBanco(
    bancoId,
    nombreActual
){

    bancoEditandoId =
        String(bancoId);

    const input =
        document.getElementById(
            "nuevoBanco"
        );

    const btnGuardar =
        document.getElementById(
            "btnGuardarBanco"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarBanco"
        );

    if(input){

        input.value =
            nombreActual;

        input.focus();

        input.select();

    }

    if(btnGuardar){

        btnGuardar.textContent =
            "Actualizar";

    }

    if(btnCancelar){

        btnCancelar.style.display =
            "inline-block";

    }

}


function cancelarEdicionBanco(){

    bancoEditandoId = null;

    const input =
        document.getElementById(
            "nuevoBanco"
        );

    const btnGuardar =
        document.getElementById(
            "btnGuardarBanco"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarBanco"
        );

    if(input){

        input.value = "";

        input.focus();

    }

    if(btnGuardar){

        btnGuardar.textContent =
            "Guardar";

    }

    if(btnCancelar){

        btnCancelar.style.display =
            "none";

    }

}


async function eliminarBanco(
    bancoId,
    nombreBanco
){

    const confirmado = confirm(
        `¿Eliminar el banco "${nombreBanco}"?`
    );

    if(!confirmado){
        return;
    }

    const empresa =
        document.getElementById(
            "empresaActiva"
        ).value;

    const formulario =
        new FormData();

    formulario.append(
        "banco",
        bancoId
    );

    formulario.append(
        "empresa",
        empresa
    );

    try{

        const respuesta = await fetch(
            "/eliminar-banco/",
            {
                method: "POST",

                headers: {
                    "X-CSRFToken": obtenerCookie(
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
                "No se pudo eliminar el banco."
            );

            return;

        }

        if(
            bancoEditandoId ===
            String(bancoId)
        ){

            bancoEditandoId = null;

        }

        await mostrarABMBancos(
            origenABM
        );

    }catch(error){

        console.error(
            "Error eliminando banco:",
            error
        );

        alert(
            "Ocurrió un error al eliminar el banco."
        );

    }

}


function obtenerCookie(nombre){

    const cookies =
        document.cookie
            ? document.cookie.split(";")
            : [];

    for(const cookieActual of cookies){

        const cookie =
            cookieActual.trim();

        if(
            cookie.startsWith(
                `${nombre}=`
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