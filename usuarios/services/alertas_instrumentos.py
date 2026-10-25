"""Fuentes read-only FIN-02 y FIN-03.

No ejecuta transiciones, no marca cheques vencidos, no determina si se puede
realizar un Pago/depósito/endoso/cesión. Esas reglas pertenecen a Cartera/Caja.
Las fechas de alertas se calculan en backend, y los permisos de cada fuente
se comprueban otra vez en cada lectura o consulta del llamador.
"""
from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.utils import timezone

from usuarios.models import AplicacionPago, Cheque, PendienteBancario
from usuarios.services.accesos_colaborador import puede
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.alcances_centros import centros_activos_de_usuario
from usuarios.services.pendientes_bancarios import alcance_pendientes
from usuarios.services.permisos_bancarios_accion import permitido as permiso_bancario
from usuarios.services.seguridad import cajas_autorizadas

CODIGOS = ('FIN-02', 'FIN-03')


def permisos_lectura_tipo(usuario, empresa, codigo):
    """Existencia de al menos una fuente autorizada; no da permiso al instrumento.

    FIN-02: Caja de terceros o Registros + Vencimientos para propios emitidos.
    FIN-03: Gestión Bancaria para cartera virtual o propios emitidos.
    """
    if codigo not in CODIGOS or not puede(usuario, empresa.pk, 'alertas.ver'):
        return False
    propios = (puede(usuario, empresa.pk, 'registros.ver') and
               puede(usuario, empresa.pk, 'vencimientos.ver'))
    if codigo == 'FIN-02':
        try:
            _, cajas = cajas_autorizadas(usuario, empresa.pk)
            fisicos = cajas.exists()
        except (PermissionDenied, ValueError, TypeError):
            fisicos = False
        return propios or fisicos
    return propios or permiso_bancario(usuario, empresa.pk, 'pendientes.ver')


def _datos(*, codigo, grupo, objeto, numero, fecha, limite, hoy,
           caja_id=None, pago_id=None, centro_id=None, pendiente=False):
    """Emite sólo los datos necesarios para una alerta, no importes ni saldos."""
    if grupo.startswith('propio_'):
        situacion = ('Vencido' if fecha < hoy else 'Hoy' if fecha == hoy else 'Proximo')
    else:
        situacion = 'Vencido' if hoy >= limite else 'En atencion'
    return {
        'codigo': codigo, 'grupo': grupo, 'id': objeto.pk,
        'numero': numero, 'fecha_acreditacion': fecha.isoformat(),
        'fecha_limite': limite.isoformat(), 'estado_alerta': situacion,
        'caja_id': caja_id, 'pago_id': pago_id, 'centro_id': centro_id,
        'pendiente_administrativo': pendiente,
    }


def fuentes_instrumentos(empresa, hoy=None):
    """Obtiene avisos vigentes de fuentes existentes; jamás modifica un estado.

    Terceros: sólo instrumentos realmente en cartera y ya acreditables.
    Día 0 a 29: atención; día 30 en adelante: alerta de vencido persistente.
    Propios: fecha de acreditación menos anticipo configurado por cuenta;
    siguen avisando si su estado persistido continúa Pendiente.
    """
    hoy = hoy or timezone.localdate()
    resultado = []

    fisicos = Cheque.objects.filter(
        empresa=empresa, tipo_instrumento='Cheque', origen='Tercero',
        cobranza__isnull=False, caja__isnull=False, estado='Disponible',
        fecha_acreditacion__isnull=False, fecha_acreditacion__lte=hoy,
    ).select_related('caja').order_by('pk')
    for valor in fisicos:
        limite = valor.fecha_acreditacion + timedelta(days=30)
        # El aviso sigue la ventana documental de 30 días.
        # La fecha_vencimiento registrada permanece bajo control de Caja.
        resultado.append(_datos(
            codigo='FIN-02', grupo='cartera_fisica', objeto=valor,
            numero=valor.numero, fecha=valor.fecha_acreditacion,
            limite=limite, hoy=hoy, caja_id=valor.caja_id,
            centro_id=valor.caja.centro_operativo_id,
        ))

    electronicos = PendienteBancario.objects.filter(
        empresa=empresa, tipo='ECheq', estado_cartera='EnCartera',
        echeq_fecha_acreditacion__isnull=False,
        echeq_fecha_acreditacion__lte=hoy,
    ).order_by('pk')
    for valor in electronicos:
        fecha = valor.echeq_fecha_acreditacion
        resultado.append(_datos(
            codigo='FIN-03', grupo='cartera_electronica', objeto=valor,
            numero=valor.echeq_numero, fecha=fecha,
            limite=fecha + timedelta(days=30), hoy=hoy,
            centro_id=valor.centro_operativo_id,
            pendiente=(valor.estado == 'Pendiente'),
        ))

    # Los propios NO forman parte de la cartera de terceros.
    propios = Cheque.objects.filter(
        empresa=empresa, origen='Propio', pago__isnull=False,
        estado='Pendiente', tipo_instrumento__in=('Cheque', 'ECheq'),
        fecha_acreditacion__isnull=False,
        cuenta_bancaria__isnull=False,
    ).select_related('cuenta_bancaria').order_by('pk')
    for valor in propios:
        anticipo = valor.cuenta_bancaria.dias_aviso_cheques_propios
        fecha = valor.fecha_acreditacion
        if hoy < fecha - timedelta(days=anticipo):
            continue
        resultado.append(_datos(
            codigo='FIN-02' if valor.tipo_instrumento == 'Cheque' else 'FIN-03',
            grupo='propio_fisico' if valor.tipo_instrumento == 'Cheque'
                  else 'propio_electronico',
            objeto=valor, numero=valor.numero, fecha=fecha,
            limite=fecha, hoy=hoy, pago_id=valor.pago_id,
        ))
    return resultado


def aviso_autorizado(usuario, empresa, aviso):
    """Aplica acceso de origen POR INSTRUMENTO (también a avisos vencidos).

    Pendiente bancario no resuelto es global a la Empresa autorizada.
    Resuelto se restringe por Centro. Para propios con varios Movimientos,
    admin de Centro sólo ve si TODOS los destinos son de su alcance.
    """
    codigo = aviso['codigo']
    if not permisos_lectura_tipo(usuario, empresa, codigo):
        return False
    grupo = aviso['grupo']
    if grupo == 'cartera_fisica':
        try:
            _, cajas = cajas_autorizadas(usuario, empresa.pk)
            return cajas.filter(pk=aviso['caja_id']).exists()
        except (PermissionDenied, ValueError, TypeError):
            return False
    if grupo == 'cartera_electronica':
        if not permiso_bancario(usuario, empresa.pk, 'pendientes.ver'):
            return False
        try:
            _, centros = alcance_pendientes(usuario, empresa.pk)
        except (PermissionDenied, ValueError, TypeError):
            return False
        if aviso['pendiente_administrativo']:
            return True  # Bandeja pendiente global, incluso con Centro legado.
        return centros is None or aviso['centro_id'] in centros
    if grupo in ('propio_fisico', 'propio_electronico'):
        if not (puede(usuario, empresa.pk, 'registros.ver') and
                puede(usuario, empresa.pk, 'vencimientos.ver')):
            return False
        try:
            contexto = obtener_contexto_capacidades_empresa(usuario, empresa.pk)
        except (PermissionDenied, TypeError, ValueError):
            return False
        if contexto.jerarquia != 'admin_centro':
            return True
        permitidos = centros_activos_de_usuario(usuario, empresa)
        destinos = list(AplicacionPago.objects.filter(
            pago_id=aviso['pago_id'],
        ).values_list('movimiento__centro_operativo_id', flat=True))
        # No divulgar instrumentos que mezclen centros, cuotas o destinos vacíos.
        return bool(destinos) and all(d in permitidos for d in destinos)
    return False


def avisos_visibles(usuario, empresa, hoy=None):
    """Un listado compartido por Alertas y Llamador, sin concesiones implícitas."""
    return [a for a in fuentes_instrumentos(empresa, hoy)
            if aviso_autorizado(usuario, empresa, a)]


def avisos_publicos(usuario, empresa, hoy=None):
    """Salida mínima sin claves internas de permiso para el frontend."""
    claves = ('codigo', 'grupo', 'id', 'numero', 'fecha_acreditacion',
              'fecha_limite', 'estado_alerta')
    return [{k: a[k] for k in claves} for a in avisos_visibles(usuario, empresa, hoy)]
