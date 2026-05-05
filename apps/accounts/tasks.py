from celery import shared_task
from django.contrib.auth import get_user_model

from .utils import send_verification_email


@shared_task
def send_email_verification_code(user_id, code):
    user = get_user_model().objects.get(pk=user_id)
    send_verification_email(user, code)
