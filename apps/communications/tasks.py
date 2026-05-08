import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Notification, NotificationDelivery, UserDevice


@shared_task
def send_notification_delivery(notification_id):
    notification = Notification.objects.select_related("recipient").get(pk=notification_id)
    recipient_email = notification.recipient.email
    delivery = NotificationDelivery.objects.create(
        notification=notification,
        channel=NotificationDelivery.Channel.EMAIL,
    )

    if not recipient_email:
        delivery.status = NotificationDelivery.Status.SKIPPED
        delivery.error = "Recipient has no email address."
        delivery.save(update_fields=("status", "error", "updated_at"))
        return

    try:
        send_mail(
            notification.title,
            notification.body or notification.title,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
    except Exception as exc:
        delivery.status = NotificationDelivery.Status.FAILED
        delivery.error = str(exc)
        delivery.save(update_fields=("status", "error", "updated_at"))
        raise

    delivery.status = NotificationDelivery.Status.SENT
    delivery.sent_at = timezone.now()
    delivery.save(update_fields=("status", "sent_at", "updated_at"))
    notification.email_sent_at = timezone.now()
    notification.save(update_fields=("email_sent_at",))


@shared_task
def send_notification_push_delivery(notification_id):
    notification = Notification.objects.select_related("recipient").get(pk=notification_id)
    provider_url = getattr(settings, "PUSH_PROVIDER_URL", "")
    provider_api_key = getattr(settings, "PUSH_PROVIDER_API_KEY", "")
    devices = UserDevice.objects.filter(
        user=notification.recipient,
        is_active=True,
    )

    if not devices.exists():
        NotificationDelivery.objects.create(
            notification=notification,
            channel=NotificationDelivery.Channel.PUSH,
            status=NotificationDelivery.Status.SKIPPED,
            error="Recipient has no active push devices.",
        )
        return

    for device in devices:
        delivery = NotificationDelivery.objects.create(
            notification=notification,
            channel=NotificationDelivery.Channel.PUSH,
            device=device,
        )

        if not provider_url:
            delivery.status = NotificationDelivery.Status.FAILED
            delivery.error = "PUSH_PROVIDER_URL is not configured."
            delivery.save(update_fields=("status", "error", "updated_at"))
            continue

        payload = {
            "provider": device.provider,
            "token": device.token,
            "title": notification.title,
            "body": notification.body,
            "data": notification.payload,
            "notification_id": notification.pk,
        }
        headers = {"Content-Type": "application/json"}
        if provider_api_key:
            headers["Authorization"] = f"Bearer {provider_api_key}"

        request = Request(
            provider_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=10) as response:
                response.read()
                if response.status >= 400:
                    raise URLError(f"Push provider returned HTTP {response.status}.")
        except Exception as exc:
            delivery.status = NotificationDelivery.Status.FAILED
            delivery.error = str(exc)
            delivery.save(update_fields=("status", "error", "updated_at"))
            continue

        delivery.status = NotificationDelivery.Status.SENT
        delivery.sent_at = timezone.now()
        delivery.save(update_fields=("status", "sent_at", "updated_at"))
        device.last_seen_at = timezone.now()
        device.save(update_fields=("last_seen_at", "updated_at"))
