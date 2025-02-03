from django.urls import path
from session.consumers import SessionConsumer


websocket_urlpatterns = [
    path('ws/session/<int:session_id>/', SessionConsumer.as_asgi()),
]
