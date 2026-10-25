from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied

from usuarios.services.financiero import (
    estado_vencimiento_movimiento,
    movimientos_con_saldo_pendiente,
    movimientos_en_alerta,
)
from usuarios.services.seguridad import obtener_empresa_autorizada, obtener_empresa_administrable
from usuarios.services.nomina import alertas_pendientes
from usuarios.services.alertas_instrumentos import avisos_visibles, avisos_publicos
from usuarios.services.destinatarios_alertas import suscripto_efectivo, sonido_habilitado
from usuarios.models import Movimiento
from usuarios.services.accesos_colaborador import exigir, puede
from usuarios.services.alcances_centros import centros_activos_de_usuario
from usuarios.services.capacidades import obtener_contexto_capacidades_empresa
from usuarios.services.alcance_nomina import restringir_nomina


@login_required
def estado_llamador_alertas(request):
    """
    Indica si corresponde mostrar el llamador de Alertas
    para la empresa activa.

    La vista no expone movimientos, importes ni cantidades.
    La política de Alertas se obtiene exclusivamente desde
    el servicio financiero central.
    """
    empresa_id = (
        request.GET.get("empresa")
        or ""
    ).strip()

    if not empresa_id:
        return JsonResponse(
            {
                "ok": False,
                "mostrar_llamador": False,
                "mensaje": "No hay una empresa seleccionada.",
            },
            status=400,
        )

    empresa = exigir(request.user, empresa_id, 'alertas.ver')
    contexto = obtener_contexto_capacidades_empresa(request.user, empresa.pk)
    centros_permitidos = (centros_activos_de_usuario(request.user,empresa)
                          if contexto.jerarquia == 'admin_centro' else None)

    mostrar_llamador = False
    if suscripto_efectivo(request.user, empresa, 'FIN-01'):
        movimientos = movimientos_en_alerta(empresa=empresa,fecha_referencia=date.today())
        if centros_permitidos is not None:
            movimientos = movimientos.filter(centro_operativo_id__in=centros_permitidos)
        mostrar_llamador = movimientos.exists()

    # Las licencias sólo pueden activar el llamador para perfiles con permiso
    # real de Nómina; no filtrar su existencia a otros usuarios.
    if not mostrar_llamador and suscripto_efectivo(request.user, empresa, 'NOM-01'):
        try:
            alertas = restringir_nomina(alertas_pendientes(empresa,date.today()),request.user,
                                       empresa.pk,'empleado__centro_operativo_id')
            mostrar_llamador = alertas.exists()
        except PermissionDenied:
            pass

    if not mostrar_llamador:
        # El llamador usa los mismos permisos y fechas del listado.
        mostrar_llamador = any(
            suscripto_efectivo(request.user, empresa, codigo)
            for codigo in {a['codigo'] for a in avisos_visibles(request.user, empresa)}
        )

    return JsonResponse(
        {
            "ok": True,
            "mostrar_llamador": mostrar_llamador,
            "sonido_habilitado": bool(mostrar_llamador and sonido_habilitado(request.user, empresa)),
        }
    )

@login_required
def listar_proximos_vencimientos(request):
    """Consultar únicamente períodos económicos. Nunca devolver Alertas por esta ruta."""
    return _listar_vencimientos_o_alertas(request, vista_alertas=False)


@login_required
def listar_alertas(request):
    """Listar fuentes de Alertas visibles, sin ampliar permisos de origen."""
    return _listar_vencimientos_o_alertas(request, vista_alertas=True)


def _listar_vencimientos_o_alertas(request, *, vista_alertas):
    """Motor de presentación común; autorizaciones independientes por módulo."""
    empresa_id = (
        request.GET.get("empresa")
        or ""
    ).strip()

    periodo = ('alertas' if vista_alertas else
               (request.GET.get('periodo') or 'hoy').strip())

    if not empresa_id:
        return JsonResponse(
            {
                "ok": False,
                "mensaje": "No hay una empresa seleccionada.",
            },
            status=400,
        )

    empresa = exigir(request.user, empresa_id, 'alertas.ver' if vista_alertas else 'vencimientos.ver')
    if not vista_alertas and periodo == 'alertas':
        return JsonResponse({'ok': False, 'mensaje': 'Utilizá el módulo Alertas.'}, status=400)
    contexto = obtener_contexto_capacidades_empresa(request.user, empresa.pk)
    centros_permitidos = (centros_activos_de_usuario(request.user,empresa)
                          if contexto.jerarquia == 'admin_centro' else None)

    hoy = date.today()

    fecha_desde = None
    fecha_hasta = None

    if periodo == "alertas":
        if puede(request.user, empresa.pk, 'vencimientos.ver'):
            movimientos = (
                movimientos_en_alerta(
                    empresa=empresa,
                    fecha_referencia=hoy,
                )
                .select_related(
                    "proveedor", "tipo_gasto", "centro_operativo",
                    "recurso_operativo", "cuenta_debito",
                )
            )
        else:
            movimientos = Movimiento.objects.none()

    elif periodo == "hoy":
        fecha_hasta = hoy

        movimientos = (
            movimientos_con_saldo_pendiente(
                empresa=empresa,
                fecha_hasta=fecha_hasta,
            )
            .select_related(
                "proveedor",
                "tipo_gasto",
                "centro_operativo",
                "recurso_operativo",
                "cuenta_debito",
            )
        )

    elif periodo == "semana":
        fecha_hasta = hoy + timedelta(
            days=6,
        )

        movimientos = (
            movimientos_con_saldo_pendiente(
                empresa=empresa,
                fecha_hasta=fecha_hasta,
            )
            .select_related(
                "proveedor",
                "tipo_gasto",
                "centro_operativo",
                "recurso_operativo",
                "cuenta_debito",
            )
        )

    elif periodo == "rango":
        fecha_desde_texto = (
            request.GET.get("fecha_desde")
            or ""
        ).strip()

        fecha_hasta_texto = (
            request.GET.get("fecha_hasta")
            or ""
        ).strip()

        if (
            not fecha_desde_texto
            or not fecha_hasta_texto
        ):
            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "Ingrese las fechas desde y hasta."
                    ),
                },
                status=400,
            )

        try:
            fecha_desde = date.fromisoformat(
                fecha_desde_texto
            )

            fecha_hasta = date.fromisoformat(
                fecha_hasta_texto
            )

        except ValueError:
            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "El rango de fechas no es válido."
                    ),
                },
                status=400,
            )

        if fecha_hasta < fecha_desde:
            return JsonResponse(
                {
                    "ok": False,
                    "mensaje": (
                        "La fecha hasta no puede ser "
                        "anterior a la fecha desde."
                    ),
                },
                status=400,
            )

        movimientos = (
            movimientos_con_saldo_pendiente(
                empresa=empresa,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
            )
            .select_related(
                "proveedor",
                "tipo_gasto",
                "centro_operativo",
                "recurso_operativo",
                "cuenta_debito",
            )
        )

    else:
        return JsonResponse(
            {
                "ok": False,
                "mensaje": "El período solicitado no es válido.",
            },
            status=400,
        )

    if centros_permitidos is not None:
        movimientos = movimientos.filter(centro_operativo_id__in=centros_permitidos)
    datos = []

    for movimiento in movimientos:
        proveedor = ""

        if movimiento.proveedor:
            proveedor = (
                movimiento.proveedor.razon_social
            )

        datos.append(
            {
                "id": movimiento.id,
                "fecha_vencimiento": (
                    movimiento.fecha_vencimiento.isoformat()
                    if movimiento.fecha_vencimiento
                    else None
                ),
                "estado_vencimiento": (
                    estado_vencimiento_movimiento(
                        movimiento
                    )
                ),
                "proveedor": proveedor,
                "tipo_comprobante": (
                    movimiento.tipo_comprobante
                    or ""
                ),
                "numero_comprobante": (
                    movimiento.numero_comprobante
                    or ""
                ),
                "total": str(
                    movimiento.total
                ),
                "total_aplicado": str(
                    movimiento.total_aplicado_calculado
                ),
                "saldo_pendiente": str(
                    movimiento.saldo_pendiente_calculado
                ),
                "modalidad_pago": (
                    movimiento.modalidad_pago
                ),
                "cuenta_debito": (
                    str(movimiento.cuenta_debito)
                    if movimiento.cuenta_debito
                    else ""
                ),
            }
        )

    alertas_instrumentos = (avisos_publicos(request.user, empresa)
                           if periodo == 'alertas' else [])
    licencias_nomina = []
    if periodo == 'alertas':
        try:
            alertas = restringir_nomina(alertas_pendientes(empresa,hoy),request.user,
                                       empresa.pk,'empleado__centro_operativo_id')
            licencias_nomina = [
                {'empleado_id': a.empleado_id, 'nombre': a.empleado.nombre_apellido,
                 'vence': a.fecha_vencimiento.isoformat()}
                for a in alertas
            ]
        except PermissionDenied:
            pass

    return JsonResponse(
        {
            "ok": True,
            "licencias_nomina": licencias_nomina,
            "alertas_instrumentos": alertas_instrumentos,
            "periodo": periodo,
            "fecha_desde": (
                fecha_desde.isoformat()
                if fecha_desde
                else None
            ),
            "fecha_hasta": (
                fecha_hasta.isoformat()
                if fecha_hasta
                else None
            ),
            "movimientos": datos,
        }
    )
