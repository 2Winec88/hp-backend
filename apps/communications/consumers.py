from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from apps.collections.models import DonorGroup
from apps.collections.permissions import is_donor_group_member
from apps.organizations.models import OrganizationMember

from .models import DonorGroupMessage, OrganizationMessage


class HealthCheckConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_json({'type': 'connection.ready'})

    async def receive_json(self, content, **kwargs):
        if content.get('type') == 'ping':
            await self.send_json({'type': 'pong'})


class OrganizationChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.organization_id = self.scope["url_route"]["kwargs"]["organization_id"]
        self.group_name = f"organization_chat_{self.organization_id}"
        if not await self._can_access():
            await self.close(code=4403)
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connection.ready"})

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") != "message.create":
            return
        if not await self._can_access():
            await self.send_json({"type": "error", "detail": "Chat access denied."})
            await self.close(code=4403)
            return
        text = (content.get("text") or "").strip()
        if not text:
            await self.send_json({"type": "error", "detail": "Message text cannot be blank."})
            return
        message = await self._create_message(text=text)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message": message,
            },
        )

    async def chat_message(self, event):
        await self.send_json({"type": "message.created", "message": event["message"]})

    @database_sync_to_async
    def _can_access(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            return False
        return OrganizationMember.objects.filter(
            organization_id=self.organization_id,
            user=user,
            is_active=True,
        ).exists()

    @database_sync_to_async
    def _create_message(self, *, text):
        message = OrganizationMessage.objects.select_related("author").create(
            organization_id=self.organization_id,
            author=self.scope["user"],
            text=text,
        )
        return serialize_message(message, context_key="organization")


class DonorGroupChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.donor_group_id = self.scope["url_route"]["kwargs"]["donor_group_id"]
        self.group_name = f"donor_group_chat_{self.donor_group_id}"
        if not await self._can_access():
            await self.close(code=4403)
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({"type": "connection.ready"})

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") != "message.create":
            return
        if not await self._can_access():
            await self.send_json({"type": "error", "detail": "Chat access denied."})
            await self.close(code=4403)
            return
        text = (content.get("text") or "").strip()
        if not text:
            await self.send_json({"type": "error", "detail": "Message text cannot be blank."})
            return
        message = await self._create_message(text=text)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.message",
                "message": message,
            },
        )

    async def chat_message(self, event):
        await self.send_json({"type": "message.created", "message": event["message"]})

    @database_sync_to_async
    def _can_access(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            return False
        try:
            donor_group = DonorGroup.objects.get(pk=self.donor_group_id)
        except DonorGroup.DoesNotExist:
            return False
        return is_donor_group_member(donor_group=donor_group, user=user)

    @database_sync_to_async
    def _create_message(self, *, text):
        message = DonorGroupMessage.objects.select_related("author").create(
            donor_group_id=self.donor_group_id,
            author=self.scope["user"],
            text=text,
        )
        return serialize_message(message, context_key="donor_group")


def serialize_message(message, *, context_key):
    return {
        "id": message.id,
        context_key: getattr(message, f"{context_key}_id"),
        "author": message.author_id,
        "author_email": message.author.email,
        "author_full_name": message.author.full_name,
        "text": message.text,
        "deleted_at": message.deleted_at.isoformat() if message.deleted_at else None,
        "created_at": message.created_at.isoformat(),
        "updated_at": message.updated_at.isoformat(),
    }
