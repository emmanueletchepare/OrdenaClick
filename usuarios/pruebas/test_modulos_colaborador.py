from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from usuarios.models import Empresa, AsignacionUsuarioEmpresa, PermisoAccesoColaborador, GestionClave
from usuarios.services.accesos_colaborador import exigir_abm
from django.core.exceptions import PermissionDenied


class ModulosColaboradorTests(TestCase):
    def setUp(self):
        self.admin=User.objects.create_user('admin_modulo',password='ClaveSegura!')
        self.colab=User.objects.create_user('colab_modulo',password='ClaveSegura!')
        self.otro=User.objects.create_user('otro_modulo',password='ClaveSegura!')
        self.e=Empresa.objects.create(propietario=self.admin,razon_social='Empresa Compartida')
        self.otra=Empresa.objects.create(propietario=self.otro,razon_social='Empresa Privada')
        self.asignacion=AsignacionUsuarioEmpresa.objects.create(empresa=self.e,usuario=self.colab,jerarquia='colaborador',activo=True)
    def dar(self,codigo):
        PermisoAccesoColaborador.objects.create(empresa=self.e,usuario=self.colab,codigo=codigo,otorgado_por=self.admin)
    def test_no_se_concede_admin_por_un_abm(self):
        self.dar('abm.proveedores')
        self.assertEqual(exigir_abm(self.colab,self.e.pk,'abm.proveedores').empresa.pk,self.e.pk)
        with self.assertRaises(PermissionDenied):exigir_abm(self.colab,self.e.pk,'abm.bancos')
        with self.assertRaises(PermissionDenied):exigir_abm(self.colab,self.otra.pk,'abm.proveedores')
    def test_sidebar_filtra_por_capacidad(self):
        self.dar('abm.proveedores')
        self.client.force_login(self.colab)
        response=self.client.get(reverse('panel_administrar'),{'empresa':self.e.pk})
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'data-oc-sidebar-accion="abm-proveedores"')
        self.assertNotContains(response,'data-oc-sidebar-accion="abm-bancos"')
        self.assertNotContains(response,'Gestion de claves')
        self.assertContains(response,'Seleccioná una función desde el menú lateral.')
    def test_claves_anteriores_no_se_asignan_solas(self):
        # No transferimos automáticamente secretos históricos sin dueño.
        self.assertTrue(GestionClave._meta.get_field('creado_por').null)

    def test_clave_ajena_no_se_lista_ni_revela(self):
        self.dar('claves.propias')
        GestionClave.objects.create(empresa=self.e,creado_por=self.colab,nombre='Mia',contrasena_cifrada='no-real')
        ajena=GestionClave.objects.create(empresa=self.e,creado_por=self.admin,nombre='Ajena',contrasena_cifrada='no-real')
        self.client.force_login(self.colab)
        response=self.client.get(reverse('listar_gestion_claves'),{'empresa':self.e.pk})
        self.assertEqual(response.status_code,200)
        self.assertIn('Mia',response.json()['html'])
        self.assertNotIn('Ajena',response.json()['html'])
        self.assertEqual(self.client.get(reverse('ver_gestion_clave'),{'empresa':self.e.pk,'clave':ajena.pk}).status_code,404)
