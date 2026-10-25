"""Contrato del catálogo: futuras alertas no son eventos ni permisos activos."""
from pathlib import Path
from django.conf import settings
from django.test import SimpleTestCase

from usuarios.services.catalogo_alertas import (
    CATEGORIAS, CODIGOS_OPERATIVOS, TIPOS_ALERTA, TIPOS_POR_CODIGO,
    tipo_operativo, tipos_operativos,
)


class CatalogoAlertasB1Tests(SimpleTestCase):
    def test_codigos_unicos_y_categorias(self):
        codigos = [tipo.codigo for tipo in TIPOS_ALERTA]
        self.assertEqual(len(codigos), len(set(codigos)))
        self.assertEqual(set(codigos), set(TIPOS_POR_CODIGO))
        self.assertEqual(set(tipo.categoria for tipo in TIPOS_ALERTA), set(CATEGORIAS))

    def test_fuentes_integradas(self):
        self.assertEqual(CODIGOS_OPERATIVOS, {'FIN-01', 'FIN-02', 'FIN-03', 'NOM-01'})
        self.assertEqual({tipo.codigo for tipo in tipos_operativos()}, CODIGOS_OPERATIVOS)
        for codigo in CODIGOS_OPERATIVOS:
            self.assertTrue(tipo_operativo(codigo).operativa)

    def test_ideas_no_se_pueden_habilitar_accidentalmente(self):
        for codigo in ('FIN-04', 'ADM-01', 'NOM-02',
                       'DOC-01', 'DOC-02', 'DOC-03', 'NO-EXISTE'):
            with self.subTest(codigo=codigo), self.assertRaises(ValueError):
                tipo_operativo(codigo)

    def test_habilitacion_municipal_asociada_al_centro(self):
        tipo = TIPOS_POR_CODIGO['DOC-03']
        self.assertEqual(tipo.alcance, 'Centro Operativo')
        self.assertFalse(tipo.operativa)

    def test_catalogo_md_refleja_codigos_y_estados(self):
        base = Path(settings.BASE_DIR) / 'Archivos de proyecto'
        maestro = (base / 'CATALOGO_ALERTAS_ORDENACLICK.md').read_text(encoding='utf-8')
        anexo = (base / 'FICHAS_ALERTAS_ORDENACLICK.md').read_text(encoding='utf-8')
        for tipo in TIPOS_ALERTA:
            marca = '[x]' if tipo.operativa else '[ ]'
            self.assertIn(f'{marca} **{tipo.codigo}**', maestro)
        self.assertIn('Sin destinatarios', maestro)
        self.assertIn('DOC-03', anexo)
        self.assertIn('Centro Operativo', anexo)
