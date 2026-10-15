"""Nómina: Empresa, permisos, legajo, documentos, alerta y desvinculación."""
from datetime import date
import tempfile
from django.test import override_settings

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from usuarios.models import (AlertaLicenciaEmpleado, AsignacionUsuarioEmpresa, Banco,
    CentroOperativo, DocumentoEmpleado, Empleado, Empresa, EventoEmpleado)
from usuarios.services.nomina import mes_anterior
from usuarios.services.backup_empresa.specs import SPEC_BY_KEY


class NominaEmpleadosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.dueno = User.objects.create_user('nm_dueno',password='Nm!pass2026')
        cls.dueno_ajeno = User.objects.create_user('nm_ajeno',password='Nm!pass2026')
        cls.colab = User.objects.create_user('nm_colab',password='Nm!pass2026')
        cls.e = Empresa.objects.create(propietario=cls.dueno,razon_social='Nomina prueba')
        cls.e2 = Empresa.objects.create(propietario=cls.dueno_ajeno,razon_social='Otra nomina')
        cls.c = CentroOperativo.objects.create(empresa=cls.e,nombre='Casa Central',tipo='Casa Central')
        cls.banco = Banco.objects.create(empresa=cls.e,nombre='Banco Principal')
        AsignacionUsuarioEmpresa.objects.create(empresa=cls.e,usuario=cls.colab,jerarquia='colaborador',activo=True)

    def setUp(self):
        self.client.force_login(self.dueno)

    def datos(self, **extra):
        return dict(cuil='20329642330', nombre_apellido='Persona Prueba', legajo='L-001',
                    fecha_ingreso='2026-01-15', tipo_contratacion='Completa',
                    centro_operativo=str(self.c.pk), **extra)

    def crear(self):
        r=self.client.post(reverse('nomina_registrar_empleado',args=[self.e.pk]),self.datos())
        self.assertEqual(r.status_code,302,r.content[:300])
        return Empleado.objects.get(empresa=self.e)

    def test_listado_vacio_y_registrar(self):
        r=self.client.get(reverse('nomina_empleados'), {'empresa':self.e.pk})
        self.assertEqual(r.status_code,200)
        self.assertContains(r,'Empleados activos')
        self.assertContains(r,'Empleados inactivos')
        self.crear()
        self.assertContains(self.client.get(reverse('nomina_empleados'),{'empresa':self.e.pk}),'Persona Prueba')

    def test_nomina_visible_en_marco_del_mismo_origen(self):
        """GET de Nómina y errores POST deben permitir sólo el iframe propio."""
        listado = self.client.get(reverse('nomina_empleados'), {'empresa': self.e.pk})
        self.assertEqual(listado.status_code, 200)
        self.assertEqual(listado['X-Frame-Options'], 'SAMEORIGIN')
        invalido = self.client.post(
            reverse('nomina_registrar_empleado', args=[self.e.pk]),
            {**self.datos(), 'nombre_apellido': ''},
        )
        self.assertEqual(invalido.status_code, 400)
        self.assertEqual(invalido['X-Frame-Options'], 'SAMEORIGIN')
        self.assertFalse(Empleado.objects.filter(empresa=self.e).exists())

    def test_cuil_con_guiones_se_guarda_normalizado(self):
        datos = self.datos()
        datos['cuil'] = '20-32964233-0'
        respuesta = self.client.post(
            reverse('nomina_registrar_empleado', args=[self.e.pk]), datos
        )
        self.assertEqual(respuesta.status_code, 302, respuesta.content[:250])
        self.assertEqual(Empleado.objects.get(empresa=self.e).cuil, '20329642330')

    def test_listado_sin_volver_y_ficha_con_abm_contextuales(self):
        lista = self.client.get(reverse('nomina_empleados'), {'empresa': self.e.pk})
        self.assertNotContains(lista, 'Volver al listado')
        ficha = self.client.get(reverse('nomina_empleados'), {
            'empresa': self.e.pk, 'nuevo': '1',
        })
        self.assertContains(ficha, 'Volver al listado')
        self.assertContains(ficha, 'maxlength="13"')
        for destino in ('centros', 'recursos', 'bancos'):
            self.assertContains(ficha, 'data-nomina-abm="' + destino + '"')
        self.assertNotContains(ficha, 'nomina_abm=')
        self.assertContains(ficha, 'nm-file-btn')
        self.assertContains(ficha, 'Clave de Alta Temprana - CAT')

    def test_contactos_laborales_separados_y_persistentes(self):
        url = reverse('nomina_registrar_empleado', args=[self.e.pk])
        respuesta = self.client.post(url, self.datos(
            mail_personal='personal@ejemplo.com',
            mail_laboral='trabajo@ejemplo.com',
            telefono_personal='2284-555-010',
            telefono_laboral='2284-555-090',
        ))
        self.assertEqual(respuesta.status_code, 302, respuesta.content[:300])
        empleado = Empleado.objects.get(empresa=self.e)
        self.assertEqual(empleado.mail_personal, 'personal@ejemplo.com')
        self.assertEqual(empleado.mail_laboral, 'trabajo@ejemplo.com')
        self.assertEqual(empleado.telefono_personal, '2284-555-010')
        self.assertEqual(empleado.telefono_laboral, '2284-555-090')

        ficha = self.client.get(reverse('nomina_empleados'), {
            'empresa': self.e.pk, 'empleado': empleado.pk,
        })
        self.assertEqual(ficha.status_code, 200)
        html = ficha.content.decode('utf-8')
        personales = html.split('<legend>Datos personales</legend>', 1)[1].split(
            '<legend>Datos laborales</legend>', 1)[0]
        laborales = html.split('<legend>Datos laborales</legend>', 1)[1].split(
            '</fieldset>', 1)[0]
        self.assertIn('Mail personal', personales)
        self.assertIn('Teléfono personal', personales)
        self.assertNotIn('Mail laboral', personales)
        self.assertNotIn('Teléfono laboral', personales)
        self.assertIn('Mail laboral', laborales)
        self.assertIn('Teléfono laboral', laborales)
        self.assertIn('name="telefono_laboral"', laborales)

        editar = reverse('nomina_editar_empleado', args=[self.e.pk, empleado.pk])
        respuesta = self.client.post(editar, self.datos(
            mail_personal='personal@ejemplo.com',
            mail_laboral='nuevo@ejemplo.com',
            telefono_personal='2284-555-010',
            telefono_laboral='2284-555-099',
        ))
        self.assertEqual(respuesta.status_code, 302, respuesta.content[:300])
        empleado.refresh_from_db()
        self.assertEqual(empleado.mail_laboral, 'nuevo@ejemplo.com')
        self.assertEqual(empleado.telefono_laboral, '2284-555-099')
        self.assertEqual(empleado.mail_personal, 'personal@ejemplo.com')

    def test_empresa_ajena_y_colaborador_denegados(self):
        self.assertEqual(self.client.get(reverse('nomina_empleados'),{'empresa':self.e2.pk}).status_code,403)
        self.client.force_login(self.colab)
        self.assertEqual(self.client.get(reverse('nomina_empleados'),{'empresa':self.e.pk}).status_code,403)
        self.assertEqual(self.client.post(reverse('nomina_registrar_empleado',args=[self.e.pk]),self.datos()).status_code,403)

    def test_empresa_relaciones_fk_bloqueadas(self):
        b2=Banco.objects.create(empresa=self.e2,nombre='Ajeno')
        r=self.client.post(reverse('nomina_registrar_empleado',args=[self.e.pk]),self.datos(banco=str(b2.pk)))
        self.assertEqual(r.status_code,400)
        self.assertFalse(Empleado.objects.exists())

    def test_legajo_y_cuil_unicos_incluso_inactivo(self):
        obj=self.crear()
        self.client.post(reverse('nomina_desvincular_empleado',args=[self.e.pk,obj.pk]),{'fecha':'2026-02-15','motivo':'Fin de contrato acordado'})
        r=self.client.post(reverse('nomina_registrar_empleado',args=[self.e.pk]),self.datos())
        self.assertEqual(r.status_code,400)
        self.assertEqual(Empleado.objects.count(),1)

    def test_alerta_mes_calendario_y_cancelacion(self):
        self.assertEqual(mes_anterior(date(2026,3,31)),date(2026,2,28))
        empleado=self.crear()
        r=self.client.post(reverse('nomina_editar_empleado',args=[self.e.pk,empleado.pk]),{
            **self.datos(), 'fecha_vencimiento_licencia':'2026-11-30',
        })
        self.assertEqual(r.status_code,302,r.content[:300])
        alerta=AlertaLicenciaEmpleado.objects.get(empleado=empleado)
        self.assertEqual(alerta.fecha_aviso,date(2026,10,30))
        self.assertIsNone(alerta.cancelada_en)
        r=self.client.post(reverse('nomina_desvincular_empleado',args=[self.e.pk,empleado.pk]),
                           {'fecha':'2026-02-15','motivo':'Finalización laboral pactada'})
        self.assertEqual(r.status_code,302)
        alerta.refresh_from_db(); empleado.refresh_from_db()
        self.assertFalse(empleado.activo)
        self.assertIsNotNone(alerta.cancelada_en)
        self.assertTrue(EventoEmpleado.objects.filter(empleado=empleado,accion='Desvinculado').exists())
        self.assertEqual(self.client.post(reverse('nomina_editar_empleado',args=[self.e.pk,empleado.pk]),self.datos()).status_code,403)

    def test_documento_privado_y_rechazo_de_texto(self):
        empleado=self.crear()
        r=self.client.post(reverse('nomina_editar_empleado',args=[self.e.pk,empleado.pk]),{
            **self.datos(), 'dni_frente':SimpleUploadedFile('dni.pdf',b'no es pdf',content_type='application/pdf'),
        })
        self.assertEqual(r.status_code,400)
        self.assertFalse(DocumentoEmpleado.objects.exists())

    def test_documento_pdf_privado_y_sin_cruce_empresa(self):
        empleado = self.crear()
        with tempfile.TemporaryDirectory() as carpeta, self.settings(MEDIA_ROOT=carpeta):
            r = self.client.post(reverse('nomina_editar_empleado',args=[self.e.pk,empleado.pk]),{
                **self.datos(),
                'dni_frente':SimpleUploadedFile('Documento Dni.pdf',b'%PDF-1.4\ncontenido de prueba',content_type='application/pdf'),
            })
            self.assertEqual(r.status_code,302,r.content[:300])
            doc = DocumentoEmpleado.objects.get(empleado=empleado)
            self.assertNotIn('Documento Dni',doc.archivo.name)
            url = reverse('descargar_documento_nomina',args=[self.e.pk,doc.pk])
            r = self.client.get(url)
            self.assertEqual(r.status_code,200)
            self.assertEqual(b''.join(r.streaming_content),b'%PDF-1.4\ncontenido de prueba')
            r.close()
            self.client.force_login(self.dueno_ajeno)
            self.assertEqual(self.client.get(url).status_code,403)

    def test_caso_con_actuacion(self):
        empleado=self.crear()
        r=self.client.post(reverse('nomina_crear_caso',args=[self.e.pk,empleado.pk]),
                           {'categoria':'Apercibimiento','fecha':'2026-10-01','descripcion':'Apercibimiento por incumplimiento documentado.'})
        self.assertEqual(r.status_code,302)
        self.assertEqual(empleado.casos.count(),1)
        caso=empleado.casos.get()
        r=self.client.post(reverse('nomina_actuar_caso',args=[self.e.pk,empleado.pk,caso.pk]),
                           {'fecha':'2026-10-02','detalle':'Se agregó descargo firmado y revisado.','cerrar':'1'})
        self.assertEqual(r.status_code,302)
        caso.refresh_from_db()
        self.assertEqual(caso.estado,'Cerrado')
        self.assertEqual(caso.actuaciones.count(),2)

    def test_backup_porta_hechos_y_no_permisos(self):
        for key in ('empleados','eventos_empleados','alertas_licencia_empleados','casos_empleados','actuaciones_casos_empleados','documentos_empleados'):
            self.assertIn(key,SPEC_BY_KEY)
