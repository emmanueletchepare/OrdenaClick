from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from django.utils.datastructures import MultiValueDict
from usuarios.services.documentos_empresa_b10a import validar_documentos_empresa


class DocumentosEmpresaB10aTests(SimpleTestCase):
    def test_pdf_aceptado_y_posicion_conservada(self):
        f = SimpleUploadedFile('estatuto.pdf', b'%PDF-1.7\ncontenido')
        validar_documentos_empresa(MultiValueDict({'estatuto': [f]}))
        self.assertEqual(f.tell(), 0)

    def test_jpeg_aceptado(self):
        f = SimpleUploadedFile('acta.jpg', b'\xff\xd8\xff' + b'0' * 32)
        validar_documentos_empresa(MultiValueDict({'acta': [f]}))

    def test_png_aceptado(self):
        f = SimpleUploadedFile('designacion.png', b'\x89PNG\r\n\x1a\n' + b'0' * 32)
        validar_documentos_empresa(MultiValueDict({'designacion': [f]}))

    def test_html_disfrazado_rechazado(self):
        f = SimpleUploadedFile('estatuto.pdf', b'<html>contenido</html>')
        with self.assertRaises(ValueError):
            validar_documentos_empresa(MultiValueDict({'estatuto': [f]}))
        self.assertEqual(f.tell(), 0)

    def test_tamano_declarado_rechazado(self):
        f = SimpleUploadedFile('acta.pdf', b'%PDF-1.7\n')
        f.size = 21 * 1024 * 1024
        with self.assertRaises(ValueError):
            validar_documentos_empresa(MultiValueDict({'acta': [f]}))
