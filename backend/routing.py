from django.urls import path
from backend.wsViews import FilesConsumer

websocket_urlpatterns = [
    path('ws/records/<str:channel_id>/', FilesConsumer.as_asgi()),
    path('ws/sections/<str:channel_id>/', FilesConsumer.as_asgi())
]
