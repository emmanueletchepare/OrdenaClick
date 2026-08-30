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
            * CHEQUES
            * =====================================
            */

            const chequesPreparados = [];

            let totalCheques =
                0;


            for(
                let indiceCheque = 0;
                indiceCheque < pago.cheques.length;
                indiceCheque++
            ){

                const cheque =
                    pago.cheques[
                        indiceCheque
                    ];


                if(
                    cheque.instrumento !== "Cheque" &&
                    cheque.instrumento !== "ECheq"
                ){

                    alert(
                        "Existe un cheque con un tipo de instrumento no válido."
                    );

                    return;

                }


                const origenCheque =
                    String(
                        cheque.origen || ""
                    ).toLowerCase();


                let origenPreparado =
                    "";


                if(
                    origenCheque === "propio"
                ){

                    origenPreparado =
                        "Propio";

                }else if(
                    origenCheque === "tercero"
                ){

                    origenPreparado =
                        "Tercero";

                }else{

                    alert(
                        "Existe un cheque con un origen no válido."
                    );

                    return;

                }


                const tipoCheque =
                    String(
                        cheque.tipo || ""
                    ).toLowerCase();


                let tipoChequePreparado =
                    "";


                if(
                    tipoCheque === "comun" ||
                    tipoCheque === "simple"
                ){

                    tipoChequePreparado =
                        "Comun";

                }else if(
                    tipoCheque === "diferido"
                ){

                    tipoChequePreparado =
                        "Diferido";

                }else{

                    alert(
                        "Existe un cheque con un tipo no válido."
                    );

                    return;

                }


                if(
                    !cheque.entidad_id
                ){

                    alert(
                        "El cheque debe tener una cuenta bancaria o banco asociado."
                    );

                    return;

                }


                if(
                    !cheque.numero
                ){

                    alert(
                        "Ingrese el número del cheque."
                    );

                    return;

                }


                if(
                    !cheque.fecha_emision
                ){

                    alert(
                        "Ingrese la fecha de emisión del cheque."
                    );

                    return;

                }


                const importeCheque =
                    Number(
                        cheque.importe || 0
                    );


                if(
                    importeCheque <= 0
                ){

                    alert(
                        "El importe del cheque debe ser mayor a cero."
                    );

                    return;

                }


                totalCheques +=
                    importeCheque;


                chequesPreparados.push(
                    {
                        tipo_instrumento:
                            cheque.instrumento,

                        origen:
                            origenPreparado,

                        tipo_cheque:
                            tipoChequePreparado,

                        entidad_id:
                            cheque.entidad_id,

                        numero:
                            cheque.numero,

                        importe:
                            importeCheque,

                        fecha_emision:
                            cheque.fecha_emision,

                        fecha_acreditacion:
                            cheque.fecha_acreditacion || "",

                        quien_entrega:
                            cheque.quien_entrega || ""
                    }
                );

            }

                        /*
                        * =====================================
                        * RETENCIONES
                        * =====================================
                        */

                        const retencionesPreparadas = [];

                        let totalRetenciones =
                            0;


                        for(
                            let indiceRetencion = 0;
                            indiceRetencion < pago.retenciones.length;
                            indiceRetencion++
                        ){

                            const operacionRetencion =
                                pago.retenciones[
                                    indiceRetencion
                                ];


                            if(
                                !operacionRetencion.retencion_id
                            ){

                                alert(
                                    "Existe una retención sin un tipo seleccionado."
                                );

                                return;

                            }


                            const importeRetencion =
                                Number(
                                    operacionRetencion.importe || 0
                                );


                            if(
                                importeRetencion <= 0
                            ){

                                alert(
                                    "El importe de la retención debe ser mayor a cero."
                                );

                                return;

                            }


                            totalRetenciones +=
                                importeRetencion;


                            /*
                            * =================================
                            * COMPROBANTE DE RETENCIÓN
                            * =================================
                            */

                            let comprobanteRetencionClave =
                                "";


                            if(
                                operacionRetencion.comprobante instanceof File
                            ){

                                comprobanteRetencionClave =
                                    `pago_${indicePago}_retencion_${indiceRetencion}_comprobante`;


                                archivosPagos.push(
                                    {
                                        clave:
                                            comprobanteRetencionClave,

                                        archivo:
                                            operacionRetencion.comprobante
                                    }
                                );

                            }


                            retencionesPreparadas.push(
                                {
                                    retencion_id:
                                        operacionRetencion.retencion_id,

                                    retencion_tipo:
                                        operacionRetencion.retencion_tipo || "",

                                    importe:
                                        importeRetencion,

                                    comprobante_clave:
                                        comprobanteRetencionClave
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
                            totalTarjetas +
                            totalCheques +
                            totalRetenciones;


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
                        tarjetasPreparadas,

                    cheques:
                        chequesPreparados,

                    retenciones:
                        retencionesPreparadas

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


    const modalidadPago =
        document.getElementById(
            "modalidadPagoRegistro"
        );


    const cuentaDebito =
        document.getElementById(
            "cuentaDebitoRegistro"
        );


    const tipoComprobante =
        document.getElementById(
            "tipoComprobanteRegistro"
        );


    const puntoVentaComprobante =
        document.getElementById(
            "puntoVentaComprobanteRegistro"
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

    /*
     * =========================================
     * COMPROBANTE
     * =========================================
     */

    let puntoVentaNormalizado =
        (
            puntoVentaComprobante?.value ||
            ""
        ).trim();


    let numeroComprobanteNormalizado =
        (
            numeroComprobante?.value ||
            ""
        ).trim();


    if(
        !/^\d{1,4}$/.test(
            puntoVentaNormalizado
        )
    ){

        alert(
            "Ingrese un punto de venta válido."
        );

        puntoVentaComprobante?.focus();

        return;

    }


    if(
        !/^\d{1,8}$/.test(
            numeroComprobanteNormalizado
        )
    ){

        alert(
            "Ingrese un número de comprobante válido."
        );

        numeroComprobante?.focus();

        return;

    }


    puntoVentaNormalizado =
        puntoVentaNormalizado.padStart(
            4,
            "0"
        );


    numeroComprobanteNormalizado =
        numeroComprobanteNormalizado.padStart(
            8,
            "0"
        );


    puntoVentaComprobante.value =
        puntoVentaNormalizado;


    numeroComprobante.value =
        numeroComprobanteNormalizado;


    const comprobanteNormalizado =
        puntoVentaNormalizado +
        "-" +
        numeroComprobanteNormalizado;


    /*
    * =========================================
    * PREVISIÓN DE PAGO
    * =========================================
    */

    if(
        !modalidadPago ||
        (
            modalidadPago.value !==
                "Manual" &&
            modalidadPago.value !==
                "DebitoAutomatico"
        )
    ){

        alert(
            "Seleccione una forma prevista de pago válida."
        );

        return;

    }


    if(
        modalidadPago.value ===
            "DebitoAutomatico" &&
        (
            !cuentaDebito ||
            !cuentaDebito.value
        )
    ){

        alert(
            "Seleccione la cuenta prevista para el débito automático."
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
     * DÉBITO AUTOMÁTICO REAL
     * =========================================
     *
     * La previsión del Movimiento y el Pago real
     * son conceptos diferentes.
     *
     * Si el usuario solamente seleccionó Débito
     * automático pero no abrió "Registrar Pago",
     * el Movimiento se guarda sin Pago y queda
     * pendiente.
     *
     * Si registró el débito, enviamos al backend:
     *
     * - fecha real del débito;
     * - importe realmente debitado;
     * - confirmación de intereses por mora cuando
     *   el importe supera el saldo.
     *
     * El backend vuelve a validar todas estas reglas.
     */

    let debitoAutomaticoPreparado =
        null;


    if(
        modalidadPago.value ===
        "DebitoAutomatico"
    ){

        const bloqueDebito =
            document.getElementById(
                "pagoDebitoAutomaticoRegistro"
            );


        if(bloqueDebito){

            const fechaPagoDebito =
                document.getElementById(
                    "fechaPagoDebitoAutomaticoRegistro"
                );


            const importePagoDebito =
                document.getElementById(
                    "importePagoDebitoAutomaticoRegistro"
                );


            if(
                !fechaPagoDebito ||
                !fechaPagoDebito.value
            ){

                alert(
                    "Ingrese la fecha real del débito."
                );

                return;

            }


            const importeDebitado =
                Number(
                    leerImporte(
                        importePagoDebito?.value
                    )
                );


            if(
                !Number.isFinite(
                    importeDebitado
                ) ||
                importeDebitado <= 0
            ){

                alert(
                    "El importe debitado debe ser mayor a cero."
                );

                return;

            }


            let confirmarInteresesMora =
                false;


            /*
             * Si el débito supera el saldo del
             * Movimiento, solamente puede tratarse
             * como interés por mora cuando ocurrió
             * después del vencimiento.
             */

            if(
                importeDebitado >
                total
            ){

                const diferencia =
                    Math.round(
                        (
                            importeDebitado -
                            total
                        ) * 100
                    ) / 100;


                if(
                    !fechaVencimiento ||
                    !fechaVencimiento.value
                ){

                    alert(
                        "El importe debitado supera el total del registro. " +
                        "Sin una fecha de vencimiento no puede clasificarse " +
                        "la diferencia como interés por mora."
                    );

                    return;

                }


                if(
                    fechaPagoDebito.value <=
                    fechaVencimiento.value
                ){

                    alert(
                        "El importe debitado supera el total del registro, " +
                        "pero el débito no ocurrió después del vencimiento. " +
                        "La diferencia no puede registrarse automáticamente " +
                        "como interés por mora."
                    );

                    return;

                }


                const diferenciaFormateada =
                    diferencia.toLocaleString(
                        "es-AR",
                        {
                            minimumFractionDigits:
                                2,

                            maximumFractionDigits:
                                2
                        }
                    );


                const confirmado =
                    confirm(
                        "El débito se produjo después del vencimiento " +
                        "y el importe ingresado supera en $" +
                        diferenciaFormateada +
                        " el saldo pendiente.\n\n" +
                        "¿Los $" +
                        diferenciaFormateada +
                        " corresponden a intereses por mora?"
                    );


                if(!confirmado){

                    /*
                     * No enviamos nada y conservamos
                     * Fecha e Importe para que el
                     * usuario pueda corregirlos.
                     */

                    return;

                }


                confirmarInteresesMora =
                    true;

            }


            debitoAutomaticoPreparado = {

                fecha:
                    fechaPagoDebito.value,

                importe_debitado:
                    importeDebitado,

                confirmar_intereses_mora:
                    confirmarInteresesMora

            };

        }

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
        "modalidad_pago",
        modalidadPago?.value || "Manual"
    );


    datos.append(
        "cuenta_debito",
        modalidadPago?.value ===
            "DebitoAutomatico"
            ? (
                cuentaDebito?.value ||
                ""
            )
            : ""
    );


    datos.append(
    "tipo_comprobante",
        tipoComprobante?.value || ""
    );


    datos.append(
        "numero_comprobante",
        comprobanteNormalizado
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
     * DÉBITO AUTOMÁTICO
     * =========================================
     */

    datos.append(
        "debito_automatico",
        JSON.stringify(
            debitoAutomaticoPreparado
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

/*
 * =========================================
 * CUENTAS PARA DÉBITO AUTOMÁTICO
 * =========================================
 *
 * Carga las cuentas bancarias disponibles para
 * la modalidad prevista Débito automático.
 *
 * Reglas Beta:
 *
 * - pertenecen a la empresa activa;
 * - solamente se muestran cuentas en ARS;
 * - el endpoint de Cuentas Bancarias entrega
 *   las cuentas disponibles de la empresa.
 *
 * No se crea ningún Pago en esta instancia.
 * Solamente se define la cuenta prevista desde
 * la cual se espera que ocurra el débito.
 */


async function cargarCuentasDebitoRegistro(){

    const empresa =
        document.getElementById(
            "empresaActiva"
        );


    const select =
        document.getElementById(
            "cuentaDebitoRegistro"
        );


    if(
        !empresa ||
        !empresa.value ||
        !select
    ){

        return;

    }


    const valorAnterior =
        select.value;


    select.innerHTML = `

        <option value="">
            Seleccione una cuenta...
        </option>

    `;


    try{

        const respuesta =
            await fetch(
                `/cuentas-bancarias/?empresa=${encodeURIComponent(empresa.value)}`
            );


        const resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !resultado.ok ||
            !Array.isArray(
                resultado.cuentas
            )
        ){

            console.error(
                "No se pudieron cargar las cuentas para débito automático."
            );

            return;

        }


        /*
         * =========================================
         * BETA ORDENACLICK
         * SOLO CUENTAS EN PESOS
         * =========================================
         */

        resultado.cuentas

            .filter(
                function(cuenta){

                    return (
                        cuenta.moneda ===
                        "ARS"
                    );

                }
            )

            .forEach(
                function(cuenta){

                    const opcion =
                        document.createElement(
                            "option"
                        );


                    opcion.value =
                        String(
                            cuenta.id
                        );


                    opcion.textContent =
                        `${cuenta.banco} · ${cuenta.nombre}`;


                    select.appendChild(
                        opcion
                    );

                }
            );


        /*
         * Si la cuenta seleccionada anteriormente
         * continúa disponible, la conservamos.
         */

        if(
            valorAnterior &&
            select.querySelector(
                `option[value="${valorAnterior}"]`
            )
        ){

            select.value =
                valorAnterior;

        }


    }catch(error){

        console.error(
            "Error cargando cuentas para débito automático:",
            error
        );

    }

}

/*
 * =========================================
 * PREVISIÓN DE PAGO
 * =========================================
 *
 * Controla la modalidad prevista del Movimiento.
 *
 * Pago manual:
 * - no requiere una cuenta bancaria;
 * - conserva el espacio visual de la segunda
 *   columna para no alterar la alineación.
 *
 * Débito automático:
 * - muestra la cuenta prevista para el débito;
 * - todavía no crea ningún Pago real.
 */

function normalizarComprobanteRegistro(){

    const puntoVenta =
        document.getElementById(
            "puntoVentaComprobanteRegistro"
        );


    const numero =
        document.getElementById(
            "numeroComprobanteRegistro"
        );


    if(
        puntoVenta &&
        puntoVenta.value.trim() !== ""
    ){

        const valorPuntoVenta =
            puntoVenta.value.trim();


        if(
            /^\d{1,4}$/.test(
                valorPuntoVenta
            )
        ){

            puntoVenta.value =
                valorPuntoVenta.padStart(
                    4,
                    "0"
                );

        }

    }


    if(
        numero &&
        numero.value.trim() !== ""
    ){

        const valorNumero =
            numero.value.trim();


        if(
            /^\d{1,8}$/.test(
                valorNumero
            )
        ){

            numero.value =
                valorNumero.padStart(
                    8,
                    "0"
                );

        }

    }

}

function actualizarPrevisionPagoRegistro(){

    const modalidad =
        document.getElementById(
            "modalidadPagoRegistro"
        );


    const campoCuenta =
        document.getElementById(
            "campoCuentaDebitoRegistro"
        );


    const cuenta =
        document.getElementById(
            "cuentaDebitoRegistro"
        );


    const listaPagos =
        document.getElementById(
            "listaPagosRegistro"
        );


    if(
        !modalidad ||
        !campoCuenta ||
        !cuenta
    ){

        return;

    }


    const esDebitoAutomatico =
        modalidad.value ===
        "DebitoAutomatico";


    /*
     * El botón debe reflejar siempre
     * la modalidad seleccionada.
     */

    actualizarBotonPagoSegunModalidad();


    if(esDebitoAutomatico){

        campoCuenta.style.visibility =
            "visible";

        campoCuenta.style.pointerEvents =
            "auto";

        cuenta.disabled =
            false;


        cargarCuentasDebitoRegistro();


        /*
         * =========================================
         * DESCARTAR BORRADORES DE PAGO MANUAL
         * =========================================
         *
         * Mientras todavía no exista un Pago
         * persistido, los Pagos abiertos dentro
         * de Carga Simple son solamente borradores.
         *
         * Al pasar a Débito automático eliminamos
         * esos borradores para no mezclar ambas
         * modalidades dentro del mismo registro.
         */

        pagosRegistro = [];


        if(listaPagos){

            listaPagos.innerHTML =
                "";

        }


        limpiarPagoDebitoAutomaticoRegistro();


        actualizarResumenGeneralPagos();


        return;

    }


    /*
     * =========================================
     * PAGO MANUAL
     * =========================================
     */

    campoCuenta.style.visibility =
        "hidden";

    campoCuenta.style.pointerEvents =
        "none";

    cuenta.disabled =
        true;

    cuenta.value =
        "";


    /*
     * Si veníamos de Débito automático,
     * retiramos su formulario reducido.
     */

    limpiarPagoDebitoAutomaticoRegistro();


    actualizarResumenGeneralPagos();

}


/*
 * =========================================
 * EVENTO MODALIDAD DE PAGO
 * =========================================
 *
 * Carga Simple se genera dinámicamente.
 * Se utiliza delegación de eventos para
 * mantener todo el JavaScript fuera del HTML.
 */


document.addEventListener(
    "change",
    function(event){

        const modalidad =
            event.target.closest(
                "#modalidadPagoRegistro"
            );


        if(!modalidad){

            return;

        }


        actualizarPrevisionPagoRegistro();

    }
);

/*
 * =========================================
 * PAGO PREVISTO POR DÉBITO AUTOMÁTICO
 * =========================================
 *
 * Adapta la interfaz de Carga Simple cuando
 * el Movimiento tiene como modalidad prevista
 * Débito automático.
 *
 * En esta etapa el bloque es solamente visual.
 * El débito real todavía NO se incorpora a
 * pagosRegistro ni se persiste como Pago.
 *
 * Esto evita registrar accidentalmente el
 * importe como Efectivo, que es la estructura
 * utilizada actualmente por los Pagos manuales.
 */


function actualizarBotonPagoSegunModalidad(){

    const modalidad =
        document.getElementById(
            "modalidadPagoRegistro"
        );


    const boton =
        document.getElementById(
            "btnAgregarPagoRegistro"
        );


    if(
        !modalidad ||
        !boton
    ){

        return;

    }


    if(
        modalidad.value ===
        "DebitoAutomatico"
    ){

        boton.textContent =
            "Registrar Pago";

        return;

    }


    boton.textContent =
        "+ Agregar pago";

}


/*
 * =========================================
 * MOSTRAR REGISTRO DE DÉBITO AUTOMÁTICO
 * =========================================
 *
 * Muestra solamente los datos que necesitamos
 * para confirmar posteriormente el débito real:
 *
 * - Fecha de Pago.
 * - Importe debitado.
 *
 * La cuenta bancaria no se vuelve a solicitar
 * porque ya fue definida en la previsión del
 * Movimiento.
 */


function mostrarPagoDebitoAutomaticoRegistro(){

    const lista =
        document.getElementById(
            "listaPagosRegistro"
        );


    if(!lista){

        return;

    }


    /*
     * Para esta modalidad solamente necesitamos
     * un bloque de confirmación del débito.
     */

    lista.innerHTML = `

        <div
            id="pagoDebitoAutomaticoRegistro"
            style="
                background:#171c26;
                border:1px solid #252c3d;
                border-radius:24px;
                padding:32px;
            "
        >

            <div
                style="
                    display:flex;
                    align-items:center;
                    justify-content:space-between;
                    margin-bottom:22px;
                "
            >

                <strong>
                    Registrar débito
                </strong>

                <span
                    style="
                        color:#8b93a7;
                        font-size:13px;
                    "
                >
                    Débito automático
                </span>

            </div>


            <div class="form-grid">

                <div class="field">

                    <label
                        class="label"
                        for="fechaPagoDebitoAutomaticoRegistro"
                    >
                        Fecha de Pago
                    </label>

                    <input
                        id="fechaPagoDebitoAutomaticoRegistro"
                        type="date"
                        class="input-box"
                    >

                </div>


                <div class="field">

                    <label
                        class="label"
                        for="importePagoDebitoAutomaticoRegistro"
                    >
                        Importe
                    </label>

                    <input
                        id="importePagoDebitoAutomaticoRegistro"
                        type="text"
                        inputmode="decimal"
                        class="input-box"
                    >

                </div>

            </div>

        </div>

    `;

}


/*
 * =========================================
 * LIMPIAR REGISTRO DE DÉBITO
 * =========================================
 */


function limpiarPagoDebitoAutomaticoRegistro(){

    const bloque =
        document.getElementById(
            "pagoDebitoAutomaticoRegistro"
        );


    if(bloque){

        bloque.remove();

    }

}

/*
 * =========================================
 * ADAPTADOR AGREGAR / REGISTRAR PAGO
 * =========================================
 *
 * Conservamos intacto agregarPagoRegistro()
 * para Pago manual.
 *
 * Cuando la modalidad prevista es Débito
 * automático desviamos la acción hacia el
 * bloque reducido.
 */


if(
    typeof agregarPagoRegistro ===
    "function"
){

    const agregarPagoRegistroManual =
        agregarPagoRegistro;


    agregarPagoRegistro =
        function(){

            const modalidad =
                document.getElementById(
                    "modalidadPagoRegistro"
                );


            if(
                modalidad &&
                modalidad.value ===
                    "DebitoAutomatico"
            ){

                mostrarPagoDebitoAutomaticoRegistro();

                return;

            }


            agregarPagoRegistroManual();

        };

}

/*
 * =========================================
 * VERIFICACIÓN TEMPRANA DE COMPROBANTES
 * =========================================
 *
 * Consulta al backend cuando ya están completos
 * los datos que identifican documentalmente
 * un comprobante:
 *
 * - Empresa.
 * - Proveedor.
 * - Tipo de comprobante.
 * - Punto de venta.
 * - Número.
 *
 * La validación definitiva se mantiene también
 * en guardar_movimiento().
 */

let ultimaClaveComprobanteDuplicadoAvisada =
    "";


/**
 * Verifica si el comprobante actualmente cargado
 * ya existe para la empresa y el proveedor.
 *
 * La función solamente consulta al backend cuando
 * todos los datos necesarios están completos.
 */
async function verificarComprobanteDuplicadoRegistro(){

    const empresa =
        document.getElementById(
            "empresaActiva"
        );

    const proveedor =
        document.getElementById(
            "proveedorRegistro"
        );

    const tipoComprobante =
        document.getElementById(
            "tipoComprobanteRegistro"
        );

    const puntoVenta =
        document.getElementById(
            "puntoVentaComprobanteRegistro"
        );

    const numeroComprobante =
        document.getElementById(
            "numeroComprobanteRegistro"
        );


    if(
        !empresa?.value ||
        !proveedor?.value ||
        !tipoComprobante?.value ||
        !puntoVenta?.value ||
        !numeroComprobante?.value
    ){

        ultimaClaveComprobanteDuplicadoAvisada =
            "";

        return;

    }


    let puntoVentaNormalizado =
        puntoVenta.value.trim();

    let numeroNormalizado =
        numeroComprobante.value.trim();


    if(
        !/^\d{1,4}$/.test(
            puntoVentaNormalizado
        ) ||
        !/^\d{1,8}$/.test(
            numeroNormalizado
        )
    ){

        return;

    }


    puntoVentaNormalizado =
        puntoVentaNormalizado.padStart(
            4,
            "0"
        );

    numeroNormalizado =
        numeroNormalizado.padStart(
            8,
            "0"
        );


    puntoVenta.value =
        puntoVentaNormalizado;

    numeroComprobante.value =
        numeroNormalizado;


    const comprobanteNormalizado =
        puntoVentaNormalizado +
        "-" +
        numeroNormalizado;


    const claveActual =
        [
            empresa.value,
            proveedor.value,
            tipoComprobante.value,
            comprobanteNormalizado
        ].join(
            "|"
        );


    const parametros =
        new URLSearchParams(
            {
                empresa:
                    empresa.value,

                proveedor:
                    proveedor.value,

                tipo_comprobante:
                    tipoComprobante.value,

                numero_comprobante:
                    comprobanteNormalizado
            }
        );


    try{

        const respuesta =
            await fetch(
                "/movimientos/verificar-comprobante/?" +
                parametros.toString(),
                {
                    method:
                        "GET",

                    headers:
                        {
                            "X-Requested-With":
                                "XMLHttpRequest"
                        }
                }
            );


        const tipoContenido =
            respuesta.headers.get(
                "content-type"
            ) || "";


        if(
            !tipoContenido.includes(
                "application/json"
            )
        ){

            return;

        }


        const resultado =
            await respuesta.json();


        if(
            !respuesta.ok ||
            !resultado.ok
        ){

            console.warn(
                "No se pudo verificar el comprobante:",
                resultado.mensaje || ""
            );

            return;

        }


        if(
            !resultado.duplicado
        ){

            ultimaClaveComprobanteDuplicadoAvisada =
                "";

            return;

        }


        if(
            ultimaClaveComprobanteDuplicadoAvisada ===
            claveActual
        ){

            return;

        }


        ultimaClaveComprobanteDuplicadoAvisada =
            claveActual;


        alert(
            "Ese comprobante ya fue registrado para este proveedor."
        );


        numeroComprobante.focus();

        numeroComprobante.select();


    }catch(error){

        console.error(
            "Error verificando comprobante:",
            error
        );

    }

}


/*
 * =========================================
 * EVENTOS DE VERIFICACIÓN
 * =========================================
 *
 * Como Carga Simple se genera dinámicamente,
 * utilizamos delegación de eventos sobre document.
 */

document.addEventListener(
    "focusout",
    function(event){

        if(
            event.target.id !==
                "puntoVentaComprobanteRegistro" &&
            event.target.id !==
                "numeroComprobanteRegistro"
        ){

            return;

        }


        verificarComprobanteDuplicadoRegistro();

    }
);


document.addEventListener(
    "change",
    function(event){

        if(
            event.target.id !==
                "empresaActiva" &&
            event.target.id !==
                "proveedorRegistro" &&
            event.target.id !==
                "tipoComprobanteRegistro"
        ){

            return;

        }


        ultimaClaveComprobanteDuplicadoAvisada =
            "";


        verificarComprobanteDuplicadoRegistro();

    }
);