/**
 * Muestra la pantalla temporal del futuro circuito
 * de Obligaciones / Liquidaciones.
 *
 * Por el momento esta pantalla es exclusivamente
 * informativa. No persiste datos ni modifica
 * Movimientos, Pagos o Vencimientos.
 */
function mostrarObligaciones() {

    const bloqueAlta =
        document.getElementById(
            "bloque-alta-empresa"
        );

    const contenido =
        document.getElementById(
            "contenido-operativo"
        );


    if (bloqueAlta) {

        bloqueAlta.style.display =
            "none";

    }


    if (!contenido) {

        return;

    }


    contenido.innerHTML = `

        <div class="card">

            <div class="section-title">
                Obligaciones
            </div>

            <div class="empty-state">

                <strong>
                    En desarrollo
                </strong>

                <br><br>

                <strong>
                    OBLIGACIÓN / LIQUIDACIÓN
                </strong>

                <br><br>

                Concepto
                (Sueldos / Aportes y Cont. /
                VEP - Impuestos / Tasas y otros)

                <br>

                Organismo / beneficiario

                <br>

                Período

                <br>

                Referencia

                <br>

                Centro operativo
                (cuando corresponda)

                <br>

                Importe

                <br>

                Vencimiento

                <br>

                Forma de pago

            </div>

        </div>

    `;

}


/**
 * Atiende el botón Obligaciones del menú Registros.
 *
 * El botón se genera dinámicamente dentro de
 * mostrarSubmenu(), por lo que se utiliza
 * delegación de eventos sobre document.
 */
document.addEventListener(
    "click",
    function (event) {

        const boton =
            event.target.closest(
                "#btn-obligaciones"
            );


        if (!boton) {

            return;

        }


        mostrarObligaciones();

    }
);