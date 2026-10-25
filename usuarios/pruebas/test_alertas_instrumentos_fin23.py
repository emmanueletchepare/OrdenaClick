"""FIN-02/FIN-03: solo lectura, días frontera, carteras y permisos."""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.models import (
    AplicacionPago, AsignacionUsuarioEmpresa, Banco, Caja, CentroOperativo,
    Cheque, Cobranza, CuentaBancaria, DestinatarioAlerta, Empresa,
    Ejercicio, Movimiento, Pago, PendienteBancario,
    PermisoAccesoColaborador,
)
from usuarios.services.identidades import obtener_identidad_usuario_empresa
from usuarios.services.alertas_instrumentos import (
    aviso_autorizado, avisos_visibles, fuentes_instrumentos,
)


class AlertasInstrumentosTests(TestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.owner = User.objects.create_user('owner_fin23', password='Clave123!')
        self.colab = User.objects.create_user('colab_fin23', password='Clave123!')
        self.centro_admin = User.objects.create_user('centro_fin23', password='Clave123!')
        self.ajeno = User.objects.create_user('ajeno_fin23', password='Clave123!')
        self.empresa = Empresa.objects.create(propietario=self.owner, razon_social='FIN23 SA')
        self.otra = Empresa.objects.create(propietario=self.ajeno, razon_social='Otra FIN23')
        self.c1 = CentroOperativo.objects.create(empresa=self.empresa, nombre='Centro 1', tipo='Casa Central')
        self.c2 = CentroOperativo.objects.create(empresa=self.empresa, nombre='Centro 2', tipo='Sucursal')
        self.caja = Caja.objects.create(empresa=self.empresa, centro_operativo=self.c1, nombre='Caja 1')
        self.banco = Banco.objects.create(empresa=self.empresa, nombre='Banco Prueba')
        self.cuenta = CuentaBancaria.objects.create(empresa=self.empresa, banco=self.banco,
            nombre='Cuenta ARS', dias_aviso_cheques_propios=3)
        self.identity = obtener_identidad_usuario_empresa(empresa=self.empresa, usuario=self.owner)
        self.cobranza = Cobranza.objects.create(empresa=self.empresa, caja=self.caja,
            fecha=self.hoy, referencia='Cobranza FIN23', creado_por=self.identity)
        self.ejercicio = Ejercicio.objects.create(empresa=self.empresa, numero=self.hoy.year,
            fecha_inicio=self.hoy.replace(month=1, day=1),
            fecha_cierre=self.hoy.replace(month=12, day=31))
        AsignacionUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=self.colab,
            jerarquia='colaborador', activo=True)
        AsignacionUsuarioEmpresa.objects.create(empresa=self.empresa, usuario=self.centro_admin,
            jerarquia='admin_centro', centro_operativo=self.c1, activo=True)

    def permiso(self, usuario, codigo, activo=True):
        PermisoAccesoColaborador.objects.update_or_create(
            empresa=self.empresa, usuario=usuario, codigo=codigo,
            defaults={'activo': activo, 'otorgado_por': self.owner})

    def asignar(self, usuario, codigo):
        DestinatarioAlerta.objects.create(empresa=self.empresa, usuario=usuario,
            codigo=codigo, activo=True, configurado_por=self.owner)

    def fisico(self, fecha=None, **extras):
        datos = {'empresa': self.empresa, 'tipo_instrumento': 'Cheque',
                 'origen': 'Tercero', 'tipo_cheque': 'Diferido', 'numero': '00000041',
                 'importe': Decimal('10.00'), 'cobranza': self.cobranza,
                 'caja': self.caja, 'estado': 'Disponible',
                 'fecha_emision': self.hoy - timedelta(days=90),
                 'fecha_acreditacion': fecha or self.hoy}
        datos.update(extras)
        return Cheque.objects.create(**datos)

    def electronico(self, fecha=None, **extras):
        datos = {'empresa': self.empresa, 'creado_por': self.identity,
                 'clave': uuid4(), 'tipo': 'ECheq', 'fecha': self.hoy,
                 'importe': Decimal('10.00'), 'referencia': '00000042',
                 'echeq_numero': '00000042', 'echeq_titular': 'Titular de prueba',
                 'echeq_fecha_acreditacion': fecha or self.hoy,
                 'estado_cartera': 'EnCartera', 'estado': 'Pendiente',
                 'echeq_condicion': 'Orden'}
        datos.update(extras)
        return PendienteBancario.objects.create(**datos)

    def propio(self, tipo='Cheque', fecha=None, **extras):
        pago = Pago.objects.create(empresa=self.empresa, fecha=self.hoy)
        datos = {'empresa': self.empresa, 'tipo_instrumento': tipo,
                 'origen': 'Propio', 'tipo_cheque': 'Diferido',
                 'numero': '00000043', 'importe': Decimal('10.00'),
                 'pago': pago, 'cuenta_bancaria': self.cuenta,
                 'fecha_emision': self.hoy - timedelta(days=2), 'fecha_acreditacion': fecha or self.hoy,
                 'estado': 'Pendiente'}
        datos.update(extras)
        cheque = Cheque.objects.create(**datos)
        return cheque, pago

    def test_fisicos_dias_frontera_y_salida(self):
        valor = self.fisico(self.hoy + timedelta(days=1))
        self.assertEqual(fuentes_instrumentos(self.empresa, self.hoy), [])
        valor.fecha_acreditacion = self.hoy - timedelta(days=29)
        valor.save(update_fields=['fecha_acreditacion'])
        self.assertEqual(fuentes_instrumentos(self.empresa, self.hoy)[0]['estado_alerta'], 'En atencion')
        valor.fecha_acreditacion = self.hoy - timedelta(days=30)
        valor.save(update_fields=['fecha_acreditacion'])
        self.assertEqual(fuentes_instrumentos(self.empresa, self.hoy)[0]['estado_alerta'], 'Vencido')
        valor.estado = 'Depositado'
        valor.save(update_fields=['estado'])
        self.assertEqual(fuentes_instrumentos(self.empresa, self.hoy), [])
        self.assertEqual(Cheque.objects.count(), 1)  # Nunca cambia estado por consultar.

    def test_echeq_pendiente_global_y_resuelto_por_centro(self):
        p = self.electronico(self.hoy - timedelta(days=30))
        self.permiso(self.centro_admin, 'alertas.ver')
        self.permiso(self.centro_admin, 'pendientes.ver')
        self.assertEqual(len(avisos_visibles(self.centro_admin, self.empresa, self.hoy)), 1)
        self.assertEqual(avisos_visibles(self.centro_admin, self.empresa, self.hoy)[0]['estado_alerta'], 'Vencido')
        p.estado = 'Resuelto'
        p.centro_operativo = self.c2
        p.save(update_fields=['estado', 'centro_operativo'])
        self.assertEqual(avisos_visibles(self.centro_admin, self.empresa, self.hoy), [])
        p.centro_operativo = self.c1
        p.save(update_fields=['centro_operativo'])
        self.assertEqual(len(avisos_visibles(self.centro_admin, self.empresa, self.hoy)), 1)

    def test_echeq_fuera_de_cartera_y_rechazo_no_alertan(self):
        self.electronico(estado_cartera='Endosado')
        self.electronico(estado_cartera='Depositado')
        self.electronico(estado_cartera='Rechazado')
        self.assertEqual(fuentes_instrumentos(self.empresa, self.hoy), [])

    def test_cheque_propio_anticipacion_y_revocacion(self):
        cheque, pago = self.propio(fecha=self.hoy + timedelta(days=4))
        self.assertEqual(fuentes_instrumentos(self.empresa, self.hoy), [])
        cheque.fecha_acreditacion = self.hoy + timedelta(days=3)
        cheque.save(update_fields=['fecha_acreditacion'])
        self.assertEqual(len(fuentes_instrumentos(self.empresa, self.hoy)), 1)
        self.permiso(self.colab, 'alertas.ver')
        self.permiso(self.colab, 'vencimientos.ver')
        self.assertEqual(avisos_visibles(self.colab, self.empresa, self.hoy), [])
        self.permiso(self.colab, 'registros.ver')
        self.assertEqual(len(avisos_visibles(self.colab, self.empresa, self.hoy)), 1)
        self.permiso(self.colab, 'registros.ver', False)
        self.assertEqual(avisos_visibles(self.colab, self.empresa, self.hoy), [])
        cheque.estado = 'Debitado'
        cheque.save(update_fields=['estado'])
        self.assertEqual(fuentes_instrumentos(self.empresa, self.hoy), [])

    def test_centro_propio_destinos_cruzados_no_filtran(self):
        cheque, pago = self.propio()
        self.permiso(self.centro_admin, 'alertas.ver')
        self.permiso(self.centro_admin, 'vencimientos.ver')
        self.permiso(self.centro_admin, 'registros.ver')
        self.assertEqual(avisos_visibles(self.centro_admin, self.empresa, self.hoy), [])
        m1 = Movimiento.objects.create(empresa=self.empresa, ejercicio=self.ejercicio,
            centro_operativo=self.c1, fecha_registro=self.hoy,
            importe=Decimal('20.00'), total=Decimal('20.00'))
        AplicacionPago.objects.create(pago=pago, movimiento=m1, importe=Decimal('5.00'))
        self.assertEqual(len(avisos_visibles(self.centro_admin, self.empresa, self.hoy)), 1)
        m2 = Movimiento.objects.create(empresa=self.empresa, ejercicio=self.ejercicio,
            centro_operativo=self.c2, fecha_registro=self.hoy,
            importe=Decimal('20.00'), total=Decimal('20.00'))
        AplicacionPago.objects.create(pago=pago, movimiento=m2, importe=Decimal('1.00'))
        self.assertEqual(avisos_visibles(self.centro_admin, self.empresa, self.hoy), [])

    def test_fisico_solo_caja_sin_permiso_no_fuga(self):
        self.fisico()
        self.permiso(self.colab, 'alertas.ver')
        self.permiso(self.colab, 'pendientes.ver')
        self.permiso(self.colab, 'vencimientos.ver')
        self.assertEqual(avisos_visibles(self.colab, self.empresa, self.hoy), [])
        self.permiso(self.centro_admin, 'alertas.ver')
        self.permiso(self.centro_admin, 'caja.total')
        self.assertEqual(len(avisos_visibles(self.centro_admin, self.empresa, self.hoy)), 1)
        self.permiso(self.centro_admin, 'caja.total', False)
        self.assertEqual(avisos_visibles(self.centro_admin, self.empresa, self.hoy), [])

    def test_llamador_requiere_suscripcion_y_listado_no(self):
        self.electronico()
        self.permiso(self.colab, 'alertas.ver')
        self.permiso(self.colab, 'pendientes.ver')
        self.client.force_login(self.colab)
        listado = self.client.get(reverse('listar_alertas'), {'empresa': self.empresa.pk}).json()
        self.assertEqual(len(listado['alertas_instrumentos']), 1)
        campana = self.client.get(reverse('estado_llamador_alertas'), {'empresa': self.empresa.pk}).json()
        self.assertFalse(campana['mostrar_llamador'])
        self.asignar(self.colab, 'FIN-03')
        campana = self.client.get(reverse('estado_llamador_alertas'), {'empresa': self.empresa.pk}).json()
        self.assertTrue(campana['mostrar_llamador'])
        self.permiso(self.colab, 'pendientes.ver', False)
        self.assertEqual(self.client.get(reverse('listar_alertas'),
                          {'empresa': self.empresa.pk}).json()['alertas_instrumentos'], [])
        self.assertFalse(self.client.get(reverse('estado_llamador_alertas'),
                         {'empresa': self.empresa.pk}).json()['mostrar_llamador'])

    def test_empresa_ajena_denegada(self):
        self.electronico()
        self.client.force_login(self.ajeno)
        self.assertEqual(self.client.get(reverse('listar_alertas'),
             {'empresa': self.empresa.pk}).status_code, 403)

    def test_propio_electronico_es_fuente_distinta(self):
        self.propio('ECheq')
        vistos = fuentes_instrumentos(self.empresa, self.hoy)
        self.assertEqual(len(vistos), 1)
        self.assertEqual(vistos[0]['codigo'], 'FIN-03')
        self.assertEqual(vistos[0]['grupo'], 'propio_electronico')
