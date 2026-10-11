from django.urls import include, path

# El contenido empresarial no se sirve nunca como directorio /media/.
# Descargas autorizadas: endpoints de usuarios y Backup Empresa v1.
urlpatterns = [
    path("", include("usuarios.urls")),
]
