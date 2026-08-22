/*
 * =========================================
 * CARGA SIMPLE
 * =========================================
 *
 * Funciones propias del registro de Carga Simple.
 *
 * Este archivo comienza extrayendo del HTML la lógica
 * de guardado ya probada, sin cambiar todavía su
 * comportamiento.
 *
 * La persistencia de Pagos se incorporará aquí por
 * etapas una vez validada esta extracción.
 */


async function guardarRegistroSimple(){

    /*
     * =========================================
     * VALIDACIÓN INICIAL
     * =========================================
     *
     * En esta primera etapa solamente guardamos
     * Movimientos SIN Pago.
     */

    /*
    * =========================================
    * PREPARAR PAGOS
    * =========================================
    *
    * Primera etapa de persistencia:
    *
    * - admite registros sin Pago;
    * - admite Pagos únicamente en efectivo;
    * - todavía no persiste transferencias,
    *   tarjetas, cheques ni retenciones.
    */

    const pagosEfectivo = [];


    if(
        Array.isArray(pagosRegistro)
    ){

        for(
            const pago of pagosRegistro
        ){

            /*
            * Antes de guardar tomamos los valores
            * actuales de los controles visibles.
            */

            actualizarPagoRegistro(
                pago.id
            );


            const tieneOtrosMedios =
                pago.transferencias.length > 0 ||
                pago.tarjetas.length > 0 ||
                pago.cheques.length > 0 ||
                pago.retenciones.length > 0;


            if(tieneOtrosMedios){

                alert(
                    "En esta etapa de prueba solamente se pueden guardar Pagos en efectivo."
                );

                return;

            }


            const efectivo =
                Number(
                    pago.efectivo || 0
                );


            if(efectivo <= 0){

                alert(
                    "El importe en efectivo del Pago debe ser mayor a cero."
                );

                return;

            }


            if(!pago.fecha_pago){

                alert(
                    "Ingrese la fecha del Pago."
                );

                return;

            }


            pagosEfectivo.push(
                {
                    fecha:
                        pago.fecha_pago,

                    importe_efectivo:
                        efectivo
                }
            );

        }

    }


    const empresa =
        document.getElementById(
            "empresaActiva"
        );


    const tipoGasto =
        document.getElementById(
            "tipoGastoRegistro"
        );


    const proveedor =
        document.getElementById(
            "proveedorRegistro"
        );


    const centroOperativo =
        document.getElementById(
            "centroOperativoRegistro"
        );


    const recursoOperativo =
        document.getElementById(
            "recursoOperativoRegistro"
        );


    const fechaRegistro =
        document.getElementById(
            "fechaRegistro"
        );


    const fechaVencimiento =
        document.getElementById(
            "fechaVencimientoRegistro"
        );


    const tipoComprobante =
        document.getElementById(
            "tipoComprobanteRegistro"
        );


    const numeroComprobante =
        document.getElementById(
            "numeroComprobanteRegistro"
        );


    const neto =
        document.getElementById(
            "neto"
        );


    const exento =
        document.getElementById(
            "exento"
        );


    const iva21 =
        document.getElementById(
            "iva21"
        );


    const iva27 =
        document.getElementById(
            "iva27"
        );


    const iva105 =
        document.getElementById(
            "iva105"
        );


    const recargos =
        document.getElementById(
            "recargosIntereses"
        );


    const ajuste =
        document.getElementById(
            "ajuste"
        );


    const percepcionIIBB =
        document.getElementById(
            "percepcionIIBB"
        );


    const percepcionIVA =
        document.getElementById(
            "percepcionIVA"
        );


    const percepcionGanancias =
        document.getElementById(
            "percepcionGanancias"
        );


    const percepcionTasas =
        document.getElementById(
            "percepcionTasasMunicipales"
        );


    const totalRegistro =
        document.getElementById(
            "total_registro"
        );


    const archivoFactura =
        document.getElementById(
            "archivoFacturaRegistro"
        );


    /*
     * =========================================
     * VALIDACIONES
     * =========================================
     */

    if(
        !empresa ||
        !empresa.value
    ){

        alert(
            "Seleccione una empresa."
        );

        return;

    }


    if(
        !tipoGasto ||
        !tipoGasto.value
    ){

        alert(
            "Seleccione un tipo de gasto."
        );

        return;

    }


    if(
        !proveedor ||
        !proveedor.value
    ){

        alert(
            "Seleccione un proveedor."
        );

        return;

    }


    if(
        !fechaRegistro ||
        !fechaRegistro.value
    ){

        alert(
            "Ingrese la fecha del registro."
        );

        return;

    }


    const total =
        Number(
            totalRegistro?.dataset.valorNumerico ||
            0
        );


    if(total <= 0){

        alert(
            "El total del registro debe ser mayor a cero."
        );

        return;

    }


    /*
     * =========================================
     * FORM DATA
     * =========================================
     */

    const datos =
        new FormData();


    datos.append(
        "empresa",
        empresa.value
    );


    datos.append(
        "tipo_gasto",
        tipoGasto.value
    );


    datos.append(
        "proveedor",
        proveedor.value
    );


    datos.append(
        "centro_operativo",
        centroOperativo?.value || ""
    );


    datos.append(
        "recurso_operativo",
        recursoOperativo?.value || ""
    );


    datos.append(
        "fecha_registro",
        fechaRegistro.value
    );


    datos.append(
        "fecha_vencimiento",
        fechaVencimiento?.value || ""
    );


    datos.append(
        "tipo_comprobante",
        tipoComprobante?.value || ""
    );


    datos.append(
        "numero_comprobante",
        numeroComprobante?.value || ""
    );


    datos.append(
        "neto_gravado",
        String(
            leerImporte(
                neto?.value
            )
        )
    );


    datos.append(
        "no_gravado_exento",
        String(
            leerImporte(
                exento?.value
            )
        )
    );


    datos.append(
        "iva_21",
        String(
            leerImporte(
                iva21?.value
            )
        )
    );


    datos.append(
        "iva_27",
        String(
            leerImporte(
                iva27?.value
            )
        )
    );


    datos.append(
        "iva_105",
        String(
            leerImporte(
                iva105?.value
            )
        )
    );


    datos.append(
        "recargos_intereses",
        String(
            leerImporte(
                recargos?.value
            )
        )
    );


    datos.append(
        "ajuste_redondeo",
        String(
            leerImporte(
                ajuste?.value
            )
        )
    );


    datos.append(
        "percepcion_iibb",
        String(
            leerImporte(
                percepcionIIBB?.value
            )
        )
    );


    datos.append(
        "percepcion_iva",
        String(
            leerImporte(
                percepcionIVA?.value
            )
        )
    );


    datos.append(
        "percepcion_ganancias",
        String(
            leerImporte(
                percepcionGanancias?.value
            )
        )
    );


    datos.append(
        "percepcion_tasas_municipales",
        String(
            leerImporte(
                percepcionTasas?.value
            )
        )
    );


    datos.append(
        "total",
        String(
            total
        )
    );

    /*
    * Pagos en efectivo.
    *
    * Se envían como JSON dentro del mismo FormData.
    * Los comprobantes de otros medios se incorporarán
    * cuando implementemos esos medios.
    */

    datos.append(
        "pagos_efectivo",
        JSON.stringify(
            pagosEfectivo
        )
    );

    if(
        archivoFactura &&
        archivoFactura.files &&
        archivoFactura.files.length > 0
    ){

        datos.append(
            "archivo",
            archivoFactura.files[0]
        );

    }


    /*
     * =========================================
     * CSRF
     * =========================================
     */

    const csrfToken =
        document.querySelector(
            "[name=csrfmiddlewaretoken]"
        )?.value;


    /*
     * =========================================
     * GUARDAR
     * =========================================
     */

    try{

        const respuesta =
            await fetch(
                "/movimientos/guardar/",
                {
                    method:
                        "POST",

                    headers:
                        csrfToken
                            ? {
                                "X-CSRFToken":
                                    csrfToken
                            }
                            : {},

                    body:
                        datos
                }
            );


        const resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            alert(
                resultado.mensaje ||
                "No se pudo guardar el registro."
            );

            return;

        }


        alert(
            "Registro guardado correctamente."
        );


        console.log(
            "Movimiento creado:",
            resultado.movimiento_id
        );


    }catch(error){

        console.error(
            "Error guardando registro:",
            error
        );


        alert(
            "Ocurrió un error al guardar el registro."
        );

    }

}


/*
 * =========================================
 * EVENTO GUARDAR REGISTRO
 * =========================================
 *
 * Carga Simple se construye dinámicamente dentro del
 * panel. Por ese motivo usamos delegación de eventos
 * sobre document y evitamos listeners inline.
 */

document.addEventListener(
    "click",
    function(event){

        const botonGuardar =
            event.target.closest(
                "#btnGuardarRegistro"
            );


        if(!botonGuardar){

            return;

        }


        guardarRegistroSimple();

    }
);