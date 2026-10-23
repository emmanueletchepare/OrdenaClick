"""Pruebas de mínimo privilegio del permiso de Nómina y Caja."""
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from usuarios.models import (AsignacionUsuarioEmpresa, CentroOperativo, Empresa,
    PermisoAccesoColaborador, PermisoNominaCentro, RolFuncionalUsuarioEmpresa)
from usuarios.services.accesos_colaborador import puede
from usuarios.services.alcance_nomina import alcance_nomina, comprobar_centro_nomina
from usuarios.services.seguridad import cajas_autorizadas

class DelegacionOperativaTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner-delegado', password='Clave12!!')
        self.colab = User.objects.create_user('colab-delegado', password='Clave12!!')
        self.admin = User.objects.create_user('admin-delegado', password='Clave12!!')
        self.legal = User.objects.create_user('legal-delegado', password='Clave12!!')
        self.otro = User.objects.create_user('otro-delegado', password='Clave12!!')
        self.empresa = Empresa.objects.create(propietario=self.owner, razon_social='Empresa permisos')
        self.ajena = Empresa.objects.create(propietario=self.otro, razon_social='Otra empresa permisos')
        self.c1 = CentroOperativo.objects.create(empresa=self.empresa, nombre='Casa permisos', tipo='Casa Central', activo=True)
        self.c2 = CentroOperativo.objects.create(empresa=self.empresa, nombre='Sucursal permisos', tipo='Sucursal', activo=True)
        self.c3 = CentroOperativo.objects.create(empresa=self.ajena, nombre='Sucursal ajena', tipo='Sucursal', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=self.colab, jerarquia='colaborador', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=self.admin, jerarquia='admin_centro', centro_operativo=self.c1, activo=True)
        RolFuncionalUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=self.legal, rol='legal', activo=True)

    def permiso(self, user, codigo):
        PermisoAccesoColaborador.objects.update_or_create(empresa=self.empresa,usuario=user,codigo=codigo,
            defaults={'activo':True,'otorgado_por':self.owner})

    def test_nomina_denegada_por_defecto_y_empresa_ajena(self):
        for user in (self.colab,self.admin,self.legal):
            with self.assertRaises(PermissionDenied):
                alcance_nomina(user,self.empresa.pk)
            with self.assertRaises(PermissionDenied):
                alcance_nomina(user,self.ajena.pk)
        self.assertFalse(puede(self.legal,self.empresa.pk,'caja.total'))

    def test_colaborador_centros_especificos(self):
        self.permiso(self.colab,'nomina.total')
        PermisoNominaCentro.objects.create(empresa=self.empresa, usuario=self.colab,
            centro_operativo=self.c1, otorgado_por=self.owner)
        self.assertEqual(alcance_nomina(self.colab,self.empresa.pk)[1],frozenset({self.c1.pk}))
        comprobar_centro_nomina(self.colab,self.empresa.pk,self.c1.pk)
        for centro in (self.c2,self.c3):
            with self.assertRaises(PermissionDenied):
                comprobar_centro_nomina(self.colab,self.empresa.pk,centro.pk)

    def test_administrador_centro_alcance_dinamico(self):
        self.permiso(self.admin,'nomina.total')
        self.assertEqual(alcance_nomina(self.admin,self.empresa.pk)[1],frozenset({self.c1.pk}))
        with self.assertRaises(PermissionDenied):
            comprobar_centro_nomina(self.admin,self.empresa.pk,self.c2.pk)
        # El rol nunca concede Caja por defecto. Sólo el permiso explícito.
        with self.assertRaises(PermissionDenied):
            cajas_autorizadas(self.admin,self.empresa.pk)
        self.permiso(self.admin,'caja.total')
        self.assertEqual(cajas_autorizadas(self.admin,self.empresa.pk)[0],self.empresa)
        self.assertTrue(puede(self.admin,self.empresa.pk,'caja.total'))
        self.assertFalse(puede(self.colab,self.empresa.pk,'caja.total'))

    def test_legal_nomina_explicita_no_es_administrador(self):
        self.permiso(self.legal,'nomina.total')
        PermisoNominaCentro.objects.create(empresa=self.empresa,usuario=self.legal,
            centro_operativo=self.c2,otorgado_por=self.owner)
        self.assertEqual(alcance_nomina(self.legal,self.empresa.pk)[1],frozenset({self.c2.pk}))
        self.assertFalse(puede(self.legal,self.empresa.pk,'claves.propias'))

    def test_revocacion_permiso_denegacion_inmediata(self):
        self.permiso(self.colab,'nomina.total')
        PermisoNominaCentro.objects.create(empresa=self.empresa,usuario=self.colab,
            centro_operativo=self.c1,otorgado_por=self.owner)
        self.assertEqual(alcance_nomina(self.colab,self.empresa.pk)[1],frozenset({self.c1.pk}))
        PermisoAccesoColaborador.objects.filter(empresa=self.empresa,usuario=self.colab,codigo='nomina.total').update(activo=False)
        with self.assertRaises(PermissionDenied):
            alcance_nomina(self.colab,self.empresa.pk)

    def test_nomina_http_idor_por_centro_y_alta_forzada(self):
        from django.urls import reverse
        from usuarios.models import Empleado
        self.client.force_login(self.owner)
        ruta=reverse('nomina_registrar_empleado',args=[self.empresa.pk])
        respuesta=self.client.post(ruta,{
            'cuil':'20329642330','nombre_apellido':'Empleado de otra sucursal',
            'legajo':'X-001','fecha_ingreso':'2026-01-15',
            'tipo_contratacion':'Completa','centro_operativo':str(self.c2.pk),
        })
        self.assertEqual(respuesta.status_code,302,str(respuesta.content[:200]))
        empleado=Empleado.objects.get(empresa=self.empresa,legajo='X-001')
        self.permiso(self.colab,'nomina.total')
        PermisoNominaCentro.objects.create(empresa=self.empresa,usuario=self.colab,
            centro_operativo=self.c1,otorgado_por=self.owner)
        self.client.force_login(self.colab)
        lista=self.client.get(reverse('nomina_empleados'),{'empresa':self.empresa.pk})
        self.assertEqual(lista.status_code,200)
        self.assertNotContains(lista,'Empleado de otra sucursal')
        ficha=self.client.get(reverse('nomina_empleados'),{'empresa':self.empresa.pk,'empleado':empleado.pk})
        self.assertEqual(ficha.status_code,404)
        denegada=self.client.post(ruta,{'cuil':'20329642330','nombre_apellido':'Intruso',
            'legajo':'X-002','fecha_ingreso':'2026-01-15',
            'tipo_contratacion':'Completa','centro_operativo':str(self.c2.pk)})
        self.assertEqual(denegada.status_code,400)
        self.assertFalse(Empleado.objects.filter(empresa=self.empresa,legajo='X-002').exists())

    def test_caja_sin_predefinido_y_reversible_desde_gestor(self):
        from django.urls import reverse
        import re
        url_gestor = reverse('gestion_accesos_colaborador', args=[self.empresa.pk])
        self.assertFalse(puede(self.admin, self.empresa.pk, 'caja.total'))
        self.client.force_login(self.admin)
        no = self.client.get(reverse('panel_caja'), {'empresa': self.empresa.pk})
        self.assertEqual(no.status_code, 403)

        self.client.force_login(self.owner)
        pagina = self.client.get(url_gestor, {'usuario': self.admin.pk})
        self.assertEqual(pagina.status_code, 200)
        html = pagina.content.decode()
        casilla = re.search(r'<input[^>]*value="caja\.total"[^>]*>', html)
        self.assertIsNotNone(casilla)
        self.assertNotIn('checked', casilla.group(0))
        self.assertNotIn('disabled', casilla.group(0))
        # Un Colaborador jamás recibe Caja, ni siquiera forzando el POST.
        forzado = self.client.post(url_gestor, {
            'usuario': str(self.colab.pk), 'capacidad': ['caja.total'],
        })
        self.assertEqual(forzado.status_code, 403)
        self.assertFalse(puede(self.colab, self.empresa.pk, 'caja.total'))

        conceder = self.client.post(url_gestor, {
            'usuario': str(self.admin.pk), 'capacidad': ['caja.total'],
        })
        self.assertEqual(conceder.status_code, 302)
        self.assertTrue(puede(self.admin, self.empresa.pk, 'caja.total'))
        self.client.force_login(self.admin)
        si = self.client.get(reverse('panel_caja'), {'empresa': self.empresa.pk})
        self.assertEqual(si.status_code, 200)

        self.client.force_login(self.owner)
        revocar = self.client.post(url_gestor, {'usuario': str(self.admin.pk)})
        self.assertEqual(revocar.status_code, 302)
        self.assertFalse(puede(self.admin, self.empresa.pk, 'caja.total'))
        self.client.force_login(self.admin)
        no = self.client.get(reverse('panel_caja'), {'empresa': self.empresa.pk})
        self.assertEqual(no.status_code, 403)
