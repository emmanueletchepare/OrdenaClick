"""Regresión de navegación de Próximos Vencimientos; sin datos reales."""
from pathlib import Path
from django.conf import settings
from django.template.loader import get_template
from django.test import SimpleTestCase


class NavegacionVencimientosSidebarTests(SimpleTestCase):
    def test_sidebar_unico_contiene_jerarquia(self):
        base = Path(settings.BASE_DIR)
        p = base / 'templates/usuarios/perfiles/administrador/partials/sidebar_modulos_empresa.html'
        texto = p.read_text(encoding='utf-8')
        self.assertIn('data-oc-grupo="vencimientos"', texto)
        self.assertIn('data-oc-subgrupo="vencimientos-periodos"', texto)
        self.assertIn('>Acción inmediata</button>', texto)
        self.assertIn('>Vencimientos</summary>', texto)
        for accion in ('vencimientos-hoy', 'vencimientos-semana', 'vencimientos-rango'):
            self.assertEqual(texto.count('data-oc-sidebar-accion="'+accion+'"'), 1)
        self.assertEqual(texto.count('id="btnProximosVencimientos"'), 1)
        # No habilitar la función a colaboradores sin permisos de backend integrados.
        self.assertIn('{% if not acceso_restringido %}', texto)
        get_template('usuarios/perfiles/administrador/partials/sidebar_modulos_empresa.html')

    def test_navegacion_usa_la_funcionalidad_original(self):
        base = Path(settings.BASE_DIR)
        js = (base / 'static/js/perfiles/administrador/sidebar_acordeon.js').read_text(encoding='utf-8')
        fuente = (base / 'static/js/componentes/vencimientos.js').read_text(encoding='utf-8')
        css = (base / 'static/css/perfiles/administrador/panel_unificado.css').read_text(encoding='utf-8')
        self.assertIn('window.construirEstructuraProximosVencimientos()', js)
        self.assertIn('window.conectarControlesProximosVencimientos()', js)
        self.assertIn("'vencimientos-hoy': 'btnVencimientosHoy'", js)
        self.assertIn("'vencimientos-semana': 'btnVencimientosSemana'", js)
        self.assertIn("'vencimientos-rango': 'btnVencimientosRango'", js)
        self.assertIn('btnProximosVencimientos', fuente)  # Llamador original sigue conectado
        self.assertIn('.vencimientos-contenedor > .vencimientos-navegacion', css)
        self.assertIn('display:none !important', css)
