"""Regresión explícita: permisos por acción, Empresa y Centro, sin efecto financiero."""
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from usuarios.models import (Empresa, CentroOperativo, AsignacionUsuarioEmpresa,
    PermisoAccesoColaborador, PermisoPendienteBancarioCentro)
from usuarios.services.alcance_registros import empresa_registros, comprobar_centro
from usuarios.services.permisos_bancarios_accion import permitido
from usuarios.services.accesos_colaborador import guardar_accesos

class PermisosAccionTests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user('acc_owner',password='x')
        self.user=User.objects.create_user('acc_member',password='x')
        self.otra=User.objects.create_user('acc_otra',password='x')
        self.e=Empresa.objects.create(propietario=self.owner,razon_social='Empresa Acciones')
        self.b=Empresa.objects.create(propietario=self.otra,razon_social='Empresa Distinta')
        self.c=CentroOperativo.objects.create(empresa=self.e,nombre='CENTRO A',tipo='Casa Central',direccion='')
        self.otro=CentroOperativo.objects.create(empresa=self.b,nombre='OTRO',tipo='Casa Central',direccion='')
        self.rel=AsignacionUsuarioEmpresa.objects.create(empresa=self.e,usuario=self.user,jerarquia='colaborador',activo=True)

    def test_sin_permiso_no_lee_ni_carga(self):
        self.assertFalse(permitido(self.user,self.e.pk,'pendientes.ver'))
        self.assertFalse(permitido(self.user,self.e.pk,'pendientes.crear'))
        with self.assertRaises(PermissionDenied): empresa_registros(self.user,self.e.pk,'registros.crear')

    def test_concesion_revocacion_y_empresa_ajena(self):
        guardar_accesos(administrador=self.owner,empresa_id=self.e.pk,colaborador_id=self.user.pk,
                        codigos=['pendientes.ver','registros.crear'])
        self.assertTrue(permitido(self.user,self.e.pk,'pendientes.ver'))
        self.assertIsNotNone(empresa_registros(self.user,self.e.pk,'registros.crear'))
        self.assertFalse(permitido(self.user,self.b.pk,'pendientes.ver'))
        # Sin Centro concedido se consulta la bandeja global, no se confirma.
        from usuarios.services.pendientes_bancarios import alcance_pendientes
        _, centros = alcance_pendientes(self.user,self.e.pk)
        self.assertEqual(centros,frozenset())
        from django.urls import reverse
        self.client.force_login(self.user)
        entrada=self.client.post(reverse('entrar_gestion_bancaria'), {
            'empresa':self.e.pk,'origen':'colaborador','destino':'pendientes'})
        self.assertIn(entrada.status_code,(302,303))
        bandeja=self.client.get(reverse('gestion_bancaria'))
        self.assertEqual(bandeja.status_code,200)
        guardar_accesos(administrador=self.owner,empresa_id=self.e.pk,colaborador_id=self.user.pk,codigos=[])
        self.assertEqual(self.client.get(reverse('gestion_bancaria')).status_code,403)
        self.assertFalse(permitido(self.user,self.e.pk,'pendientes.ver'))
        with self.assertRaises(PermissionDenied): empresa_registros(self.user,self.e.pk,'registros.crear')

    def test_registrar_comprobante_no_implica_abrir_pagos(self):
        from usuarios.services.alcance_registros import impedir_pagos_delegados
        guardar_accesos(administrador=self.owner,empresa_id=self.e.pk,colaborador_id=self.user.pk,
                        codigos=['registros.crear'])
        with self.assertRaises(PermissionDenied):
            impedir_pagos_delegados(self.user,self.e,{'pagos':'[{"importe":"1"}]'})
        with self.assertRaises(PermissionDenied):
            impedir_pagos_delegados(self.user,self.e,{'modalidad_pago':'DebitoAutomatico'})
        impedir_pagos_delegados(self.user,self.e,{'pagos':'[]','modalidad_pago':'Manual'})
        impedir_pagos_delegados(self.owner,self.e,{'pagos':'[{"importe":"1"}]'})

    def test_bandeja_global_y_confirmacion_solo_centro(self):
        # Las concesiones antiguas POR CENTRO se preservan hasta nuevo guardado.
        PermisoPendienteBancarioCentro.objects.create(
            empresa=self.e,usuario=self.user,centro_operativo=self.c,activo=True)
        self.assertTrue(permitido(self.user,self.e.pk,'pendientes.ver'))
        self.assertTrue(permitido(self.user,self.e.pk,'pendientes.resolver'))
        guardar_accesos(administrador=self.owner,empresa_id=self.e.pk,colaborador_id=self.user.pk,
                        codigos=['pendientes.ver'])
        self.assertFalse(permitido(self.user,self.e.pk,'pendientes.resolver'))

    def test_maestro_solo_lectura_no_concede_abm(self):
        from django.urls import reverse
        guardar_accesos(administrador=self.owner,empresa_id=self.e.pk,colaborador_id=self.user.pk,
                        codigos=['registros.crear'])
        self.client.force_login(self.user)
        consulta=self.client.get(reverse('listar_centros_operativos'), {'empresa':self.e.pk})
        self.assertEqual(consulta.status_code,200)
        crear=self.client.post(reverse('guardar_centro_operativo'), {
            'empresa':self.e.pk,'nombre':'CENTRO FICTICIO','tipo':'Sucursal'})
        self.assertEqual(crear.status_code,403)

    def test_admin_centro_limite_estricto(self):
        self.rel.jerarquia='admin_centro'; self.rel.centro_operativo=self.c; self.rel.save()
        guardar_accesos(administrador=self.owner,empresa_id=self.e.pk,colaborador_id=self.user.pk,
                        codigos=['registros.crear'])
        comprobar_centro(self.user,self.e,self.c.pk)
        with self.assertRaises(PermissionDenied): comprobar_centro(self.user,self.e,self.otro.pk)
        with self.assertRaises(PermissionDenied): comprobar_centro(self.user,self.e,None)
