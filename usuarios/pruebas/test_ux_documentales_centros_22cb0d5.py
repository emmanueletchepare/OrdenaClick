"""Contrato UI de documentos/centros: sin modificar servicios o permisos."""
from pathlib import Path
from django.conf import settings
from django.test import SimpleTestCase

class AjusteVisualDocumentalesCentrosTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = Path(settings.BASE_DIR)
        cls.empresa = (root / 'templates/usuarios/perfiles/administrador/partials/main.html').read_text(encoding='utf-8')
        cls.centros = (root / 'templates/usuarios/maestros/centros_operativos.html').read_text(encoding='utf-8')
        cls.js = (root / 'static/js/maestros/habilitaciones_centros.js').read_text(encoding='utf-8')
        cls.css = (root / 'static/css/empresa/vencimientos_documentales.css').read_text(encoding='utf-8')

    def test_documentos_grilla_y_fechas(self):
        self.assertEqual(self.empresa.count('class="field oc-sociedad-documento"'), 1)
        self.assertIn('class="field oc-acta-directorio oc-sociedad-documento"', self.empresa)
        self.assertNotIn('class="field field-full"\n\n<label\nclass="label"\nstyle="\ndisplay:block;\nmargin-top:20px;\n">\n\nDesignación', self.empresa)
        for field in ('vencimiento_designacion', 'vencimiento_acta_directorio'):
            self.assertEqual(self.empresa.count('name="' + field + '"'), 1)
        self.assertNotIn('name="acta"', self.empresa)
        self.assertIn('class="field field-full oc-sociedad-estatuto"', self.empresa)
        self.assertIn('grid-column:2', self.css)

    def test_habilitaciones_solo_en_formulario_superior(self):
        self.assertIn('<details class="oc-centros-documentacion"', self.centros)
        self.assertIn('data-oc-centro-editar-documentacion="{{ centro.pk }}"', self.centros)
        self.assertNotIn('<details class="oc-habilitaciones-centro"', self.centros)
        self.assertEqual(self.centros.count('class="oc-habilitaciones-centro"'), 1)
        self.assertLess(self.centros.index('class="oc-centros-documentacion"'), self.centros.index('id="buscarCentroOperativoABM"'))
        self.assertIn('onclick="modificarCentroOperativo(', self.centros)
        self.assertIn('onclick="eliminarCentroOperativo(', self.centros)

    def test_archivo_estandar_y_retorno(self):
        self.assertIn('class="file-btn"', self.centros)
        self.assertIn('data-oc-archivo-nombre', self.centros)
        self.assertIn('mostrarABMCentrosOperativos(origenABM)', self.js)
        self.assertIn('seleccionarCentro(centroId)', self.js)
        self.assertIn('seleccionarCentro(null)', self.js)
