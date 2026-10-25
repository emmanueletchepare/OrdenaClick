"""Destinatarios de avisos: una asignación NUNCA sustituye permisos de origen.

La lectura del módulo Alertas sigue regida por alertas.ver + permiso de fuente.
Este servicio determina únicamente el envío del llamador/sonido.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q

from usuarios.models import (AsignacionUsuarioEmpresa, DestinatarioAlerta,
                             EventoConfiguracionAlerta, PreferenciaSonidoAlerta,
                             RolFuncionalUsuarioEmpresa)
from usuarios.services.accesos_colaborador import exigir_administrar_permisos, puede
from usuarios.services.alcance_nomina import alcance_nomina
from usuarios.services.alcances_centros import centros_activos_de_usuario
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.catalogo_alertas import CODIGOS_OPERATIVOS, tipo_operativo


def miembros_empresa(empresa):
    """Usuarios activos con vínculo vigente; no incluye permisos de otra Empresa."""
    asignaciones = AsignacionUsuarioEmpresa.objects.filter(empresa=empresa, activo=True).values_list('usuario_id', flat=True)
    funcionales = RolFuncionalUsuarioEmpresa.objects.filter(empresa=empresa, activo=True).values_list('usuario_id', flat=True)
    ids = set(asignaciones) | set(funcionales) | {empresa.propietario_id}
    return list(get_user_model().objects.filter(pk__in=ids, is_active=True).order_by('username', 'pk'))


def alcance_fuente(usuario, empresa, codigo):
    """None significa todos los Centros, frozenset limita; denegado devuelve False."""
    tipo_operativo(codigo)
    if not usuario.is_active or not puede(usuario, empresa.pk, 'alertas.ver'):
        return False, frozenset()
    if codigo == 'FIN-01':
        if not puede(usuario, empresa.pk, 'vencimientos.ver'):
            return False, frozenset()
        contexto = obtener_contexto_capacidades_empresa(usuario, empresa.pk)
        centros = (frozenset(centros_activos_de_usuario(usuario, empresa))
                   if contexto.jerarquia == 'admin_centro' else None)
        if centros is not None and not centros:
            return False, frozenset()
        return True, centros
    if codigo == 'NOM-01':
        try:
            _, centros = alcance_nomina(usuario, empresa.pk)
            return True, centros
        except PermissionDenied:
            return False, frozenset()
    return False, frozenset()


def receptores_efectivos(empresa, codigo):
    """Lista de (usuario, centros o None) válida AHORA, con revocaciones aplicadas."""
    tipo_operativo(codigo)
    miembros = {u.pk: u for u in miembros_empresa(empresa)}
    asignados = DestinatarioAlerta.objects.filter(empresa=empresa, codigo=codigo, activo=True)
    resultado = []
    for usuario_id in asignados.values_list('usuario_id', flat=True):
        usuario = miembros.get(usuario_id)
        if usuario is not None:
            permitido, centros = alcance_fuente(usuario, empresa, codigo)
            if permitido:
                resultado.append((usuario, centros))
    return resultado


def suscripto_efectivo(usuario, empresa, codigo):
    """Revocación inmediata por asignación, permiso, vínculo y Centro."""
    tipo_operativo(codigo)
    if not any(u.pk == usuario.pk for u in miembros_empresa(empresa)):
        return False
    if not DestinatarioAlerta.objects.filter(empresa=empresa, usuario=usuario,
                                             codigo=codigo, activo=True).exists():
        return False
    return alcance_fuente(usuario, empresa, codigo)[0]


def sonido_habilitado(usuario, empresa):
    valor = PreferenciaSonidoAlerta.objects.filter(empresa=empresa, usuario=usuario).values_list('habilitado', flat=True).first()
    return True if valor is None else bool(valor)


def cubre_centro(receptores, centro_id):
    return any(centros is None or centro_id in centros for _, centros in receptores)


def alertas_sin_destinatarios(empresa):
    """Sólo el administrador puede consultar esto. No crea ni modifica alertas."""
    from datetime import date
    from usuarios.services.financiero import movimientos_en_alerta
    from usuarios.services.nomina import alertas_pendientes
    receptores = {c: receptores_efectivos(empresa, c) for c in CODIGOS_OPERATIVOS}
    filas = []
    movimientos = movimientos_en_alerta(empresa, date.today()).values_list('centro_operativo_id', flat=True)
    nomina = alertas_pendientes(empresa, date.today()).values_list('empleado__centro_operativo_id', flat=True)
    fuentes = {'FIN-01': movimientos, 'NOM-01': nomina}
    for codigo in ('FIN-01', 'NOM-01'):
        rec = receptores[codigo]
        cantidad = sum(1 for centro in fuentes[codigo] if not cubre_centro(rec, centro))
        if not rec or cantidad:
            filas.append({'codigo': codigo, 'sin_receptores': not bool(rec),
                          'ocurrencias_sin_receptor': cantidad})
    return filas


@transaction.atomic
def guardar_destinatarios(*, administrador, empresa_id, codigos_usuario, sonidos_usuario):
    """POST completo, atómico, con auditoría. No modifica autorizaciones de origen."""
    empresa = exigir_administrar_permisos(administrador, empresa_id)
    # Serializa concurrencia sin introducir locks en Caja ni finanzas.
    type(empresa).objects.select_for_update().get(pk=empresa.pk)
    usuarios = {u.pk: u for u in miembros_empresa(empresa)}
    seleccionados = set()
    for entrada in codigos_usuario:
        if ':' not in entrada:
            raise ValueError('Asignación inválida.')
        codigo, usuario_texto = entrada.split(':', 1)
        tipo_operativo(codigo)
        if not usuario_texto.isascii() or not usuario_texto.isdecimal():
            raise ValueError('Destinatario inválido.')
        usuario_id = int(usuario_texto)
        usuario = usuarios.get(usuario_id)
        if usuario is None or not alcance_fuente(usuario, empresa, codigo)[0]:
            raise PermissionDenied('El destinatario no posee permiso de origen y alcance activo.')
        seleccionados.add((codigo, usuario_id))
    sonidos = set()
    for entrada in sonidos_usuario:
        if not entrada.isascii() or not entrada.isdecimal():
            raise ValueError('Usuario de sonido inválido.')
        usuario_id = int(entrada)
        if usuario_id not in usuarios:
            raise PermissionDenied('Usuario ajeno a la Empresa.')
        sonidos.add(usuario_id)
    previos = {(d.codigo, d.usuario_id): d for d in DestinatarioAlerta.objects.select_for_update().filter(empresa=empresa)}
    # Incluye filas históricas para impedir reactivar avisos tras desvincular y revincular.
    for clave in sorted(set(previos) | seleccionados):
        antes_obj = previos.get(clave)
        antes = bool(antes_obj and antes_obj.activo)
        despues = clave in seleccionados
        if antes == despues:
            continue
        codigo, usuario_id = clave
        if antes_obj:
            antes_obj.activo = despues
            antes_obj.configurado_por = administrador
            antes_obj.save(update_fields=['activo', 'configurado_por', 'modificado'])
        else:
            DestinatarioAlerta.objects.create(empresa=empresa, usuario_id=usuario_id,
                codigo=codigo, activo=True, configurado_por=administrador)
        EventoConfiguracionAlerta.objects.create(empresa=empresa, usuario_id=usuario_id,
            actor=administrador, codigo=codigo, activo=despues)
    preferencias = {p.usuario_id: p for p in PreferenciaSonidoAlerta.objects.select_for_update().filter(empresa=empresa)}
    for usuario_id in usuarios:
        anterior = preferencias.get(usuario_id)
        antes = True if anterior is None else anterior.habilitado
        despues = usuario_id in sonidos
        if antes == despues:
            continue
        if anterior:
            anterior.habilitado = despues
            anterior.save(update_fields=['habilitado', 'modificado'])
        else:
            PreferenciaSonidoAlerta.objects.create(empresa=empresa, usuario_id=usuario_id, habilitado=despues)
        EventoConfiguracionAlerta.objects.create(empresa=empresa, usuario_id=usuario_id,
            actor=administrador, codigo='SONIDO', activo=despues)


@transaction.atomic
def guardar_destinatarios_usuario(*, administrador, empresa_id, usuario_id, codigos):
    """Edita SOLO el destinatario seleccionado; nunca desmarca a otros usuarios."""
    empresa = exigir_administrar_permisos(administrador, empresa_id)
    type(empresa).objects.select_for_update().get(pk=empresa.pk)
    if isinstance(usuario_id, bool) or not isinstance(usuario_id, int):
        raise ValueError('Usuario inválido.')
    usuario = next((u for u in miembros_empresa(empresa) if u.pk == usuario_id), None)
    if usuario is None:
        raise PermissionDenied('Usuario ajeno a la Empresa.')
    if not isinstance(codigos, (list, tuple, set)) or len(codigos) > len(CODIGOS_OPERATIVOS):
        raise ValueError('Selección inválida.')
    nuevos = set(codigos)
    for codigo in nuevos:
        tipo_operativo(codigo)  # Impide activar ideas futuras o códigos extraños.
        if not alcance_fuente(usuario, empresa, codigo)[0]:
            raise PermissionDenied('La fuente no está autorizada para el usuario.')
    previos = {d.codigo: d for d in DestinatarioAlerta.objects.select_for_update().filter(
        empresa=empresa, usuario_id=usuario_id)}
    for codigo in sorted(set(previos) | nuevos):
        anterior = previos.get(codigo)
        antes = bool(anterior and anterior.activo)
        despues = codigo in nuevos
        if antes == despues:
            continue
        if anterior:
            anterior.activo = despues
            anterior.configurado_por = administrador
            anterior.save(update_fields=['activo', 'configurado_por', 'modificado'])
        else:
            DestinatarioAlerta.objects.create(empresa=empresa, usuario=usuario,
                codigo=codigo, activo=True, configurado_por=administrador)
        EventoConfiguracionAlerta.objects.create(empresa=empresa, usuario=usuario,
            actor=administrador, codigo=codigo, activo=despues)
    return nuevos


@transaction.atomic
def guardar_sonido_propio(*, usuario, empresa_id, habilitado):
    """Sólo el usuario autenticado controla su sonido; audita cambios efectivos."""
    if not isinstance(habilitado, bool):
        raise ValueError('Preferencia inválida.')
    from usuarios.services.accesos_colaborador import exigir
    empresa = exigir(usuario, empresa_id, 'alertas.ver')
    if not any(u.pk == usuario.pk for u in miembros_empresa(empresa)):
        raise PermissionDenied('Vínculo inactivo.')
    type(empresa).objects.select_for_update().get(pk=empresa.pk)
    previa = PreferenciaSonidoAlerta.objects.select_for_update().filter(
        empresa=empresa, usuario=usuario).first()
    antes = True if previa is None else previa.habilitado
    if antes == habilitado:
        return habilitado
    if previa:
        previa.habilitado = habilitado
        previa.save(update_fields=['habilitado', 'modificado'])
    else:
        PreferenciaSonidoAlerta.objects.create(empresa=empresa, usuario=usuario,
                                                habilitado=habilitado)
    EventoConfiguracionAlerta.objects.create(empresa=empresa, usuario=usuario,
        actor=usuario, codigo='SONIDO', activo=habilitado)
    return habilitado
