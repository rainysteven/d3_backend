from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import backend.routing
from channels.security.websocket import AllowedHostsOriginValidator

from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # 普通的HTTP协议在这里不需要写，框架会自己指明
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                # 指定去对应应用的routing中去找路由
                backend.routing.websocket_urlpatterns
            )
        ),
    )
})
