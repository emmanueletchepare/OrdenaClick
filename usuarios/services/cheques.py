def normalizar_numero_cheque(valor):
    """
    Normaliza un número de cheque al formato canónico de OrdenaClick.

    Acepta entre 1 y 8 dígitos numéricos y devuelve siempre una cadena
    de exactamente 8 posiciones, completando con ceros a la izquierda.

    Ejemplo:
        1698 -> "00001698"

    No elimina caracteres arbitrarios: si el valor recibido contiene
    letras, espacios internos, signos u otros caracteres, se rechaza.
    """
    numero = str(
        valor or ""
    ).strip()

    if not numero:
        raise ValueError(
            "Ingrese el número del cheque."
        )

    if not numero.isdigit():
        raise ValueError(
            "El número del cheque debe contener sólo dígitos."
        )

    if len(numero) > 8:
        raise ValueError(
            "El número del cheque no puede superar los 8 dígitos."
        )

    return numero.zfill(8)


def validar_fechas_cheque(
    tipo_cheque,
    fecha_emision,
    fecha_acreditacion=None,
):
    """
    Valida y normaliza las fechas comunes de un cheque.

    Para cheque Común, la fecha de acreditación coincide con la fecha
    de emisión.

    Para cheque Diferido, la fecha de acreditación es obligatoria,
    debe ser posterior a la emisión y no puede superar los 360 días
    desde esa fecha.
    """
    from datetime import datetime

    tipo_cheque = str(
        tipo_cheque or ""
    ).strip()

    if tipo_cheque not in {
        "Comun",
        "Diferido",
    }:
        raise ValueError(
            "El tipo de cheque no es válido."
        )

    fecha_emision_raw = str(
        fecha_emision or ""
    ).strip()

    if not fecha_emision_raw:
        raise ValueError(
            "Ingrese la fecha de emisión del cheque."
        )

    try:
        fecha_emision_validada = datetime.strptime(
            fecha_emision_raw,
            "%Y-%m-%d",
        ).date()
    except ValueError as error:
        raise ValueError(
            "La fecha de emisión del cheque no es válida."
        ) from error

    if tipo_cheque == "Comun":
        return (
            fecha_emision_validada,
            fecha_emision_validada,
        )

    fecha_acreditacion_raw = str(
        fecha_acreditacion or ""
    ).strip()

    if not fecha_acreditacion_raw:
        raise ValueError(
            "Ingrese la fecha de acreditación del cheque diferido."
        )

    try:
        fecha_acreditacion_validada = datetime.strptime(
            fecha_acreditacion_raw,
            "%Y-%m-%d",
        ).date()
    except ValueError as error:
        raise ValueError(
            "La fecha de acreditación del cheque no es válida."
        ) from error

    if fecha_acreditacion_validada <= fecha_emision_validada:
        raise ValueError(
            "La fecha de acreditación del cheque diferido "
            "debe ser posterior a la fecha de emisión."
        )

    dias_diferencia = (
        fecha_acreditacion_validada
        - fecha_emision_validada
    ).days

    if dias_diferencia > 360:
        raise ValueError(
            "La fecha de acreditación del cheque diferido "
            "no puede superar los 360 días desde la emisión."
        )

    return (
        fecha_emision_validada,
        fecha_acreditacion_validada,
    )
