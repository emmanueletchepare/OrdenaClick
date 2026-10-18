"""Regresión: navegación única compartida, sin exponer módulos administrativos."""
from pathlib import Path
from django.conf import settings
from django.template.loader import get_template
from django.test import SimpleTestCase


class SidebarUnicoTests(SimpleTestCase):
    def test_plantillas_compilan(self):
        for nombre in ('panel.html', 'partials/sidebar.html',
                       'partials/sidebar_modulos_empresa.html', 'partials/main.html'):
            get_template('usuarios/perfiles/administrador/' + nombre)

    def test_modulos_en_un_solo_archivo(self):
        base = Path(settings.BASE_DIR)
        folder = base / 'templates/usuarios/perfiles/administrador/partials'
        sidebar = (folder / 'sidebar.html').read_text(encoding='utf-8')
        modulos = (folder / 'sidebar_modulos_empresa.html').read_text(encoding='utf-8')
        self.assertEqual(sidebar.count('sidebar_modulos_empresa.html'), 2)
        self.assertEqual(modulos.count('data-oc-grupo="abms"'), 1)
        self.assertEqual(modulos.count('data-oc-grupo="herramientas"'), 1)
        self.assertEqual(modulos.count('data-oc-grupo="registros"'), 1)
        self.assertNotIn('data-oc-modulo=', sidebar)
        self.assertFalse((base / 'static/js/perfiles/administrador/panel_modulos_colaborador.js').exists())
