from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Notification


@shared_task
def send_notification_delivery(notification_id):
    notification = Notification.objects.select_related("recipient").get(pk=notification_id)
    recipient_email = notification.recipient.email

    if not recipient_email:
        return

    send_mail(
        notification.title,
        notification.body or notification.title,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        fail_silently=False,
    )
    notification.email_sent_at = timezone.now()
    notification.save(update_fields=("email_sent_at",))
