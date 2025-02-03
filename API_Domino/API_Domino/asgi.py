import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from session.routing import websocket_urlpatterns as session_websockets
from middleware import JWTAuthMiddleware  # Middleware personnalisé

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'API_Domino.settings')


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
    URLRouter(
        session_websockets
    )
),
})