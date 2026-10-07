/**
 * Marca un único segmento como activo dentro de una
 * botonera de navegación segmentada.
 *
 * La búsqueda queda limitada a la botonera recibida
 * para evitar interferencias entre distintos módulos.
 */
function marcarSegmentoNavegacionActivo(
    botonera,
    botonActivo
){

    if(!botonera){
        return;
    }


    const botones =
        botonera.querySelectorAll(
            ".vencimientos-segmento"
        );


    botones.forEach(
        function(boton){

            boton.classList.remove(
                "activo"
            );

        }
    );


    if(botonActivo){

        botonActivo.classList.add(
            "activo"
        );

    }

}


/**
 * Actualiza la visibilidad y disponibilidad de las
 * flechas de una navegación segmentada.
 *
 * Las flechas aparecen cuando existen más de cuatro
 * segmentos o cuando la botonera tiene desbordamiento
 * horizontal real.
 */
function actualizarFlechasNavegacion(
    botonera,
    btnAnterior,
    btnSiguiente
){

    if(
        !botonera ||
        !btnAnterior ||
        !btnSiguiente
    ){
        return;
    }


    const botones =
        botonera.querySelectorAll(
            ".vencimientos-segmento"
        );


    const necesitaNavegacion =
        botones.length > 4 ||
        botonera.scrollWidth >
            botonera.clientWidth + 2;


    btnAnterior.classList.toggle(
        "visible",
        necesitaNavegacion
    );


    btnSiguiente.classList.toggle(
        "visible",
        necesitaNavegacion
    );


    if(!necesitaNavegacion){

        btnAnterior.disabled = true;
        btnSiguiente.disabled = true;

        return;

    }


    const maximoScroll =
        botonera.scrollWidth -
        botonera.clientWidth;


    btnAnterior.disabled =
        botonera.scrollLeft <= 2;


    btnSiguiente.disabled =
        botonera.scrollLeft >=
        maximoScroll - 2;

}


/**
 * Desplaza horizontalmente una botonera segmentada.
 */
function desplazarBotoneraNavegacion(
    botonera,
    direccion
){

    if(!botonera){
        return;
    }


    const desplazamiento =
        Math.max(
            180,
            botonera.clientWidth * 0.45
        );


    botonera.scrollBy({
        left:
            direccion *
            desplazamiento,
        behavior: "smooth"
    });

}


/**
 * Inicializa las flechas y el estado activo de la
 * navegación del módulo Registros.
 *
 * La botonera se genera dinámicamente desde
 * mostrarSubmenu(), por lo que esta función puede
 * ejecutarse varias veces sin conservar referencias
 * al DOM anterior.
 */
function inicializarNavegacionRegistros(){

    const botonera =
        document.getElementById(
            "botoneraRegistros"
        );

    const btnAnterior =
        document.getElementById(
            "btnRegistrosAnterior"
        );

    const btnSiguiente =
        document.getElementById(
            "btnRegistrosSiguiente"
        );


    if(
        !botonera ||
        !btnAnterior ||
        !btnSiguiente
    ){
        return;
    }


    btnAnterior.addEventListener(
        "click",
        function(){

            desplazarBotoneraNavegacion(
                botonera,
                -1
            );

        }
    );


    btnSiguiente.addEventListener(
        "click",
        function(){

            desplazarBotoneraNavegacion(
                botonera,
                1
            );

        }
    );


    botonera.addEventListener(
        "scroll",
        function(){

            actualizarFlechasNavegacion(
                botonera,
                btnAnterior,
                btnSiguiente
            );

        }
    );


    window.setTimeout(
        function(){

            actualizarFlechasNavegacion(
                botonera,
                btnAnterior,
                btnSiguiente
            );

        },
        0
    );

}

/**
 * Inicializa las flechas de la botonera de Estructura
 * Operativa dentro del menú general de ABMs.
 *
 * Cuando existen más de cuatro opciones, conserva cuatro
 * segmentos visibles y permite recorrer las restantes con
 * las mismas flechas utilizadas por Registros.
 */
function inicializarNavegacionEstructuraOperativa(){

    const botonera =
        document.getElementById(
            "botoneraEstructuraOperativa"
        );

    const btnAnterior =
        document.getElementById(
            "btnEstructuraOperativaAnterior"
        );

    const btnSiguiente =
        document.getElementById(
            "btnEstructuraOperativaSiguiente"
        );


    if(
        !botonera ||
        !btnAnterior ||
        !btnSiguiente
    ){

        return;

    }


    btnAnterior.addEventListener(
        "click",
        function(){

            desplazarBotoneraNavegacion(
                botonera,
                -1
            );

        }
    );


    btnSiguiente.addEventListener(
        "click",
        function(){

            desplazarBotoneraNavegacion(
                botonera,
                1
            );

        }
    );


    botonera.addEventListener(
        "scroll",
        function(){

            actualizarFlechasNavegacion(
                botonera,
                btnAnterior,
                btnSiguiente
            );

        }
    );


    window.setTimeout(
        function(){

            actualizarFlechasNavegacion(
                botonera,
                btnAnterior,
                btnSiguiente
            );

        },
        0
    );

}

/**
 * Atiende segmentos creados dinámicamente dentro del
 * módulo Registros.
 *
 * También detecta la apertura del menú Registros para
 * inicializar sus flechas después de que mostrarSubmenu()
 * haya construido la botonera.
 */
document.addEventListener(
    "click",
    function(event){

        const segmentoRegistro =
            event.target.closest(
                ".registros-botonera " +
                ".vencimientos-segmento"
            );


        if(segmentoRegistro){

            const botonera =
                segmentoRegistro.closest(
                    ".registros-botonera"
                );


            marcarSegmentoNavegacionActivo(
                botonera,
                segmentoRegistro
            );

        }


        const botonRegistros =
            event.target.closest(
                '[onclick*="mostrarSubmenu(\'registros\')"]'
            );


        if(!botonRegistros){
            return;
        }


        window.setTimeout(
            inicializarNavegacionRegistros,
            0
        );

    }
);

/**
 * Marca el ABM actualmente abierto dentro del menú
 * general de ABMs.
 *
 * El estado activo es único entre todos los grupos
 * para representar el módulo realmente visible.
 */
document.addEventListener(
    "click",
    function(event){

        const segmentoABM =
            event.target.closest(
                ".abms-grupos " +
                ".vencimientos-segmento"
            );


        if(!segmentoABM){
            return;
        }


        const contenedorABMs =
            segmentoABM.closest(
                ".abms-grupos"
            );


        if(!contenedorABMs){
            return;
        }


        const botones =
            contenedorABMs.querySelectorAll(
                ".vencimientos-segmento"
            );


        botones.forEach(
            function(boton){

                boton.classList.remove(
                    "activo"
                );

            }
        );


        segmentoABM.classList.add(
            "activo"
        );

    }
);