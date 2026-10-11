"""Recuperación de contraseña: enlaces de un solo uso sin enumerar cuentas.

Utiliza las vistas y tokens oficiales de Django. Los envíos se limitan por
origen con un contador distinto del login y nunca se registran emails/tokens.
"""
import logging

from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetView
from django.shortcuts import redirect
from django.urls import reverse_lazy

from usuarios.services.limite_login import bloqueado, registrar_fallo


audit = logging.getLogger("ordenaclick.audit")


class SolicitarRecuperacion(PasswordResetView):
    """Gestiona solicitudes con respuesta indistinguible para emails desconocidos."""

    template_name = "usuarios/auth/recuperacion.html"
    email_template_name = "usuarios/auth/recuperacion_correo.txt"
    subject_template_name = "usuarios/auth/recuperacion_asunto.txt"
    success_url = reverse_lazy("recuperar_contrasena_enviada")

    def post(self, request, *args, **kwargs):
        """Limita envíos por origen, sin bloquear intentos normales de login."""
        if bloqueado(request, contexto="recuperacion"):
            audit.warning("auth.password_reset_rate_limited")
            return redirect(self.success_url)
        registrar_fallo(request, contexto="recuperacion")
        audit.info("auth.password_reset_requested")
        return super().post(request, *args, **kwargs)


class ConfirmarRecuperacion(PasswordResetConfirmView):
    """Confirma un token temporal y audita el cambio, sin guardar secretos."""

    template_name = "usuarios/auth/recuperacion_confirmar.html"
    success_url = reverse_lazy("recuperar_contrasena_completada")

    def form_valid(self, form):
        """Registra solo el identificador interno después del cambio exitoso."""
        respuesta = super().form_valid(form)
        audit.info("auth.password_reset_completed user_id=%s", self.user.pk)
        return respuesta
