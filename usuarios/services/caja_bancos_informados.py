"""Disponibilidad bancaria informada: lecturas restringidas y actualizaciones auditadas.

Nunca calcula saldo contable desde Pendientes bancarios ni modifica instrumentos.
"""
import re
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import OuterRef, Subquery
from django.utils import timezone

from usuarios.models import CuentaBancaria, Empresa, SaldoInformadoCuentaBancaria
from usuarios.services.accesos_colaborador import puede
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.identidades import obtener_identidad_usuario_empresa


def puede_ver_bancos(usuario, empresa_id):
    """Sólo administración general, o admin de Centro con accesos explícitos.

    'caja.bancos_actualizar' se concede por separado en Gestión de Accesos.
    No depende de 'abm.cuentas', ni concede acceso a Caja por sí solo.
    """
    try:
        c = obtener_contexto_capacidades_empresa(usuario, empresa_id)
    except (PermissionDenied, TypeError, ValueError):
        return False
    if c.es_superusuario or c.es_propietario or c.jerarquia == 'admin_general':
        return True
    return (c.jerarquia == 'admin_centro' and puede(usuario, empresa_id, 'caja.total')
            and puede(usuario, empresa_id, 'caja.bancos_actualizar'))


def exigir_bancos(usuario, empresa_id):
    """Deniega acceso fuera de la Empresa y al resto de perfiles."""
    if not puede_ver_bancos(usuario, empresa_id):
        raise PermissionDenied('No tiene acceso a disponibilidades bancarias informadas.')
    return obtener_contexto_capacidades_empresa(usuario, empresa_id).empresa


def resumen_bancos(empresa):
    """Lee exclusivamente el último importe informado de cada cuenta activa.

    Las cuentas sin declaración se distinguen de saldo cero; las monedas nunca
    se suman entre sí ni se agregan datos de otra Empresa.
    """
    ultima_id = (SaldoInformadoCuentaBancaria.objects
        .filter(empresa=empresa, cuenta_bancaria_id=OuterRef('pk'))
        .order_by('-creado', '-pk').values('pk')[:1])
    cuentas = list(CuentaBancaria.objects.filter(empresa=empresa, activo=True)
                   .select_related('banco').annotate(ultima_posicion_id=Subquery(ultima_id))
                   .order_by('banco__nombre', 'nombre', 'pk'))
    ids = [c.ultima_posicion_id for c in cuentas if c.ultima_posicion_id]
    ultimos = {p.pk: p for p in SaldoInformadoCuentaBancaria.objects
               .filter(pk__in=ids, empresa=empresa).select_related('creado_por__usuario')}
    filas = []
    totales = {'ARS': Decimal('0.00'), 'USD': Decimal('0.00')}
    informadas = {'ARS': 0, 'USD': 0}
    for cuenta in cuentas:
        posicion = ultimos.get(cuenta.ultima_posicion_id)
        vigente = bool(cuenta.descubierto_importe is not None
            and cuenta.descubierto_importe > 0
            and cuenta.descubierto_vencimiento is not None
            and cuenta.descubierto_vencimiento >= timezone.localdate())
        filas.append({'cuenta': cuenta, 'posicion': posicion,
                      'descubierto_vigente': vigente})
        if posicion is not None:
            totales[cuenta.moneda] += posicion.importe
            informadas[cuenta.moneda] += 1
    return {'filas': filas, 'totales': totales, 'informadas': informadas,
            'faltantes': sum(f['posicion'] is None for f in filas),
            'cantidad': len(filas)}


def _importe_declarado(valor):
    """Acepta pesos de formulario en formato AR/decimal sin redondear importes."""
    if not isinstance(valor, str) or len(valor) > 32:
        raise ValueError('Ingrese un importe bancario válido.')
    s = valor.strip()
    if re.fullmatch(r'-?\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?', s):
        s = s.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'-?\d{1,12}(?:[.,]\d{1,2})?', s):
        s = s.replace(',', '.')
    else:
        raise ValueError('Importe inválido; utilice hasta dos decimales.')
    try:
        n = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError('Importe bancario inválido.') from exc
    if not n.is_finite() or abs(n) >= Decimal('1000000000000'):
        raise ValueError('El importe excede el límite permitido.')
    return n


def guardar_posiciones(*, usuario, empresa_id, clave, filas):
    """Registra un lote atómico e idempotente de disponibilidades informadas.

    No cambia saldo de Caja, cartera electrónica ni gestión bancaria.
    """
    empresa = exigir_bancos(usuario, empresa_id)
    try:
        clave = UUID(str(clave))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError('Identificador de actualización inválido.') from exc
    if not isinstance(filas, list) or not 1 <= len(filas) <= 100:
        raise ValueError('Indique entre 1 y 100 cuentas bancarias.')
    ids = []
    valores = {}
    for fila in filas:
        if not isinstance(fila, dict) or type(fila.get('cuenta_id')) is not int or fila['cuenta_id'] <= 0:
            raise ValueError('Cuenta bancaria inválida.')
        ident = fila['cuenta_id']
        if ident in valores:
            raise ValueError('Una cuenta aparece dos veces en la actualización.')
        valores[ident] = _importe_declarado(fila.get('importe'))
        ids.append(ident)
    with transaction.atomic():
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        cuentas = CuentaBancaria.objects.select_for_update().filter(empresa=empresa, activo=True, pk__in=ids)
        if cuentas.count() != len(ids):
            raise PermissionDenied('Hay cuentas inactivas o ajenas a la Empresa.')
        actor = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        existentes = list(SaldoInformadoCuentaBancaria.objects.filter(empresa=empresa, clave=clave))
        if existentes:
            if (len(existentes) != len(ids) or any(
                p.cuenta_bancaria_id not in valores or p.importe != valores[p.cuenta_bancaria_id]
                or p.creado_por_id != actor.pk for p in existentes)):
                raise ValueError('Esta identificación ya se usó para otros importes.')
            return False
        # Evita que otra Empresa reutilice una clave conocida como si fuese propia.
        if SaldoInformadoCuentaBancaria.objects.filter(clave=clave).exclude(empresa=empresa).exists():
            raise ValueError('La identificación pertenece a otra Empresa.')
        SaldoInformadoCuentaBancaria.objects.bulk_create([
            SaldoInformadoCuentaBancaria(empresa=empresa, cuenta_bancaria_id=pk,
                importe=valores[pk], creado_por=actor, clave=clave) for pk in ids
        ])
    return True
