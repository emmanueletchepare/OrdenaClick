"""API de disposición, estrictamente ligada a la Empresa activa."""
import json
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db.models import Count, Q
from usuarios.models import PendienteBancario
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST
from usuarios.services.salidas_echeq import cartera, confirmar


def _empresa(request):
    empresa_id = request.session.get('gestion_bancaria_empresa')
    if not empresa_id:
        raise PermissionDenied('Ingrese desde una Empresa autorizada.')
    return empresa_id

@login_required
@never_cache
@require_GET
def listar_salidas(request):
    try:
        empresa, valores = cartera(usuario=request.user, empresa_id=_empresa(request))
        estadisticas=PendienteBancario.objects.filter(empresa=empresa,tipo='ECheq').aggregate(
            otros_estados_orden=Count('pk',filter=~Q(estado_cartera='EnCartera') & Q(echeq_condicion='Orden')),
            otros_estados_no_orden=Count('pk',filter=~Q(estado_cartera='EnCartera') & Q(echeq_condicion='NoOrden')),
            en_cartera_sin_clasificar=Count('pk',filter=Q(estado_cartera='EnCartera') & ~Q(echeq_condicion__in=('Orden','NoOrden'))))
        return JsonResponse({'ok':True,'diagnostico':estadisticas,'instrumentos':[{'id':v.pk,'numero':v.echeq_numero,
            'titular':v.echeq_titular,'importe':str(v.importe),'condicion':v.echeq_condicion,
            'acreditacion':v.echeq_fecha_acreditacion.isoformat() if v.echeq_fecha_acreditacion else ''} for v in valores[:1000]]})
    except (PermissionDenied, ValueError, TypeError):
        return JsonResponse({'ok':False,'mensaje':'Sin autorización.'},status=403)

@login_required
@never_cache
@require_POST
def confirmar_salida(request):
    if len(request.body)>30000:
        return JsonResponse({'ok':False,'mensaje':'Carga demasiado extensa.'},status=400)
    try:
        data=json.loads(request.body.decode('utf-8'))
        if not isinstance(data,dict): raise ValueError('Solicitud inválida.')
        operacion, nueva = confirmar(usuario=request.user, empresa_id=_empresa(request), datos=data)
    except (PermissionDenied, TypeError):
        return JsonResponse({'ok':False,'mensaje':'Sin autorización.'},status=403)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return JsonResponse({'ok':False,'mensaje':str(exc)},status=400)
    return JsonResponse({'ok':True,'operacion':operacion.pk,'creada':nueva})


@login_required
@never_cache
@require_GET
def pdf_salida(request, operacion_id):
    from django.http import HttpResponse
    from django.db.models import Prefetch
    from usuarios.models import OperacionSalidaECheq, ItemSalidaECheq
    from usuarios.services.pendientes_bancarios import alcance_pendientes
    from usuarios.services.documentos_pdf import crear_documento
    try:
        empresa, alcance = alcance_pendientes(request.user, _empresa(request))
        if alcance is not None:
            raise PermissionDenied('No autorizado.')
        operacion = (OperacionSalidaECheq.objects.filter(pk=operacion_id,empresa=empresa,tipo='EndosarCeder')
            .select_related('empresa','proveedor','banco_destino','actor','actor__usuario')
            .prefetch_related('items__pendiente').first())
        if operacion is None:
            return JsonResponse({'ok':False,'mensaje':'Operación no encontrada.'},status=404)
        from decimal import Decimal
        def pesos(n):
            v=f'{n:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
            return '$ '+v
        def grupo(accion):
            items=sorted([x for x in operacion.items.all() if x.accion==accion],key=lambda x:(x.pendiente.echeq_fecha_acreditacion or timezone.localdate(),x.pk))
            return sum((v.importe for v in items),Decimal('0.00')),[(i,v.numero,(v.pendiente.echeq_fecha_acreditacion.strftime('%d/%m/%Y') if v.pendiente.echeq_fecha_acreditacion else '—'),pesos(v.importe)) for i,v in enumerate(items,1)]
        from django.utils import timezone
        t1,f1=grupo('Endosado');t2,f2=grupo('Cedido')
        pdf=crear_documento(titulo='Detalle para gestión bancaria',subtitulo='Listado de e-Cheqs · Endoso y cesión',
            empresa=operacion.empresa.razon_social,referencia=f'#{operacion.pk}',fecha=operacion.creado,
            emisor=operacion.actor.usuario.get_username(),
            datos=[('Proveedor',operacion.proveedor.razon_social),('Banco destino',operacion.banco_destino.nombre),('CBU / Destino',operacion.destino)],
            secciones=[('Cheques a endosar',pesos(t1),f1),('Cheques a ceder',pesos(t2),f2)],total=pesos(t1+t2),
            nota='Documento de gestión. No acredita depósito ni recepción bancaria.')
        respuesta=HttpResponse(pdf,content_type='application/pdf')
        respuesta['Content-Disposition']=f'inline; filename="ordenaclick_gestion_bancaria_{operacion.pk}.pdf"'
        respuesta['X-Content-Type-Options']='nosniff'
        return respuesta
    except (PermissionDenied, TypeError, ValueError):
        return JsonResponse({'ok':False,'mensaje':'No autorizado.'},status=403)


@login_required
@never_cache
@require_GET
def pdf_salida(request, operacion_id):
    from django.http import HttpResponse
    from django.db.models import Prefetch
    from usuarios.models import OperacionSalidaECheq, ItemSalidaECheq
    from usuarios.services.pendientes_bancarios import alcance_pendientes
    from usuarios.services.documentos_pdf import crear_documento
    try:
        empresa, alcance = alcance_pendientes(request.user, _empresa(request))
        if alcance is not None:
            raise PermissionDenied('No autorizado.')
        operacion = (OperacionSalidaECheq.objects.filter(pk=operacion_id,empresa=empresa,tipo='EndosarCeder')
            .select_related('empresa','proveedor','banco_destino','actor','actor__usuario')
            .prefetch_related('items__pendiente').first())
        if operacion is None:
            return JsonResponse({'ok':False,'mensaje':'Operación no encontrada.'},status=404)
        from decimal import Decimal
        def pesos(n):
            v=f'{n:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
            return '$ '+v
        def grupo(accion):
            items=sorted([x for x in operacion.items.all() if x.accion==accion],key=lambda x:(x.pendiente.echeq_fecha_acreditacion or timezone.localdate(),x.pk))
            return sum((v.importe for v in items),Decimal('0.00')),[(i,v.numero,(v.pendiente.echeq_fecha_acreditacion.strftime('%d/%m/%Y') if v.pendiente.echeq_fecha_acreditacion else '—'),pesos(v.importe)) for i,v in enumerate(items,1)]
        from django.utils import timezone
        t1,f1=grupo('Endosado');t2,f2=grupo('Cedido')
        pdf=crear_documento(titulo='Detalle para gestión bancaria',subtitulo='Listado de e-Cheqs · Endoso y cesión',
            empresa=operacion.empresa.razon_social,referencia=f'#{operacion.pk}',fecha=operacion.creado,
            emisor=operacion.actor.usuario.get_username(),
            datos=[('Proveedor',operacion.proveedor.razon_social),('Banco destino',operacion.banco_destino.nombre),('CBU / Destino',operacion.destino)],
            secciones=[('Cheques a endosar',pesos(t1),f1),('Cheques a ceder',pesos(t2),f2)],total=pesos(t1+t2),
            nota='Documento de gestión. No acredita depósito ni recepción bancaria.')
        respuesta=HttpResponse(pdf,content_type='application/pdf')
        respuesta['Content-Disposition']=f'inline; filename="ordenaclick_gestion_bancaria_{operacion.pk}.pdf"'
        respuesta['X-Content-Type-Options']='nosniff'
        return respuesta
    except (PermissionDenied, TypeError, ValueError):
        return JsonResponse({'ok':False,'mensaje':'No autorizado.'},status=403)
