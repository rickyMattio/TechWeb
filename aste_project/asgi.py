"""
ASGI config for aste_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""


import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import aste.routing

# Imposta la variabile d'ambiente PRIMA di fare qualsiasi altro import di Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aste_project.settings')

# Importa l'applicazione HTTP standard di Django DOPO aver impostato la variabile d'ambiente
django_asgi_app = get_asgi_application()

# Importa i componenti di Channels


# Definisci l'applicazione principale che il server ASGI eseguirà
application = ProtocolTypeRouter({
    # Se la connessione è di tipo HTTP, usa la vista standard di Django
    "http": django_asgi_app,

    # Se la connessione è di tipo WebSocket, gestiscila con la nostra logica
    "websocket": AuthMiddlewareStack(
        URLRouter(
            aste.routing.websocket_urlpatterns
        )
    ),
})