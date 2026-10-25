"""Contrato del panel segmentado: solo vista Alertas; no redefine fuentes.

Las pruebas de permisos, multiempresa, FIN-02/03 y movimientos permanecen
cubiertas por sus suites originales. Estas validan el cableado de la UI.
"""
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class PanelAlertasSegmentadoTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        raiz = Path(settings.BASE_DIR)
        cls.js = (raiz / 'static/js/componentes/vencimientos.js').read_text(encoding='utf-8')
        cls.css = (raiz / 'static/css/componentes/alertas_segmentadas.css').read_text(encoding='utf-8')
        cls.plantilla = (raiz / 'templates/usuarios/perfiles/administrador/panel.html').read_text(encoding='utf-8')

    def test_tres_segmentos_con_fuentes_reales(self):
        self.assertIn('function construirPanelAlertasSegmentado(datos)', self.js)
        self.assertIn("clave: 'compromisos'", self.js)
        self.assertIn("clave: 'instrumentos'", self.js)
        self.assertIn("clave: 'documentacion'", self.js)
        self.assertIn('datos.movimientos', self.js)
        self.assertIn('datos.alertas_instrumentos', self.js)
        self.assertIn('datos.licencias_nomina', self.js)
        self.assertIn('construirPanelAlertasSegmentado(datos);', self.js)

    def test_reutiliza_componentes_sin_perder_acciones_existentes(self):
        self.assertIn('while (contenedor.firstChild) tablaCompromisos.appendChild(contenedor.firstChild);', self.js)
        self.assertIn('mostrarAlertasInstrumentos(instrumentos, paneles[1]);', self.js)
        self.assertIn('mostrarAlertasLicenciasNomina(documentos, paneles[2]);', self.js)
        self.assertIn('function mostrarProximosVencimientos()', self.js)
        self.assertIn("/proximos-vencimientos/?empresa=", self.js)
        self.assertIn("/alertas/listado/?empresa=", self.js)

    def test_sin_falsas_alertas_documentales(self):
        self.assertIn('fuentes todavía no operativas; no generan avisos', self.js)
        self.assertIn("clave: 'documentacion', nombre: 'Documentación', cantidad: documentos.length", self.js)

    def test_pestanas_accesibles_y_estilos_aislados(self):
        for marca in ('aria-selected', 'aria-controls', 'role', 'tabpanel', 'ArrowRight', 'ArrowLeft'):
            self.assertIn(marca, self.js)
        self.assertIn('oc-alertas-panel[hidden]', self.css)
        self.assertIn('[data-oc-vista="alertas"]', self.css)
        self.assertIn('css/componentes/alertas_segmentadas.css', self.plantilla)
        self.assertIn('js/componentes/vencimientos.js', self.plantilla)
