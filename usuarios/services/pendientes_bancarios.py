"""Gestión bancaria: cola global POR EMPRESA y asignación de Centro al resolver.

Ni los pendientes ni los e-Cheqs detectados generan saldos, cheques de Cartera,
recibos o Pagos. Los permisos funcionales jamás conceden capacidad de Caja.
"""
import logging
import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from usuarios.models import (
    AsignacionUsuarioEmpresa, Banco, CentroOperativo, CuentaBancaria, Empresa,
    EventoPendienteBancario, EventoPermisoBancario, PendienteBancario,
    PermisoPendienteBancarioCentro,
)
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.identidades import obtener_identidad_usuario_empresa
from usuarios.services.cheques import normalizar_numero_cheque

LOG = logging.getLogger('ordenaclick.audit')
MAX_LOTE = 80


def alcance_pendientes(usuario, empresa_id):
    """(Empresa, None = administración general; frozenset = Centros resolubles).

    Cualquier usuario con este alcance puede ver TODOS los pendientes DE LA
    EMPRESA; los resueltos se filtran por Centro autorizado en la consulta.
    """
    contexto = obtener_contexto_capacidades_empresa(usuario, empresa_id)
    empresa = contexto.empresa
    if contexto.es_superusuario or contexto.es_propietario or contexto.jerarquia == 'admin_general':
        return empresa, None
    if contexto.jerarquia == 'admin_centro':
        pk = contexto.centro_operativo_id
        if not pk or not CentroOperativo.objects.filter(pk=pk, empresa=empresa, activo=True).exists():
            raise PermissionDenied('Centro no autorizado.')
        return empresa, frozenset({pk})
    if contexto.jerarquia == 'colaborador':
        centros = frozenset(PermisoPendienteBancarioCentro.objects.filter(
            empresa=empresa, usuario=usuario, activo=True,
            centro_operativo__empresa=empresa, centro_operativo__activo=True,
        ).values_list('centro_operativo_id', flat=True))
        if centros:
            return empresa, centros
    raise PermissionDenied('No tiene permisos para gestionar pendientes bancarios.')


def exigir_centro(centro_id, alcance, empresa=None):
    """Comprobación obligatoria de Centro en resolución, incluida Empresa."""
    try:
        centro = int(centro_id)
    except (ValueError, TypeError) as exc:
        raise PermissionDenied('Seleccione un Centro autorizado.') from exc
    if alcance is not None and centro not in alcance:
        raise PermissionDenied('Centro no autorizado.')
    if empresa is not None and not CentroOperativo.objects.filter(
        pk=centro, empresa=empresa, activo=True).exists():
        raise PermissionDenied('Centro no autorizado.')
    return centro


def importe_positivo(valor):
    if not isinstance(valor, str) or len(valor) > 30:
        raise ValueError('El importe no es válido.')
    texto = valor.strip()
    if re.fullmatch(r'[0-9]{1,3}(?:\.[0-9]{3})+(?:,[0-9]{1,2})?', texto):
        texto = texto.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'[0-9]+,[0-9]{1,2}', texto):
        texto = texto.replace(',', '.')
    elif not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,2})?', texto):
        raise ValueError('El importe no es válido.')
    try:
        importe = Decimal(texto)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('El importe no es válido.') from exc
    if not importe.is_finite() or importe <= 0 or importe >= Decimal('1000000000000') or importe.as_tuple().exponent < -2:
        raise ValueError('El importe debe ser positivo, con hasta dos decimales.')
    return importe.quantize(Decimal('0.01'))


def _fecha(valor, nombre='fecha'):
    if not isinstance(valor, str):
        raise ValueError(f'La {nombre} no es válida.')
    try:
        resultado = date.fromisoformat(valor)
    except ValueError as exc:
        raise ValueError(f'La {nombre} no es válida.') from exc
    if resultado.isoformat() != valor:
        raise ValueError(f'La {nombre} no es válida.')
    return resultado


def _texto(valor, nombre, limite, obligatorio=False):
    if not isinstance(valor, str):
        raise ValueError(f'{nombre} no es válido.')
    valor = valor.strip()
    if len(valor) > limite or (obligatorio and not valor):
        raise ValueError(f'{nombre} no es válido (máximo {limite} caracteres).')
    return valor


def _normalizar_fila(empresa, datos, cuenta_id, clase):
    if not isinstance(datos, dict):
        raise ValueError('Fila de carga inválida.')
    if 'centro' in datos and datos['centro'] not in (None, ''):
        raise ValueError('El Centro se determina al resolver, no al detectar el movimiento.')
    cuenta = None
    if clase == 'bancos':
        cuenta = CuentaBancaria.objects.filter(pk=cuenta_id, empresa=empresa, activo=True).first()
        if cuenta is None:
            raise ValueError('Seleccione una cuenta bancaria de esta Empresa.')
    elif clase == 'echeqs':
        if cuenta_id not in (None, ''):
            raise ValueError('Un e-Cheq detectado no debe vincularse a una cuenta bancaria receptora.')
    try:
        clave = UUID(datos.get('clave', ''))
    except (TypeError, AttributeError, ValueError) as exc:
        raise ValueError('Identificador de operación inválido.') from exc
    importe = importe_positivo(datos.get('importe'))
    if clase == 'bancos':
        tipo = datos.get('tipo')
        if tipo not in ('Transferencia', 'Deposito'):
            raise ValueError('Seleccione depósito o transferencia.')
        fecha = _fecha(datos.get('fecha'))
        identificacion = _texto(datos.get('identificacion', ''), 'Identificación', 200)
        numero = titular = banco = codigo = ''
        acreditacion = None
        condicion = 'Orden'
        referencia = identificacion or 'Sin identificar'
    elif clase == 'echeqs':
        tipo = 'ECheq'
        titular = _texto(datos.get('titular', ''), 'Titular', 200, obligatorio=True)
        numero = normalizar_numero_cheque(datos.get('numero', ''))

        # El banco emisor es un ABM de la Empresa, no texto libre enviado por el navegador.
        try:
            banco_id = int(datos.get('banco_id'))
        except (ValueError, TypeError) as exc:
            raise ValueError('Seleccione un banco registrado de esta Empresa.') from exc
        emisor = Banco.objects.filter(pk=banco_id, empresa=empresa, activo=True).first()
        if emisor is None:
            raise ValueError('Seleccione un banco registrado de esta Empresa.')
        banco = emisor.nombre  # Snapshot histórico: no cambia si luego se renombra el ABM.
        codigo = ''  # Campo legado: no se pide código de banco en la carga de e-Cheq.
        acreditacion = _fecha(datos.get('acreditacion'), 'fecha de acreditación')
        if acreditacion < timezone.localdate() - timedelta(days=30):
            raise ValueError('La fecha de acreditación de un e-Cheq no puede tener más de 30 días de antigüedad.')
        fecha = _fecha(datos.get('fecha', acreditacion.isoformat()))
        condicion = datos.get('condicion', 'Orden')
        if condicion not in ('Orden', 'NoOrden'):
            raise ValueError('Condición de circulación inválida.')
        identificacion = _texto(datos.get('identificacion', ''), 'Identificación', 200)
        referencia = numero
    else:
        raise ValueError('Seleccione un tipo de carga válido.')
    return {
        'cuenta_bancaria': cuenta, 'clave': clave, 'fecha': fecha,
        'tipo': tipo, 'importe': importe, 'referencia': referencia,
        'identificacion': identificacion, 'echeq_titular': titular,
        'echeq_numero': numero, 'echeq_banco_nombre': banco,
        'echeq_banco_codigo': codigo, 'echeq_fecha_acreditacion': acreditacion,
        'echeq_condicion': condicion,
    }


def registrar_lote(*, usuario, empresa_id, cuenta_id, clase, filas):
    """Lote atómico, idempotencia por fila, sin filas parciales ni saldos."""
    empresa, alcance = alcance_pendientes(usuario, empresa_id)
    if alcance is not None:
        raise PermissionDenied('Sólo administración general registra movimientos detectados.')
    if not isinstance(filas, list) or not 1 <= len(filas) <= MAX_LOTE:
        raise ValueError(f'La carga admite entre 1 y {MAX_LOTE} filas.')
    # Validación global antes de persistir.
    normalizadas = [_normalizar_fila(empresa, fila, cuenta_id, clase) for fila in filas]
    claves = [fila['clave'] for fila in normalizadas]
    if len(claves) != len(set(claves)):
        raise ValueError('Un mismo identificador aparece dos veces en la carga.')
    with transaction.atomic():
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        identidad = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        ids = []
        for fila in normalizadas:
            anterior = PendienteBancario.objects.filter(clave=fila['clave']).first()
            if anterior is not None:
                if anterior.empresa_id != empresa.pk or anterior.creado_por_id != identidad.pk or any(
                    anterior.cuenta_bancaria_id != (valor.pk if valor is not None else None) if campo == 'cuenta_bancaria' else
                    getattr(anterior, campo) != valor
                    for campo, valor in fila.items() if campo != 'clave'
                ):
                    raise ValueError('La clave ya se utilizó para otro registro.')
                ids.append(anterior.pk)
                continue
            nuevo = PendienteBancario.objects.create(
                empresa=empresa, centro_operativo=None,
                creado_por=identidad, **fila)
            EventoPendienteBancario.objects.create(pendiente=nuevo, actor=identidad, accion='Creado')
            ids.append(nuevo.pk)
    LOG.info('banco.lote_creado empresa_id=%s cantidad=%s', empresa.pk, len(ids))
    return ids


def registrar_pendiente(*, usuario, empresa_id, datos):
    """Compatibilidad HTTP legado; nuevas pantallas usan registrar_lote."""
    tipo = datos.get('tipo')
    if tipo == 'ECheq':
        raise ValueError('Utilice la carga de e-Cheqs con sus datos completos.')
    fila = {'tipo': tipo, 'importe': datos.get('importe'), 'fecha': datos.get('fecha'),
            'identificacion': datos.get('referencia', ''), 'clave': datos.get('clave', '')}
    ids = registrar_lote(usuario=usuario, empresa_id=empresa_id,
                        cuenta_id=datos.get('cuenta'), clase='bancos', filas=[fila])
    return PendienteBancario.objects.get(pk=ids[0]), True


def resolver_pendiente(*, usuario, empresa_id, pendiente_id, centro_id,
                       identificacion, tipo_resolucion, referencia):
    empresa, alcance = alcance_pendientes(usuario, empresa_id)
    centro = exigir_centro(centro_id, alcance, empresa)
    identificacion = _texto(identificacion, 'Identificación del cliente', 200, obligatorio=True)
    if tipo_resolucion not in ('YaImputado', 'ReciboGenerado'):
        raise ValueError('Seleccione qué gestión realizó.')
    referencia = _texto(referencia, 'Referencia de comprobación', 200)
    if tipo_resolucion == 'ReciboGenerado' and len(referencia) < 3:
        raise ValueError('Indique el número o referencia del recibo realizado.')
    with transaction.atomic():
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        pendiente = PendienteBancario.objects.select_for_update().filter(
            pk=pendiente_id, empresa=empresa).first()
        if pendiente is None:
            raise PermissionDenied('Pendiente no autorizado.')
        if pendiente.estado != 'Pendiente':
            raise ValueError('Este movimiento ya fue resuelto.')
        actor = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        pendiente.centro_operativo_id = centro
        pendiente.identificacion = identificacion
        pendiente.estado = 'Resuelto'
        pendiente.tipo_resolucion = tipo_resolucion
        pendiente.referencia_resolucion = referencia
        pendiente.resuelto_por = actor
        pendiente.resuelto_en = timezone.now()
        pendiente.save(update_fields=['centro_operativo', 'identificacion', 'estado',
            'tipo_resolucion', 'referencia_resolucion', 'resuelto_por', 'resuelto_en', 'modificado'])
        EventoPendienteBancario.objects.create(pendiente=pendiente, actor=actor,
            accion='Resuelto', detalle=f'Centro {centro}; {tipo_resolucion}')
    LOG.info('banco.pendiente_resuelto empresa_id=%s pendiente_id=%s centro_id=%s',
             empresa.pk, pendiente.pk, centro)
    return pendiente


def cambiar_permiso(*, admin, empresa_id, usuario_id, centro_id, activo):
    contexto = obtener_contexto_capacidades_empresa(admin, empresa_id)
    if not (contexto.es_superusuario or contexto.es_propietario or contexto.jerarquia == 'admin_general'):
        raise PermissionDenied('Sólo la administración general asigna Centros de gestión.')
    empresa = contexto.empresa
    usuario = get_user_model().objects.filter(pk=usuario_id, is_active=True).first()
    centro = CentroOperativo.objects.filter(pk=centro_id, empresa=empresa, activo=True).first()
    if not centro or not usuario or not AsignacionUsuarioEmpresa.objects.filter(
        empresa=empresa, usuario=usuario, jerarquia='colaborador', activo=True).exists():
        raise ValueError('Seleccione un Colaborador activo y un Centro de la Empresa.')
    if activo not in ('1', '0'):
        raise ValueError('Seleccione conceder o revocar permiso.')
    with transaction.atomic():
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        identidad = obtener_identidad_usuario_empresa(empresa=empresa, usuario=admin)
        permiso, _ = PermisoPendienteBancarioCentro.objects.update_or_create(
            empresa=empresa, usuario=usuario, centro_operativo=centro,
            defaults={'activo': activo == '1', 'otorgado_por': identidad})
        EventoPermisoBancario.objects.create(empresa=empresa, usuario=usuario, centro_operativo=centro,
            actor=identidad, concedido=permiso.activo)
    LOG.info('banco.permiso_centro_%s empresa_id=%s centro_id=%s usuario_id=%s actor_id=%s',
             'concedido' if permiso.activo else 'revocado', empresa.pk, centro.pk, usuario.pk, admin.pk)
    return permiso
