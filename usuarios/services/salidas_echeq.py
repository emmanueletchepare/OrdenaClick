"""Salidas de e-Cheqs: único punto de mutación, alcance general y lote atómico."""
from datetime import timedelta
from uuid import UUID
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from usuarios.models import (Empresa, PendienteBancario, CuentaBancaria, Proveedor, Banco,
                             OperacionSalidaECheq, ItemSalidaECheq)
from usuarios.services.pendientes_bancarios import alcance_pendientes
from usuarios.services.identidades import obtener_identidad_usuario_empresa


def cartera(*, usuario, empresa_id):
    empresa, alcance = alcance_pendientes(usuario, empresa_id)
    if alcance is not None:
        raise PermissionDenied('La disposición de e-Cheqs exige administración general.')
    valores = PendienteBancario.objects.filter(empresa=empresa, tipo='ECheq', estado_cartera='EnCartera').order_by('echeq_fecha_acreditacion', 'pk')
    return empresa, valores


def confirmar(*, usuario, empresa_id, datos):
    empresa, _ = cartera(usuario=usuario, empresa_id=empresa_id)
    try:
        clave = UUID(str(datos.get('clave')))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError('Clave de operación inválida.') from exc
    tipo = datos.get('tipo')
    if tipo not in ('Depositar', 'EndosarCeder'):
        raise ValueError('Operación inválida.')
    ids = datos.get('ids')
    if (not isinstance(ids, list) or not 1 <= len(ids) <= 80
            or any(type(x) is not int or x <= 0 for x in ids) or len(ids) != len(set(ids))):
        raise ValueError('Seleccione entre 1 y 80 e-Cheqs distintos.')
    cuenta_id = datos.get('cuenta') if tipo == 'Depositar' else None
    proveedor_id = datos.get('proveedor') if tipo == 'EndosarCeder' else None
    banco_id = datos.get('banco') if tipo == 'EndosarCeder' else None
    for valor in (cuenta_id, proveedor_id, banco_id):
        if valor is not None and (not isinstance(valor, (str, int)) or not str(valor).isdigit()):
            raise ValueError('Identificador de destino inválido.')
    cuenta_id = int(cuenta_id) if cuenta_id is not None else None
    proveedor_id = int(proveedor_id) if proveedor_id is not None else None
    banco_id = int(banco_id) if banco_id is not None else None
    destino_valor = datos.get('destino')
    if tipo == 'EndosarCeder' and not isinstance(destino_valor, str):
        raise ValueError('Destino inválido.')
    destino = destino_valor.strip() if tipo == 'EndosarCeder' else ''
    # Cuenta / alias / CBU o referencia de destino: nunca truncar silenciosamente.
    if len(destino) > 80:
        raise ValueError('El destino admite hasta 80 caracteres.')
    if tipo == 'Depositar':
        if not CuentaBancaria.objects.filter(pk=cuenta_id, empresa=empresa, activo=True).exists():
            raise ValueError('Seleccione una cuenta propia activa.')
    elif (not Proveedor.objects.filter(pk=proveedor_id, empresa=empresa, activo=True).exists()
          or not Banco.objects.filter(pk=banco_id, empresa=empresa, activo=True).exists()
          or not destino):
        raise ValueError('Seleccione un proveedor, banco y destino válidos.')
    with transaction.atomic():
        # Serializar operaciones de esta Empresa, incluso bajo SQLite.
        Empresa.objects.select_for_update().get(pk=empresa.pk)
        anterior = OperacionSalidaECheq.objects.filter(clave=clave).first()
        if anterior:
            guardados = list(anterior.items.order_by('pendiente_id').values_list('pendiente_id', flat=True))
            if (anterior.empresa_id != empresa.pk or anterior.actor.usuario_id != usuario.pk
                or anterior.tipo != tipo or anterior.cuenta_id != cuenta_id
                or anterior.proveedor_id != proveedor_id or anterior.banco_destino_id != banco_id
                or anterior.destino != destino or guardados != sorted(ids)):
                raise ValueError('La clave ya fue usada en otra operación.')
            return anterior, False
        valores = list(PendienteBancario.objects.select_for_update().filter(empresa=empresa, pk__in=ids, tipo='ECheq'))
        if len(valores) != len(ids) or any(v.estado_cartera != 'EnCartera' for v in valores):
            raise ValueError('Hay e-Cheqs que ya salieron de cartera o no pertenecen a esta Empresa.')
        if any(v.echeq_condicion not in ('Orden', 'NoOrden') for v in valores):
            raise ValueError('Hay e-Cheqs con una condición de circulación no reconocida.')
        hoy = timezone.localdate()
        if tipo == 'Depositar' and any(not v.echeq_fecha_acreditacion or not (v.echeq_fecha_acreditacion <= hoy < v.echeq_fecha_acreditacion + timedelta(days=30)) for v in valores):
            raise ValueError('El depósito requiere e-Cheqs acreditables y no vencidos.')
        actor = obtener_identidad_usuario_empresa(empresa=empresa, usuario=usuario)
        operacion = OperacionSalidaECheq.objects.create(empresa=empresa, clave=clave, tipo=tipo, actor=actor,
            cuenta_id=cuenta_id, proveedor_id=proveedor_id, banco_destino_id=banco_id, destino=destino)
        for v in valores:
            accion = ('Depositado' if tipo == 'Depositar' else ('Endosado' if v.echeq_condicion == 'Orden' else 'Cedido'))
            actualizados = PendienteBancario.objects.filter(pk=v.pk, empresa=empresa, estado_cartera='EnCartera').update(estado_cartera=accion, modificado=timezone.now())
            if actualizados != 1:
                raise ValueError('La cartera cambió antes de confirmar.')
            ItemSalidaECheq.objects.create(operacion=operacion, pendiente=v, accion=accion, importe=v.importe, numero=v.echeq_numero)
    return operacion, True
