import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application

# Initialize Django FIRST
django_asgi_app = get_asgi_application()

# Import Channels stuff AFTER Django is initialized
from channels.routing import ProtocolTypeRouter, URLRouter
from apps.users.jwt_auth_middleware import JWTAuthMiddleware
from apps.lectures.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})