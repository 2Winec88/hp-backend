from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, override_settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import status
from rest_framework.test import APITestCase

from apps.collections.models import Collection, DonorGroup, DonorGroupMember
from apps.organizations.models import Organization, OrganizationMember
from hp_backend.asgi import application

from .models import (
    DonorGroupMessage,
    Invitation,
    Notification,
    NotificationDelivery,
    OrganizationMessage,
    UserDevice,
)
from .tasks import send_notification_push_delivery


@override_settings(
    CHANNEL_LAYERS={
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
)
class CommunicationsWebSocketTests(TransactionTestCase):
    databases = {"default"}

    def setUp(self):
        self.user_model = get_user_model()
        self.manager = self.user_model.objects.create_user(
            username="manager-ws",
            email="manager-ws@example.com",
            password="StrongPassword123!",
        )
        self.member = self.user_model.objects.create_user(
            username="member-ws",
            email="member-ws@example.com",
            password="StrongPassword123!",
        )
        self.donor = self.user_model.objects.create_user(
            username="donor-ws",
            email="donor-ws@example.com",
            password="StrongPassword123!",
        )
        self.outsider = self.user_model.objects.create_user(
            username="outsider-ws",
            email="outsider-ws@example.com",
            password="StrongPassword123!",
        )
        self.organization = Organization.objects.create(
            created_by=self.manager,
            official_name="WS Org",
            legal_address="Address",
            phone="+7 777 000 00 00",
            email="ws-org@example.com",
            executive_person_full_name="Executive Person",
            executive_authority_basis="Charter",
            executive_body_name="Board",
        )
        self.manager_membership = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.manager,
            role=OrganizationMember.Role.MANAGER,
        )
        self.member_membership = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.member,
            role=OrganizationMember.Role.MEMBER,
        )
        self.collection = Collection.objects.create(
            organization=self.organization,
            created_by_member=self.manager_membership,
            title="WS collection",
        )
        self.donor_group = DonorGroup.objects.create(
            collection=self.collection,
            created_by_member=self.manager_membership,
            title="WS donor group",
        )
        self.donor_membership = DonorGroupMember.objects.create(
            donor_group=self.donor_group,
            user=self.donor,
        )

    async def test_health_check_websocket_connects_and_responds_to_ping(self):
        communicator = WebsocketCommunicator(
            application,
            '/ws/communications/health/',
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        self.assertEqual(
            await communicator.receive_json_from(),
            {'type': 'connection.ready'},
        )

        await communicator.send_json_to({'type': 'ping'})
        self.assertEqual(
            await communicator.receive_json_from(),
            {'type': 'pong'},
        )

        await communicator.disconnect()

    async def test_organization_chat_websocket_creates_and_broadcasts_message(self):
        communicator = WebsocketCommunicator(
            application,
            self._ws_path(
                f"/ws/communications/organizations/{self.organization.pk}/chat/",
                user=self.member,
            ),
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        self.assertEqual(await communicator.receive_json_from(), {"type": "connection.ready"})

        await communicator.send_json_to({"type": "message.create", "text": "Hello org"})
        event = await communicator.receive_json_from()

        self.assertEqual(event["type"], "message.created")
        self.assertEqual(event["message"]["organization"], self.organization.pk)
        self.assertEqual(event["message"]["author"], self.member.pk)
        self.assertEqual(event["message"]["text"], "Hello org")
        self.assertTrue(
            await database_sync_to_async(
                OrganizationMessage.objects.filter(
                    organization=self.organization,
                    author=self.member,
                    text="Hello org",
                ).exists
            )()
        )

        await communicator.disconnect()

    async def test_outsider_cannot_connect_to_organization_chat_websocket(self):
        communicator = WebsocketCommunicator(
            application,
            self._ws_path(
                f"/ws/communications/organizations/{self.organization.pk}/chat/",
                user=self.outsider,
            ),
        )

        connected, _ = await communicator.connect()

        self.assertFalse(connected)

    async def test_donor_group_chat_websocket_creates_and_broadcasts_message(self):
        communicator = WebsocketCommunicator(
            application,
            self._ws_path(
                f"/ws/communications/donor-groups/{self.donor_group.pk}/chat/",
                user=self.donor,
            ),
        )

        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        self.assertEqual(await communicator.receive_json_from(), {"type": "connection.ready"})

        await communicator.send_json_to({"type": "message.create", "text": "Hello group"})
        event = await communicator.receive_json_from()

        self.assertEqual(event["type"], "message.created")
        self.assertEqual(event["message"]["donor_group"], self.donor_group.pk)
        self.assertEqual(event["message"]["author"], self.donor.pk)
        self.assertEqual(event["message"]["text"], "Hello group")
        self.assertTrue(
            await database_sync_to_async(
                DonorGroupMessage.objects.filter(
                    donor_group=self.donor_group,
                    author=self.donor,
                    text="Hello group",
                ).exists
            )()
        )

        await communicator.disconnect()

    async def test_removed_donor_group_member_cannot_keep_sending_on_open_websocket(self):
        communicator = WebsocketCommunicator(
            application,
            self._ws_path(
                f"/ws/communications/donor-groups/{self.donor_group.pk}/chat/",
                user=self.donor,
            ),
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        self.assertEqual(await communicator.receive_json_from(), {"type": "connection.ready"})

        await database_sync_to_async(self.donor_membership.delete)()
        await communicator.send_json_to({"type": "message.create", "text": "No longer a member"})
        event = await communicator.receive_json_from()

        self.assertEqual(event["type"], "error")
        self.assertEqual(event["detail"], "Chat access denied.")
        self.assertFalse(
            await database_sync_to_async(
                DonorGroupMessage.objects.filter(
                    donor_group=self.donor_group,
                    author=self.donor,
                    text="No longer a member",
                ).exists
            )()
        )

        await communicator.wait()

    def _ws_path(self, path, *, user):
        token = AccessToken.for_user(user)
        return f"{path}?token={token}"


class NotificationApiTests(APITestCase):
    url = "/api/v1/communications/notifications/"

    def setUp(self):
        self.user_model = get_user_model()
        self.sender = self.user_model.objects.create_user(
            username="sender",
            email="sender@example.com",
            password="StrongPassword123!",
        )
        self.recipient = self.user_model.objects.create_user(
            username="recipient",
            email="recipient@example.com",
            password="StrongPassword123!",
        )

    def test_user_can_create_text_notification_for_another_user(self):
        self.client.force_authenticate(self.sender)

        response = self.client.post(
            self.url,
            data={
                "recipient": self.recipient.pk,
                "type": Notification.Type.TEXT,
                "title": "Hello",
                "body": "Plain text notification",
                "payload": {"kind": "manual"},
                "send_email": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification = Notification.objects.get(pk=response.data["id"])
        self.assertEqual(notification.recipient, self.recipient)
        self.assertEqual(notification.actor, self.sender)
        self.assertEqual(notification.type, Notification.Type.TEXT)

    def test_user_only_lists_own_notifications(self):
        Notification.objects.create(
            recipient=self.recipient,
            actor=self.sender,
            type=Notification.Type.TEXT,
            title="Visible",
        )
        Notification.objects.create(
            recipient=self.sender,
            actor=self.recipient,
            type=Notification.Type.TEXT,
            title="Hidden",
        )
        self.client.force_authenticate(self.recipient)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Visible")

    def test_user_can_mark_notification_read(self):
        notification = Notification.objects.create(
            recipient=self.recipient,
            actor=self.sender,
            type=Notification.Type.TEXT,
            title="Unread",
        )
        self.client.force_authenticate(self.recipient)

        response = self.client.post(f"{self.url}{notification.pk}/mark-read/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)
        self.assertIsNotNone(notification.read_at)

    def test_regular_user_cannot_request_external_notification_delivery(self):
        self.client.force_authenticate(self.sender)

        response = self.client.post(
            self.url,
            data={
                "recipient": self.recipient.pk,
                "type": Notification.Type.TEXT,
                "title": "External",
                "send_push": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_register_own_push_device(self):
        self.client.force_authenticate(self.recipient)

        response = self.client.post(
            "/api/v1/communications/devices/",
            data={
                "provider": UserDevice.Provider.FCM,
                "token": "device-token",
                "device_id": "phone-1",
                "platform": "android",
                "app_version": "1.0.0",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        device = UserDevice.objects.get(pk=response.data["id"])
        self.assertEqual(device.user, self.recipient)

    @override_settings(PUSH_PROVIDER_URL="")
    def test_push_delivery_records_failure_when_provider_is_not_configured(self):
        UserDevice.objects.create(
            user=self.recipient,
            provider=UserDevice.Provider.FCM,
            token="device-token",
        )
        notification = Notification.objects.create(
            recipient=self.recipient,
            actor=self.sender,
            type=Notification.Type.TEXT,
            title="Push me",
            payload={"kind": "test"},
        )

        send_notification_push_delivery(notification.pk)

        delivery = NotificationDelivery.objects.get(notification=notification)
        self.assertEqual(delivery.channel, NotificationDelivery.Channel.PUSH)
        self.assertEqual(delivery.status, NotificationDelivery.Status.FAILED)


class InvitationApiTests(APITestCase):
    url = "/api/v1/communications/invitations/"

    def setUp(self):
        self.user_model = get_user_model()
        self.manager = self.user_model.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="StrongPassword123!",
        )
        self.member = self.user_model.objects.create_user(
            username="member",
            email="member@example.com",
            password="StrongPassword123!",
        )
        self.outsider = self.user_model.objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password="StrongPassword123!",
        )
        self.organization = Organization.objects.create(
            created_by=self.manager,
            official_name="Helping Hands",
            legal_address="Address",
            phone="+7 777 000 00 00",
            email="org@example.com",
            executive_person_full_name="Executive Person",
            executive_authority_basis="Charter",
            executive_body_name="Board",
        )
        self.manager_membership = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.manager,
            role=OrganizationMember.Role.MANAGER,
        )

    def test_manager_can_invite_user_and_acceptance_creates_membership(self):
        self.client.force_authenticate(self.manager)

        create_response = self.client.post(
            self.url,
            data={
                "target_type": "organization",
                "target_id": self.organization.pk,
                "invited_user": self.member.pk,
                "role": OrganizationMember.Role.MEMBER,
                "send_email": False,
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        invitation = Invitation.objects.get(pk=create_response.data["id"])
        self.assertEqual(invitation.notification.type, Notification.Type.INVITATION)
        self.assertEqual(invitation.notification.recipient, self.member)

        self.client.force_authenticate(self.member)
        accept_response = self.client.post(f"{self.url}{invitation.pk}/accept/")

        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, Invitation.Status.ACCEPTED)
        self.assertTrue(
            OrganizationMember.objects.filter(
                organization=self.organization,
                user=self.member,
                role=OrganizationMember.Role.MEMBER,
            ).exists()
        )

    def test_non_manager_cannot_invite_user_to_organization(self):
        self.client.force_authenticate(self.outsider)

        response = self.client.post(
            self.url,
            data={
                "target_type": "organization",
                "target_id": self.organization.pk,
                "invited_user": self.member.pk,
                "role": OrganizationMember.Role.MEMBER,
                "send_email": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pending_invitation_cannot_be_duplicated(self):
        self.client.force_authenticate(self.manager)
        payload = {
            "target_type": "organization",
            "target_id": self.organization.pk,
            "invited_user": self.member.pk,
            "role": OrganizationMember.Role.MEMBER,
            "send_email": False,
        }

        first_response = self.client.post(self.url, data=payload, format="json")
        second_response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_collection_manager_can_invite_user_to_donor_group(self):
        collection = Collection.objects.create(
            organization=self.organization,
            created_by_member=self.manager_membership,
            title="Winter help",
        )
        donor_group = DonorGroup.objects.create(
            collection=collection,
            created_by_member=self.manager_membership,
        )
        self.client.force_authenticate(self.manager)

        create_response = self.client.post(
            self.url,
            data={
                "target_type": "donor_group",
                "target_id": donor_group.pk,
                "invited_user": self.member.pk,
                "send_email": False,
                "send_push": False,
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        invitation = Invitation.objects.get(pk=create_response.data["id"])
        self.assertEqual(create_response.data["target_type"], "donor_group")

        self.client.force_authenticate(self.member)
        accept_response = self.client.post(f"{self.url}{invitation.pk}/accept/")

        self.assertEqual(accept_response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            DonorGroupMember.objects.filter(
                donor_group=donor_group,
                user=self.member,
            ).exists()
        )


class ChatMessageApiTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.manager = self.user_model.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="StrongPassword123!",
        )
        self.member = self.user_model.objects.create_user(
            username="member",
            email="member@example.com",
            password="StrongPassword123!",
        )
        self.donor = self.user_model.objects.create_user(
            username="donor",
            email="donor@example.com",
            password="StrongPassword123!",
        )
        self.outsider = self.user_model.objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password="StrongPassword123!",
        )
        self.organization = Organization.objects.create(
            created_by=self.manager,
            official_name="Helping Hands",
            legal_address="Address",
            phone="+7 777 000 00 00",
            email="org@example.com",
            executive_person_full_name="Executive Person",
            executive_authority_basis="Charter",
            executive_body_name="Board",
        )
        self.manager_membership = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.manager,
            role=OrganizationMember.Role.MANAGER,
        )
        self.member_membership = OrganizationMember.objects.create(
            organization=self.organization,
            user=self.member,
            role=OrganizationMember.Role.MEMBER,
        )
        self.collection = Collection.objects.create(
            organization=self.organization,
            created_by_member=self.manager_membership,
            title="Winter help",
        )
        self.donor_group = DonorGroup.objects.create(
            collection=self.collection,
            created_by_member=self.manager_membership,
            title="Central group",
        )
        DonorGroupMember.objects.create(donor_group=self.donor_group, user=self.donor)

    def test_organization_member_can_create_and_list_organization_messages(self):
        self.client.force_authenticate(self.member)

        create_response = self.client.post(
            "/api/v1/communications/organization-messages/",
            data={
                "organization": self.organization.pk,
                "text": "Hello organization",
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        message = OrganizationMessage.objects.get(pk=create_response.data["id"])
        self.assertEqual(message.author, self.member)

        list_response = self.client.get(
            f"/api/v1/communications/organization-messages/?organization={self.organization.pk}"
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["text"], "Hello organization")

    def test_outsider_cannot_use_organization_chat(self):
        self.client.force_authenticate(self.outsider)

        create_response = self.client.post(
            "/api/v1/communications/organization-messages/",
            data={
                "organization": self.organization.pk,
                "text": "Nope",
            },
            format="json",
        )
        list_response = self.client.get(
            f"/api/v1/communications/organization-messages/?organization={self.organization.pk}"
        )

        self.assertEqual(create_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 0)

    def test_organization_manager_can_soft_delete_message(self):
        message = OrganizationMessage.objects.create(
            organization=self.organization,
            author=self.member,
            text="Needs moderation",
        )

        self.client.force_authenticate(self.manager)
        response = self.client.delete(
            f"/api/v1/communications/organization-messages/{message.pk}/"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        message.refresh_from_db()
        self.assertIsNotNone(message.deleted_at)

    def test_donor_group_member_can_create_and_list_donor_group_messages(self):
        self.client.force_authenticate(self.donor)

        create_response = self.client.post(
            "/api/v1/communications/donor-group-messages/",
            data={
                "donor_group": self.donor_group.pk,
                "text": "I can bring blankets",
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        message = DonorGroupMessage.objects.get(pk=create_response.data["id"])
        self.assertEqual(message.author, self.donor)

        list_response = self.client.get(
            f"/api/v1/communications/donor-group-messages/?donor_group={self.donor_group.pk}"
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["text"], "I can bring blankets")

    def test_outsider_cannot_use_donor_group_chat(self):
        self.client.force_authenticate(self.outsider)

        create_response = self.client.post(
            "/api/v1/communications/donor-group-messages/",
            data={
                "donor_group": self.donor_group.pk,
                "text": "No access",
            },
            format="json",
        )
        list_response = self.client.get(
            f"/api/v1/communications/donor-group-messages/?donor_group={self.donor_group.pk}"
        )

        self.assertEqual(create_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 0)

    def test_collection_manager_can_soft_delete_donor_group_message(self):
        message = DonorGroupMessage.objects.create(
            donor_group=self.donor_group,
            author=self.donor,
            text="Needs moderation",
        )

        self.client.force_authenticate(self.manager)
        response = self.client.delete(
            f"/api/v1/communications/donor-group-messages/{message.pk}/"
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        message.refresh_from_db()
        self.assertIsNotNone(message.deleted_at)
