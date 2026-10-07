from decimal import Decimal

from usuarios.services.cheques import (
    normalizar_numero_cheque,
    validar_fechas_cheque,
)


# =========================================
# COBRANZAS / INGRESOS DE CAJA
# =========================================

def validar_cobranza(
    empresa,
    cobranza_datos,
):
    """
    Valida y normaliza una Cobranza antes de persistirla.

    La Cobranza puede contener efectivo en ARS y/o USD y cheques físicos
    de terceros. El total declarado debe coincidir con la suma de todos
    los componentes recibidos.

    Esta función no persiste información ni depende de request o de
    formularios HTTP. Devuelve una estructura normalizada apta para el
    servicio de creación de la Cobranza.

    Lanza ValueError cuando algún dato no cumple las reglas del dominio.
    """
    from datetime import datetime
    from decimal import (
        Decimal,
        InvalidOperation,
    )

    from usuarios.models import (
        Banco,
        Caja,
        Cliente,
    )

    if not isinstance(cobranza_datos, dict):
        raise ValueError(
            "La Cobranza tiene un formato inválido."
        )

    # =========================================
    # CAJA
    # =========================================

    caja_id = cobranza_datos.get("caja_id")

    try:
        caja = Caja.objects.get(
            id=caja_id,
            empresa=empresa,
            activo=True,
        )
    except (
        Caja.DoesNotExist,
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "La Caja seleccionada no es válida para esta Empresa."
        ) from error

    if caja.centro_operativo.tipo not in {
        "Casa Central",
        "Sucursal",
        "Mostrador",
    }:
        raise ValueError(
            "La Caja seleccionada no pertenece a una "
            "Casa Central, Sucursal o Mostrador."
        )

    # =========================================
    # FECHA
    # =========================================

    fecha_raw = str(
        cobranza_datos.get("fecha", "") or ""
    ).strip()

    if not fecha_raw:
        raise ValueError(
            "La Cobranza debe tener una fecha."
        )

    try:
        fecha = datetime.strptime(
            fecha_raw,
            "%Y-%m-%d",
        ).date()
    except ValueError as error:
        raise ValueError(
            "La fecha de la Cobranza no es válida."
        ) from error

    # =========================================
    # DATOS GENERALES
    # =========================================

    referencia = str(
        cobranza_datos.get("referencia", "") or ""
    ).strip()

    if not referencia:
        raise ValueError(
            "La referencia de la Cobranza es obligatoria."
        )

    if len(referencia) > 200:
        raise ValueError(
            "La referencia de la Cobranza es demasiado extensa."
        )

    vendedor_referencia = str(
        cobranza_datos.get(
            "vendedor_referencia",
            "",
        )
        or ""
    ).strip()

    if len(vendedor_referencia) > 150:
        raise ValueError(
            "La referencia del vendedor es demasiado extensa."
        )

    observaciones = str(
        cobranza_datos.get("observaciones", "") or ""
    ).strip()

    # =========================================
    # TOTAL DECLARADO
    # =========================================
    #
    # El total declarado es un dato opcional de control.
    # Su ausencia no representa cero: se conserva como None.
    # Cuando se informa, debe ser positivo y posteriormente
    # se utiliza para conciliar Efectivo ARS + Cheques.
    #

    total_declarado_raw = cobranza_datos.get(
        "total_declarado"
    )

    if (
        total_declarado_raw is None
        or str(total_declarado_raw).strip() == ""
    ):
        total_declarado = None

    else:
        try:
            total_declarado = Decimal(
                str(total_declarado_raw)
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                "El total declarado de la Cobranza no es válido."
            ) from error

        if total_declarado <= Decimal("0.00"):
            raise ValueError(
                "El total declarado debe ser mayor que cero."
            )

    # =========================================
    # EFECTIVO
    # =========================================

    efectivo_raw = (
        cobranza_datos.get("efectivo")
        or {}
    )

    if not isinstance(efectivo_raw, dict):
        raise ValueError(
            "El efectivo de la Cobranza tiene un formato inválido."
        )

    efectivo = {}

    for moneda in ("ARS", "USD"):
        valor_raw = efectivo_raw.get(
            moneda,
            "0.00",
        )

        try:
            importe = Decimal(
                str(valor_raw or "0.00")
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"El importe en efectivo {moneda} no es válido."
            ) from error

        if importe < Decimal("0.00"):
            raise ValueError(
                f"El efectivo {moneda} no puede ser negativo."
            )

        if importe > Decimal("0.00"):
            efectivo[moneda] = importe

    # =========================================
    # CHEQUES FÍSICOS RECIBIDOS
    # =========================================

    cheques_raw = (
        cobranza_datos.get("cheques")
        or []
    )

    if not isinstance(cheques_raw, list):
        raise ValueError(
            "Los cheques de la Cobranza tienen un formato inválido."
        )

    cheques = []
    total_cheques = Decimal("0.00")

    for indice, cheque_raw in enumerate(
        cheques_raw,
        start=1,
    ):
        if not isinstance(cheque_raw, dict):
            raise ValueError(
                f"El cheque {indice} tiene un formato inválido."
            )

        try:
            numero = normalizar_numero_cheque(
                cheque_raw.get(
                    "numero",
                    "",
                )
            )
        except ValueError as error:
            raise ValueError(
                f"Cheque {indice}: {error}"
            ) from error

        try:
            importe = Decimal(
                str(
                    cheque_raw.get(
                        "importe",
                        "0.00",
                    )
                )
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"El importe del cheque {indice} no es válido."
            ) from error

        if importe <= Decimal("0.00"):
            raise ValueError(
                f"El importe del cheque {indice} debe ser mayor que cero."
            )

        banco_id = cheque_raw.get("banco_id")

        try:
            banco = Banco.objects.get(
                id=banco_id,
                empresa=empresa,
            )
        except (
            Banco.DoesNotExist,
            TypeError,
            ValueError,
        ) as error:
            raise ValueError(
                f"El banco del cheque {indice} no es válido."
            ) from error

        cliente = None
        cliente_id = cheque_raw.get("cliente_id")

        if cliente_id not in (
            None,
            "",
        ):
            try:
                cliente = Cliente.objects.get(
                    id=cliente_id,
                    empresa=empresa,
                    activo=True,
                )
            except (
                Cliente.DoesNotExist,
                TypeError,
                ValueError,
            ) as error:
                raise ValueError(
                    f"El Cliente del cheque {indice} no es válido."
                ) from error

        fecha_acreditacion = _validar_fecha_opcional_cobranza(
            cheque_raw.get("fecha_acreditacion"),
            f"fecha de acreditación del cheque {indice}",
        )

        tipo_cheque = str(
            cheque_raw.get(
                "tipo_cheque",
                "Diferido",
            )
            or ""
        ).strip()

        try:
            (
                fecha_emision,
                fecha_acreditacion,
            ) = validar_fechas_cheque(
                tipo_cheque,
                cheque_raw.get(
                    "fecha_emision",
                    "",
                ),
                cheque_raw.get(
                    "fecha_acreditacion",
                    "",
                ),
            )
        except ValueError as error:
            raise ValueError(
                f"Cheque {indice}: {error}"
            ) from error

        fecha_vencimiento = _validar_fecha_opcional_cobranza(
            cheque_raw.get(
                "fecha_vencimiento"
            ),
            f"fecha de vencimiento del cheque {indice}",
        )

        quien_entrega = str(
            cheque_raw.get(
                "quien_entrega",
                "",
            )
            or ""
        ).strip()

        if len(quien_entrega) > 200:
            raise ValueError(
                f"El dato de entrega del cheque {indice} es demasiado extenso."
            )

        cheques.append({
            "numero": numero,
            "importe": importe,
            "banco": banco,
            "cliente": cliente,
            "tipo_cheque": tipo_cheque,
            "fecha_emision": fecha_emision,
            "fecha_acreditacion": fecha_acreditacion,
            "fecha_vencimiento": fecha_vencimiento,
            "quien_entrega": quien_entrega,
        })

        total_cheques += importe

    # =========================================
    # CONCILIACIÓN
    # =========================================
    #
    # El Total declarado es opcional y funciona exclusivamente
    # como control. Si fue informado, debe coincidir con los
    # componentes recibidos expresados en ARS.
    #
    # En esta primera versión, USD no se convierte a ARS y por
    # lo tanto no participa de esta conciliación.
    #

    total_efectivo_ars = efectivo.get(
        "ARS",
        Decimal("0.00"),
    )

    total_componentes_ars = (
        total_efectivo_ars
        + total_cheques
    )

    if (
        total_declarado is not None
        and total_componentes_ars != total_declarado
    ):
        diferencia = (
            total_componentes_ars
            - total_declarado
        )

        raise ValueError(
            "La Cobranza no concilia. "
            f"Diferencia: {diferencia:.2f}."
        )

    if (
        not efectivo
        and not cheques
    ):
        raise ValueError(
            "La Cobranza debe contener al menos un medio recibido."
        )

    return {
        "caja": caja,
        "fecha": fecha,
        "referencia": referencia,
        "vendedor_referencia": vendedor_referencia,
        "total_declarado": total_declarado,
        "observaciones": observaciones,
        "efectivo": efectivo,
        "cheques": cheques,
        "total_cheques": total_cheques,
        "total_componentes_ars": total_componentes_ars,
    }


def _validar_fecha_opcional_cobranza(
    valor,
    descripcion,
):
    """
    Normaliza una fecha opcional utilizada por los componentes de una
    Cobranza.

    Devuelve None cuando no se informó una fecha y lanza ValueError
    cuando el valor recibido no utiliza el formato ISO YYYY-MM-DD.
    """
    from datetime import datetime

    valor = str(
        valor or ""
    ).strip()

    if not valor:
        return None

    try:
        return datetime.strptime(
            valor,
            "%Y-%m-%d",
        ).date()
    except ValueError as error:
        raise ValueError(
            f"La {descripcion} no es válida."
        ) from error

def crear_cobranza_validada(
    empresa,
    usuario,
    cobranza_datos,
):
    """
    Crea una Cobranza y todos sus componentes financieros dentro de una
    única transacción atómica.

    Primero valida y normaliza la información recibida. Luego crea la
    cabecera de Cobranza, los movimientos de efectivo y los cheques
    físicos de terceros incorporados a cartera.

    Si falla cualquier componente, la transacción completa se revierte
    para evitar cobranzas parciales o disponibilidades inconsistentes.
    """
    from django.db import transaction

    from usuarios.models import (
        Cheque,
        Cobranza,
        MovimientoCaja,
    )

    datos = validar_cobranza(
        empresa=empresa,
        cobranza_datos=cobranza_datos,
    )

    if not usuario or not usuario.is_authenticated:
        raise ValueError(
            "Se requiere un usuario autenticado para registrar la Cobranza."
        )

    from usuarios.services.identidades import obtener_identidad_usuario_empresa

    with transaction.atomic():
        identidad_usuario = obtener_identidad_usuario_empresa(
            empresa=empresa,
            usuario=usuario,
        )

        cobranza = Cobranza.objects.create(
            empresa=empresa,
            caja=datos["caja"],
            fecha=datos["fecha"],
            referencia=datos["referencia"],
            vendedor_referencia=datos[
                "vendedor_referencia"
            ],
            total_declarado=datos[
                "total_declarado"
            ],
            observaciones=datos[
                "observaciones"
            ],
            creado_por=identidad_usuario,
        )

        movimientos_efectivo = []

        for moneda, importe in datos[
            "efectivo"
        ].items():

            movimiento = MovimientoCaja.objects.create(
                empresa=empresa,
                caja=datos["caja"],
                cobranza=cobranza,
                fecha=datos["fecha"],
                tipo="Ingreso",
                moneda=moneda,
                importe=importe,
                concepto=(
                    f"Cobranza: {datos['referencia']}"
                ),
                creado_por=identidad_usuario,
            )

            movimientos_efectivo.append(
                movimiento
            )

        cheques_creados = []

        for cheque_datos in datos[
            "cheques"
        ]:

            cheque = Cheque.objects.create(
                empresa=empresa,
                cobranza=cobranza,
                caja=datos["caja"],
                cliente=cheque_datos[
                    "cliente"
                ],
                pago=None,
                tipo_instrumento="Cheque",
                origen="Tercero",
                tipo_cheque=cheque_datos[
                    "tipo_cheque"
                ],
                banco=cheque_datos[
                    "banco"
                ],
                cuenta_bancaria=None,
                numero=cheque_datos[
                    "numero"
                ],
                importe=cheque_datos[
                    "importe"
                ],
                fecha_emision=cheque_datos[
                    "fecha_emision"
                ],
                fecha_acreditacion=cheque_datos[
                    "fecha_acreditacion"
                ],
                fecha_vencimiento=cheque_datos[
                    "fecha_vencimiento"
                ],
                quien_entrega=cheque_datos[
                    "quien_entrega"
                ],
                estado="Disponible",
            )

            cheques_creados.append(
                cheque
            )

    return {
        "cobranza": cobranza,
        "movimientos_efectivo":
            movimientos_efectivo,
        "cheques":
            cheques_creados,
    }
