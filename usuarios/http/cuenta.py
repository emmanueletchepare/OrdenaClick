from django.contrib.auth import logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect, render

from usuarios.models import PerfilUsuario, SolicitudRelacionEmpresa


@login_required
def home(request):
    """Muestra los perfiles de plataforma y avisa relaciones pendientes."""
    solicitudes_pendientes_count = SolicitudRelacionEmpresa.objects.filter(
        usuario_destino=request.user,
        estado=SolicitudRelacionEmpresa.ESTADO_PENDIENTE,
    ).count()

    return render(
        request,
        "usuarios/cuenta/home.html",
        {
            "solicitudes_pendientes_count": solicitudes_pendientes_count,
        },
    )


@login_required
def seleccionar_perfil(request, perfil):
    """Dirige al panel correspondiente al perfil elegido."""
    destinos = {
        "administrador": "panel_admin",
        "colaborador": "panel_colaborador",
        "contable": "panel_contable",
        "legal": "panel_legal",
        "relaciones": "panel_relaciones",
    }

    destino = destinos.get(perfil)

    if destino is None:
        return redirect("home")

    return redirect(destino)


@login_required
def modificar_usuario(request):
    """Permite al usuario actualizar sus datos personales y contraseña."""
    perfil, _ = PerfilUsuario.objects.get_or_create(
        user=request.user,
        defaults={
            "nombre": request.user.first_name or request.user.username,
            "apellido": request.user.last_name or "",
            "estado_acceso": "activo"
        }
    )

    error = None

    if request.method == "POST":
        nombre = (request.POST.get("nombre") or "").strip()
        apellido = (request.POST.get("apellido") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        password_actual = request.POST.get("password_actual") or ""

        if not nombre or not apellido or not email:
            error = "Nombre, apellido y correo electrónico son obligatorios."
        elif User.objects.filter(email__iexact=email).exclude(id=request.user.id).exists():
            error = "Ese correo electrónico ya está registrado."
        else:
            try:
                validate_email(email)
            except ValidationError:
                error = "Ingresá un correo electrónico válido."

        if error is None and password:
            if not password_actual or not request.user.check_password(password_actual):
                error = "La contraseña actual es incorrecta."
            elif request.user.check_password(password):
                error = "La nueva contraseña debe ser distinta de la actual."
            else:
                try:
                    validate_password(password, user=request.user)
                except ValidationError as validacion:
                    error = " ".join(validacion.messages)

        if error is None:
            request.user.first_name = nombre
            request.user.last_name = apellido
            request.user.email = email

            if password:
                request.user.set_password(password)

            request.user.save()

            perfil.nombre = nombre
            perfil.apellido = apellido
            perfil.telefono_personal = (request.POST.get("telefono_personal") or "").strip()
            perfil.telefono_laboral = (request.POST.get("telefono_laboral") or "").strip()
            perfil.direccion_laboral = (request.POST.get("direccion_laboral") or "").strip()
            perfil.save()

            if password:
                update_session_auth_hash(request, request.user)

            return redirect("home")

    return render(
        request,
        "usuarios/cuenta/modificar_usuario.html",
        {
            "perfil": perfil,
            "error": error,
            "valores_formulario": {
                "nombre": (request.POST.get("nombre") or "") if request.method == "POST" else perfil.nombre,
                "apellido": (request.POST.get("apellido") or "") if request.method == "POST" else perfil.apellido,
                "email": (request.POST.get("email") or "") if request.method == "POST" else request.user.email,
                "telefono_personal": (request.POST.get("telefono_personal") or "") if request.method == "POST" else perfil.telefono_personal,
                "telefono_laboral": (request.POST.get("telefono_laboral") or "") if request.method == "POST" else perfil.telefono_laboral,
                "direccion_laboral": (request.POST.get("direccion_laboral") or "") if request.method == "POST" else perfil.direccion_laboral,
            },
        }
    )


@login_required
def baja_usuario(request):
    """Desactiva la cuenta sin eliminar físicamente su historial."""
    if request.method != "POST":
        return redirect("home")

    perfil, _ = PerfilUsuario.objects.get_or_create(
        user=request.user,
        defaults={
            "nombre": request.user.first_name or request.user.username,
            "apellido": request.user.last_name or ""
        }
    )

    perfil.estado_acceso = "bloqueado"
    perfil.save(update_fields=["estado_acceso", "actualizado"])

    request.user.is_active = False
    request.user.save(update_fields=["is_active"])

    logout(request)
    return redirect("login")
