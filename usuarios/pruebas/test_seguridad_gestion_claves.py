from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    Empresa,
    GestionClave,
)


class SeguridadGestionClavesTests(TestCase):

    def setUp(self):
        self.propietario = User.objects.create_user(
            username="seg_claves_propietario",
            password="prueba123",
        )
        self.otro = User.objects.create_user(
            username="seg_claves_otro",
            password="prueba123",
        )
        self.admin_general = User.objects.create_user(
            username="seg_claves_admin_general",
            password="prueba123",
        )
        self.inactivo = User.objects.create_user(
            username="seg_claves_inactivo",
            password="prueba123",
        )

        self.empresa = Empresa.objects.create(
            propietario=self.propietario,
            razon_social="Empresa Claves",
        )
        self.empresa_ajena = Empresa.objects.create(
            propietario=self.otro,
            razon_social="Empresa Claves Ajena",
        )

        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin_general,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=True,
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.inactivo,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=False,
        )

        self.clave = GestionClave.objects.create(
            empresa=self.empresa,
            nombre="Portal Propio",
            sitio="https://propio.example",
            usuario="usuario-propio",
            correo="propio@example.com",
            contrasena_cifrada="CIFRADO-PROPIO",
            referencia_recuperacion_1="ref 1",
            referencia_recuperacion_2="ref 2",
            observaciones="propia",
            activo=True,
        )
        self.clave_ajena = GestionClave.objects.create(
            empresa=self.empresa_ajena,
            nombre="Portal Ajeno",
            sitio="https://ajeno.example",
            usuario="usuario-ajeno",
            correo="ajeno@example.com",
            contrasena_cifrada="CIFRADO-AJENO",
            referencia_recuperacion_1="ref ajena 1",
            referencia_recuperacion_2="ref ajena 2",
            observaciones="ajena",
            activo=True,
        )
        self.clave_ajena_inactiva = GestionClave.objects.create(
            empresa=self.empresa_ajena,
            nombre="Portal Ajeno Inactivo",
            sitio="",
            usuario="",
            correo="",
            contrasena_cifrada="CIFRADO-AJENO-INACTIVO",
            referencia_recuperacion_1="",
            referencia_recuperacion_2="",
            observaciones="",
            activo=False,
        )

    def test_rutas_privadas_requieren_login(self):
        casos_get = (
            "listar_gestion_claves",
            "ver_gestion_clave",
        )

        for nombre_url in casos_get:
            with self.subTest(metodo="GET", url=nombre_url):
                respuesta = self.client.get(
                    reverse(nombre_url),
                    {"empresa": self.empresa.pk},
                )
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn(
                    reverse("login"),
                    respuesta["Location"],
                )

        casos_post = (
            "guardar_gestion_clave",
            "modificar_gestion_clave",
            "eliminar_gestion_clave",
            "reactivar_gestion_clave",
        )

        for nombre_url in casos_post:
            with self.subTest(metodo="POST", url=nombre_url):
                respuesta = self.client.post(
                    reverse(nombre_url),
                    {"empresa": self.empresa.pk},
                )
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn(
                    reverse("login"),
                    respuesta["Location"],
                )

    def test_listado_rechaza_empresa_ajena(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.get(
            reverse("listar_gestion_claves"),
            {"empresa": self.empresa_ajena.pk},
        )
        self.assertEqual(respuesta.status_code, 403)

    def test_admin_general_activo_puede_listar(self):
        self.client.force_login(self.admin_general)
        respuesta = self.client.get(
            reverse("listar_gestion_claves"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.json()["ok"])

    def test_asignacion_inactiva_no_concede_acceso(self):
        self.client.force_login(self.inactivo)
        respuesta = self.client.get(
            reverse("listar_gestion_claves"),
            {"empresa": self.empresa.pk},
        )
        self.assertEqual(respuesta.status_code, 403)

    def test_ver_no_expone_clave_de_empresa_ajena(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.get(
            reverse("ver_gestion_clave"),
            {
                "empresa": self.empresa.pk,
                "clave": self.clave_ajena.pk,
            },
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_modificar_no_toca_clave_de_empresa_ajena(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.post(
            reverse("modificar_gestion_clave"),
            {
                "empresa": self.empresa.pk,
                "clave": self.clave_ajena.pk,
                "nombre": "FORZADA",
                "sitio": "",
                "usuario": "",
                "correo": "",
                "contrasena": "",
                "referencia_recuperacion_1": "",
                "referencia_recuperacion_2": "",
                "observaciones": "",
            },
        )
        self.assertEqual(respuesta.status_code, 404)
        self.clave_ajena.refresh_from_db()
        self.assertEqual(self.clave_ajena.nombre, "Portal Ajeno")
        self.assertEqual(
            self.clave_ajena.contrasena_cifrada,
            "CIFRADO-AJENO",
        )

    def test_eliminar_no_toca_clave_de_empresa_ajena(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.post(
            reverse("eliminar_gestion_clave"),
            {
                "empresa": self.empresa.pk,
                "clave": self.clave_ajena.pk,
            },
        )
        self.assertEqual(respuesta.status_code, 404)
        self.clave_ajena.refresh_from_db()
        self.assertTrue(self.clave_ajena.activo)

    def test_reactivar_no_toca_clave_de_empresa_ajena(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.post(
            reverse("reactivar_gestion_clave"),
            {
                "empresa": self.empresa.pk,
                "clave": self.clave_ajena_inactiva.pk,
            },
        )
        self.assertEqual(respuesta.status_code, 404)
        self.clave_ajena_inactiva.refresh_from_db()
        self.assertFalse(self.clave_ajena_inactiva.activo)

    def test_guardar_rechaza_empresa_ajena_antes_de_cifrar(self):
        self.client.force_login(self.propietario)
        respuesta = self.client.post(
            reverse("guardar_gestion_clave"),
            {
                "empresa": self.empresa_ajena.pk,
                "nombre": "Intento Ajeno",
                "contrasena": "NO-DEBE-CIFRARSE",
            },
        )
        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(
            GestionClave.objects.filter(
                empresa=self.empresa_ajena,
                nombre="Intento Ajeno",
            ).exists()
        )
