# Push Notifications

Push delivery is implemented as an additional `Notification` delivery channel.

## Device Registration

Authenticated users register devices through:

```http
GET    /api/v1/communications/devices/
POST   /api/v1/communications/devices/
PATCH  /api/v1/communications/devices/{id}/
DELETE /api/v1/communications/devices/{id}/
```

Payload:

```json
{
  "provider": "fcm",
  "token": "device-token",
  "device_id": "phone-1",
  "platform": "android",
  "app_version": "1.0.0"
}
```

Supported provider values: `fcm`, `apns`, `webpush`, `custom`.

## Delivery

Notification creation supports:

```json
{
  "send_push": true
}
```

Only staff superusers can request external delivery through direct notification creation. Invitation delivery uses the invitation permission handlers instead.

Invitation creation also supports `send_push`; the default is `true`.

Push delivery is scheduled through Celery with `transaction.on_commit(...)`, the same pattern as email delivery. The task sends one request per active user device.

## Provider

Configure an HTTP push provider endpoint:

```text
PUSH_PROVIDER_URL=https://push-provider.example/send
PUSH_PROVIDER_API_KEY=optional-token
```

The backend sends this JSON payload:

```json
{
  "provider": "fcm",
  "token": "device-token",
  "title": "Notification title",
  "body": "Notification body",
  "data": {},
  "notification_id": 1
}
```

If `PUSH_PROVIDER_API_KEY` is set, it is sent as `Authorization: Bearer <token>`.

## Delivery Audit

Delivery attempts are stored in `/api/v1/communications/notification-deliveries/`.

```http
GET /api/v1/communications/notification-deliveries/
GET /api/v1/communications/notification-deliveries/?notification=1
GET /api/v1/communications/notification-deliveries/?channel=push
```
