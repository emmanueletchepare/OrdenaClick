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
     * PREPARAR PAGOS
     * =========================================
     *
     * Esta etapa permite persistir:
     *
     * - Efectivo.
     * - Transferencias.
     * - Depósitos.
     * - Tarjetas.
     *
     * Todavía no se persisten:
     *
     * - Cheques.
     * - Retenciones.
     *
     * Los comprobantes de los medios de pago
     * se envían como archivos independientes dentro
     * del mismo FormData.
     */

    const pagosPreparados = [];

    const archivosPagos = [];


    if(
        Array.isArray(pagosRegistro)
    ){

        for(
            let indicePago = 0;
            indicePago < pagosRegistro.length;
            indicePago++
        ){

            const pago =
                pagosRegistro[
                    indicePago
                ];


            /*
             * Tomamos los valores actuales de
             * Fecha y Efectivo antes de guardar.
             */

            actualizarPagoRegistro(
                pago.id
            );


            /*
             * =====================================
             * MEDIOS TODAVÍA NO IMPLEMENTADOS
             * =====================================
             */

            if(
                pago.cheques.length > 0 ||
                pago.retenciones.length > 0
            ){

                alert(
                    "En esta etapa todavía no se pueden guardar Cheques ni Retenciones."
                );

                return;

            }


            /*
             * =====================================
             * FECHA DEL PAGO
             * =====================================
             */

            if(!pago.fecha_pago){

                alert(
                    "Ingrese la fecha del Pago."
                );

                return;

            }


            /*
             * =====================================
             * EFECTIVO
             * =====================================
             */

            const efectivo =
                Number(
                    pago.efectivo || 0
                );


            if(efectivo < 0){

                alert(
                    "El importe en efectivo no puede ser negativo."
                );

                return;

            }


            /*
             * =====================================
             * OPERACIONES BANCARIAS
             * =====================================
             */

            const operacionesBancarias = [];

            let totalOperaciones =
                0;


            for(
                let indiceOperacion = 0;
                indiceOperacion < pago.transferencias.length;
                indiceOperacion++
            ){

                const operacion =
                    pago.transferencias[
                        indiceOperacion
                    ];


                if(
                    operacion.tipo_operacion !==
                        "Transferencia" &&
                    operacion.tipo_operacion !==
                        "Deposito"
                ){

                    alert(
                        "Existe una operación bancaria con un tipo no válido."
                    );

                    return;

                }


                /*
                 * Beta:
                 * todos los Pagos deben ser ARS.
                 */

                if(
                    operacion.moneda !==
                    "ARS"
                ){

                    alert(
                        "La versión Beta de OrdenaClick admite pagos únicamente en Pesos."
                    );

                    return;

                }


                if(
                    operacion.tipo_operacion ===
                        "Transferencia" &&
                    !operacion.cuenta_origen_id
                ){

                    alert(
                        "Una transferencia debe tener una cuenta bancaria de origen."
                    );

                    return;

                }


                if(
                    !operacion.banco_destino_id
                ){

                    alert(
                        "La operación bancaria debe tener un banco de destino."
                    );

                    return;

                }


                if(!operacion.fecha){

                    alert(
                        "La operación bancaria debe tener una fecha."
                    );

                    return;

                }


                const importeOperacion =
                    Number(
                        operacion.importe || 0
                    );


                if(
                    importeOperacion <= 0
                ){

                    alert(
                        "El importe de la operación bancaria debe ser mayor a cero."
                    );

                    return;

                }


                totalOperaciones +=
                    importeOperacion;


                /*
                 * =================================
                 * COMPROBANTE
                 * =================================
                 */

                let comprobanteClave =
                    "";


                if(
                    operacion.comprobante instanceof File
                ){

                    comprobanteClave =
                        `pago_${indicePago}_operacion_${indiceOperacion}_comprobante`;


                    archivosPagos.push(
                        {
                            clave:
                                comprobanteClave,

                            archivo:
                                operacion.comprobante
                        }
                    );

                }


                operacionesBancarias.push(
                    {
                        tipo_operacion:
                            operacion.tipo_operacion,

                        cuenta_origen_id:
                            operacion.tipo_operacion ===
                                "Transferencia"
                                ? operacion.cuenta_origen_id
                                : null,

                        banco_destino_id:
                            operacion.banco_destino_id,

                        referencia_destino:
                            operacion.referencia_destino || "",

                        moneda:
                            operacion.moneda,

                        fecha:
                            operacion.fecha,

                        importe:
                            importeOperacion,

                        comprobante_clave:
                            comprobanteClave
                    }
                );

            }


            /*
             * =====================================
             * TARJETAS
             * =====================================
             */

            const tarjetasPreparadas = [];

            let totalTarjetas =
                0;


            for(
                let indiceTarjeta = 0;
                indiceTarjeta < pago.tarjetas.length;
                indiceTarjeta++
            ){

                const operacionTarjeta =
                    pago.tarjetas[
                        indiceTarjeta
                    ];


                if(
                    !operacionTarjeta.tarjeta_id
                ){

                    alert(
                        "Existe una operación con tarjeta sin una tarjeta seleccionada."
                    );

                    return;

                }


                if(
                    !operacionTarjeta.fecha
                ){

                    alert(
                        "La operación con tarjeta debe tener una fecha."
                    );

                    return;

                }


                const importeTarjeta =
                    Number(
                        operacionTarjeta.importe || 0
                    );


                if(
                    importeTarjeta <= 0
                ){

                    alert(
                        "El importe aplicado de la operación con tarjeta debe ser mayor a cero."
                    );

                    return;

                }


                /*
                 * El importe aplicado sí forma parte
                 * del Pago.
                 *
                 * Los intereses de financiación se
                 * conservan como dato independiente
                 * y NO vuelven a sumarse al aplicado.
                 */

                totalTarjetas +=
                    importeTarjeta;


                const tipoTarjeta =
                    String(
                        operacionTarjeta.tipo_tarjeta || ""
                    );


                const esCredito =
                    tipoTarjeta.toLowerCase() ===
                    "credito";


                const esDebito =
                    tipoTarjeta.toLowerCase() ===
                    "debito";


                const cuotas =
                    Number(
                        operacionTarjeta.cuotas || 1
                    );


                if(
                    !Number.isInteger(cuotas) ||
                    cuotas < 1
                ){

                    alert(
                        "La cantidad de cuotas de la operación con tarjeta no es válida."
                    );

                    return;

                }


                const interesesFinanciacion =
                    Number(
                        operacionTarjeta.intereses_financiacion || 0
                    );


                if(
                    interesesFinanciacion < 0
                ){

                    alert(
                        "Los intereses de financiación no pueden ser negativos."
                    );

                    return;

                }


                /*
                 * Débito:
                 *
                 * - una sola cuota;
                 * - sin intereses de financiación.
                 */

                if(
                    esDebito &&
                    cuotas !== 1
                ){

                    alert(
                        "Una operación con tarjeta de débito debe registrarse en una sola cuota."
                    );

                    return;

                }


                if(
                    esDebito &&
                    interesesFinanciacion !== 0
                ){

                    alert(
                        "Una operación con tarjeta de débito no puede tener intereses de financiación."
                    );

                    return;

                }


                /*
                 * Si no es Crédito ni Débito,
                 * dejamos que el backend valide
                 * contra la Tarjeta real.
                 */

                if(
                    !esCredito &&
                    !esDebito
                ){

                    alert(
                        "Existe una operación con un tipo de tarjeta no válido."
                    );

                    return;

                }


                /*
                 * =================================
                 * COMPROBANTE DE TARJETA
                 * =================================
                 */

                let comprobanteTarjetaClave =
                    "";


                if(
                    operacionTarjeta.comprobante instanceof File
                ){

                    comprobanteTarjetaClave =
                        `pago_${indicePago}_tarjeta_${indiceTarjeta}_comprobante`;


                    archivosPagos.push(
                        {
                            clave:
                                comprobanteTarjetaClave,

                            archivo:
                                operacionTarjeta.comprobante
                        }
                    );

                }


                tarjetasPreparadas.push(
                    {
                        tarjeta_id:
                            operacionTarjeta.tarjeta_id,

                        tipo_tarjeta:
                            tipoTarjeta,

                        fecha:
                            operacionTarjeta.fecha,

                        importe:
                            importeTarjeta,

                        cuotas:
                            cuotas,

                        intereses_financiacion:
                            interesesFinanciacion,

                        referencia:
                            operacionTarjeta.referencia || "",

                        comprobante_clave:
                            comprobanteTarjetaClave
                    }
                );

            }


            /*
             * =====================================
             * TOTAL DEL PAGO
             * =====================================
             */

            const totalPago =
                efectivo +
                totalOperaciones +
                totalTarjetas;


            if(
                totalPago <= 0
            ){

                alert(
                    "El Pago debe tener un importe mayor a cero."
                );

                return;

            }


            /*
             * =====================================
             * PAGO PREPARADO
             * =====================================
             */

            pagosPreparados.push(
                {
                    fecha:
                        pago.fecha_pago,

                    importe_efectivo:
                        efectivo,

                    operaciones_bancarias:
                        operacionesBancarias,

                    tarjetas:
                        tarjetasPreparadas
                }
            );

        }

    }


    /*
     * =========================================
     * DATOS DEL MOVIMIENTO
     * =========================================
     */

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
     * VALIDACIONES DEL MOVIMIENTO
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


    if(
        total <= 0
    ){

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
     * =========================================
     * PAGOS
     * =========================================
     */

    datos.append(
        "pagos",
        JSON.stringify(
            pagosPreparados
        )
    );


    /*
     * =========================================
     * ARCHIVOS DE MEDIOS DE PAGO
     * =========================================
     */

    for(
        const archivoPago of archivosPagos
    ){

        datos.append(
            archivoPago.clave,
            archivoPago.archivo
        );

    }


    /*
     * =========================================
     * FACTURA / COMPROBANTE DEL MOVIMIENTO
     * =========================================
     */

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


        /*
         * =========================================
         * LIMPIAR CARGA SIMPLE
         * =========================================
         *
         * El guardado ya fue confirmado por el backend.
         *
         * Recién en este punto descartamos el borrador
         * de Pagos y retiramos el formulario para evitar
         * registrar accidentalmente el mismo movimiento
         * más de una vez.
         */

        pagosRegistro = [];


        /*
         * =========================================
         * VOLVER AL MENÚ DE REGISTROS
         * =========================================
         */

        mostrarSubmenu(
            "registros"
        );


        /*
         * =========================================
         * POSICIONAR ARRIBA
         * =========================================
         */

        const submenuRegistros =
            document.getElementById(
                "submenu-dinamico"
            );


        if(submenuRegistros){

            posicionarMainEnElemento(
                submenuRegistros
            );

        }


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