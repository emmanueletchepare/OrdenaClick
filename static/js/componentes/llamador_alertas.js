/*
 * =========================================
 * LLAMADOR DE ALERTAS
 * =========================================
 *
 * Consulta al backend si existen Alertas
 * para la empresa activa y, en ese caso,
 * muestra el llamador flotante.
 *
 * El llamador realiza una primera llamada
 * luego de una breve espera y repite el aviso
 * mientras el usuario no lo haya abierto.
 */

const DEMORA_INICIAL_LLAMADOR_ALERTAS = 18000;

const INTERVALO_RECORDATORIO_LLAMADOR_ALERTAS =
    180000;

let temporizadorInicialLlamadorAlertas = null;

let temporizadorRecordatorioLlamadorAlertas =
    null;

let llamadorAlertasAbierto = false;

let audioLlamadorAlertas = null;


/**
 * Obtiene el identificador de la empresa
 * actualmente activa en el panel.
 *
 * @returns {string}
 */
function obtenerEmpresaActivaLlamador(){

    const empresaActiva =
        document.getElementById(
            "empresaActiva"
        );


    if(!empresaActiva){

        return "";

    }


    return (
        empresaActiva.value || ""
    ).trim();

}


/**
 * Prepara el sonido breve utilizado por
 * el llamador.
 *
 * Se genera mediante Web Audio API para
 * evitar depender de un archivo de audio.
 */
function prepararAudioLlamadorAlertas(){

    if(audioLlamadorAlertas){

        return audioLlamadorAlertas;

    }


    const AudioContext =
        window.AudioContext ||
        window.webkitAudioContext;


    if(!AudioContext){

        return null;

    }


    audioLlamadorAlertas =
        new AudioContext();


    return audioLlamadorAlertas;

}


/**
 * Reproduce un sonido breve de campana.
 *
 * Algunos navegadores pueden impedir el
 * primer sonido si todavía no existió una
 * interacción del usuario con la página.
 */
function reproducirSonidoLlamadorAlertas(){

    const contexto =
        prepararAudioLlamadorAlertas();


    if(!contexto){

        return;

    }


    if(contexto.state === "suspended"){

        contexto.resume()
            .then(
                function(){

                    emitirSonidoLlamadorAlertas(
                        contexto
                    );

                }
            )
            .catch(
                function(){

                    /*
                     * El navegador todavía no
                     * autorizó audio automático.
                     */
                }
            );

        return;

    }


    emitirSonidoLlamadorAlertas(
        contexto
    );

}


/**
 * Genera dos tonos breves para simular
 * una pequeña campana de notificación.
 *
 * @param {AudioContext} contexto
 */
function emitirSonidoLlamadorAlertas(
    contexto
){

    const ahora =
        contexto.currentTime;


    const frecuencias = [
        880,
        1174
    ];


    frecuencias.forEach(
        function(
            frecuencia,
            indice
        ){

            const oscilador =
                contexto.createOscillator();

            const ganancia =
                contexto.createGain();


            oscilador.type =
                "sine";

            oscilador.frequency.value =
                frecuencia;


            const inicio =
                ahora +
                (
                    indice * .10
                );


            ganancia.gain.setValueAtTime(
                0,
                inicio
            );

            ganancia.gain.linearRampToValueAtTime(
                .10,
                inicio + .015
            );

            ganancia.gain.exponentialRampToValueAtTime(
                .001,
                inicio + .32
            );


            oscilador.connect(
                ganancia
            );

            ganancia.connect(
                contexto.destination
            );


            oscilador.start(
                inicio
            );

            oscilador.stop(
                inicio + .34
            );

        }
    );

}


/**
 * Reinicia la animación visual del llamador
 * para que pueda volver a llamar la atención.
 */
function animarLlamadorAlertas(){

    const llamador =
        document.getElementById(
            "llamadorAlertas"
        );


    if(
        !llamador ||
        llamadorAlertasAbierto
    ){

        return;

    }


    llamador.classList.remove(
        "visible"
    );


    void llamador.offsetWidth;


    llamador.classList.add(
        "visible"
    );

}


/**
 * Ejecuta una llamada de atención completa:
 * animación y sonido.
 */
function llamarAtencionAlertas(){

    if(llamadorAlertasAbierto){

        return;

    }


    animarLlamadorAlertas();

    reproducirSonidoLlamadorAlertas();

}


/**
 * Inicia los recordatorios periódicos mientras
 * el usuario no haya abierto Alertas.
 */
function iniciarRecordatoriosLlamadorAlertas(){

    detenerRecordatoriosLlamadorAlertas();


    temporizadorRecordatorioLlamadorAlertas =
        setInterval(
            function(){

                if(llamadorAlertasAbierto){

                    detenerRecordatoriosLlamadorAlertas();

                    return;

                }


                llamarAtencionAlertas();

            },
            INTERVALO_RECORDATORIO_LLAMADOR_ALERTAS
        );

}


/**
 * Detiene los recordatorios periódicos.
 */
function detenerRecordatoriosLlamadorAlertas(){

    if(
        temporizadorRecordatorioLlamadorAlertas
    ){

        clearInterval(
            temporizadorRecordatorioLlamadorAlertas
        );

        temporizadorRecordatorioLlamadorAlertas =
            null;

    }

}


/**
 * Consulta al backend si corresponde
 * mostrar el llamador de Alertas.
 */
async function consultarEstadoLlamadorAlertas(){

    const empresaId =
        obtenerEmpresaActivaLlamador();


    if(
        !empresaId ||
        llamadorAlertasAbierto
    ){

        return;

    }


    try{

        const respuesta =
            await fetch(
                (
                    "/alertas/llamador/" +
                    "?empresa=" +
                    encodeURIComponent(
                        empresaId
                    )
                ),
                {
                    method:"GET",
                    credentials:"same-origin",
                }
            );


        if(!respuesta.ok){

            return;

        }


        const datos =
            await respuesta.json();


        if(
            datos.ok === true &&
            datos.mostrar_llamador === true
        ){

            mostrarLlamadorAlertas();

            llamarAtencionAlertas();

            iniciarRecordatoriosLlamadorAlertas();

        }

    }
    catch(error){

        console.error(
            "Error consultando llamador de Alertas:",
            error
        );

    }

}


/**
 * Hace visible el llamador de Alertas.
 */
function mostrarLlamadorAlertas(){

    const llamador =
        document.getElementById(
            "llamadorAlertas"
        );


    if(!llamador){

        return;

    }


    llamador.classList.add(
        "visible"
    );

}


/**
 * Oculta el llamador y detiene sus avisos.
 */
function cerrarLlamadorAlertas(){

    llamadorAlertasAbierto =
        true;


    if(
        temporizadorInicialLlamadorAlertas
    ){

        clearTimeout(
            temporizadorInicialLlamadorAlertas
        );

        temporizadorInicialLlamadorAlertas =
            null;

    }


    detenerRecordatoriosLlamadorAlertas();


    const llamador =
        document.getElementById(
            "llamadorAlertas"
        );


    if(llamador){

        llamador.classList.remove(
            "visible"
        );

    }

}


/**
 * Abre Próximos Vencimientos en Alertas
 * utilizando la navegación ya existente.
 */
function abrirAlertasDesdeLlamador(){

    cerrarLlamadorAlertas();


    const botonProximos =
        document.getElementById(
            "btnProximosVencimientos"
        );


    if(botonProximos){

        botonProximos.click();

        return;

    }


    if(
        typeof mostrarProximosVencimientos ===
        "function"
    ){

        mostrarProximosVencimientos();

    }

}


/**
 * Conecta el click del llamador.
 */
function conectarLlamadorAlertas(){

    const llamador =
        document.getElementById(
            "llamadorAlertas"
        );


    if(!llamador){

        return;

    }


    llamador.addEventListener(
        "click",
        abrirAlertasDesdeLlamador
    );

}


/**
 * Inicia la espera previa a consultar
 * si corresponde mostrar el llamador.
 */
function iniciarLlamadorAlertas(){

    const empresaId =
        obtenerEmpresaActivaLlamador();


    if(!empresaId){

        return;

    }


    conectarLlamadorAlertas();


    temporizadorInicialLlamadorAlertas =
        setTimeout(
            consultarEstadoLlamadorAlertas,
            DEMORA_INICIAL_LLAMADOR_ALERTAS
        );

}


document.addEventListener(
    "DOMContentLoaded",
    iniciarLlamadorAlertas
);