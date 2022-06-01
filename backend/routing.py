from django.urls import path
from backend.wsViews import FilesConsumer

websocket_urlpatterns = [
    path('ws/records/<str:channel_id>/', FilesConsumer.as_asgi()),
    path('ws/sections/<str:channel_id>/', FilesConsumer.as_asgi())
    # path('ws/<str:username>/',MessagesConsumer) # 如果是传参的路由在连接中获取关键字参数方法：self.scope['url_route']['kwargs']['username']
]
