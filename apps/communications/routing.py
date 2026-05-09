from django.urls import path

from . import consumers


websocket_urlpatterns = [
    path('ws/communications/health/', consumers.HealthCheckConsumer.as_asgi()),
    path(
        'ws/communications/organizations/<int:organization_id>/chat/',
        consumers.OrganizationChatConsumer.as_asgi(),
    ),
    path(
        'ws/communications/donor-groups/<int:donor_group_id>/chat/',
        consumers.DonorGroupChatConsumer.as_asgi(),
    ),
]
