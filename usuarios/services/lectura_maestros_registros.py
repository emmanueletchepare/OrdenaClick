"""Autorizar SOLO lecturas de selectores de Carga Simple, nunca altas de ABM."""
from usuarios.services.accesos_colaborador import exigir_abm, puede
from usuarios.services.alcance_registros import empresa_registros
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa

def exigir_abm_o_registro(usuario,empresa_id,codigo):
    if puede(usuario,empresa_id,codigo):
        return exigir_abm(usuario,empresa_id,codigo)
    empresa_registros(usuario,empresa_id,('registros.ver','registros.crear','registros.editar'))
    return obtener_contexto_capacidades_empresa(usuario,empresa_id)

def limitar_centros(qs,usuario,empresa):
    from usuarios.services.alcances_centros import centros_activos_de_usuario
    c=obtener_contexto_capacidades_empresa(usuario,empresa.pk)
    if c.jerarquia=='admin_centro':
        return qs.filter(pk__in=centros_activos_de_usuario(usuario,empresa))
    return qs

def limitar_recursos(qs,usuario,empresa):
    from usuarios.services.alcances_centros import centros_activos_de_usuario
    c=obtener_contexto_capacidades_empresa(usuario,empresa.pk)
    if c.jerarquia=='admin_centro':
        return qs.filter(relaciones_centros__centro_operativo_id__in=centros_activos_de_usuario(usuario,empresa)).distinct()
    return qs
