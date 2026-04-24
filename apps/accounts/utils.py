from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def build_email_verification_link(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse("verify_email", kwargs={"uidb64": uid, "token": token})
    return request.build_absolute_uri(path)


def send_verification_email(request, user):
    verification_link = build_email_verification_link(request, user)
    subject = "Verify your email address"
    message = (
        f"Hello, {user.username}!\n\n"
        "Please verify your email address by opening the link below:\n"
        f"{verification_link}\n\n"
        "If you did not create this account, you can ignore this email."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
