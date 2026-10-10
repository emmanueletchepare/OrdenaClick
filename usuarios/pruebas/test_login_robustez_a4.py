from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from usuarios.modelo_intentos_login import IntentoLoginOrigen
from usuarios.services.limite_login import MAX_FALLOS, _origen, registrar_fallo


class RobustezLoginA4Tests(TestCase):
    def setUp(self):
        self.url = reverse('login')
        User.objects.create_user(username='acceso_a4', password='Prueba-Segura-2026!')

    def intento(self, ip=None, forwarded=None):
        meta = {'REMOTE_ADDR': ip}
        if forwarded is not None:
            meta['HTTP_X_FORWARDED_FOR'] = forwarded
        return self.client.post(self.url, {'username':'acceso_a4','password':'incorrecta'}, **meta)

    def test_ip_invalida_no_produce_error_500(self):
        self.assertEqual(self.intento(ip='no-es-una-ip').status_code, 200)
        self.assertEqual(IntentoLoginOrigen.objects.count(), 1)

    def test_ip_ausente_tambien_queda_limitada(self):
        for _ in range(MAX_FALLOS):
            self.intento(ip=None)
        respuesta = self.intento(ip='not-an-ip')
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('Demasiados intentos', respuesta.context['error'])
        self.assertEqual(IntentoLoginOrigen.objects.count(), 1)

    @override_settings(ORDENACLICK_LOGIN_PROXIES_CONFIABLES=('127.0.0.1',))
    def test_proxy_con_cabecera_invalida_usa_ip_proxy(self):
        self.intento(ip='127.0.0.1', forwarded='falsa')
        self.intento(ip='127.0.0.1')
        self.assertEqual(IntentoLoginOrigen.objects.get().fallos, 2)

    @override_settings(ORDENACLICK_LOGIN_PROXIES_CONFIABLES=('127.0.0.1',))
    def test_proxy_con_cabecera_valida_distingue_origen(self):
        self.intento(ip='127.0.0.1', forwarded='198.51.100.14')
        self.intento(ip='127.0.0.1', forwarded='198.51.100.15')
        self.assertEqual(IntentoLoginOrigen.objects.count(), 2)

    def test_incrementos_multiples_no_pierden_cuentas(self):
        for _ in range(7):
            self.intento(ip='192.0.2.44')
        self.assertEqual(IntentoLoginOrigen.objects.get().fallos, 7)

    def test_ventana_vencida_reinicia_contador(self):
        self.intento(ip='192.0.2.44')
        IntentoLoginOrigen.objects.update(inicio_ventana=timezone.now()-timedelta(minutes=11),fallos=9)
        self.intento(ip='192.0.2.44')
        self.assertEqual(IntentoLoginOrigen.objects.get().fallos, 1)

    def test_contador_se_satura_en_el_limite(self):
        for _ in range(MAX_FALLOS + 3):
            registrar_fallo(type('Req', (), {'META': {'REMOTE_ADDR': '192.0.2.44'}})())
        self.assertEqual(IntentoLoginOrigen.objects.get().fallos, MAX_FALLOS)
