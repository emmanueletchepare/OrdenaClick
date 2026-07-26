let ultimoCentroOperativoCreado = null;
let centroOperativoEditandoId = null;


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

    const btnCancelar =
        document.getElementById(
            "btnCancelarCentroOperativo"
        );

    if(btnCancelar){

        btnCancelar.addEventListener(
            "click",
            cancelarEdicionCentroOperativo
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

    const inputEmpresa =
        document.getElementById(
            "empresaActiva"
        );

    if(
        !inputNombre ||
        !selectTipo ||
        !inputDireccion ||
        !inputEmpresa
    ){

        console.error(
            "No se encontraron todos los elementos del formulario de centros operativos."
        );

        return;

    }

    const empresa =
        inputEmpresa.value;

    const nombre =
        inputNombre.value.trim();

    const tipo =
        selectTipo.value;

    const direccion =
        inputDireccion.value.trim();

    if(!empresa){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }

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

    const estaEditando =
        centroOperativoEditandoId !== null;

    let url =
        "/guardar-centro-operativo/";

    if(estaEditando){

        url =
            "/modificar-centro-operativo/";

        formulario.append(
            "centro",
            centroOperativoEditandoId
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

        if(!respuesta.ok || !resultado.ok){

            alert(
                resultado.mensaje ||
                (
                    estaEditando
                        ? "No se pudo modificar el centro operativo."
                        : "No se pudo guardar el centro operativo."
                )
            );

            return;

        }

        if(!estaEditando){

            ultimoCentroOperativoCreado =
                resultado.centro
                    ? String(
                        resultado.centro.id
                    )
                    : null;

        }

        centroOperativoEditandoId = null;

        await mostrarABMCentrosOperativos(
            origenABM
        );

    }catch(error){

        console.error(
            "Error guardando centro operativo:",
            error
        );

        alert(
            estaEditando
                ? "Ocurrió un error al modificar el centro operativo."
                : "Ocurrió un error al guardar el centro operativo."
        );

    }

}


function modificarCentroOperativo(
    centroId,
    nombreActual,
    tipoActual,
    direccionActual
){

    centroOperativoEditandoId =
        String(centroId);

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

    const btnGuardar =
        document.getElementById(
            "btnGuardarCentroOperativo"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarCentroOperativo"
        );

    if(inputNombre){

        inputNombre.value =
            nombreActual || "";

    }

    if(selectTipo){

        selectTipo.value =
            tipoActual || "";

    }

    if(inputDireccion){

        inputDireccion.value =
            direccionActual || "";

    }

    if(btnGuardar){

        btnGuardar.textContent =
            "Actualizar";

    }

    if(btnCancelar){

        btnCancelar.style.display =
            "inline-block";

    }

    if(inputNombre){

        inputNombre.focus();
        inputNombre.select();

    }

}


function cancelarEdicionCentroOperativo(){

    centroOperativoEditandoId = null;

    limpiarFormularioCentroOperativo();

}


function limpiarFormularioCentroOperativo(){

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

    const btnGuardar =
        document.getElementById(
            "btnGuardarCentroOperativo"
        );

    const btnCancelar =
        document.getElementById(
            "btnCancelarCentroOperativo"
        );

    if(inputNombre){

        inputNombre.value = "";

    }

    if(selectTipo){

        selectTipo.value = "";

    }

    if(inputDireccion){

        inputDireccion.value = "";

    }

    if(btnGuardar){

        btnGuardar.textContent =
            "Guardar";

    }

    if(btnCancelar){

        btnCancelar.style.display =
            "none";

    }

    if(inputNombre){

        inputNombre.focus();

    }

}


async function eliminarCentroOperativo(
    centroId,
    nombreCentro
){

    const confirmado =
        confirm(
            `¿Eliminar el centro operativo "${nombreCentro}"?\n\n` +
            "La empresa debe conservar al menos un centro operativo activo."
        );

    if(!confirmado){

        return;

    }

    const inputEmpresa =
        document.getElementById(
            "empresaActiva"
        );

    if(!inputEmpresa || !inputEmpresa.value){

        alert(
            "No hay una empresa activa seleccionada."
        );

        return;

    }

    const formulario =
        new FormData();

    formulario.append(
        "centro",
        centroId
    );

    formulario.append(
        "empresa",
        inputEmpresa.value
    );

    try{

        const respuesta =
            await fetch(
                "/eliminar-centro-operativo/",
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

        if(!respuesta.ok || !resultado.ok){

            alert(
                resultado.mensaje ||
                "No se pudo eliminar el centro operativo."
            );

            return;

        }

        if(
            centroOperativoEditandoId ===
            String(centroId)
        ){

            centroOperativoEditandoId = null;

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