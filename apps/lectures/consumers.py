import json

from channels.generic.websocket import AsyncWebsocketConsumer


class LectureStatusConsumer(AsyncWebsocketConsumer):
    """
    One connection per logged-in user. JWTAuthMiddleware has already
    populated self.scope["user"] before connect() runs (or set it to
    AnonymousUser if the token was missing/invalid).

    Joins a group named "user_<id>" so the Celery task can push a status
    update to exactly this user via channel_layer.group_send, regardless
    of which lecture changed — the frontend filters by lecture id itself.
    """

    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close(code=4401)
            return

        self.group_name = f"user_{user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Called by channel_layer.group_send(group_name, {"type": "lecture_status_update", ...})
    async def lecture_status_update(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "type": "lecture_status_update",
                    "lecture_id": event["lecture_id"],
                    "status": event["status"],
                }
            )
        )