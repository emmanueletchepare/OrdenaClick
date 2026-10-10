"""B8: contrato HTTP de las protecciones configuradas para producción.

Prueba los middlewares reales con settings de seguridad sobre el entorno de test.
No implica validación de un proxy ni de un despliegue HTTPS verdadero.
"""
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse


class SeguridadHTTPB8Tests(TestCase):
    def test_proteccion_frame_y_nosniff_en_respuesta(self):
        with override_settings(X_FRAME_OPTIONS='DENY', SECURE_CONTENT_TYPE_NOSNIFF=True):
            respuesta = self.client.get(reverse('login'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['X-Frame-Options'], 'DENY')
        self.assertEqual(respuesta['X-Content-Type-Options'], 'nosniff')

    def test_redireccion_https_sin_perder_ruta(self):
        with override_settings(SECURE_SSL_REDIRECT=True, SECURE_PROXY_SSL_HEADER=None):
            respuesta = self.client.get(reverse('login'))
        self.assertEqual(respuesta.status_code, 301)
        self.assertEqual(respuesta['Location'], 'https://testserver' + reverse('login'))

    def test_cookies_de_sesion_y_csrf_con_atributos_seguros(self):
        with override_settings(
            SESSION_COOKIE_SECURE=True,
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax',
            CSRF_COOKIE_SECURE=True,
            CSRF_COOKIE_SAMESITE='Lax',
        ):
            cliente = Client(enforce_csrf_checks=True)
            respuesta = cliente.get(reverse('login'), HTTP_HOST='testserver')
            self.assertEqual(respuesta.status_code, 200)
            # El middleware CSRF solo crea cookie cuando se solicita token.
            from django.middleware.csrf import get_token
            from django.test import RequestFactory
            solicitud = RequestFactory().get(reverse('login'))
            get_token(solicitud)
            self.assertTrue(solicitud.META.get('CSRF_COOKIE_NEEDS_UPDATE'))
            # Iniciar sesion sin exigir CSRF permite inspeccionar la cookie de sesion.
            usuario = User.objects.create_user(username='b8_cookie', password='ClaveSeguraB8!2026')
            cliente_sesion = Client()
            respuesta_login = cliente_sesion.post(reverse('login'), {
                'username': 'b8_cookie',
                'password': 'ClaveSeguraB8!2026',
            })
            self.assertEqual(respuesta_login.status_code, 302)
            self.assertIn('sessionid', respuesta_login.cookies)
            cookie = respuesta_login.cookies['sessionid']
            self.assertTrue(cookie['secure'])
            self.assertTrue(cookie['httponly'])
            self.assertEqual(cookie['samesite'], 'Lax')
            # Verificar CSRF cookie sobre respuesta con token creado explícitamente.
            from django.middleware.csrf import get_token
            from django.http import HttpResponse
            from django.middleware.csrf import CsrfViewMiddleware
            peticion = RequestFactory().get('/prueba-csrf/')
            middleware = CsrfViewMiddleware(lambda req: HttpResponse('ok'))
            middleware.process_request(peticion)
            get_token(peticion)
            respuesta_csrf = middleware.process_response(peticion, HttpResponse('ok'))
            csrf_cookie = respuesta_csrf.cookies['csrftoken']
            self.assertTrue(csrf_cookie['secure'])
            self.assertEqual(csrf_cookie['samesite'], 'Lax')

    def test_login_post_sin_token_csrf_es_rechazado(self):
        cliente = Client(enforce_csrf_checks=True)
        respuesta = cliente.post(reverse('login'), {
            'username': 'sin_csrf', 'password': 'NoImportaB8!',
        })
        self.assertEqual(respuesta.status_code, 403)
        self.assertNotIn('_auth_user_id', cliente.session)
