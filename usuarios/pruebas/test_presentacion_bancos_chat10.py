"""Regresiones de presentación: sólo Caja y ABM de Cuentas Bancarias.

No acceden a SQLite ni cambian el comportamiento financiero o los permisos.
"""
from datetime import datetime
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.template.loader import render_to_string
from django.test import SimpleTestCase


class _PadresDeCampos(HTMLParser):
    """Localiza contenedores de inputs sin depender de selectores externos."""

    VACIOS = frozenset(('input', 'br', 'hr', 'img', 'meta', 'link', 'source', 'area'))

    def __init__(self):
        super().__init__()
        self.pila = []
        self.contenedores = {}

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if atributos.get('id'):
            self.contenedores[atributos['id']] = tuple(self.pila)
        if tag not in self.VACIOS:
            self.pila.append((tag, atributos.get('class', '')))

    def handle_endtag(self, tag):
        for indice in range(len(self.pila) - 1, -1, -1):
            if self.pila[indice][0] == tag:
                del self.pila[indice:]
                return


class PresentacionBancosChat10Tests(SimpleTestCase):
    """Protege la ubicación del aviso y la coherencia visual de monedas."""

    def test_aviso_cheques_ocupa_columna_propia_sin_cambiar_identificador(self):
        html = render_to_string('usuarios/maestros/cuentas_bancarias.html', {
            'bancos': (), 'tipos_cuenta': (), 'monedas': (),
            'cuentas': (), 'acceso_descubierto': True,
        })
        parser = _PadresDeCampos()
        parser.feed(html)
        padres_alias = parser.contenedores['aliasCuentaBancaria']
        padres_aviso = parser.contenedores['diasAvisoChequesPropios']
        self.assertIn(('div', 'oc-cuentas-aviso-cheques'), padres_aviso)
        self.assertNotIn(('div', 'oc-cuentas-aviso-cheques'), padres_alias)
        self.assertIn('id="descubiertoImporteCuenta"', html)
        self.assertIn('id="descubiertoAlertaActivaCuenta"', html)

    def _render_caja(self, moneda):
        cuenta = SimpleNamespace(
            pk=31, nombre='CUENTA PRUEBA', moneda=moneda,
            banco=SimpleNamespace(nombre='BANCO DE PRUEBA'),
            descubierto_vencimiento=None,
        )
        fila = {
            'cuenta': cuenta,
            'posicion': SimpleNamespace(importe=Decimal('150.00'), creado=datetime(2026, 11, 7, 12, 30)),
            'descubierto_vigente': False,
        }
        informado = {'ARS': 0, 'USD': 0}
        informado[moneda] = 1
        return render_to_string('usuarios/caja/dashboard.html', {
            'resumenes': (), 'acceso_bancos': True,
            'cartera_echeqs': {'total': Decimal('0.00'), 'cantidad': 0},
            'bancos_informados': {
                'filas': [fila], 'informadas': informado,
                'totales': {'ARS': Decimal('150.00'), 'USD': Decimal('150.00')},
                'faltantes': 0,
            },
            'empresa': SimpleNamespace(pk=2),
        })

    def test_total_bancario_no_muestra_moneda_sin_importes(self):
        for moneda, ausente in [('ARS', 'USD'), ('USD', 'ARS')]:
            with self.subTest(moneda=moneda):
                html = self._render_caja(moneda)
                inicio = html.index('<div class="caja-bancos-totales">')
                final = html.index('</div>', inicio)
                detalle_total = html[inicio:final]
                self.assertIn(moneda, detalle_total)
                self.assertNotIn(ausente, detalle_total)
                self.assertIn('data-caja-banco-abrir=', html)

    def test_css_alinea_bancos_e_iguala_altura_de_tarjetas(self):
        css = (Path(settings.BASE_DIR) / 'static/css/caja/caja.css').read_text(encoding='utf-8')
        self.assertIn('.caja-otras-disponibilidades {\n    align-items: stretch;', css)
        self.assertIn('.caja-bancos-encabezado span:nth-child(n+2) { text-align: right; }', css)
        self.assertIn('.caja-bancos-totales-importes', css)
