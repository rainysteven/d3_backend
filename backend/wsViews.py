import json

from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync


class FilesConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        self.channel_id = ""
        super(FilesConsumer, self).__init__(*args, **kwargs)

    def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        async_to_sync(self.channel_layer.group_add)(
            self.channel_id,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        # 断开连接时从组里面删除
        async_to_sync(self.channel_layer.group_discard)(
            self.channel_id,
            self.channel_name
        )

    def send_message(self, event):
        # 发送信息执行
        message = event['message']
        self.send(text_data=json.dumps({
            'message': message
        }))
