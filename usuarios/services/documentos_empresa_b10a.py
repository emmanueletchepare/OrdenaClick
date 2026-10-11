"""Validaciones de archivos legales de Empresa (B10a)."""
from usuarios.services.adjuntos_financieros_b10a import MAX_ADJUNTO_BYTES

CAMPOS = frozenset(('estatuto', 'acta', 'designacion'))


def validar_documentos_empresa(archivos):
    """Valida peso real y cabecera; no consume los archivos recibidos."""
    for campo in CAMPOS:
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
