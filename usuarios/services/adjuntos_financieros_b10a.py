"""Límite técnico inicial por adjunto empresarial o financiero (20 MiB)."""

MAX_ADJUNTO_BYTES = 20 * 1024 * 1024


def validar_adjuntos_financieros(archivos):
    """Revisa todos los uploads y restaura su posición antes de persistir."""
    for nombre in archivos:
        for archivo in archivos.getlist(nombre):
            if archivo.size > MAX_ADJUNTO_BYTES:
                raise ValueError("El archivo adjunto supera el límite de 20 MB.")
            posicion = archivo.tell()
            total = 0
            try:
                for bloque in archivo.chunks():
                    total += len(bloque)
                    if total > MAX_ADJUNTO_BYTES:
                        raise ValueError("El archivo adjunto supera el límite de 20 MB.")
            finally:
                archivo.seek(posicion)
