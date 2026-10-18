from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from usuarios.models import AsignacionUsuarioEmpresa, Empresa, PermisoAccesoColaborador, EventoPermisoAccesoColaborador
from usuarios.services.accesos_colaborador import puede


class AccesosColaboradorTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_user('admin_test_accesos',password='ClaveSegura!')
        self.colab=User.objects.create_user('colab_test_accesos',password='ClaveSegura!')
        self.ajeno=User.objects.create_user('ajeno_test_accesos',password='ClaveSegura!')
        self.e=Empresa.objects.create(propietario=self.admin,razon_social='Empresa Propia')
        self.otra=Empresa.objects.create(propietario=self.ajeno,razon_social='Empresa Ajena')
        self.vinculo=AsignacionUsuarioEmpresa.objects.create(empresa=self.e,usuario=self.colab,jerarquia='colaborador',activo=True)
        self.url=reverse('gestion_accesos_colaborador',args=[self.e.pk]);self.client.force_login(self.admin)

    def test_permiso_no_existe_por_defecto(self):
        self.assertFalse(puede(self.colab,self.e.pk,'abm.proveedores'))
        self.assertFalse(puede(self.colab,self.e.pk,'claves.propias'))

    def test_guardar_revocar_y_auditar(self):
        self.assertEqual(self.client.post(self.url,{'usuario':self.colab.pk,'capacidad':['abm.proveedores']}).status_code,302)
        self.assertTrue(puede(self.colab,self.e.pk,'abm.proveedores'))
        self.assertFalse(puede(self.colab,self.e.pk,'abm.bancos'))
        self.client.post(self.url,{'usuario':self.colab.pk})
        self.assertFalse(puede(self.colab,self.e.pk,'abm.proveedores'))
        self.assertEqual(EventoPermisoAccesoColaborador.objects.filter(empresa=self.e,usuario=self.colab).count(),2)

    def test_usuario_ajeno_no_es_destinatario(self):
        r=self.client.post(self.url,{'usuario':self.ajeno.pk,'capacidad':['claves.propias']})
        self.assertEqual(r.status_code,403)
        self.assertFalse(PermisoAccesoColaborador.objects.exists())

    def test_colaborador_no_puede_modificar_ni_espiar_permisos(self):
        self.client.force_login(self.colab)
        self.assertEqual(self.client.get(self.url).status_code,403)
        self.assertEqual(self.client.post(self.url,{'usuario':self.colab.pk,'capacidad':['abm.bancos']}).status_code,403)

    def test_revocacion_estructural_inmediata(self):
        self.client.post(self.url,{'usuario':self.colab.pk,'capacidad':['abm.proveedores']})
        self.vinculo.activo=False;self.vinculo.save(update_fields=['activo'])
        self.assertFalse(puede(self.colab,self.e.pk,'abm.proveedores'))
