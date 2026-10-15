"""Nómina de Empleados por Empresa activa. Sin permisos granulares anticipados."""
from datetime import date
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import content_disposition_header
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET, require_POST

from usuarios.models import (AlertaLicenciaEmpleado, ActuacionCasoEmpleado, Banco,
    CasoEmpleado, CentroOperativo, DocumentoEmpleado, Empleado, RecursoOperativo)
from usuarios.services.identidades import obtener_identidad_usuario_empresa
from usuarios.services.nomina import acceso_nomina, alertas_pendientes, archivo_validado, evento, sincronizar_alerta
from usuarios.services.nomina_forms import EmpleadoForm


def _empresa(request, empresa_id):
    try:
        return acceso_nomina(request.user, empresa_id)
    except (PermissionDenied, ValueError, TypeError):
        raise PermissionDenied('No tenés autorización para Nómina en esta Empresa.')


def _empleado(empresa, empleado_id):
    return get_object_or_404(Empleado.objects.select_related('centro_operativo', 'vehiculo', 'banco'),
                             empresa=empresa, pk=empleado_id)


def _volver(empresa, empleado=None, seccion=None):
    q = f'?empresa={empresa.pk}'
    if empleado:
        q += f'&empleado={empleado.pk}'
    if seccion:
        q += f'&seccion={seccion}'
    return reverse('nomina_empleados') + q


def _documentos(request, empleado, caso=None):
    """Agrega versiones, jamás reemplaza archivos históricos. Sólo luego de validación."""
    actor = obtener_identidad_usuario_empresa(empresa=empleado.empresa, usuario=request.user)
    campos = {
        'dni_frente': 'DNIFrente', 'dni_dorso': 'DNIDorso',
        'licencia_archivo': 'Licencia', 'cat_archivo': 'CAT',
        'preocupacional_archivo': 'Preocupacional', 'caso_archivo': 'Caso',
    }
    documentos = []
    permitidos = ('caso_archivo',) if caso else tuple(k for k in campos if k != 'caso_archivo')
    for campo in permitidos:
        archivo = request.FILES.get(campo)
        if not archivo:
            continue
        ext, digest = archivo_validado(archivo)
        doc = DocumentoEmpleado(
            empleado=empleado, caso=caso if isinstance(caso, CasoEmpleado) else None, tipo=campos[campo],
            nombre_original=Path(archivo.name.replace('\\', '/')).name[:150],
            sha256=digest, actor=actor,
        )
        doc._extension_verificada = ext
        documentos.append((doc, archivo))
    return documentos


def _guardar_documentos(documentos, creados):
    for doc, archivo in documentos:
        doc.archivo.save('privado', archivo, save=False)
        creados.append(doc.archivo.name)
        doc.save()


def _limpiar_documentos(nombres):
    if not nombres:
        return
    campo = DocumentoEmpleado._meta.get_field('archivo')
    for nombre in nombres:
        try:
            campo.storage.delete(nombre)
        except OSError:
            pass


@login_required
@never_cache
@require_GET
@xframe_options_sameorigin
def nomina_empleados(request):
    empresa = _empresa(request, request.GET.get('empresa'))
    empleado_id = request.GET.get('empleado')
    empleado = _empleado(empresa, empleado_id) if empleado_id else None
    nuevo = request.GET.get('nuevo') == '1'
    seccion = request.GET.get('seccion', '')
    if empleado and seccion == 'casos':
        casos = list(empleado.casos.select_related('actor').prefetch_related('actuaciones', 'documentos'))
        return render(request, 'usuarios/nomina/nomina.html', {
            'empresa': empresa, 'vista': 'casos', 'empleado': empleado, 'casos': casos,
            'hoy': timezone.localdate(),
        })
    if empleado or nuevo:
        form = EmpleadoForm(empresa=empresa, instance=empleado)
        docs = empleado.documentos.filter(caso__isnull=True).select_related('actor') if empleado else []
        eventos = empleado.eventos.select_related('actor') if empleado else []
        return render(request, 'usuarios/nomina/nomina.html', {
            'empresa': empresa, 'vista': 'ficha', 'empleado': empleado, 'form': form,
            'documentos': docs, 'eventos': eventos, 'hoy': timezone.localdate(),
        })
    buscar = (request.GET.get('buscar') or '').strip()[:80]
    qs = Empleado.objects.filter(empresa=empresa).select_related('centro_operativo')
    if buscar:
        from django.db.models import Q
        qs = qs.filter(Q(nombre_apellido__icontains=buscar) | Q(cuil__icontains=buscar) | Q(legajo__icontains=buscar))
    centro = request.GET.get('centro', '')
    if centro:
        try:
            centro_id = int(centro)
        except (TypeError, ValueError):
            raise PermissionDenied('Centro inválido.')
        if not CentroOperativo.objects.filter(pk=centro_id, empresa=empresa).exists():
            raise PermissionDenied('Centro no autorizado.')
        qs = qs.filter(centro_operativo_id=centro_id)
    return render(request, 'usuarios/nomina/nomina.html', {
        'empresa': empresa, 'vista': 'listado',
        'activos': qs.filter(activo=True), 'inactivos': qs.filter(activo=False),
        'buscar': buscar, 'centro_filtro': centro,
        'centros': CentroOperativo.objects.filter(empresa=empresa, activo=True),
        'alertas': alertas_pendientes(empresa),
    })


@login_required
@never_cache
@require_POST
@xframe_options_sameorigin
def guardar_empleado(request, empresa_id, empleado_id=None):
    empresa = _empresa(request, empresa_id)
    empleado = _empleado(empresa, empleado_id) if empleado_id else None
    if empleado and not empleado.activo:
        return HttpResponseForbidden('Una ficha desvinculada es histórica; no se modifica.')
    form = EmpleadoForm(request.POST, empresa=empresa, instance=empleado)
    if not form.is_valid():
        return render(request, 'usuarios/nomina/nomina.html', {
            'empresa': empresa, 'vista': 'ficha', 'form': form, 'empleado': empleado,
            'documentos': empleado.documentos.filter(caso__isnull=True) if empleado else [],
            'eventos': empleado.eventos.all() if empleado else [],
            'hoy': timezone.localdate(),
        }, status=400)
    try:
        docs = _documentos(request, empleado or Empleado(empresa=empresa), None)
    except ValidationError as error:
        form.add_error(None, error)
        return render(request, 'usuarios/nomina/nomina.html', {
            'empresa': empresa, 'vista': 'ficha', 'form': form, 'empleado': empleado,
            'documentos': empleado.documentos.filter(caso__isnull=True) if empleado else [],
            'eventos': empleado.eventos.all() if empleado else [],
        }, status=400)
    creados = []
    try:
        with transaction.atomic():
            # Bloqueo por Empresa para evitar altas/ediciones concurrentes.
            type(empresa).objects.select_for_update().get(pk=empresa.pk)
            if empleado:
                bloqueado = Empleado.objects.select_for_update().get(pk=empleado.pk, empresa=empresa, activo=True)
                if bloqueado.modificado != empleado.modificado:
                    raise ValueError('La ficha fue modificada por otra operación. Volvé a cargarla.')
            obj = form.save(commit=False)
            obj.empresa = empresa
            obj.save()
            # Los documentos se prepararon antes de persistir la ficha.
            for doc, archivo in docs:
                doc.empleado = obj
            _guardar_documentos(docs, creados)
            sincronizar_alerta(obj)
            cambios = ', '.join(form.changed_data)[:240]
            evento(obj, request.user, 'Editado' if empleado else 'Registrado', f'Campos: {cambios}' if empleado else 'Alta en Nómina')
            if docs:
                evento(obj, request.user, 'Documentos', f'{len(docs)} archivo(s) incorporado(s)')
    except (ValidationError, IntegrityError, ValueError) as error:
        _limpiar_documentos(creados)
        form.add_error(None, 'No se pudo guardar; revisá los datos o duplicados.')
        return render(request, 'usuarios/nomina/nomina.html', {
            'empresa': empresa, 'vista': 'ficha', 'form': form, 'empleado': empleado,
            'documentos': empleado.documentos.filter(caso__isnull=True) if empleado else [],
            'eventos': empleado.eventos.all() if empleado else [],
        }, status=400)
    except Exception:
        _limpiar_documentos(creados)
        raise
    return redirect(_volver(empresa, obj))


@login_required
@never_cache
@require_POST
def desvincular_empleado(request, empresa_id, empleado_id):
    empresa = _empresa(request, empresa_id)
    motivo = (request.POST.get('motivo') or '').strip()
    if len(motivo) < 8 or len(motivo) > 300:
        return JsonResponse({'ok': False, 'mensaje': 'Ingresá un motivo de 8 a 300 caracteres.'}, status=400)
    try:
        fecha = date.fromisoformat(request.POST.get('fecha', ''))
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'mensaje': 'Fecha inválida.'}, status=400)
    if fecha > timezone.localdate():
        return JsonResponse({'ok': False, 'mensaje': 'La desvinculación no puede ser futura.'}, status=400)
    with transaction.atomic():
        type(empresa).objects.select_for_update().get(pk=empresa.pk)
        empleado = Empleado.objects.select_for_update().filter(pk=empleado_id, empresa=empresa).first()
        if not empleado:
            raise Http404('Empleado inexistente.')
        if not empleado.activo:
            return JsonResponse({'ok': False, 'mensaje': 'El empleado ya está desvinculado.'}, status=409)
        if fecha < empleado.fecha_ingreso:
            return JsonResponse({'ok': False, 'mensaje': 'Fecha anterior al ingreso.'}, status=400)
        empleado.activo = False
        empleado.fecha_desvinculacion = fecha
        empleado.motivo_desvinculacion = motivo
        empleado.save(update_fields=['activo','fecha_desvinculacion','motivo_desvinculacion','modificado'])
        sincronizar_alerta(empleado)
        evento(empleado, request.user, 'Desvinculado', f'{fecha.isoformat()}: {motivo}')
    return redirect(_volver(empresa, empleado))


@login_required
@never_cache
@require_POST
def reconocer_licencia(request, empresa_id, empleado_id):
    empresa = _empresa(request, empresa_id)
    with transaction.atomic():
        type(empresa).objects.select_for_update().get(pk=empresa.pk)
        empleado = Empleado.objects.select_for_update().filter(pk=empleado_id, empresa=empresa, activo=True).first()
        if not empleado:
            raise Http404('Empleado no disponible.')
        alerta = AlertaLicenciaEmpleado.objects.select_for_update().filter(
            empleado=empleado, cancelada_en__isnull=True, reconocida_en__isnull=True,
            fecha_aviso__lte=timezone.localdate(),
        ).first()
        if alerta is None:
            return JsonResponse({'ok': False, 'mensaje': 'No hay aviso activo para reconocer.'}, status=409)
        alerta.reconocida_en = timezone.now()
        alerta.save(update_fields=['reconocida_en','modificado'])
        evento(empleado, request.user, 'AvisoReconocido', 'Licencia de conducir; el vencimiento sigue registrado')
    return redirect(_volver(empresa))


@login_required
@never_cache
@require_POST
def crear_caso(request, empresa_id, empleado_id):
    empresa = _empresa(request, empresa_id)
    empleado = _empleado(empresa, empleado_id)
    categoria = request.POST.get('categoria', '')
    fecha_s = request.POST.get('fecha', '')
    detalle = (request.POST.get('descripcion') or '').strip()
    if categoria not in dict(CasoEmpleado.CATEGORIAS) or not 8 <= len(detalle) <= 3000:
        return JsonResponse({'ok': False, 'mensaje': 'Categoría o descripción inválida.'}, status=400)
    try:
        fecha = date.fromisoformat(fecha_s)
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'mensaje': 'Fecha inválida.'}, status=400)
    try:
        docs = _documentos(request, empleado, caso=True)
    except ValidationError as error:
        return JsonResponse({'ok': False, 'mensaje': str(error)}, status=400)
    creados = []
    try:
        with transaction.atomic():
            type(empresa).objects.select_for_update().get(pk=empresa.pk)
            actor = obtener_identidad_usuario_empresa(empresa=empresa, usuario=request.user)
            caso = CasoEmpleado.objects.create(empleado=empleado, categoria=categoria, fecha=fecha, descripcion=detalle, actor=actor)
            ActuacionCasoEmpleado.objects.create(caso=caso, fecha=fecha, detalle=detalle, actor=actor)
            for doc, archivo in docs:
                doc.caso = caso
            _guardar_documentos(docs, creados)
            evento(empleado, request.user, 'CasoAbierto', f'{categoria} #{caso.pk}')
    except Exception:
        _limpiar_documentos(creados)
        raise
    return redirect(_volver(empresa, empleado, 'casos'))


@login_required
@never_cache
@require_POST
def actuar_caso(request, empresa_id, empleado_id, caso_id):
    empresa = _empresa(request, empresa_id)
    empleado = _empleado(empresa, empleado_id)
    detalle = (request.POST.get('detalle') or '').strip()
    cerrar = request.POST.get('cerrar') == '1'
    if not 8 <= len(detalle) <= 3000:
        return JsonResponse({'ok': False, 'mensaje': 'Ingresá una actuación de 8 a 3000 caracteres.'}, status=400)
    try:
        fecha = date.fromisoformat(request.POST.get('fecha',''))
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'mensaje': 'Fecha inválida.'}, status=400)
    try:
        docs = _documentos(request, empleado, caso=True)
    except ValidationError as error:
        return JsonResponse({'ok': False, 'mensaje': str(error)}, status=400)
    creados = []
    try:
        with transaction.atomic():
            type(empresa).objects.select_for_update().get(pk=empresa.pk)
            caso = CasoEmpleado.objects.select_for_update().filter(empleado=empleado, pk=caso_id).first()
            if not caso:
                raise Http404('Caso inexistente.')
            if caso.estado != 'Abierto':
                return JsonResponse({'ok': False, 'mensaje': 'Este caso está cerrado.'}, status=409)
            actor = obtener_identidad_usuario_empresa(empresa=empresa, usuario=request.user)
            ActuacionCasoEmpleado.objects.create(caso=caso, fecha=fecha, detalle=detalle, actor=actor)
            for doc, archivo in docs:
                doc.caso = caso
            _guardar_documentos(docs, creados)
            if cerrar:
                caso.estado = 'Cerrado'
                caso.save(update_fields=['estado'])
            evento(empleado, request.user, 'CasoCerrado' if cerrar else 'ActuacionCaso', f'Caso #{caso.pk}')
    except Exception:
        _limpiar_documentos(creados)
        raise
    return redirect(_volver(empresa, empleado, 'casos'))


@login_required
@never_cache
@require_GET
def descargar_documento_nomina(request, empresa_id, documento_id):
    empresa = _empresa(request, empresa_id)
    doc = get_object_or_404(DocumentoEmpleado.objects.select_related('empleado'), pk=documento_id, empleado__empresa=empresa)
    try:
        doc.archivo.open('rb')
    except (ValueError, OSError):
        raise Http404('Archivo no disponible.')
    tipos = {'.pdf':'application/pdf', '.jpg':'image/jpeg', '.png':'image/png'}
    ext = Path(doc.archivo.name).suffix.lower()
    respuesta = FileResponse(doc.archivo, content_type=tipos.get(ext,'application/octet-stream'))
    respuesta['Content-Disposition'] = content_disposition_header(True, doc.nombre_original)
    respuesta['X-Content-Type-Options'] = 'nosniff'
    respuesta['Referrer-Policy'] = 'no-referrer'
    respuesta['Cache-Control'] = 'no-store'
    return respuesta


@login_required
@never_cache
@require_GET
def opciones_nomina(request, empresa_id):
    empresa = _empresa(request, empresa_id)
    return JsonResponse({'ok': True,
        'centro_operativo': list(CentroOperativo.objects.filter(empresa=empresa, activo=True).values('id','nombre')),
        'vehiculo': list(RecursoOperativo.objects.filter(empresa=empresa, activo=True, tipo_recurso='Vehiculo').values('id','nombre')),
        'banco': list(Banco.objects.filter(empresa=empresa, activo=True).values('id','nombre')),
    })
