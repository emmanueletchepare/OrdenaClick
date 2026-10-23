"""Estados de cartera virtual: aislamiento, auditoría, idempotencia y permisos."""
from datetime import timedelta
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.models import (
    AsignacionUsuarioEmpresa, Banco, CentroOperativo, Empresa,
    EventoEstadoECheq, PendienteBancario, PermisoPendienteBancarioCentro,
)
from usuarios.services.pendientes_bancarios import registrar_lote
from usuarios.services.backup_empresa.specs import SPEC_BY_KEY


class CarteraVirtualECheqTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dueno = User.objects.create_user('echeqdueno', password='Clave.2026.A')
        cls.otro = User.objects.create_user('echeqajeno', password='Clave.2026.A')
        cls.colab = User.objects.create_user('echeqcolab', password='Clave.2026.A')
        cls.e = Empresa.objects.create(propietario=cls.dueno, razon_social='Empresa Test ECheq')
        cls.e2 = Empresa.objects.create(propietario=cls.otro, razon_social='Empresa Ajena')
        cls.c = CentroOperativo.objects.create(empresa=cls.e, nombre='Central', tipo='Casa Central')
        cls.b = Banco.objects.create(empresa=cls.e, nombre='Banco Test')
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.e, usuario=cls.colab,
            jerarquia='colaborador', activo=True)
        PermisoPendienteBancarioCentro.objects.create(empresa=cls.e, usuario=cls.colab,
            centro_operativo=cls.c, activo=True)

    def crear(self):
        hoy = timezone.localdate().isoformat()
        ids = registrar_lote(usuario=self.dueno, empresa_id=self.e.pk, cuenta_id=None,
            clase='echeqs', filas=[{
                'clave': str(uuid4()), 'titular': 'Titular Ejemplo', 'numero': '185',
                'banco_id': str(self.b.pk), 'banco': self.b.nombre, 'importe': '12300.00',
                'acreditacion': hoy, 'condicion': 'Orden',
            }])
        return PendienteBancario.objects.get(pk=ids[0])

    def activar(self, usuario=None, empresa=None):
        self.client.force_login(usuario or self.dueno)
        r = self.client.post(reverse('entrar_gestion_bancaria'), {
            'empresa': (empresa or self.e).pk, 'origen': 'admin',
        })
        self.assertEqual(r.status_code, 302)

    def detalle(self, p):
        return reverse('estado_echeq_detalle', args=[p.pk])

    def guardar(self, p, estado='Rechazado', clave=None, fecha=None, **extra):
        return self.client.post(reverse('estado_echeq_registrar', args=[p.pk]), {
            'clave': clave or str(uuid4()), 'estado': estado,
            'fecha': fecha or timezone.localdate().isoformat(),
            'observaciones': extra.get('observaciones', 'Prueba'),
        })

    def test_ingreso_ya_es_cartera_y_no_duplica_cheque(self):
        p = self.crear()
        self.assertEqual(p.estado_cartera, 'EnCartera')
        self.assertEqual(p.estado, 'Pendiente')
        from usuarios.models import Cheque
        self.assertEqual(Cheque.objects.count(), 0)

    def test_registrar_rechazo_audita_y_resuelve_en_misma_transaccion(self):
        p = self.crear()
        self.activar()
        r = self.guardar(p)
        self.assertEqual(r.status_code, 200, r.content)
        p.refresh_from_db()
        self.assertEqual(p.estado_cartera, 'Rechazado')
        self.assertEqual(p.estado, 'Resuelto')
        self.assertEqual(p.tipo_resolucion, 'Rechazado')
        self.assertEqual(p.resuelto_por.usuario_id, self.dueno.pk)
        self.assertIsNotNone(p.resuelto_en)
        e = EventoEstadoECheq.objects.get(pendiente=p)
        self.assertEqual(e.estado_anterior, 'EnCartera')
        self.assertEqual(e.estado_nuevo, 'Rechazado')
        historial = self.client.get(self.detalle(p)).json()
        self.assertEqual(historial['estado'], 'Rechazado')
        self.assertEqual(historial['acciones'], ['Devuelto'])
        self.assertTrue(any(x['accion'] == 'Rechazado' for x in historial['historial']))
        self.assertTrue(any(x['accion'] == 'Creado' for x in historial['historial']))

    def test_rechazado_despues_devuelto_guarda_dos_hechos(self):
        p = self.crear()
        self.activar()
        self.assertEqual(self.guardar(p).status_code, 200)
        self.assertEqual(self.guardar(p, 'Devuelto').status_code, 200)
        self.assertEqual(list(EventoEstadoECheq.objects.filter(pendiente=p).values_list(
            'estado_nuevo', flat=True)), ['Rechazado', 'Devuelto'])
        p.refresh_from_db()
        self.assertEqual(p.estado_cartera, 'Devuelto')
        self.assertEqual(p.estado, 'Resuelto')
        self.assertEqual(p.tipo_resolucion, 'Rechazado')

    def test_no_admite_repetir_estado_ni_mutar_devuelto(self):
        p = self.crear()
        self.activar()
        self.assertEqual(self.guardar(p, 'Devuelto').status_code, 200)
        self.assertEqual(self.guardar(p, 'Rechazado').status_code, 400)
        self.assertEqual(EventoEstadoECheq.objects.filter(pendiente=p).count(), 1)

    def test_reenvio_idempotente_misma_clave(self):
        p = self.crear()
        self.activar()
        clave = str(uuid4())
        r1 = self.guardar(p, clave=clave)
        r2 = self.guardar(p, clave=clave)
        self.assertTrue(r1.json()['creada'])
        self.assertFalse(r2.json()['creada'])
        self.assertEqual(EventoEstadoECheq.objects.filter(pendiente=p).count(), 1)
        self.assertEqual(self.guardar(p, estado='Devuelto', clave=clave).status_code, 400)

    def test_vencido_solo_tras_treinta_dias(self):
        p = self.crear()
        self.activar()
        self.assertNotIn('Vencido', self.client.get(self.detalle(p)).json()['acciones'])
        self.assertEqual(self.guardar(p, 'Vencido').status_code, 400)
        p.echeq_fecha_acreditacion = timezone.localdate()-timedelta(days=31)
        p.save(update_fields=['echeq_fecha_acreditacion'])
        self.assertIn('Vencido', self.client.get(self.detalle(p)).json()['acciones'])
        self.assertEqual(self.guardar(p, 'Vencido').status_code, 200)

    def test_fecha_futura_rechazada(self):
        p = self.crear()
        self.activar()
        self.assertEqual(self.guardar(p, fecha=(timezone.localdate()+timedelta(days=1)).isoformat()).status_code, 400)
        self.assertEqual(p.estados_cartera.count(), 0)

    def test_colaborador_autorizado_lee_pero_no_cambia_estado(self):
        p = self.crear()
        self.activar(self.colab)
        r = self.client.get(self.detalle(p))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['acciones'], [])
        self.assertEqual(self.guardar(p).status_code, 403)

    def test_empresa_ajena_no_accede_ni_modifica(self):
        p = self.crear()
        self.activar(self.otro, self.e2)
        self.assertEqual(self.client.get(self.detalle(p)).status_code, 403)
        self.assertEqual(self.guardar(p).status_code, 403)

    def test_rutas_exigen_sesion_de_empresa(self):
        p = self.crear()
        self.client.force_login(self.dueno)
        self.assertEqual(self.client.get(self.detalle(p)).status_code, 403)
        self.assertEqual(self.guardar(p).status_code, 403)

    def test_backup_incluye_estados(self):
        self.assertIn('estados_cartera_echeq', SPEC_BY_KEY)

    def test_rechazado_en_resueltos_rojo_y_no_en_pendientes(self):
        p = self.crear()
        self.activar()
        self.assertEqual(self.guardar(p).status_code, 200)
        pendientes = self.client.get(reverse('gestion_bancaria') + '?estado=Pendiente')
        self.assertEqual(pendientes.status_code, 200)
        self.assertFalse(any(
            fila.pk == p.pk for fila in pendientes.context['pagina'].object_list
        ), 'Un e-Cheq rechazado no debe aparecer en la tabla de Pendientes')
        resueltos = self.client.get(reverse('gestion_bancaria') + '?estado=Resuelto')
        self.assertContains(resueltos, p.echeq_numero)
        self.assertContains(resueltos, 'gb-registro-rechazado')
        self.assertContains(resueltos, 'Rechazado')

    def test_regularizacion_legacy_exige_rechazo_auditado_y_permiso(self):
        p = self.crear()
        self.activar()
        from usuarios.models import EventoPendienteBancario
        url = reverse('estado_echeq_regularizar_rechazo', args=[p.pk])
        self.assertEqual(self.client.post(url).status_code, 400)
        # Simular registro histórico con rechazo auditado, sin pasar por el servicio nuevo.
        from usuarios.services.identidades import obtener_identidad_usuario_empresa
        actor = obtener_identidad_usuario_empresa(empresa=self.e, usuario=self.dueno)
        p.estado_cartera = 'Rechazado'
        p.save(update_fields=['estado_cartera'])
        EventoEstadoECheq.objects.create(pendiente=p, actor=actor, clave=uuid4(),
            estado_anterior='EnCartera', estado_nuevo='Rechazado',
            fecha=timezone.localdate(), observaciones='Rechazo histórico')
        self.assertEqual(self.client.get(self.detalle(p)).json()['regularizar_rechazo'], True)
        antes = EventoPendienteBancario.objects.filter(pendiente=p).count()
        respuesta = self.client.post(url)
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        self.assertTrue(respuesta.json()['creada'])
        p.refresh_from_db()
        self.assertEqual((p.estado, p.tipo_resolucion), ('Resuelto', 'Rechazado'))
        self.assertEqual(EventoPendienteBancario.objects.filter(pendiente=p).count(), antes + 1)
        self.assertEqual(self.client.post(url).json()['creada'], False)
        self.assertEqual(EventoPendienteBancario.objects.filter(pendiente=p).count(), antes + 1)
        self.assertEqual(self.client.get(self.detalle(p)).json()['regularizar_rechazo'], False)

    def test_colaborador_no_regulariza_rechazo_historico(self):
        p = self.crear()
        p.estado_cartera = 'Rechazado'
        p.save(update_fields=['estado_cartera'])
        self.activar(self.colab)
        respuesta = self.client.post(reverse('estado_echeq_regularizar_rechazo', args=[p.pk]))
        self.assertEqual(respuesta.status_code, 403)
        p.refresh_from_db()
        self.assertEqual(p.estado, 'Pendiente')
