from django.conf import settings
from django.core.mail import send_mail


def send_verification_email(user, code):
    subject = "Verify your email address"
    message = (
        f"Hello, {user.username}!\n\n"
        "Use this code to verify your email address:\n"
        f"{code}\n\n"
        "The code expires soon. If you did not create this account, you can ignore this email."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
