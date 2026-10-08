from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    CentroOperativo,
    Empresa,
    RolFuncionalUsuarioEmpresa,
)
from usuarios.services.capacidades import (
    CAPACIDAD_CAJA_OPERAR,
    CAPACIDAD_CAJA_VER,
    CAPACIDAD_EMPRESA_ADMINISTRAR,
    CAPACIDAD_EMPRESA_BACKUP,
    CAPACIDAD_EMPRESA_RESTAURAR,
    exigir_capacidad_empresa,
    obtener_contexto_capacidades_empresa,
)


class CapacidadesEmpresaTests(TestCase):
    """Verifica el contrato inicial de capacidades sin cambiar views actuales."""

    def setUp(self):
        self.propietario = User.objects.create_user(
            username="propietario_capacidades",
            password="Segura123!",
        )
        self.superusuario = User.objects.create_superuser(
            username="super_capacidades",
            email="super@example.com",
            password="Segura123!",
        )
        self.admin_general = User.objects.create_user(
            username="admin_general_capacidades",
            password="Segura123!",
        )
        self.admin_centro = User.objects.create_user(
            username="admin_centro_capacidades",
            password="Segura123!",
        )
        self.colaborador = User.objects.create_user(
            username="colaborador_capacidades",
            password="Segura123!",
        )
        self.contable = User.objects.create_user(
            username="contable_capacidades",
            password="Segura123!",
        )
        self.ajeno = User.objects.create_user(
            username="ajeno_capacidades",
            password="Segura123!",
        )

        self.empresa = Empresa.objects.create(
            propietario=self.propietario,
            razon_social="Empresa Capacidades SA",
        )

        self.centro = CentroOperativo.objects.create(
            empresa=self.empresa,
            nombre="Centro Capacidades",
            tipo="Sucursal",
            activo=True,
        )

        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin_general,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=True,
        )

        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.admin_centro,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_CENTRO,
            centro_operativo=self.centro,
            activo=True,
        )

        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.colaborador,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_COLABORADOR,
            activo=True,
        )

        RolFuncionalUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.contable,
            rol=RolFuncionalUsuarioEmpresa.ROL_CONTABLE,
            activo=True,
        )

    def test_superusuario_conserva_acceso_completo(self):
        contexto = obtener_contexto_capacidades_empresa(
            self.superusuario,
            self.empresa.pk,
        )

        self.assertTrue(contexto.es_superusuario)
        self.assertTrue(contexto.tiene(CAPACIDAD_EMPRESA_ADMINISTRAR))
        self.assertTrue(contexto.tiene(CAPACIDAD_EMPRESA_BACKUP))
        self.assertTrue(contexto.tiene(CAPACIDAD_EMPRESA_RESTAURAR))
        self.assertTrue(contexto.tiene(CAPACIDAD_CAJA_VER))
        self.assertTrue(contexto.tiene(CAPACIDAD_CAJA_OPERAR))

    def test_propietario_posee_alcance_completo(self):
        contexto = obtener_contexto_capacidades_empresa(
            self.propietario,
            self.empresa.pk,
        )

        self.assertTrue(contexto.es_propietario)
        self.assertTrue(contexto.tiene(CAPACIDAD_EMPRESA_ADMINISTRAR))
        self.assertTrue(contexto.tiene(CAPACIDAD_EMPRESA_BACKUP))
        self.assertTrue(contexto.tiene(CAPACIDAD_CAJA_OPERAR))

    def test_admin_general_preserva_capacidades_actuales(self):
        contexto = obtener_contexto_capacidades_empresa(
            self.admin_general,
            self.empresa.pk,
        )

        self.assertEqual(
            contexto.jerarquia,
            AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
        )
        self.assertTrue(contexto.tiene(CAPACIDAD_EMPRESA_ADMINISTRAR))
        self.assertTrue(contexto.tiene(CAPACIDAD_EMPRESA_BACKUP))
        self.assertTrue(contexto.tiene(CAPACIDAD_EMPRESA_RESTAURAR))
        self.assertTrue(contexto.tiene(CAPACIDAD_CAJA_OPERAR))

    def test_admin_centro_solo_recibe_capacidades_caja_y_su_centro(self):
        contexto = obtener_contexto_capacidades_empresa(
            self.admin_centro,
            self.empresa.pk,
        )

        self.assertFalse(contexto.tiene(CAPACIDAD_EMPRESA_ADMINISTRAR))
        self.assertFalse(contexto.tiene(CAPACIDAD_EMPRESA_BACKUP))
        self.assertTrue(contexto.tiene(CAPACIDAD_CAJA_VER))
        self.assertTrue(contexto.tiene(CAPACIDAD_CAJA_OPERAR))
        self.assertEqual(contexto.centro_operativo_id, self.centro.pk)

    def test_colaborador_no_recibe_capacidades_implicitas(self):
        contexto = obtener_contexto_capacidades_empresa(
            self.colaborador,
            self.empresa.pk,
        )

        self.assertEqual(contexto.capacidades, frozenset())

    def test_rol_funcional_no_eleva_permisos_administrativos(self):
        contexto = obtener_contexto_capacidades_empresa(
            self.contable,
            self.empresa.pk,
        )

        self.assertIn(
            RolFuncionalUsuarioEmpresa.ROL_CONTABLE,
            contexto.roles_funcionales,
        )
        self.assertFalse(contexto.tiene(CAPACIDAD_EMPRESA_ADMINISTRAR))
        self.assertFalse(contexto.tiene(CAPACIDAD_CAJA_VER))

    def test_usuario_ajeno_es_rechazado(self):
        with self.assertRaises(PermissionDenied):
            obtener_contexto_capacidades_empresa(
                self.ajeno,
                self.empresa.pk,
            )

    def test_anonimo_es_rechazado(self):
        with self.assertRaises(PermissionDenied):
            obtener_contexto_capacidades_empresa(
                AnonymousUser(),
                self.empresa.pk,
            )

    def test_exigir_capacidad_rechaza_capacidad_ausente(self):
        with self.assertRaises(PermissionDenied):
            exigir_capacidad_empresa(
                self.admin_centro,
                self.empresa.pk,
                CAPACIDAD_EMPRESA_ADMINISTRAR,
            )

    def test_asignacion_inactiva_no_concede_capacidad(self):
        asignacion = AsignacionUsuarioEmpresa.objects.get(
            empresa=self.empresa,
            usuario=self.admin_general,
        )
        asignacion.activo = False
        asignacion.save(update_fields=["activo"])

        with self.assertRaises(PermissionDenied):
            obtener_contexto_capacidades_empresa(
                self.admin_general,
                self.empresa.pk,
            )
