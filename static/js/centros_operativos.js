let ultimoCentroOperativoCreado = null;

function iniciarABMCentrosOperativos(){

    const btnGuardar =
        document.getElementById(
            "btnGuardarCentroOperativo"
        );

    if(btnGuardar){

        btnGuardar.addEventListener(
            "click",
            guardarCentroOperativo
        );

    }

    const btnVolver =
        document.getElementById(
            "btnVolverCentroOperativo"
        );

    if(btnVolver){

        btnVolver.addEventListener(
            "click",
            volverDesdeABMCentrosOperativos
        );

    }

}


async function guardarCentroOperativo(){

    const inputNombre =
        document.getElementById(
            "nuevoCentroOperativo"
        );

    const selectTipo =
        document.getElementById(
            "tipoCentroOperativo"
        );

    const inputDireccion =
        document.getElementById(
            "direccionCentroOperativo"
        );

    const empresa =
        document.getElementById(
            "empresaActiva"
        ).value;

    const nombre =
        inputNombre.value.trim();

    const tipo =
        selectTipo.value;

    const direccion =
        inputDireccion.value.trim();

    if(!nombre){

        alert(
            "Ingrese el nombre del centro operativo."
        );

        inputNombre.focus();

        return;

    }

    if(!tipo){

        alert(
            "Seleccione el tipo de centro operativo."
        );

        selectTipo.focus();

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
        "tipo",
        tipo
    );

    formulario.append(
        "direccion",
        direccion
    );

    const respuesta = await fetch(
        "/guardar-centro-operativo/",
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
            "No se pudo guardar el centro operativo."
        );

        return;

    }

    ultimoCentroOperativoCreado =
        resultado.centro
            ? String(resultado.centro.id)
            : null;

    await mostrarABMCentrosOperativos(
        origenABM
    );

}

async function modificarCentroOperativo(
    centroId,
    nombreActual,
    tipoActual,
    direccionActual
){

    const nuevoNombre = prompt(
        "Nuevo nombre del centro operativo:",
        nombreActual
    );

    if(nuevoNombre === null){
        return;
    }

    const nombre =
        nuevoNombre.trim();

    if(!nombre){

        alert(
            "Ingrese el nombre del centro operativo."
        );

        return;
    }

    const nuevoTipo = prompt(
        "Tipo: Casa Central, Sucursal, Deposito o Mostrador",
        tipoActual
    );

    if(nuevoTipo === null){
        return;
    }

    const tipo =
        nuevoTipo.trim();

    const tiposValidos = [
        "Casa Central",
        "Sucursal",
        "Deposito",
        "Mostrador"
    ];

    if(!tiposValidos.includes(tipo)){

        alert(
            "El tipo debe ser Casa Central, Sucursal, Deposito o Mostrador."
        );

        return;
    }

    const nuevaDireccion = prompt(
        "Nueva dirección:",
        direccionActual || ""
    );

    if(nuevaDireccion === null){
        return;
    }

    const empresa =
        document.getElementById(
            "empresaActiva"
        ).value;

    const formulario =
        new FormData();

    formulario.append(
        "centro",
        centroId
    );

    formulario.append(
        "empresa",
        empresa
    );

    formulario.append(
        "nombre",
        nombre
    );

    formulario.append(
        "tipo",
        tipo
    );

    formulario.append(
        "direccion",
        nuevaDireccion.trim()
    );

    try{

        const respuesta = await fetch(
            "/modificar-centro-operativo/",
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
                "No se pudo modificar el centro operativo."
            );

            return;
        }

        await mostrarABMCentrosOperativos(
            origenABM
        );

    }catch(error){

        console.error(
            "Error modificando centro operativo:",
            error
        );

        alert(
            "Ocurrió un error al modificar el centro operativo."
        );

    }

}


async function eliminarCentroOperativo(
    centroId,
    nombreCentro
){

    const confirmado = confirm(
        `¿Eliminar el centro operativo "${nombreCentro}"?\n\n` +
        "La empresa debe conservar al menos un centro operativo activo."
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
        "centro",
        centroId
    );

    formulario.append(
        "empresa",
        empresa
    );

    try{

        const respuesta = await fetch(
            "/eliminar-centro-operativo/",
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
                "No se pudo eliminar el centro operativo."
            );

            return;
        }

        await mostrarABMCentrosOperativos(
            origenABM
        );

    }catch(error){

        console.error(
            "Error eliminando centro operativo:",
            error
        );

        alert(
            "Ocurrió un error al eliminar el centro operativo."
        );

    }

}