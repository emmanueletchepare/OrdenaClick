# Regresiones de la navegación compartida; no requiere datos reales.
from pathlib import Path
from django.conf import settings
from django.template.loader import get_template
from django.test import SimpleTestCase


class NavegacionUnicaUXTests(SimpleTestCase):
    def test_sidebar_empresa_es_unico_para_ambos_roles(self):
        base = Path(settings.BASE_DIR)
        carpeta = base / 'templates/usuarios/perfiles/administrador/partials'
        principal = (carpeta / 'sidebar.html').read_text(encoding='utf-8')
        modulos = (carpeta / 'sidebar_modulos_empresa.html').read_text(encoding='utf-8')
        self.assertEqual(principal.count('sidebar_modulos_empresa.html'), 2)
        self.assertEqual(modulos.count('data-oc-grupo="abms"'), 1)
        self.assertEqual(modulos.count('data-oc-grupo="registros"'), 1)
        get_template('usuarios/perfiles/administrador/partials/sidebar_modulos_empresa.html')

    def test_registros_no_recrea_botonera_superior(self):
        js = (Path(settings.BASE_DIR) / 'static/js/perfiles/administrador/sidebar_acordeon.js').read_text(encoding='utf-8')
        self.assertIn('window.mostrarCargaSimple', js)
        self.assertIn('window.mostrarObligaciones', js)
        self.assertIn('const original = window.mostrarSubmenu', js)
        # Registros debe abrir sus módulos sin generar la botonera superior.
        # Vencimientos sí reutiliza, por diseño, sus botones internos ocultos.
        inicio = js.index("if (accion === 'registros-comprobantes' || accion === 'registros-obligaciones') {")
        fin = js.index('const funciones = {', inicio)
        bloque_registros = js[inicio:fin]
        self.assertNotIn('document.getElementById(id)?.click()', bloque_registros)
        self.assertIn("if (typeof abrir === 'function') abrir();", bloque_registros)
        self.assertIn("['registros', 'abms', 'herramientas', 'configuracion']", js)

    def test_accesos_se_abre_dentro_del_panel(self):
        js = (Path(settings.BASE_DIR) / 'static/js/perfiles/administrador/sidebar_acordeon.js').read_text(encoding='utf-8')
        self.assertIn('ocGestionAccesosFrame', js)
        self.assertIn("alta.style.display = 'none'", js)
        self.assertIn('oc-accesos-contenido', js)
        self.assertIn("marcarOpcion(opcion)", js)
