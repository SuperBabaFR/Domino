import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

import authentification.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'API_Domino.settings')

# import authentification.routing


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(authentification.routing.websocket_urlpatterns),
})