import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # ← must be FIRST

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from apps.users.routing import websocket_urlpatterns  # ← now safe to import

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(
        websocket_urlpatterns
    ),
})