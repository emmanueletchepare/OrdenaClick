"""Regresión de autorización, re-asignación y revocación sin cambiar el sidebar."""
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from usuarios.models import (
    AsignacionUsuarioEmpresa, CentroOperativo, Empresa,
    CentroAdicionalAdministrador, EventoGestionAsignacion,
    PermisoAccesoColaborador,
)
from usuarios.services.gestionar_asignaciones import guardar_centros_asignacion, revocar_relacion
from usuarios.services.seguridad import obtener_centro_autorizado
from usuarios.services.alcances_centros import centros_activos_de_usuario
from usuarios.services.pendientes_bancarios import alcance_pendientes
from usuarios.services.accesos_colaborador import guardar_accesos, puede


class AdministradoresCentrosMultiplesTests(TestCase):
    def setUp(self):
        self.propietario = User.objects.create_user('propietario-centros', password='Contra123!')
        self.admin = User.objects.create_user('admin-centros', password='Contra123!')
        self.ajeno = User.objects.create_user('ajeno-centros', password='Contra123!')
        self.empresa = Empresa.objects.create(propietario=self.propietario, razon_social='Empresa centros')
        self.otra = Empresa.objects.create(propietario=self.ajeno, razon_social='Empresa ajena')
        self.casa = CentroOperativo.objects.create(empresa=self.empresa, nombre='Casa central', tipo='Casa Central', activo=True)
        self.sucursal = CentroOperativo.objects.create(empresa=self.empresa, nombre='Sucursal 2', tipo='Sucursal', activo=True)
        self.no_permitido = CentroOperativo.objects.create(empresa=self.empresa, nombre='Sucursal 3', tipo='Sucursal', activo=True)
        self.ajeno_centro = CentroOperativo.objects.create(empresa=self.otra, nombre='Otro centro', tipo='Sucursal', activo=True)
        self.asignacion = AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa, usuario=self.admin, jerarquia='admin_centro',
            centro_operativo=self.casa, activo=True,
        )

    def test_dos_centros_y_denegacion_tercero(self):
        guardar_centros_asignacion(actor=self.propietario, empresa_id=self.empresa.id,
            asignacion_id=self.asignacion.id, centros=[str(self.casa.id),str(self.sucursal.id)])
        self.assertEqual(centros_activos_de_usuario(self.admin,self.empresa),
            frozenset([self.casa.pk,self.sucursal.pk]))
        for c in (self.casa,self.sucursal):
            self.assertEqual(obtener_centro_autorizado(self.admin,self.empresa.pk,c.pk)[1], c)
        for c in (self.no_permitido,self.ajeno_centro):
            with self.assertRaises(PermissionDenied):
                obtener_centro_autorizado(self.admin,self.empresa.pk,c.pk)
        self.assertEqual(alcance_pendientes(self.admin,self.empresa.pk)[1],
            frozenset([self.casa.pk,self.sucursal.pk]))
        self.assertTrue(EventoGestionAsignacion.objects.filter(accion='actualizar_centros').exists())

    def test_reemplazo_centro_no_reasigna_empresa_ajena(self):
        with self.assertRaises(PermissionDenied):
            guardar_centros_asignacion(actor=self.propietario, empresa_id=self.empresa.pk,
                asignacion_id=self.asignacion.pk, centros=[str(self.casa.pk),str(self.ajeno_centro.pk)])
        self.assertEqual(self.asignacion.centros_adicionales.count(),0)
        guardar_centros_asignacion(actor=self.propietario,empresa_id=self.empresa.pk,
            asignacion_id=self.asignacion.pk,centros=[str(self.sucursal.pk)])
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.centro_operativo_id,self.sucursal.pk)
        self.assertEqual(centros_activos_de_usuario(self.admin,self.empresa), frozenset([self.sucursal.pk]))

    def test_solo_general_administra_y_no_se_puede_quitar_todo(self):
        with self.assertRaises(PermissionDenied):
            guardar_centros_asignacion(actor=self.admin,empresa_id=self.empresa.pk,
                asignacion_id=self.asignacion.pk,centros=[str(self.sucursal.pk)])
        with self.assertRaises(ValidationError):
            guardar_centros_asignacion(actor=self.propietario,empresa_id=self.empresa.pk,
                asignacion_id=self.asignacion.pk,centros=[])
        with self.assertRaises(PermissionDenied):
            guardar_centros_asignacion(actor=self.propietario,empresa_id=self.otra.pk,
                asignacion_id=self.asignacion.pk,centros=[str(self.ajeno_centro.pk)])

    def test_revocar_corta_acceso_y_no_resucita_permisos(self):
        guardar_accesos(administrador=self.propietario,empresa_id=self.empresa.pk,
            colaborador_id=self.admin.pk,codigos=['claves.propias'])
        self.assertTrue(puede(self.admin,self.empresa.pk,'claves.propias'))
        revocar_relacion(actor=self.propietario,empresa_id=self.empresa.pk,
            relacion_id=self.asignacion.pk,tipo='jerarquia')
        self.assertFalse(puede(self.admin,self.empresa.pk,'claves.propias'))
        self.assertFalse(PermisoAccesoColaborador.objects.get(
            empresa=self.empresa,usuario=self.admin,codigo='claves.propias').activo)
        with self.assertRaises(PermissionDenied):
            alcance_pendientes(self.admin,self.empresa.pk)
        self.assertTrue(EventoGestionAsignacion.objects.filter(accion='revocar_jerarquia').exists())

    def test_http_permisos_incluye_admin_centro_y_no_ajeno(self):
        self.client.force_login(self.propietario)
        response=self.client.get(reverse('gestion_accesos_colaborador',args=[self.empresa.pk]))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,self.admin.username)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('gestion_accesos_colaborador',args=[self.empresa.pk])).status_code,403)

    def test_post_editar_centros_desde_la_pantalla_compartida(self):
        self.client.force_login(self.propietario)
        ruta=reverse('gestionar_relaciones_empresa',args=[self.empresa.pk])
        response=self.client.post(ruta, {'accion':'centros','asignacion':str(self.asignacion.pk),
            'centros':[str(self.casa.pk),str(self.sucursal.pk)]},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Centros autorizados actualizados')
        self.assertEqual(centros_activos_de_usuario(self.admin,self.empresa),
            frozenset([self.casa.pk,self.sucursal.pk]))
