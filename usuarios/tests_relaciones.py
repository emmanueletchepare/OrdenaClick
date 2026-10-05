from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    CentroOperativo,
    Empresa,
    RolFuncionalUsuarioEmpresa,
    SolicitudRelacionEmpresa,
)
from usuarios.services.relaciones import (
    crear_solicitud_relacion,
    resolver_solicitud_relacion,
)


class RelacionesUsuarioEmpresaTests(TestCase):
    def setUp(self):
        self.fundador = User.objects.create_user("fundador", "fundador@test.com", "clave")
        self.admin_general = User.objects.create_user("admin", "admin@test.com", "clave")
        self.pedrito = User.objects.create_user("pedrito", "pedrito@test.com", "clave")
        self.otro = User.objects.create_user("otro", "otro@test.com", "clave")
        self.empresa = Empresa.objects.create(
            propietario=self.fundador,
            razon_social="Empresa Uno SA",
            nombre_fantasia="EMPRESA UNO",
        )
        self.centro = CentroOperativo.objects.create(
            empresa=self.empresa,
            nombre="CASA CENTRAL",
            tipo="Casa Central",
            direccion="",
        )
        self.centro_otro = CentroOperativo.objects.create(
            empresa=Empresa.objects.create(
                propietario=self.otro,
                razon_social="Empresa Dos SA",
                nombre_fantasia="EMPRESA DOS",
            ),
            nombre="OTRO CENTRO",
            tipo="Casa Central",
            direccion="",
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin_general,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=True,
        )

    def test_usuario_puede_ser_colaborador_y_contable_en_misma_empresa(self):
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.pedrito,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR,
            activo=True,
        )
        RolFuncionalUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.pedrito,
            rol=RolFuncionalUsuarioEmpresa.ROL_CONTABLE,
            activo=True,
        )
        self.assertTrue(
            AsignacionUsuarioEmpresa.objects.filter(
                empresa=self.empresa,
                usuario=self.pedrito,
                jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR,
                activo=True,
            ).exists()
        )
        self.assertTrue(
            RolFuncionalUsuarioEmpresa.objects.filter(
                empresa=self.empresa,
                usuario=self.pedrito,
                rol=RolFuncionalUsuarioEmpresa.ROL_CONTABLE,
                activo=True,
            ).exists()
        )

    def test_fundador_envia_solicitud_y_no_concede_acceso_antes_de_aceptar(self):
        solicitud = crear_solicitud_relacion(
            solicitante=self.fundador,
            empresa_id=self.empresa.id,
            identificador_usuario="pedrito@test.com",
            rol=SolicitudRelacionEmpresa.ROL_COLABORADOR,
        )
        self.assertEqual(solicitud.estado, SolicitudRelacionEmpresa.ESTADO_PENDIENTE)
        self.assertFalse(
            AsignacionUsuarioEmpresa.objects.filter(
                empresa=self.empresa,
                usuario=self.pedrito,
            ).exists()
        )

    def test_admin_general_puede_enviar_solicitud(self):
        solicitud = crear_solicitud_relacion(
            solicitante=self.admin_general,
            empresa_id=self.empresa.id,
            identificador_usuario="pedrito",
            rol=SolicitudRelacionEmpresa.ROL_CONTABLE,
        )
        self.assertEqual(solicitud.solicitada_por, self.admin_general)

    def test_admin_centro_exige_centro_de_la_misma_empresa(self):
        with self.assertRaises(ValidationError):
            crear_solicitud_relacion(
                solicitante=self.fundador,
                empresa_id=self.empresa.id,
                identificador_usuario="pedrito",
                rol=SolicitudRelacionEmpresa.ROL_ADMIN_CENTRO,
                centro_id=self.centro_otro.id,
            )

    def test_aceptar_colaborador_crea_asignacion(self):
        solicitud = crear_solicitud_relacion(
            solicitante=self.fundador,
            empresa_id=self.empresa.id,
            identificador_usuario="pedrito",
            rol=SolicitudRelacionEmpresa.ROL_COLABORADOR,
        )
        resolver_solicitud_relacion(
            usuario=self.pedrito,
            solicitud_id=solicitud.id,
            accion="aceptar",
        )
        self.assertTrue(
            AsignacionUsuarioEmpresa.objects.filter(
                empresa=self.empresa,
                usuario=self.pedrito,
                jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR,
                activo=True,
            ).exists()
        )
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudRelacionEmpresa.ESTADO_ACEPTADA)

    def test_aceptar_contable_no_modifica_jerarquia_existente(self):
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.pedrito,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR,
            activo=True,
        )
        solicitud = crear_solicitud_relacion(
            solicitante=self.fundador,
            empresa_id=self.empresa.id,
            identificador_usuario="pedrito",
            rol=SolicitudRelacionEmpresa.ROL_CONTABLE,
        )
        resolver_solicitud_relacion(
            usuario=self.pedrito,
            solicitud_id=solicitud.id,
            accion="aceptar",
        )
        self.assertTrue(
            RolFuncionalUsuarioEmpresa.objects.filter(
                empresa=self.empresa,
                usuario=self.pedrito,
                rol=RolFuncionalUsuarioEmpresa.ROL_CONTABLE,
                activo=True,
            ).exists()
        )
        self.assertEqual(
            AsignacionUsuarioEmpresa.objects.get(
                empresa=self.empresa,
                usuario=self.pedrito,
            ).jerarquia,
            AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR,
        )

    def test_usuario_no_puede_aceptar_solicitud_ajena(self):
        solicitud = crear_solicitud_relacion(
            solicitante=self.fundador,
            empresa_id=self.empresa.id,
            identificador_usuario="pedrito",
            rol=SolicitudRelacionEmpresa.ROL_LEGAL,
        )
        with self.assertRaises(PermissionDenied):
            resolver_solicitud_relacion(
                usuario=self.otro,
                solicitud_id=solicitud.id,
                accion="aceptar",
            )

    def test_rechazar_no_crea_relacion(self):
        solicitud = crear_solicitud_relacion(
            solicitante=self.fundador,
            empresa_id=self.empresa.id,
            identificador_usuario="pedrito",
            rol=SolicitudRelacionEmpresa.ROL_LEGAL,
        )
        resolver_solicitud_relacion(
            usuario=self.pedrito,
            solicitud_id=solicitud.id,
            accion="rechazar",
        )
        self.assertFalse(
            RolFuncionalUsuarioEmpresa.objects.filter(
                empresa=self.empresa,
                usuario=self.pedrito,
                rol=RolFuncionalUsuarioEmpresa.ROL_LEGAL,
            ).exists()
        )

    def test_home_muestra_aviso_de_solicitudes_pendientes(self):
        crear_solicitud_relacion(
            solicitante=self.fundador,
            empresa_id=self.empresa.id,
            identificador_usuario="pedrito",
            rol=SolicitudRelacionEmpresa.ROL_COLABORADOR,
        )
        self.client.force_login(self.pedrito)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solicitudes pendientes")
        self.assertContains(response, "Relaciones")

    def test_relaciones_idor_en_http_no_permite_resolver_solicitud_ajena(self):
        solicitud = crear_solicitud_relacion(
            solicitante=self.fundador,
            empresa_id=self.empresa.id,
            identificador_usuario="pedrito",
            rol=SolicitudRelacionEmpresa.ROL_COLABORADOR,
        )
        self.client.force_login(self.otro)
        response = self.client.post(
            reverse(
                "resolver_solicitud_relacion",
                kwargs={"solicitud_id": solicitud.id, "accion": "aceptar"},
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, SolicitudRelacionEmpresa.ESTADO_PENDIENTE)


    def test_fundador_puede_abrir_gestion_relaciones_empresa(self):
        self.client.force_login(self.fundador)
        response = self.client.get(
            reverse("gestionar_relaciones_empresa", kwargs={"empresa_id": self.empresa.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Designar perfiles")

    def test_gestion_relaciones_fragmento_no_renderiza_pagina_independiente(self):
        self.client.force_login(self.fundador)
        response = self.client.get(
            reverse("gestionar_relaciones_empresa", kwargs={"empresa_id": self.empresa.id}),
            {"fragment": "1"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Volver a Configuración")
        self.assertContains(response, "Enviar solicitud")
        self.assertNotContains(response, "<body")
        self.assertNotContains(response, "Designar perfiles")

    def test_gestion_relaciones_ajax_envia_solicitud_y_devuelve_fragmento(self):
        self.client.force_login(self.fundador)
        response = self.client.post(
            reverse("gestionar_relaciones_empresa", kwargs={"empresa_id": self.empresa.id}),
            {"usuario": "pedrito", "rol": SolicitudRelacionEmpresa.ROL_CONTABLE, "mensaje": "Solicitud de prueba"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Solicitud enviada a pedrito.")
        self.assertContains(response, "Volver a Configuración")
        self.assertTrue(SolicitudRelacionEmpresa.objects.filter(
            empresa=self.empresa, usuario_destino=self.pedrito,
            rol=SolicitudRelacionEmpresa.ROL_CONTABLE,
            estado=SolicitudRelacionEmpresa.ESTADO_PENDIENTE,
        ).exists())


    def test_panel_relaciones_muestra_vinculos_actuales(self):
        RolFuncionalUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.pedrito,
            rol=RolFuncionalUsuarioEmpresa.ROL_CONTABLE,
            activo=True,
        )
        self.client.force_login(self.pedrito)
        response = self.client.get(reverse("panel_relaciones"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EMPRESA UNO")
        self.assertContains(response, "Contable")

    def test_usuario_no_existente_no_puede_recibir_solicitud(self):
        with self.assertRaises(ValidationError):
            crear_solicitud_relacion(
                solicitante=self.fundador,
                empresa_id=self.empresa.id,
                identificador_usuario="nadie@test.com",
                rol=SolicitudRelacionEmpresa.ROL_COLABORADOR,
            )
