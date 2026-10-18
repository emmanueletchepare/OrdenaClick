"""Formato institucional aprobado: boceto OrdenaClick de gestión bancaria.

Generación paginada desde una operación ya confirmada, sin datos del navegador.
"""
from io import BytesIO
from pathlib import Path
from django.conf import settings
from django.utils import timezone


def crear_documento(*, titulo, subtitulo, empresa, referencia, fecha, emisor, secciones, datos, total, nota):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError as exc:
        raise RuntimeError('Falta reportlab: pip install reportlab>=4,<5') from exc

    logo = Path(settings.BASE_DIR) / 'static' / 'branding' / 'ordenaclick_logo_horizontal.png'
    if not logo.is_file():
        raise RuntimeError('Logo institucional no disponible.')
    W, H = A4
    margen = 44
    azul_oscuro = HexColor('#14243D')
    azul = HexColor('#1674D8')
    fondo = HexColor('#EAF2FC')
    gris = HexColor('#5D6D83')
    borde = HexColor('#DCE4ED')
    blanco = HexColor('#FFFFFF')
    fuentes = Path(settings.BASE_DIR) / 'static' / 'branding'
    # Fuente incorporada por ReportLab si la fuente corporativa no está disponible.
    fuente = 'Helvetica'
    negrita = 'Helvetica-Bold'
    for f in ('DejaVuSans.ttf', 'DejaVuSans-Bold.ttf'):
        if not (fuentes / f).is_file():
            break
    else:
        pdfmetrics.registerFont(TTFont('OCNormal', str(fuentes / 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('OCBold', str(fuentes / 'DejaVuSans-Bold.ttf')))
        fuente, negrita = 'OCNormal', 'OCBold'

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(str(titulo))
    c.setAuthor('OrdenaClick')
    try:
        fecha_emision = timezone.localtime(fecha).strftime('%d/%m/%Y · %H:%M')
    except (ValueError, TypeError):
        fecha_emision = str(fecha)

    def truncar(valor, ancho, tam=9, bold=False):
        s = str(valor or '—')
        nombre = negrita if bold else fuente
        if pdfmetrics.stringWidth(s, nombre, tam) <= ancho:
            return s
        while s and pdfmetrics.stringWidth(s + '…', nombre, tam) > ancho:
            s = s[:-1]
        return s + '…'

    def texto(x, y, valor, tam=9, color=azul_oscuro, bold=False):
        c.setFillColor(color)
        c.setFont(negrita if bold else fuente, tam)
        c.drawString(x, y, str(valor))

    def derecha(x, y, valor, tam=9, color=azul_oscuro, bold=False):
        c.setFillColor(color)
        c.setFont(negrita if bold else fuente, tam)
        c.drawRightString(x, y, str(valor))

    def linea(y):
        c.setStrokeColor(borde)
        c.setLineWidth(.8)
        c.line(margen, y, W - margen, y)

    pagina = 0
    def iniciar():
        nonlocal pagina
        pagina += 1
        c.setFillColor(azul_oscuro)
        c.rect(0, H - 10, W, 10, stroke=0, fill=1)
        c.drawImage(str(logo), margen, H - 103, width=232, height=60,
                    preserveAspectRatio=True, anchor='c', mask='auto')
        derecha(W - margen, H - 66, 'DOCUMENTO OPERATIVO', 8, gris, True)
        derecha(W - margen, H - 85, 'N.º ' + str(referencia), 8, gris)
        linea(H - 111)
        texto(margen, H - 151, titulo, 17, azul_oscuro, True)
        texto(margen, H - 172, subtitulo, 9, gris)
        c.setFillColor(fondo)
        c.roundRect(margen, H - 228, W - margen * 2, 40, 7, stroke=0, fill=1)
        texto(58, H - 204, 'EMPRESA', 7, gris, True)
        texto(58, H - 220, truncar(empresa, 310, 9, True), 9, azul_oscuro, True)
        derecha(W - 58, H - 204, 'EMITIDO', 7, gris, True)
        derecha(W - 58, H - 220, fecha_emision, 9, azul_oscuro)
        # Pie idéntico al boceto, con usuario y referencia en las páginas.
        linea(92)
        texto(margen, 77, 'Emitido por: ' + truncar(emisor, 260, 8), 8, gris)
        texto(margen, 61, 'Referencia: ' + str(referencia) + ' · Detalle generado desde la operación confirmada.', 7, gris)
        texto(margen, 45, truncar(nota, 445, 7), 7, gris)
        derecha(W - margen, 45, str(pagina), 7, gris)
        c.setFillColor(azul)
        c.rect(0, 0, W, 5, stroke=0, fill=1)

    iniciar()
    y = H - 258
    texto(margen, y, 'DATOS DE DESTINO', 9, azul, True)
    linea(y - 12)
    for i, (etiqueta, valor) in enumerate(datos):
        if i > 4:
            break
        pos = y - 34 - i * 22
        texto(margen, pos, etiqueta, 8, gris)
        texto(172, pos, truncar(valor, W - 216, 9, i == 0), 9, azul_oscuro, i == 0)
    y -= max(113, 46 + len(datos) * 22)

    def nueva_pagina():
        nonlocal y
        c.showPage()
        iniciar()
        y = H - 267

    for nombre, subtotal, filas in secciones:
        if y < 210:
            nueva_pagina()
        c.setFillColor(fondo)
        c.roundRect(margen, y - 25, W - margen * 2, 31, 5, stroke=0, fill=1)
        texto(56, y - 14, str(nombre).upper(), 10, azul_oscuro, True)
        derecha(W - 56, y - 14, subtotal, 10, azul_oscuro, True)
        y -= 32
        def encabezado():
            texto(56, y - 14, 'N.º', 7, gris, True)
            texto(92, y - 14, 'E-CHEQ', 7, gris, True)
            texto(250, y - 14, 'ACREDITACIÓN', 7, gris, True)
            derecha(W - 56, y - 14, 'IMPORTE', 7, gris, True)
        encabezado()
        y -= 38
        if not filas:
            texto(92, y, 'Sin e-Cheqs en esta categoría', 9, gris)
            y -= 45
        for numero, echeq, acreditacion, importe in filas:
            if y < 133:
                nueva_pagina()
                texto(margen, y, str(nombre).upper() + ' (continuación)', 9, azul_oscuro, True)
                y -= 20
                encabezado()
                y -= 38
            texto(56, y, f'{int(numero):02}', 8, gris)
            texto(92, y, truncar(echeq, 145), 9)
            texto(250, y, acreditacion, 8)
            derecha(W - 56, y, importe, 9, azul_oscuro, True)
            linea(y - 11)
            y -= 34
        y -= 25

    if y < 157:
        nueva_pagina()
    c.setFillColor(azul_oscuro)
    c.roundRect(margen, y - 48, W - margen * 2, 55, 8, stroke=0, fill=1)
    texto(58, y - 13, 'TOTAL OPERACIÓN', 10, blanco, True)
    derecha(W - 58, y - 26, total, 18, blanco, True)
    c.save()
    return buffer.getvalue()
