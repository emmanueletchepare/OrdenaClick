(function () {

    "use strict";


    function obtenerEmpresaActiva() {

        const campo =
            document.getElementById("empresaActiva");

        if (!campo) {
            return "";
        }

        return campo.value || "";
    }


    function numeroSeguro(valor) {

        const texto =
            String(valor || "").trim();

        if (!texto) {
            return 0;
        }

        const normalizado =
            texto
                .replace(/\./g, "")
                .replace(",", ".");

        const numero =
            Number.parseFloat(
                normalizado
            );

        if (Number.isNaN(numero)) {
            return 0;
        }

        return numero;
    }


    function formatearImporteCampo(valor) {

        const texto =
            String(valor || "").trim();

        if (!texto) {
            return "";
        }

        const numero =
            numeroSeguro(texto);

        return new Intl.NumberFormat(
            "es-AR",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        ).format(numero);
    }

    function formatearImportesDashboardCaja() {

        document.querySelectorAll(
            "[data-caja-importe]"
        ).forEach(
            function (elemento) {

                const valor =
                    Number(
                        elemento.dataset.valor
                    );

                if (!Number.isFinite(valor)) {
                    elemento.textContent = "0,00";
                    return;
                }

                elemento.textContent =
                    valor.toLocaleString(
                        "es-AR",
                        {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        }
                    );
            }
        );
    }

    function formatearPesos(valor) {

        return new Intl.NumberFormat(
            "es-AR",
            {
                style: "currency",
                currency: "ARS"
            }
        ).format(valor);
    }


    let chequesCobranza = [];
    let chequeCobranzaEditando = null;


    function actualizarConciliacionCobranza() {

        const totalDeclarado =
            document.getElementById(
                "cobranzaTotalDeclarado"
            );

        const efectivoArs =
            document.getElementById(
                "cobranzaEfectivoArs"
            );

        const resumenDeclarado =
            document.getElementById(
                "cobranzaResumenDeclarado"
            );

        const resumenEfectivo =
            document.getElementById(
                "cobranzaResumenEfectivo"
            );

        const resumenCheques =
            document.getElementById(
                "cobranzaResumenCheques"
            );

        const resumenDiferencia =
            document.getElementById(
                "cobranzaResumenDiferencia"
            );

        const tarjetaDeclarado =
            document.getElementById(
                "cobranzaConciliacionDeclarado"
            );

        const tarjetaDiferencia =
            document.getElementById(
                "cobranzaConciliacionDiferencia"
            );

        if (
            !totalDeclarado ||
            !efectivoArs ||
            !resumenDeclarado ||
            !resumenEfectivo ||
            !resumenCheques ||
            !resumenDiferencia ||
            !tarjetaDeclarado ||
            !tarjetaDiferencia
        ) {
            return;
        }

        const totalCheques =
            chequesCobranza.reduce(
                function (total, cheque) {
                    return total + cheque.importe;
                },
                0
            );

        const efectivo =
            numeroSeguro(
                efectivoArs.value
            );

        const hayTotalDeclarado =
            String(
                totalDeclarado.value || ""
            ).trim() !== "";

        resumenEfectivo.textContent =
            formatearPesos(efectivo);

        resumenCheques.textContent =
            formatearPesos(totalCheques);

        tarjetaDeclarado.hidden =
            !hayTotalDeclarado;

        tarjetaDiferencia.hidden =
            !hayTotalDeclarado;

        if (!hayTotalDeclarado) {

            tarjetaDiferencia.classList.remove(
                "es-cero",
                "tiene-diferencia"
            );

            return;
        }

        const declarado =
            numeroSeguro(
                totalDeclarado.value
            );

        const diferencia =
            efectivo +
            totalCheques -
            declarado;

        resumenDeclarado.textContent =
            formatearPesos(declarado);

        resumenDiferencia.textContent =
            formatearPesos(diferencia);

        const diferenciaEsCero =
            Math.abs(diferencia) < 0.005;

        tarjetaDiferencia.classList.toggle(
            "es-cero",
            diferenciaEsCero
        );

        tarjetaDiferencia.classList.toggle(
            "tiene-diferencia",
            !diferenciaEsCero
        );
    }


    function actualizarTipoChequeCobranza() {

        const tipo =
            document.getElementById(
                "cobranzaChequeTipo"
            );

        const emision =
            document.getElementById(
                "cobranzaChequeFechaEmision"
            );

        const acreditacion =
            document.getElementById(
                "cobranzaChequeFechaAcreditacion"
            );

        const campoAcreditacion =
            document.getElementById(
                "cobranzaChequeCampoAcreditacion"
            );

        if (
            !tipo ||
            !emision ||
            !acreditacion ||
            !campoAcreditacion
        ) {
            return;
        }

        const esSimple =
            tipo.value === "Comun";

        /*
        * Replica el comportamiento validado de Carga Simple:
        * para Simple la acreditación coincide con la emisión,
        * pero se conserva su lugar dentro de la grilla.
        */
        if (esSimple) {

            acreditacion.value =
                emision.value;

            acreditacion.disabled = true;

            campoAcreditacion.style.visibility =
                "hidden";

            campoAcreditacion.style.pointerEvents =
                "none";

            return;
        }

        acreditacion.disabled = false;

        campoAcreditacion.style.visibility =
            "visible";

        campoAcreditacion.style.pointerEvents =
            "auto";
    }


    function normalizarNumeroChequeCampo(campo) {

        const valor =
            String(campo.value || "").trim();

        if (!valor) {
            return "";
        }

        if (!/^\d{1,8}$/.test(valor)) {
            return "";
        }

        const numero =
            valor.padStart(8, "0");

        campo.value = numero;

        return numero;
    }


    function abrirFormularioChequeCobranza() {

        const formularioCheque =
            document.getElementById(
                "cobranzaChequeFormulario"
            );

        const botonAbrir =
            document.getElementById(
                "btnAbrirChequeCobranza"
            );

        if (formularioCheque) {
            formularioCheque.hidden = false;
        }

        if (botonAbrir) {
            botonAbrir.hidden = true;
        }

        actualizarTipoChequeCobranza();

        const cliente =
            document.getElementById(
                "cobranzaChequeCliente"
            );

        if (cliente) {
            cliente.focus();
        }
    }


    function cerrarFormularioChequeCobranza() {

        const formularioCheque =
            document.getElementById(
                "cobranzaChequeFormulario"
            );

        const botonAbrir =
            document.getElementById(
                "btnAbrirChequeCobranza"
            );

        if (formularioCheque) {
            formularioCheque.hidden = true;
        }

        if (botonAbrir) {
            botonAbrir.hidden = false;
        }
    }


    function limpiarFormularioChequeCobranza() {

        const cliente =
            document.getElementById(
                "cobranzaChequeCliente"
            );

        const numero =
            document.getElementById(
                "cobranzaChequeNumero"
            );

        const banco =
            document.getElementById(
                "cobranzaChequeBanco"
            );

        const tipo =
            document.getElementById(
                "cobranzaChequeTipo"
            );

        const emision =
            document.getElementById(
                "cobranzaChequeFechaEmision"
            );

        const acreditacion =
            document.getElementById(
                "cobranzaChequeFechaAcreditacion"
            );

        const importe =
            document.getElementById(
                "cobranzaChequeImporte"
            );

        if (cliente) cliente.value = "";
        if (numero) numero.value = "";
        if (banco) banco.value = "";
        if (tipo) tipo.value = "Comun";
        if (emision) emision.value = "";
        if (acreditacion) acreditacion.value = "";
        if (importe) importe.value = "";

        chequeCobranzaEditando = null;

        const botonGuardar =
            document.getElementById(
                "btnGuardarChequeCobranza"
            );

        const botonCancelar =
            document.getElementById(
                "btnCancelarEdicionChequeCobranza"
            );

        if (botonGuardar) {
            botonGuardar.textContent =
                "Agregar cheque";
        }

        if (botonCancelar) {
            botonCancelar.hidden = true;
        }

        actualizarTipoChequeCobranza();
    }


    function cancelarFormularioChequeCobranza() {

        limpiarFormularioChequeCobranza();
        cerrarFormularioChequeCobranza();
    }


    function obtenerDatosChequeCobranza() {

        const cliente =
            document.getElementById(
                "cobranzaChequeCliente"
            );

        const numero =
            document.getElementById(
                "cobranzaChequeNumero"
            );

        const banco =
            document.getElementById(
                "cobranzaChequeBanco"
            );

        const tipo =
            document.getElementById(
                "cobranzaChequeTipo"
            );

        const emision =
            document.getElementById(
                "cobranzaChequeFechaEmision"
            );

        const acreditacion =
            document.getElementById(
                "cobranzaChequeFechaAcreditacion"
            );

        const importe =
            document.getElementById(
                "cobranzaChequeImporte"
            );

        if (
            !cliente ||
            !numero ||
            !banco ||
            !tipo ||
            !emision ||
            !acreditacion ||
            !importe
        ) {
            return null;
        }

        const numeroNormalizado =
            normalizarNumeroChequeCampo(
                numero
            );

        if (!numeroNormalizado) {

            alert(
                "Ingrese un número de cheque válido " +
                "de hasta 8 dígitos."
            );

            numero.focus();
            return null;
        }

        if (!banco.value) {

            alert("Seleccione el Banco.");

            banco.focus();
            return null;
        }

        if (!emision.value) {

            alert(
                "Ingrese la fecha de emisión."
            );

            emision.focus();
            return null;
        }

        let fechaAcreditacion =
            acreditacion.value;

        if (tipo.value === "Comun") {

            fechaAcreditacion =
                emision.value;

            acreditacion.value =
                emision.value;

        } else {

            if (!fechaAcreditacion) {

                alert(
                    "Ingrese la fecha de acreditación."
                );

                acreditacion.focus();
                return null;
            }

            const fechaEmision =
                new Date(
                    emision.value + "T00:00:00"
                );

            const fechaAcreditacionDate =
                new Date(
                    fechaAcreditacion + "T00:00:00"
                );

            if (
                fechaAcreditacionDate <=
                fechaEmision
            ) {

                alert(
                    "La fecha de acreditación debe " +
                    "ser posterior a la fecha de emisión."
                );

                acreditacion.focus();
                return null;
            }

            const dias =
                (
                    fechaAcreditacionDate -
                    fechaEmision
                ) /
                (
                    1000 *
                    60 *
                    60 *
                    24
                );

            if (dias > 360) {

                alert(
                    "La acreditación no puede superar " +
                    "los 360 días desde la emisión."
                );

                acreditacion.focus();
                return null;
            }
        }

        const valorImporte =
            numeroSeguro(
                importe.value
            );

        if (valorImporte <= 0) {

            alert(
                "Ingrese un importe válido."
            );

            importe.focus();
            return null;
        }

        return {
            id:
                chequeCobranzaEditando ??
                (
                    Date.now().toString() +
                    "-" +
                    chequesCobranza.length
                ),

            cliente_id:
                cliente.value,

            cliente_nombre:
                cliente.selectedOptions[0]
                    ?.textContent
                    .trim() ||
                "Sin cliente asociado",

            numero:
                numeroNormalizado,

            banco_id:
                banco.value,

            banco_nombre:
                banco.selectedOptions[0]
                    ?.textContent
                    .trim() ||
                "",

            tipo_cheque:
                tipo.value,

            fecha_emision:
                emision.value,

            fecha_acreditacion:
                fechaAcreditacion,

            importe:
                valorImporte
        };
    }


    function formatearFechaChequeCobranza(valor) {

        if (!valor) {
            return "—";
        }

        const partes =
            valor.split("-");

        if (partes.length !== 3) {
            return valor;
        }

        return (
            partes[2] +
            "/" +
            partes[1] +
            "/" +
            partes[0]
        );
    }


    function crearCeldaChequeCobranza(
        texto,
        clase = ""
    ) {

        const celda =
            document.createElement(
                "div"
            );

        if (clase) {
            celda.className = clase;
        }

        celda.textContent = texto;

        return celda;
    }


    function crearBotonAccionChequeCobranza(
        accion,
        chequeId,
        titulo,
        simbolo
    ) {

        const boton =
            document.createElement(
                "button"
            );

        boton.type = "button";

        boton.className =
            "cobranza-cheque-btn-icono";

        boton.dataset[accion] =
            String(chequeId);

        boton.title = titulo;
        boton.setAttribute(
            "aria-label",
            titulo
        );

        /*
        * Se usa texto Unicode para mantener esta UI
        * libre de HTML/JS inline.
        */
        boton.textContent = simbolo;

        return boton;
    }


    function renderizarChequesCobranza() {

        const contenedor =
            document.getElementById(
                "cobranzaChequesContenedor"
            );

        const vacio =
            document.getElementById(
                "cobranzaChequesVacio"
            );

        const listado =
            document.getElementById(
                "cobranzaListadoCheques"
            );

        if (
            !contenedor ||
            !vacio ||
            !listado
        ) {
            return;
        }

        contenedor.innerHTML = "";

        const hayCheques =
            chequesCobranza.length > 0;

        vacio.hidden = hayCheques;
        listado.hidden = !hayCheques;

        chequesCobranza.forEach(
            function (cheque) {

                const fila =
                    document.createElement(
                        "div"
                    );

                fila.className =
                    "cobranza-cheques-fila";

                fila.appendChild(
                    crearCeldaChequeCobranza(
                        cheque.cliente_nombre
                    )
                );

                fila.appendChild(
                    crearCeldaChequeCobranza(
                        cheque.banco_nombre
                    )
                );

                fila.appendChild(
                    crearCeldaChequeCobranza(
                        cheque.numero,
                        "cobranza-cheque-numero-listado"
                    )
                );

                fila.appendChild(
                    crearCeldaChequeCobranza(
                        cheque.tipo_cheque ===
                        "Diferido"
                            ? "Diferido"
                            : "Simple"
                    )
                );

                fila.appendChild(
                    crearCeldaChequeCobranza(
                        formatearFechaChequeCobranza(
                            cheque.fecha_emision
                        )
                    )
                );

                fila.appendChild(
                    crearCeldaChequeCobranza(
                        cheque.tipo_cheque ===
                        "Diferido"
                            ? formatearFechaChequeCobranza(
                                cheque.fecha_acreditacion
                            )
                            : "—"
                    )
                );

                fila.appendChild(
                    crearCeldaChequeCobranza(
                        formatearPesos(
                            cheque.importe
                        ),
                        "cobranza-cheque-importe-listado"
                    )
                );

                const acciones =
                    document.createElement(
                        "div"
                    );

                acciones.className =
                    "cobranza-cheques-acciones";

                acciones.appendChild(
                    crearBotonAccionChequeCobranza(
                        "editarCheque",
                        cheque.id,
                        "Editar cheque",
                        "✎"
                    )
                );

                acciones.appendChild(
                    crearBotonAccionChequeCobranza(
                        "eliminarCheque",
                        cheque.id,
                        "Eliminar cheque",
                        "×"
                    )
                );

                fila.appendChild(
                    acciones
                );

                contenedor.appendChild(
                    fila
                );
            }
        );

        actualizarConciliacionCobranza();
    }


    function guardarChequeCobranza() {

        const cheque =
            obtenerDatosChequeCobranza();

        if (!cheque) {
            return;
        }

        if (chequeCobranzaEditando !== null) {

            const indice =
                chequesCobranza.findIndex(
                    function (item) {
                        return (
                            String(item.id) ===
                            String(
                                chequeCobranzaEditando
                            )
                        );
                    }
                );

            if (indice !== -1) {
                chequesCobranza[indice] =
                    cheque;
            }

        } else {

            chequesCobranza.push(
                cheque
            );
        }

        limpiarFormularioChequeCobranza();
        cerrarFormularioChequeCobranza();
        renderizarChequesCobranza();
    }


    function editarChequeCobranza(id) {

        const cheque =
            chequesCobranza.find(
                function (item) {
                    return (
                        String(item.id) ===
                        String(id)
                    );
                }
            );

        if (!cheque) {
            return;
        }

        chequeCobranzaEditando =
            cheque.id;

        document.getElementById(
            "cobranzaChequeCliente"
        ).value =
            cheque.cliente_id;

        document.getElementById(
            "cobranzaChequeNumero"
        ).value =
            cheque.numero;

        document.getElementById(
            "cobranzaChequeBanco"
        ).value =
            cheque.banco_id;

        document.getElementById(
            "cobranzaChequeTipo"
        ).value =
            cheque.tipo_cheque;

        document.getElementById(
            "cobranzaChequeFechaEmision"
        ).value =
            cheque.fecha_emision;

        document.getElementById(
            "cobranzaChequeFechaAcreditacion"
        ).value =
            cheque.fecha_acreditacion;

        document.getElementById(
            "cobranzaChequeImporte"
        ).value =
            formatearImporteCampo(
                cheque.importe
            );

        const botonGuardar =
            document.getElementById(
                "btnGuardarChequeCobranza"
            );

        const botonCancelar =
            document.getElementById(
                "btnCancelarEdicionChequeCobranza"
            );

        if (botonGuardar) {
            botonGuardar.textContent =
                "Guardar cambios";
        }

        if (botonCancelar) {
            botonCancelar.hidden = false;
        }

        abrirFormularioChequeCobranza();
        actualizarTipoChequeCobranza();
    }


    function eliminarChequeCobranza(id) {

        if (
            chequeCobranzaEditando !== null &&
            String(chequeCobranzaEditando) ===
            String(id)
        ) {
            cancelarFormularioChequeCobranza();
        }

        chequesCobranza =
            chequesCobranza.filter(
                function (item) {
                    return (
                        String(item.id) !==
                        String(id)
                    );
                }
            );

        renderizarChequesCobranza();
    }


    function prepararNuevaCobranza() {

        chequesCobranza = [];
        chequeCobranzaEditando = null;

        const formulario =
            document.getElementById(
                "formNuevaCobranza"
            );

        if (!formulario) {
            return;
        }

        const botonAbrir =
            document.getElementById(
                "btnAbrirChequeCobranza"
            );

        const botonGuardar =
            document.getElementById(
                "btnGuardarChequeCobranza"
            );

        const botonCancelar =
            document.getElementById(
                "btnCancelarEdicionChequeCobranza"
            );

        if (botonAbrir) {
            botonAbrir.addEventListener(
                "click",
                function () {
                    limpiarFormularioChequeCobranza();
                    abrirFormularioChequeCobranza();
                }
            );
        }

        if (botonGuardar) {
            botonGuardar.addEventListener(
                "click",
                guardarChequeCobranza
            );
        }

        if (botonCancelar) {
            botonCancelar.addEventListener(
                "click",
                cancelarFormularioChequeCobranza
            );
        }


        formulario.addEventListener(
            "input",
            function (evento) {

                if (
                    evento.target.matches(
                        "#cobranzaTotalDeclarado, " +
                        "#cobranzaEfectivoArs"
                    )
                ) {
                    actualizarConciliacionCobranza();
                }

                if (
                    evento.target.matches(
                        "#cobranzaChequeFechaEmision"
                    )
                ) {
                    actualizarTipoChequeCobranza();
                }
            }
        );


        formulario.addEventListener(
            "change",
            function (evento) {

                if (
                    evento.target.matches(
                        "#cobranzaChequeTipo"
                    )
                ) {
                    actualizarTipoChequeCobranza();
                }
            }
        );


        formulario.addEventListener(
            "focusout",
            function (evento) {

                if (
                    evento.target.matches(
                        "#cobranzaChequeNumero"
                    )
                ) {
                    normalizarNumeroChequeCampo(
                        evento.target
                    );

                    return;
                }

                if (
                    evento.target.matches(
                        "#cobranzaTotalDeclarado, " +
                        "#cobranzaEfectivoArs, " +
                        "#cobranzaEfectivoUsd, " +
                        "#cobranzaChequeImporte"
                    )
                ) {
                    evento.target.value =
                        formatearImporteCampo(
                            evento.target.value
                        );

                    actualizarConciliacionCobranza();
                }
            }
        );


        formulario.addEventListener(
            "click",
            function (evento) {

                const editar =
                    evento.target.closest(
                        "[data-editar-cheque]"
                    );

                if (editar) {

                    editarChequeCobranza(
                        editar.dataset.editarCheque
                    );

                    return;
                }

                const eliminar =
                    evento.target.closest(
                        "[data-eliminar-cheque]"
                    );

                if (eliminar) {

                    eliminarChequeCobranza(
                        eliminar.dataset.eliminarCheque
                    );
                }
            }
        );


        formulario.addEventListener(
            "submit",
            function (evento) {

                evento.preventDefault();

                const mensaje =
                    document.getElementById(
                        "cobranzaMensaje"
                    );

                if (mensaje) {

                    mensaje.hidden = false;

                    mensaje.textContent =
                        "La pantalla está lista. " +
                        "El guardado se conectará al backend " +
                        "en el siguiente bloque.";
                }
            }
        );

        limpiarFormularioChequeCobranza();
        cerrarFormularioChequeCobranza();
        renderizarChequesCobranza();
    }

    async function mostrarCaja() {

        const empresaId =
            obtenerEmpresaActiva();

        if (!empresaId) {
            return;
        }

        const submenu =
            document.getElementById(
                "submenu-dinamico"
            );

        const contenido =
            document.getElementById(
                "contenido-operativo"
            );

        if (!contenido) {
            return;
        }

        /*
        * Caja es un módulo principal del sidebar.
        * Al ingresar se elimina cualquier submenu
        * perteneciente al módulo visitado anteriormente.
        */
        if (submenu) {
            submenu.innerHTML = "";
        }

        contenido.innerHTML =
            '<div class="empty-state">' +
            'Cargando Caja...' +
            '</div>';

        try {

            const respuesta =
                await fetch(
                    "/caja/?empresa=" +
                    encodeURIComponent(empresaId),
                    {
                        method: "GET",
                        credentials: "same-origin",
                        headers: {
                            "X-Requested-With":
                                "XMLHttpRequest"
                        }
                    }
                );

            const datos =
                await respuesta.json();

            if (!respuesta.ok || !datos.ok) {

                throw new Error(
                    datos.mensaje ||
                    "No se pudo abrir Caja."
                );
            }

            contenido.innerHTML =
                datos.html;

            formatearImportesDashboardCaja();

        } catch (error) {

            contenido.innerHTML =
                '<div class="empty-state">' +
                error.message +
                '</div>';
        }
    }

    function obtenerCajaSeleccionada() {

        const selector =
            document.getElementById(
                "cajaFiltroDisponibilidad"
            );

        /*
        * Con una sola Caja el selector no se renderiza.
        * En ese caso se toma el único resumen visible.
        */
        if (!selector) {

            const resumen =
                document.querySelector(
                    "[data-caja-resumen]"
                );

            return resumen
                ? resumen.dataset.cajaResumen || ""
                : "";
        }

        if (
            !selector.value ||
            selector.value === "todas"
        ) {
            return "";
        }

        return selector.value;
    }

    async function mostrarNuevaCobranza() {

        const empresaId =
            obtenerEmpresaActiva();

        if (!empresaId) {
            return;
        }

        const cajaId =
            obtenerCajaSeleccionada();

        if (!cajaId) {

            alert(
                "Seleccione una Caja concreta " +
                "antes de registrar la cobranza."
            );

            return;
        }

        const contenido =
            document.getElementById(
                "contenido-operativo"
            );

        if (!contenido) {
            return;
        }

        contenido.innerHTML =
            '<div class="empty-state">' +
            'Cargando Caja...' +
            '</div>';

        try {

            const respuesta =
                await fetch(
                    "/caja/cobranzas/nueva/" +
                    "?empresa=" +
                    encodeURIComponent(empresaId) +
                    "&caja=" +
                    encodeURIComponent(cajaId),
                    {
                        method: "GET",
                        credentials: "same-origin",
                        headers: {
                            "X-Requested-With":
                                "XMLHttpRequest"
                        }
                    }
                );

            const datos =
                await respuesta.json();

            if (!respuesta.ok || !datos.ok) {

                throw new Error(
                    datos.mensaje ||
                    "No se pudo abrir Nueva Cobranza."
                );
            }

            contenido.innerHTML =
                datos.html;

            prepararNuevaCobranza();

        } catch (error) {

            contenido.innerHTML =
                '<div class="empty-state">' +
                error.message +
                '</div>';
        }
    }

        document.addEventListener(
            "click",
            function (evento) {

                const botonCaja =
                    evento.target.closest(
                        "#btnSidebarCaja"
                    );

                if (botonCaja) {
                    mostrarCaja();
                    return;
                }

                const accion =
                    evento.target.closest(
                        "[data-caja-accion]"
                    );

                if (!accion || accion.disabled) {
                    return;
                }

                            if (
                                accion.dataset.cajaAccion ===
                                "registrar-cobranza"
                            ) {
                                mostrarNuevaCobranza();
                                return;
                            }

                            if (
                                accion.dataset.cajaAccion ===
                                "volver-caja"
                            ) {
                                mostrarCaja();
                            }
            }
        );


        window.mostrarCaja =
            mostrarCaja;

        window.mostrarNuevaCobranza =
            mostrarNuevaCobranza;

    })();