"""Validaciones de archivos legales de Empresa (B10a)."""
from datetime import date
from usuarios.services.adjuntos_financieros_b10a import MAX_ADJUNTO_BYTES

CAMPOS_VENCIMIENTO = ('vencimiento_acta_directorio', 'vencimiento_acta', 'vencimiento_designacion')


def leer_vencimientos_documentales(datos):
    """Fechas ingresadas; campos ausentes no se sobrescriben al editar."""
    fechas = {}
    for campo in CAMPOS_VENCIMIENTO:
        if campo not in datos:
            continue
        texto = (datos.get(campo) or '').strip()
        try:
            fechas[campo] = date.fromisoformat(texto) if texto else None
        except ValueError as exc:
            raise ValueError('Fecha de vencimiento inválida: ' + campo) from exc
    return fechas


CAMPOS = frozenset(('estatuto', 'acta', 'designacion', 'acta_directorio'))


def validar_documentos_empresa(archivos, campos=CAMPOS):
    """Valida peso real y cabecera; no consume los archivos recibidos."""
    for campo in campos:
        for archivo in archivos.getlist(campo):
            if archivo.size > MAX_ADJUNTO_BYTES:
                raise ValueError('El documento supera el límite de 20 MB.')
            posicion = archivo.tell()
            try:
                inicio = archivo.read(16)
                valido = (
                    inicio.startswith(b'%PDF-') or
                    inicio.startswith(b'\xff\xd8\xff') or
                    inicio.startswith(b'\x89PNG\r\n\x1a\n')
                )
                if not valido:
                    raise ValueError('Adjuntá un documento PDF, JPG o PNG válido.')
                archivo.seek(posicion)
                total = 0
                for bloque in archivo.chunks():
                    total += len(bloque)
                    if total > MAX_ADJUNTO_BYTES:
                        raise ValueError('El documento supera el límite de 20 MB.')
            finally:
                archivo.seek(posicion)
