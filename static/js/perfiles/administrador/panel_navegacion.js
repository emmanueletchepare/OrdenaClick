function limpiarPanelOperativo(){

    const submenu =
    document.getElementById(
        "submenu-dinamico"
    );

    if(submenu){

        submenu.innerHTML = "";

    }

    const contenido =
    document.getElementById(
        "contenido-operativo"
    );

    if(contenido){

        contenido.innerHTML = "";

    }

}

function posicionarMainEnElemento(
    elemento,
    margenSuperior = 15
){

    if(!elemento){

        return;

    }


    const main =
        document.querySelector(
            ".main"
        );


    if(!main){

        return;

    }


    function posicionar(){

        const rectMain =
            main.getBoundingClientRect();


        const rectElemento =
            elemento.getBoundingClientRect();


        const destino =
            main.scrollTop +
            rectElemento.top -
            rectMain.top -
            margenSuperior;


        main.scrollTop =
            Math.max(
                0,
                destino
            );

    }


    /*
     * Primer posicionamiento:
     * después de restaurar el DOM.
     */

    requestAnimationFrame(
        function(){

            requestAnimationFrame(
                function(){

                    posicionar();


                    /*
                     * Segundo posicionamiento:
                     *
                     * Algunas reconstrucciones del formulario
                     * todavía modifican alturas después de los
                     * requestAnimationFrame.
                     *
                     * Este es el que deja la posición definitiva.
                     */

                    setTimeout(
                        function(){

                            posicionar();

                        },
                        80
                    );

                }
            );

        }
    );

}

function posicionarCargaSimpleEnCampo(
    campoId
){

    const campo =
        document.getElementById(
            campoId
        );


    if(!campo){

        return;

    }


    /*
     * Apuntamos al field completo para que
     * queden visibles:
     *
     * - la etiqueta;
     * - el select;
     * - el [+].
     */

    const field =
        campo.closest(
            ".field"
        );


    posicionarMainEnElemento(
        field || campo,
        15
    );

}

function mostrarAltaEmpresa(){

    limpiarPanelOperativo();

    const panelEmpresa =
    document.getElementById(
        "panel-empresa"
    );

    if(panelEmpresa){

        panelEmpresa.style.display = "none";

    }

    document.getElementById(
        "bloque-alta-empresa"
    ).style.display = "block";

    const form =
    document.getElementById("form-alta");

    const contenido =
    document.getElementById("contenido");

    const titulo =
    document.getElementById("titulo-panel");

    titulo.innerHTML =
    'Alta nueva <span>empresa</span>';

    if(contenido){

        contenido.style.display = "none";

    }

    if(form){

        form.style.display = "block";

    }

    document.getElementById(
        "botonera-alta"
    ).style.display = "flex";

    document.getElementById(
        "botonera-modificar"
    ).style.display = "none";
}

function mostrarEmpresas(){

    console.log("1");

    limpiarPanelOperativo();

    console.log("2");

    const bloqueAlta =
    document.getElementById(
        "bloque-alta-empresa"
    );

    console.log("3", bloqueAlta);

    if(bloqueAlta){

        bloqueAlta.style.display = "none";

    }

    console.log("4");

    const panelEmpresa =
    document.getElementById(
        "panel-empresa"
    );

    console.log("5", panelEmpresa);

    if(panelEmpresa){

        panelEmpresa.style.display = "block";

    }

    console.log("6");

    const menuPrincipal =
    document.getElementById(
        "menu-principal"
    );

    console.log("7", menuPrincipal);

    if(menuPrincipal){

        menuPrincipal.style.display = "none";

    }

    console.log("8");

    const menuEmpresa =
    document.getElementById(
        "menu-empresa"
    );

    if(menuEmpresa){

        menuEmpresa.style.display = "none";

    }

    const menuEmpresas =
    document.getElementById(
        "menu-empresas"
    );

    console.log("9", menuEmpresas);

    if(menuEmpresas){

        menuEmpresas.style.display = "flex";

    }

    console.log("10");
}

function volverMenuPrincipal(){

    limpiarPanelOperativo();

    const menuPrincipal =
    document.getElementById(
        "menu-principal"
    );

    if(menuPrincipal){

        menuPrincipal.style.display = "none";

    }

    document.getElementById(
        "menu-empresas"
    ).style.display = "none";
}

function mostrarNombreArchivo(input,id){

    if(input.files.length > 0){

        document.getElementById(id).innerText =
        input.files[0].name;

    }

}

function mostrarContenido(titulo){

    const bloqueAlta =
    document.getElementById(
        "bloque-alta-empresa"
    );

    if(bloqueAlta){

        bloqueAlta.style.display = "none";

    }

    document.getElementById(
        "submenu-dinamico"
    ).innerHTML = "";

    document.getElementById(
        "contenido-operativo"
    ).innerHTML = `
        <div class="empty-state">
            ${titulo} en desarrollo
        </div>
    `;
}

function mostrarSubmenu(tipo){

    const bloqueAlta =
        document.getElementById(
            "bloque-alta-empresa"
        );


    if(bloqueAlta){

        bloqueAlta.style.display =
            "none";

    }

    /*
     * Cada entrada desde el menú lateral vuelve al estado base
     * de la Empresa. Las subpantallas pueden ocultar/modificar
     * esta cabecera después, pero nunca dejan residuos al salir.
     */
    if(typeof window.restaurarCabeceraEmpresa === "function"){
        window.restaurarCabeceraEmpresa();
    }


    let html =
        "";


    /*
     * =========================================
     * REGISTROS
     * =========================================
     */

    if(tipo === "registros"){

        html = `

            <div
                class="
                    vencimientos-navegacion
                    registros-navegacion
                "
            >

                <button
                    type="button"
                    class="
                        vencimientos-flecha
                        vencimientos-flecha-izquierda
                    "
                    id="btnRegistrosAnterior"
                    aria-label="Opciones anteriores"
                    title="Opciones anteriores"
                >
                    ❮
                </button>

                <div
                    class="
                        vencimientos-botonera
                        registros-botonera
                    "
                    id="botoneraRegistros"
                >

                    <button
                        type="button"
                        class="vencimientos-segmento"
                        id="btnRegistrosComprobantes"
                        onclick="mostrarCargaSimple()"
                    >
                        Comprobantes
                    </button>

                    <button
                        type="button"
                        class="vencimientos-segmento"
                        id="btn-obligaciones"
                    >
                        Obligaciones
                    </button>

                    <button
                        type="button"
                        class="vencimientos-segmento"
                    >
                        Carga Planificada
                    </button>

                    <button
                        type="button"
                        class="vencimientos-segmento"
                    >
                        Registrar Pago
                    </button>

                    <button
                        type="button"
                        class="vencimientos-segmento"
                    >
                        Modificar / Eliminar
                    </button>

                </div>

                <button
                    type="button"
                    class="
                        vencimientos-flecha
                        vencimientos-flecha-derecha
                    "
                    id="btnRegistrosSiguiente"
                    aria-label="Opciones siguientes"
                    title="Opciones siguientes"
                >
                    ❯
                </button>

            </div>

        `;

    }


    /*
     * =========================================
     * ABMs
     * =========================================
     */

    if(tipo === "abms"){

        html = `

            <div class="abms-grupos">


                <!-- =================================
                    ESTRUCTURA OPERATIVA
                ================================== -->

                <section class="abms-grupo">

                    <div class="abms-grupo-titulo">
                        Estructura operativa
                    </div>

                    <div
                        class="
                            vencimientos-navegacion
                            abms-navegacion
                        "
                    >

                        <button
                            type="button"
                            class="
                                vencimientos-flecha
                                vencimientos-flecha-izquierda
                            "
                            id="btnEstructuraOperativaAnterior"
                            aria-label="Opciones anteriores"
                            title="Opciones anteriores"
                        >
                            ❮
                        </button>

                        <div
                            class="
                                vencimientos-botonera
                                abms-botonera
                            "
                            id="botoneraEstructuraOperativa"
                        >

                            <button
                                type="button"
                                class="vencimientos-segmento"
                                onclick="
                                    mostrarABMCentrosOperativos(
                                        'menu'
                                    )
                                "
                            >
                                Centros Operativos
                            </button>


                            <button
                                type="button"
                                class="vencimientos-segmento"
                                onclick="
                                    mostrarABMRecursosOperativos(
                                        'menu'
                                    )
                                "
                            >
                                Recurso operativo
                            </button>


                            <button
                                type="button"
                                class="vencimientos-segmento"
                                onclick="
                                    mostrarABMProveedores(
                                        'menu'
                                    )
                                "
                            >
                                Proveedores
                            </button>


                            <button
                                type="button"
                                class="vencimientos-segmento"
                                onclick="
                                    mostrarABMTiposGasto(
                                        'menu'
                                    )
                                "
                            >
                                Tipos de gasto
                            </button>


                            <button
                                type="button"
                                class="vencimientos-segmento"
                                onclick="
                                    mostrarABMClientes(
                                        'menu'
                                    )
                                "
                            >
                                Clientes
                            </button>

                        </div>

                        <button
                            type="button"
                            class="
                                vencimientos-flecha
                                vencimientos-flecha-derecha
                            "
                            id="btnEstructuraOperativaSiguiente"
                            aria-label="Opciones siguientes"
                            title="Opciones siguientes"
                        >
                            ❯
                        </button>

                    </div>

                </section>



                <!-- =================================
                     FINANZAS Y MEDIOS DE PAGO
                ================================== -->

                <section class="abms-grupo">

                    <div class="abms-grupo-titulo">
                        Finanzas y medios de pago
                    </div>

                    <div
                        class="
                            vencimientos-navegacion
                            abms-navegacion
                        "
                    >

                        <div
                            class="
                                vencimientos-botonera
                                abms-botonera
                            "
                        >

                            <button
                                type="button"
                                class="vencimientos-segmento"
                                onclick="
                                    mostrarABMBancos(
                                        'menu'
                                    )
                                "
                            >
                                Bancos
                            </button>


                            <button
                                type="button"
                                class="vencimientos-segmento"
                                onclick="
                                    mostrarABMCuentasBancarias(
                                        'menu'
                                    )
                                "
                            >
                                Cuentas Bancarias
                            </button>


                            <button
                                type="button"
                                class="vencimientos-segmento"
                                onclick="
                                    mostrarABMTarjetas(
                                        'menu'
                                    )
                                "
                            >
                                Tarjetas
                            </button>


                            <button
                                id="btnAbrirABMRetenciones"
                                type="button"
                                class="vencimientos-segmento"
                            >
                                Retenciones
                            </button>

                        </div>

                    </div>

                </section>

            </div>

        `;

    }


    /*
     * =========================================
     * HERRAMIENTAS
     * =========================================
     */

    if(tipo === "herramientas"){

        html = `

            <button
                class="module-card"
                onclick="mostrarABMGestionClaves()"
            >
                Gestión de claves
            </button>

        `;

    }


    /*
     * =========================================
     * CONFIGURACIÓN
     * =========================================
     */

    if(tipo === "configuracion"){

        html = `

            <button
                class="module-card"
                onclick="mostrarModificarEmpresa()"
            >
                Modificar Empresa
            </button>


            <button
                type="button"
                class="module-card"
                id="btn-designar-perfiles"
                data-designar-perfiles-url="${document.getElementById('panel-empresa')?.dataset.designarPerfilesUrl || ''}"
            >
                Designar perfiles
            </button>

        `;

    }


    const submenu =
        document.getElementById(
            "submenu-dinamico"
        );


    const contenido =
        document.getElementById(
            "contenido-operativo"
        );


    if(submenu){

        submenu.innerHTML =
            html;

    }


    if(tipo === "abms"){

        inicializarNavegacionEstructuraOperativa();

    }


    if(contenido){

        contenido.innerHTML = "";

    }


    /*
     * =========================================
     * EVENTOS DEL SUBMENÚ
     * =========================================
     *
     * Retenciones se incorpora sin agregar
     * JavaScript inline nuevo.
     */

    const btnRetenciones =
        document.getElementById(
            "btnAbrirABMRetenciones"
        );


    if(btnRetenciones){

        btnRetenciones.addEventListener(
            "click",
            function(){

                mostrarABMRetenciones(
                    "menu"
                );

            }
        );

    }

}

function mostrarModificarEmpresa(){

    limpiarPanelOperativo();

    document.getElementById(
        "bloque-alta-empresa"
    ).style.display = "block";

    document.getElementById(
        "form-alta"
    ).style.display = "block";

    document.getElementById(
        "contenido"
    ).style.display = "none";

    document.getElementById(
        "titulo-panel"
    ).innerHTML =
    'Modificar <span>Empresa</span>';

    document.getElementById(
        "botonera-alta"
    ).style.display = "none";

    document.getElementById(
         "botonera-modificar"
    ).style.display = "flex";

}

async function mostrarABMGestionClaves(){

    const contenidoOperativo =
        document.getElementById(
            "contenido-operativo"
        );

    const empresaActiva =
        document.getElementById(
            "empresaActiva"
        );

    if(
        !contenidoOperativo ||
        !empresaActiva
    ){

        alert(
            "No se pudo preparar Gestión de claves."
        );

        return;

    }

    const empresa =
        empresaActiva.value;

    if(!empresa){

        alert(
            "No hay una empresa seleccionada."
        );

        return;

    }

    try{

        const respuesta =
            await fetch(
                `/gestion-claves/?empresa=${encodeURIComponent(empresa)}`
            );

        const resultado =
            await respuesta.json();

        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                "No se pudo cargar Gestión de claves."
            );

            return;

        }

        const bloqueAlta =
            document.getElementById(
                "bloque-alta-empresa"
            );

        if(bloqueAlta){

            bloqueAlta.style.display =
                "none";

        }

        contenidoOperativo.innerHTML =
            resultado.html;

        if(
            typeof iniciarABMGestionClaves ===
            "function"
        ){

            iniciarABMGestionClaves();

        }else{

            console.error(
                "No se encontró iniciarABMGestionClaves()."
            );

            alert(
                "Gestión de claves se cargó, pero no pudo iniciarse."
            );

        }

    }catch(error){

        console.error(
            "Error cargando Gestión de claves:",
            error
        );

        alert(
            "No se pudo conectar con Gestión de claves."
        );

    }

}
