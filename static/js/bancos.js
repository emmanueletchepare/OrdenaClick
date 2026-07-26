let bancoEditandoId = null;


function iniciarABMBancos(){

    const btnGuardar =
        document.getElementById(
            "btnGuardarBanco"
        );

    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarBanco
        );

    }

    const btnCancelar =
        document.getElementById(
            "btnCancelarBanco"
        );

    if(btnCancelar){

        btnCancelar.addEventListener(
            "click",
            cancelarEdicionBanco
        );

    }

    const btnVolver =
        document.getElementById(
            "btnVolverBanco"
        );

    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeABMBancos
        );

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

    if(bancoEditandoId){

        url =
            "/modificar-banco/";

        formulario.append(
            "banco",
            bancoEditandoId
        );

    }

    try{

        const respuesta = await fetch(
            url,
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
                (
                    bancoEditandoId
                        ? "No se pudo modificar el banco."
                        : "No se pudo guardar el banco."
                )
            );

            return;

        }

        bancoEditandoId = null;

        await mostrarABMBancos(
            origenABM
        );

    }catch(error){

        console.error(
            "Error guardando banco:",
            error
        );

        alert(
            bancoEditandoId
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