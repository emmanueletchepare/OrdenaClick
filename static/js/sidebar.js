/*
 * =========================================
 * SIDEBAR
 * =========================================
 *
 * Mantiene resaltada la sección principal
 * desde la que el usuario inició su recorrido.
 *
 * La navegación interna y los ABMs abiertos
 * desde botones [+] no modifican este origen.
 */


document.addEventListener(
    "DOMContentLoaded",
    function(){

        const botonesSidebar =
            document.querySelectorAll(
                "[data-sidebar-item]"
            );

        botonesSidebar.forEach(
            function(boton){

                boton.addEventListener(
                    "click",
                    function(){

                        marcarSidebarActivo(
                            boton
                        );

                    }
                );

            }
        );

    }
);


/**
 * Marca un único botón principal del sidebar
 * como origen activo de navegación.
 *
 * @param {HTMLElement} botonActivo
 */
function marcarSidebarActivo(
    botonActivo
){

    const botonesSidebar =
        document.querySelectorAll(
            "[data-sidebar-item]"
        );

    botonesSidebar.forEach(
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