import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(
    AsyncWebsocketConsumer
):

    async def connect(self):

        await self.accept()

        await self.send(
            text_data=json.dumps({
                "message": "WebSocket connected"
            })
        )

    async def disconnect(
        self,
        close_code
    ):

        print("Disconnected")

    async def receive(
        self,
        text_data
    ):

        data = json.loads(text_data)

        message = data["message"]

        await self.send(
            text_data=json.dumps({
                "message": message
            })
        )