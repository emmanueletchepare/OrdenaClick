"""Regresión de separación visual: sidebar único, dos módulos y tres filtros."""
from pathlib import Path
from django.conf import settings
from django.template.loader import get_template
from django.test import SimpleTestCase


class NavegacionVencimientosSidebarTests(SimpleTestCase):
    def test_sidebar_con_alertas_separadas(self):
        base = Path(settings.BASE_DIR)
        archivo = base / 'templates/usuarios/perfiles/administrador/partials/sidebar_modulos_empresa.html'
        texto = archivo.read_text(encoding='utf-8')
        self.assertEqual(texto.count('id="btnSidebarAlertas"'), 1)
        self.assertEqual(texto.count('data-oc-grupo="vencimientos"'), 1)
        self.assertNotIn('data-oc-subgrupo="vencimientos-periodos"', texto)
        self.assertNotIn('>Acción inmediata</button>', texto)
        for accion in ('vencimientos-hoy', 'vencimientos-semana', 'vencimientos-rango'):
            self.assertEqual(texto.count('data-oc-sidebar-accion="'+accion+'"'), 1)
        get_template('usuarios/perfiles/administrador/partials/sidebar_modulos_empresa.html')

    def test_sin_botonera_duplicada_y_sin_cambio_de_panel(self):
        base = Path(settings.BASE_DIR)
        js = (base / 'static/js/perfiles/administrador/sidebar_acordeon.js').read_text(encoding='utf-8')
        fuente = (base / 'static/js/componentes/vencimientos.js').read_text(encoding='utf-8')
        llamador = (base / 'static/js/componentes/llamador_alertas.js').read_text(encoding='utf-8')
        css = (base / 'static/css/perfiles/administrador/panel_unificado.css').read_text(encoding='utf-8')
        self.assertIn('window.construirEstructuraProximosVencimientos()', js)
        self.assertIn('window.conectarControlesProximosVencimientos()', js)
        for p in ('hoy','semana','rango'):
            self.assertIn("'vencimientos-"+p+"': 'btnVencimientos"+p.capitalize()+"'", js)
        self.assertIn('btnSidebarAlertas', fuente)
        self.assertIn('btnSidebarAlertas', llamador)
        self.assertIn('contenido-operativo', fuente)
        self.assertIn('.vencimientos-contenedor > .vencimientos-navegacion', css)
        self.assertIn('display:none !important', css)
