from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect, render

from usuarios.models import PerfilUsuario
from usuarios.services.limite_login import bloqueado, registrar_fallo, limpiar_exito


def login_view(request):
    """Autentica al usuario y lo dirige a la selección de perfil."""
    if request.user.is_authenticated:
        return redirect("home")

    error = None

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        if bloqueado(request):
            return render(request, "usuarios/auth/login.html", {"error": "Demasiados intentos de acceso. Intentá nuevamente en unos minutos."})

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is None:
            registrar_fallo(request)
            error = "Usuario o contraseña incorrectos."
        else:
            perfil, _ = PerfilUsuario.objects.get_or_create(
                user=user,
                defaults={
                    "nombre": user.first_name or user.username,
                    "apellido": user.last_name or "",
                    "estado_acceso": "activo"
                }
            )

            if perfil.estado_acceso == "bloqueado":
                error = "Tu acceso a OrdenaClick se encuentra bloqueado."
            elif perfil.estado_acceso == "pendiente":
                error = "Tu cuenta está pendiente de habilitación."
            else:
                login(request, user)
                limpiar_exito(request)
                return redirect("home")

    return render(
        request,
        "usuarios/auth/login.html",
        {"error": error}
    )


def registro_view(request):
    """Crea la cuenta de usuario y su perfil inicial de OrdenaClick."""
    if request.user.is_authenticated:
        return redirect("home")

    error = None

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        password2 = request.POST.get("password2") or ""
        nombre = (request.POST.get("nombre") or "").strip()
        apellido = (request.POST.get("apellido") or "").strip()

        if not username or not email or not password or not nombre or not apellido:
            error = "Completá todos los campos obligatorios."
        elif password != password2:
            error = "Las contraseñas no coinciden."
        elif User.objects.filter(username__iexact=username).exists():
            error = "Ese nombre de usuario ya está registrado."
        elif User.objects.filter(email__iexact=email).exists():
            error = "Ese correo electrónico ya está registrado."
        else:
            try:
                validate_email(email)
            except ValidationError:
                error = "Ingresá un correo electrónico válido."

        if error is None:
            candidato = User(
                username=username,
                email=email,
                first_name=nombre,
                last_name=apellido,
            )
            try:
                validate_password(password, user=candidato)
            except ValidationError as validacion:
                error = " ".join(validacion.messages)

        if error is None:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido
            )

            PerfilUsuario.objects.create(
                user=user,
                nombre=nombre,
                apellido=apellido,
                telefono_personal=(request.POST.get("telefono_personal") or "").strip(),
                telefono_laboral=(request.POST.get("telefono_laboral") or "").strip(),
                direccion_laboral=(request.POST.get("direccion_laboral") or "").strip(),
                estado_acceso="demo"
            )

            return redirect("login")

    return render(
        request,
        "usuarios/auth/register.html",
        {"error": error}
    )


@login_required
def logout_view(request):
    """Cierra la sesión actual y vuelve al login."""
    logout(request)
    return redirect("login")
