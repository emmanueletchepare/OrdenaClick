import io
import json
import os
import uuid
import zipfile
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from usuarios.models import (
    AsignacionUsuarioEmpresa,
    Banco,
    Caja,
    CentroOperativo,
    Cobranza,
    Empresa,
    GestionClave,
    IdentidadUsuarioEmpresa,
    MovimientoCaja,
    RolFuncionalUsuarioEmpresa,
)
from usuarios.services.backup_empresa.common import BackupEmpresaError, import_path
from usuarios.services.backup_empresa.exportacion import construir_backup_empresa
from usuarios.services.backup_empresa.importacion import guardar_upload_temporal, inspeccionar_backup
from usuarios.services.backup_empresa.restauracion import restaurar_empresa


class BackupEmpresaV1Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="fundador", password="test")
        self.empresa = Empresa.objects.create(
            propietario=self.user,
            razon_social="Empresa de prueba SA",
            nombre_fantasia="Empresa Test",
            cuit="30-00000000-1",
            condicion_fiscal="Responsable inscripto",
        )
        self.centro = CentroOperativo.objects.create(
            empresa=self.empresa,
            nombre="Casa Central",
            tipo="Casa Central",
            direccion="Prueba 123",
            activo=True,
        )
        self.caja = Caja.objects.create(
            empresa=self.empresa,
            centro_operativo=self.centro,
            nombre="Caja 1",
            activo=True,
        )
        self.banco = Banco.objects.create(empresa=self.empresa, nombre="Banco Test", activo=True)
        self.identidad = IdentidadUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.user,
            username_historico=self.user.username,
            nombre_historico="Fundador",
            email_historico="fundador@example.com",
        )
        self.cobranza = Cobranza.objects.create(
            empresa=self.empresa,
            caja=self.caja,
            fecha="2026-10-04",
            referencia="TEST",
            vendedor_referencia="",
            total_declarado=Decimal("100.00"),
            observaciones="",
            creado_por=self.identidad,
        )
        MovimientoCaja.objects.create(
            empresa=self.empresa,
            caja=self.caja,
            cobranza=self.cobranza,
            fecha="2026-10-04",
            tipo="Ingreso",
            moneda="ARS",
            importe=Decimal("100.00"),
            concepto="Prueba",
            creado_por=self.identidad,
        )

    def _token_from_blob(self, blob):
        token = str(uuid.uuid4())
        with open(import_path(token), "wb") as target:
            target.write(blob)
        return token

    def test_exporta_manifest_v1_y_no_exporta_password_de_gestion_clave(self):
        GestionClave.objects.create(
            empresa=self.empresa,
            nombre="Portal",
            sitio="https://example.com",
            usuario="usuario",
            correo="u@example.com",
            contrasena_cifrada="SECRETO-QUE-NO-DEBE-VIAJAR",
            activo=True,
        )
        blob, manifest = construir_backup_empresa(self.empresa)
        self.assertEqual(manifest["format"], "ordenaclick_empresa")
        self.assertEqual(manifest["version"], 1)
        self.assertFalse(manifest["security"]["contains_passwords"])
        with zipfile.ZipFile(io.BytesIO(blob), "r") as archive:
            claves = json.loads(archive.read("data/gestion_claves.json"))
        serializado = json.dumps(claves)
        self.assertNotIn("SECRETO-QUE-NO-DEBE-VIAJAR", serializado)
        self.assertTrue(claves[0]["fields"]["requiere_reconfiguracion"])


    def test_exporta_roles_funcionales_sin_convertirlos_en_permisos_django(self):
        RolFuncionalUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=self.user,
            rol=RolFuncionalUsuarioEmpresa.ROL_CONTABLE,
            activo=True,
        )
        blob, _manifest = construir_backup_empresa(self.empresa)
        with zipfile.ZipFile(io.BytesIO(blob), "r") as archive:
            usuarios = json.loads(archive.read("data/usuarios.json"))
        registro = next(item for item in usuarios if item["username"] == self.user.username)
        self.assertEqual(
            registro["functional_roles"],
            [{"rol": "contable", "activo": True}],
        )

    def test_inspector_rechaza_backup_legacy_sin_manifest(self):
        content = io.BytesIO()
        with zipfile.ZipFile(content, "w") as archive:
            archive.writestr("empresa.json", "{}")
        upload = SimpleUploadedFile("legacy.zip", content.getvalue(), content_type="application/zip")
        token = guardar_upload_temporal(upload)
        with self.assertRaises(BackupEmpresaError):
            inspeccionar_backup(token, self.user)

    def test_inspector_rechaza_path_traversal(self):
        content = io.BytesIO()
        with zipfile.ZipFile(content, "w") as archive:
            archive.writestr("../fuera.txt", "no")
            archive.writestr("manifest.json", "{}")
        token = self._token_from_blob(content.getvalue())
        with self.assertRaises(BackupEmpresaError):
            inspeccionar_backup(token, self.user)

    def test_round_trip_reconstruye_relaciones_sin_conservar_pk_hijos(self):
        old_centro_pk = self.centro.pk
        old_caja_pk = self.caja.pk
        blob, _manifest = construir_backup_empresa(self.empresa)
        token = self._token_from_blob(blob)
        info = inspeccionar_backup(token, self.user)
        restored = restaurar_empresa(
            token,
            self.user,
            {
                "empresa_existente_id": self.empresa.pk,
                "empresa": info["empresa"],
                "documentos": {},
                "documentos_nombres": {},
                "usuarios": {},
            },
        )
        self.assertEqual(restored.pk, self.empresa.pk)
        new_centro = CentroOperativo.objects.get(empresa=restored, nombre="Casa Central")
        new_caja = Caja.objects.get(empresa=restored, nombre="Caja 1")
        self.assertNotEqual(new_centro.pk, old_centro_pk)
        self.assertNotEqual(new_caja.pk, old_caja_pk)
        cobranza = Cobranza.objects.get(empresa=restored, referencia="TEST")
        self.assertEqual(cobranza.caja, new_caja)
        self.assertEqual(cobranza.creado_por.empresa, restored)
        movimiento = MovimientoCaja.objects.get(empresa=restored, cobranza=cobranza)
        self.assertEqual(movimiento.caja, new_caja)


    def test_admin_general_puede_restaurar_sin_reemplazar_al_fundador(self):
        admin_general = User.objects.create_user(
            username="admin_general_backup",
            password="test",
        )
        AsignacionUsuarioEmpresa.objects.create(
            empresa=self.empresa,
            usuario=admin_general,
            jerarquia=AsignacionUsuarioEmpresa.JERARQUIA_ADMIN_GENERAL,
            activo=True,
        )

        propietario_original_id = self.empresa.propietario_id
        blob, _manifest = construir_backup_empresa(self.empresa)
        token = self._token_from_blob(blob)

        info = inspeccionar_backup(
            token,
            admin_general,
        )
        self.assertEqual(
            info["propietario_actual_id"],
            propietario_original_id,
        )

        restored = restaurar_empresa(
            token,
            admin_general,
            {
                "empresa_existente_id": self.empresa.pk,
                "empresa": info["empresa"],
                "documentos": {},
                "documentos_nombres": {},
                "usuarios": {},
            },
        )

        self.assertEqual(
            restored.propietario_id,
            propietario_original_id,
        )
        self.assertNotEqual(
            restored.propietario_id,
            admin_general.pk,
        )
