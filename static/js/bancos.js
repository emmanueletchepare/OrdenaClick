function iniciarABMBancos(){

    const btnGuardar =
        document.getElementById("btnGuardarBanco");

    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarBanco
        );

    }

    const btnVolver =
        document.getElementById("btnVolverBanco");

    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeABMBancos
        );

    }

}

async function guardarBanco(){

    const input =
        document.getElementById("nuevoBanco");

    const empresa =
        document.getElementById("empresaActiva").value;

    const nombre =
        input.value.trim();

    if(!nombre){

        alert("Ingrese el nombre del banco.");

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

    const respuesta = await fetch(
        "/guardar-banco/",
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

    if(!resultado.ok){

        alert(
            resultado.mensaje ||
            "No se pudo guardar el banco."
        );

        return;

    }

    await mostrarABMBancos(
        origenABM
    );

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

async function modificarBanco(
    bancoId,
    nombreActual
){

    const nuevoNombre = prompt(
        "Nuevo nombre del banco:",
        nombreActual
    );

    if(nuevoNombre === null){
        return;
    }

    const nombre =
        nuevoNombre.trim();

    if(!nombre){

        alert(
            "Ingrese el nombre del banco."
        );

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

    formulario.append(
        "nombre",
        nombre
    );

    try{

        const respuesta = await fetch(
            "/modificar-banco/",
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
                "No se pudo modificar el banco."
            );

            return;
        }

        await mostrarABMBancos(
            origenABM
        );

    }catch(error){

        console.error(
            "Error modificando banco:",
            error
        );

        alert(
            "Ocurrió un error al modificar el banco."
        );

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