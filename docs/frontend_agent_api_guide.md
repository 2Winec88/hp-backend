# Frontend Agent API Guide

������ ���� ��� frontend-������. ��� �������� ���� � frontend-facing API-�������������, ������� Collections, push-����������� � flow ��� �������� API.

�������� ������ ��� ������ ����� ����� �������� � OpenAPI:

- `GET /api/schema/`
- `GET /api/docs/`
- `GET /api/redoc/`

������� REST-�������: `/api/v1/`.

��� �������������� �������� �����������:

```text
Authorization: Bearer <access_token>
```

JSON-����� ������� � �������� � `docs` �������� ����������� �������, � �� API-������, ������� � ���� ���� �� ��������.

---

## File Upload Limits

Use `multipart/form-data` for every endpoint that accepts files.

Current backend validation:

- Images and avatars: `jpg`, `jpeg`, `png`, `webp`, `gif`; MIME `image/jpeg`, `image/png`, `image/webp`, `image/gif`; max `5 MB`.
- PDF documents: `pdf`; MIME `application/pdf`; max `25 MB`; file content must start with a PDF signature.
- Donor group video reports: `mp4`, `mov`, `webm`; MIME `video/mp4`, `video/quicktime`, `video/webm`; max `500 MB`.

If validation fails, the API returns `400` with the file field name in the response body, for example `avatar`, `document`, `image`, or `video`.

## Accounts

### Register

```http
POST /api/v1/accounts/register/
```

Payload:

```json
{
  "username": "manager",
  "email": "manager@example.com",
  "password": "StrongPassword123!",
  "password_confirm": "StrongPassword123!",
  "first_name": "Manager",
  "last_name": "User"
}
```

����� ����������� ������������ ��������� �� ������������� email. ��� ������������ backend-�� ����� Celery.

### Verify Email

```http
POST /api/v1/accounts/verify-email/
```

Payload:

```json
{
  "email": "manager@example.com",
  "code": "123456"
}
```

### Login

```http
POST /api/v1/accounts/login/
```

Payload:

```json
{
  "email": "manager@example.com",
  "password": "StrongPassword123!"
}
```

Response �������� `access`, `refresh`, `user`.

### Refresh Token

```http
POST /api/v1/accounts/token/refresh/
```

Payload:

```json
{
  "refresh": "<refresh_token>"
}
```

### Logout

```http
POST /api/v1/accounts/logout/
```

Payload:

```json
{
  "refresh_token": "<refresh_token>"
}
```

### Profile

```http
GET   /api/v1/accounts/profile/
PATCH /api/v1/accounts/profile/
PUT   /api/v1/accounts/profile/
```

Profile fields:

```json
{
  "id": 1,
  "username": "manager",
  "email": "manager@example.com",
  "first_name": "Manager",
  "last_name": "User",
  "full_name": "Manager User",
  "avatar": null,
  "bio": "",
  "geodata": 1
}
```

Update payload supports: `first_name`, `last_name`, `avatar`, `bio`, `geodata`.

## Common

`common` �������� ���������������� ����������� � ���������.

### Regions

```http
GET /api/v1/common/regions/
GET /api/v1/common/regions/?search=�����
GET /api/v1/common/regions/{id}/
```

������� read-only ��� ���������� API. ��������, �������������� � �������� ����� frontend ���������.

Response item:

```json
{
  "id": 1,
  "name": "������������ �������",
  "latitude": null,
  "longitude": null,
  "country_code": "RU",
  "created_at": "...",
  "updated_at": "..."
}
```

### Cities

```http
GET /api/v1/common/cities/
GET /api/v1/common/cities/?search=����
GET /api/v1/common/cities/?search=����&limit=10
GET /api/v1/common/cities/{id}/
```

������ read-only ��� ���������� API. ��� ������ ������ � ������ ����������� ��� ������� ����������� autocomplete ����� `search`. Backend ���� �� �������� ������, �������� ������� � ���� ������, �������������� ���������� � ������� �������� ������ � ���������� �� `limit` �������. `limit` optional, �� ��������� `20`, �������� `100`.

Response item:

```json
{
  "id": 1,
  "name": "������������",
  "latitude": "56.838011",
  "longitude": "60.597465",
  "country_code": "RU",
  "region": 1,
  "region_name": "������������ �������",
  "created_at": "...",
  "updated_at": "..."
}
```

### GeoData

```http
GET    /api/v1/common/geodata/
POST   /api/v1/common/geodata/
GET    /api/v1/common/geodata/{id}/
PATCH  /api/v1/common/geodata/{id}/
DELETE /api/v1/common/geodata/{id}/
```

��� ���� optional. ����� ������� ������ �����, ������ �����, ������ ���������� ��� ������ ���������.

Payload:

```json
{
  "city": 1,
  "street": "Lenina, 1",
  "latitude": "56.838011",
  "longitude": "60.597465"
}
```

Response:

```json
{
  "id": 1,
  "city": 1,
  "city_name": "������������",
  "region_name": "������������ �������",
  "street": "Lenina, 1",
  "latitude": "56.838011",
  "longitude": "60.597465",
  "created_at": "...",
  "updated_at": "..."
}
```

Coordinates validation: `latitude` �� `-90` �� `90`, `longitude` �� `-180` �� `180`.

## Organizations

### Organizations

```http
GET   /api/v1/organizations/organizations/
GET   /api/v1/organizations/organizations/{id}/
PATCH /api/v1/organizations/organizations/{id}/
```

������ ����� ���. ������������� ����� �������� �������� �����������.

Fields:

```json
{
  "id": 1,
  "official_name": "Help Org",
  "legal_address": "Address",
  "phone": "+7 777 000 00 00",
  "email": "org@example.com",
  "max_url": "https://max.example.com/org",
  "vk_url": "https://vk.com/org",
  "website_url": "https://org.example.com",
  "executive_person_full_name": "Executive Person",
  "executive_authority_basis": "Charter",
  "executive_body_name": "Board",
  "created_by": 1,
  "created_at": "...",
  "updated_at": "..."
}
```

����������� ��������� ����� ������ �� �����������, � �� ������ `POST /organizations/organizations/`.

### Registration Requests

```http
GET  /api/v1/organizations/organization-registration-requests/
POST /api/v1/organizations/organization-registration-requests/
GET  /api/v1/organizations/organization-registration-requests/{id}/
POST /api/v1/organizations/organization-registration-requests/{id}/approve/
POST /api/v1/organizations/organization-registration-requests/{id}/reject/
```

`POST` ������ ����������� ��� `multipart/form-data`, ������ ��� ����� ���������.

Create fields:

```text
official_name
legal_address
phone
email
max_url
vk_url
website_url
executive_person_full_name
executive_authority_basis
executive_body_name
charter_document
inn_certificate
state_registration_certificate
founders_appointment_decision
executive_passport_copy
egrul_extract
nko_registry_notice
```

������������ ����� ������ ���� ������. Staff superuser ����� ��� � ����� approve/reject.

Reject payload:

```json
{
  "rejection_reason": "Not enough documents"
}
```

### Members

```http
GET    /api/v1/organizations/members/
GET    /api/v1/organizations/members/?organization=1
DELETE /api/v1/organizations/members/{id}/
```

������ ������ ��������� �����������. `DELETE` ����� ��������� ���������: ������ ��������, �� `is_active=false`. �������� �� ����� ��������� ���� � ������ ��������� ���������� ���������.

Response item:

```json
{
  "id": 1,
  "organization": 1,
  "organization_name": "Help Org",
  "user": 2,
  "user_email": "member@example.com",
  "user_full_name": "Member User",
  "role": "member",
  "is_active": true,
  "removed_at": null,
  "removed_by": null,
  "created_at": "..."
}
```

### Categories

```http
GET /api/v1/organizations/categories/
GET /api/v1/organizations/categories/{id}/
```

��������� read-only ��� frontend.

### Branches

```http
GET    /api/v1/organizations/branches/
GET    /api/v1/organizations/branches/?organization=1
POST   /api/v1/organizations/branches/
GET    /api/v1/organizations/branches/{id}/
PATCH  /api/v1/organizations/branches/{id}/
DELETE /api/v1/organizations/branches/{id}/
```

������� ����������� ����������� � ���������� `common.GeoData` ��� ����������. ������ ����� ���. ���������, ������������� � ������� ������� ����� ������ �������� �������� �����������. `organization` ������ ������ ����� ��������.

Payload:

```json
{
  "organization": 1,
  "geodata": 1,
  "name": "Central branch",
  "description": "Donation point description",
  "phone": "+7 777 000 00 02",
  "email": "branch@example.com",
  "working_hours": "Mon-Fri 10:00-19:00",
  "is_active": true
}
```

Response item includes read-only gallery fields:

```json
{
  "id": 1,
  "organization": 1,
  "geodata": 1,
  "name": "Central branch",
  "description": "Donation point description",
  "phone": "+7 777 000 00 02",
  "email": "branch@example.com",
  "working_hours": "Mon-Fri 10:00-19:00",
  "is_active": true,
  "images": [],
  "images_count": 0,
  "created_at": "...",
  "updated_at": "..."
}
```

### Branch Images

```http
GET    /api/v1/organizations/branch-images/
GET    /api/v1/organizations/branch-images/?branch=1
POST   /api/v1/organizations/branch-images/
GET    /api/v1/organizations/branch-images/{id}/
PATCH  /api/v1/organizations/branch-images/{id}/
DELETE /api/v1/organizations/branch-images/{id}/
```

������ ����� ����� ��������� ����������� ����� ��������� `branch-images` ������. ��� `image` ����������� `multipart/form-data`. ��������� ������������� ����� ������ �������� �������� ����������� �������. ������ ����� ���. `branch` ������ ������ ����� ��������.

Payload:

```json
{
  "branch": 1,
  "image": "<file>",
  "alt_text": "Image description",
  "sort_order": 1
}
```

### Events

```http
GET    /api/v1/organizations/events/
POST   /api/v1/organizations/events/
GET    /api/v1/organizations/events/{id}/
PATCH  /api/v1/organizations/events/{id}/
DELETE /api/v1/organizations/events/{id}/
```

������ ����� ���. ��������� ����� ������ �������� �������� �����������. �������������/������� ����� ����� ��� �������� �������� �����������.

Payload:

```json
{
  "title": "Volunteer Meeting",
  "content": "Description",
  "category": 1,
  "organization": 1,
  "geodata": 1,
  "status": "draft",
  "starts_at": "2026-06-01T10:00:00+05:00",
  "ends_at": "2026-06-01T12:00:00+05:00",
  "is_online": false,
  "max_url": "https://max.example.com/event-post",
  "vk_url": "https://vk.com/event-post",
  "website_url": "https://example.com/events/help"
}
```

`ends_at` �� ����� ���� ������ `starts_at`. `geodata = null` �� �������� ������������� online; ����������� ��������� ���� `is_online`.

������ ��������� ���� `city` ��������� ��� �������������. ����� ������ ������ ������������ `geodata`.

### Event Images

```http
GET    /api/v1/organizations/event-images/
GET    /api/v1/organizations/event-images/?event=1
POST   /api/v1/organizations/event-images/
GET    /api/v1/organizations/event-images/{id}/
PATCH  /api/v1/organizations/event-images/{id}/
DELETE /api/v1/organizations/event-images/{id}/
```

��� �������� ����������� `multipart/form-data`.

Fields:

```text
event
image
alt_text
sort_order
```

`event` ������ ������ ����� ��������.

### News

```http
GET    /api/v1/organizations/news/
GET    /api/v1/organizations/news/?organization=1
POST   /api/v1/organizations/news/
GET    /api/v1/organizations/news/{id}/
PATCH  /api/v1/organizations/news/{id}/
DELETE /api/v1/organizations/news/{id}/
```

������� ����������� �����������, �� �����������. Detail-������ ����������� `views_count`.

Payload:

```json
{
  "organization": 1,
  "title": "News title",
  "text": "News text",
  "comments": ""
}
```

��� ���������� legacy-���� `image` ����������� `multipart/form-data`. ��� ������� ����������� ��������� `news-images` endpoint. `organization` ������ ������ ����� ��������. Response ������� �������� read-only ���� `images`, `images_count`, `comments_count` � `views_count`.

Alias ��� �������� �������������:

```http
/api/v1/organizations/event-news/
```

����� frontend ������ ������������ `/news/`.

### News Images

```http
GET    /api/v1/organizations/news-images/
GET    /api/v1/organizations/news-images/?news=1
POST   /api/v1/organizations/news-images/
GET    /api/v1/organizations/news-images/{id}/
PATCH  /api/v1/organizations/news-images/{id}/
DELETE /api/v1/organizations/news-images/{id}/
```

������� ����� ����� ��������� ����������� ����� ��������� `news-images` ������. ��� `image` ����������� `multipart/form-data`. ���������, ������������� � ������� ����������� ����� ����� ������� ��� �������� �������� �����������. ������ ����� ���. `news` ������ ������ ����� ��������.

Payload:

```json
{
  "news": 1,
  "image": "<file>",
  "alt_text": "Image description",
  "sort_order": 1
}
```

### News Comments

```http
GET    /api/v1/organizations/news-comments/
GET    /api/v1/organizations/news-comments/?news=1
POST   /api/v1/organizations/news-comments/
GET    /api/v1/organizations/news-comments/{id}/
PATCH  /api/v1/organizations/news-comments/{id}/
DELETE /api/v1/organizations/news-comments/{id}/
```

��������� ����������� ����� ����� �������������� ������������. �������������/������� ����� ����� ����������� ��� �������� �������� ����������� �������. `news` ������ ������ ����� ��������.

Payload:

```json
{
  "news": 1,
  "text": "Comment text"
}
```

### Organization Report Documents

```http
GET    /api/v1/organizations/report-documents/
GET    /api/v1/organizations/report-documents/?organization=1
POST   /api/v1/organizations/report-documents/
GET    /api/v1/organizations/report-documents/{id}/
PATCH  /api/v1/organizations/report-documents/{id}/
DELETE /api/v1/organizations/report-documents/{id}/
```

Organizations can publish public PDF reports through `report-documents`. Use `multipart/form-data`; `document` accepts PDF files. Reading is public. Creating, editing, and deleting report documents is available to the report author or an active organization manager; creation requires an active organization manager.

Payload:

```json
{
  "organization": 1,
  "title": "Monthly report",
  "description": "Optional description",
  "document": "<pdf file>"
}
```

## Communications

���������� ������������:

- Invitations support `target_type="organization"` and `target_type="donor_group"`.
- Push notifications are documented below in `Detailed Push Notifications API`.

### Notifications

```http
GET  /api/v1/communications/notifications/
GET  /api/v1/communications/notifications/?is_read=false
POST /api/v1/communications/notifications/
GET  /api/v1/communications/notifications/{id}/
POST /api/v1/communications/notifications/{id}/mark-read/
POST /api/v1/communications/notifications/mark-all-read/
```

������������ ����� ������ ���� �����������.

Create payload:

```json
{
  "recipient": 2,
  "type": "text",
  "title": "Title",
  "body": "Body",
  "payload": {},
  "send_email": false,
  "send_push": false
}
```

Allowed create types: `text`, `message`, `system`. Invitation notifications ��������� ����� invitations API. ������ `send_email=true` ��� `send_push=true` ��� �������� ����������� �������� ������ staff superuser.

### Devices

```http
GET    /api/v1/communications/devices/
POST   /api/v1/communications/devices/
PATCH  /api/v1/communications/devices/{id}/
DELETE /api/v1/communications/devices/{id}/
```

������������ ��������� ������ ������ push-������������.

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

### Notification Deliveries

```http
GET /api/v1/communications/notification-deliveries/
GET /api/v1/communications/notification-deliveries/?notification=1
GET /api/v1/communications/notification-deliveries/?channel=push
```

Read-only ����� email/push-��������. ������������ ����� �������� ������ ����� �����������.

### Organization Messages

```http
GET    /api/v1/communications/organization-messages/?organization=1
GET    /api/v1/communications/organization-messages/?organization=1&after_id=123
POST   /api/v1/communications/organization-messages/
PATCH  /api/v1/communications/organization-messages/{id}/
DELETE /api/v1/communications/organization-messages/{id}/
```

������� � REST fallback ��� ���� �����������. ������ � ������ ����� ������ �������� `OrganizationMember`. ����� ����� �������������/������� ��� ���������, �������� ����������� ����� ������������. `DELETE` ������: ��������� `deleted_at`.

Payload:

```json
{
  "organization": 1,
  "text": "��� ������� �� �����?"
}
```

### Donor Group Messages

```http
GET    /api/v1/communications/donor-group-messages/?donor_group=1
GET    /api/v1/communications/donor-group-messages/?donor_group=1&after_id=123
POST   /api/v1/communications/donor-group-messages/
PATCH  /api/v1/communications/donor-group-messages/{id}/
DELETE /api/v1/communications/donor-group-messages/{id}/
```

������� � REST fallback ��� ���� ��������� ������. ������ � ������ ����� `DonorGroupMember`. ����� ����� �������������/������� ��� ���������; ����� ����� ��� �������� �������� ����������� ����� ������������. `DELETE` ������: ��������� `deleted_at`.

Payload:

```json
{
  "donor_group": 1,
  "text": "� ���� �������� ���� ����� 18:00"
}
```

### Invitations

```http
GET  /api/v1/communications/invitations/
POST /api/v1/communications/invitations/
GET  /api/v1/communications/invitations/{id}/
POST /api/v1/communications/invitations/{id}/accept/
POST /api/v1/communications/invitations/{id}/decline/
POST /api/v1/communications/invitations/{id}/cancel/
```

������������ ����� �����������, ��� �� ������������ ��� ������������.

Create payload for organization invitation:

```json
{
  "target_type": "organization",
  "target_id": 1,
  "invited_user": 2,
  "role": "member",
  "send_email": true,
  "send_push": true
}
```

Allowed organization roles: `manager`, `member`. ��������� ����������� ����� ������ invited user. �������� ����� ������������, ������� ����� ����� ���������� � target.

������ ���������� `target_type="organization"` � `target_type="donor_group"`.

## WebSocket

Channels ���������. ������ frontend-facing WebSocket endpoint:

```text
ws://<host>/ws/communications/health/
wss://<host>/ws/communications/health/
ws://<host>/ws/communications/organizations/{organization_id}/chat/
wss://<host>/ws/communications/organizations/{organization_id}/chat/
ws://<host>/ws/communications/donor-groups/{donor_group_id}/chat/
wss://<host>/ws/communications/donor-groups/{donor_group_id}/chat/
```

JWT middleware ��������� token �� query param:

```text
?token=<access_token>
```

��� �� header:

```text
Authorization: Bearer <access_token>
```

`health` endpoint ������ health-check. Chat endpoints ��������� JSON:

```json
{
  "type": "message.create",
  "text": "Message text"
}
```

� ����� ���� ������������ ���������� ���������������� ���� ������������:

```json
{
  "type": "message.created",
  "message": {
    "id": 1,
    "donor_group": 1,
    "author": 2,
    "author_email": "user@example.com",
    "author_full_name": "User Name",
    "text": "Message text",
    "deleted_at": null,
    "created_at": "...",
    "updated_at": "..."
  }
}
```

REST � ���� �������� ���������� ������; WebSocket �� ������ ���� ������������ �������� �������� ������� ��� ����������� ���������.

## Collections

���������� ������� Collections:

- ������ ������������ Collections ��������� ���� � ���� �� �����.
- Base prefix: `/api/v1/collections/`.
- Public read endpoints exist for item categories, user items, collections, collection items, branch items, donor groups, donor group members, donor group items, and courier profiles.
- Authenticated users create their own `user-items` and `courier-profiles`.
- Active organization members create collections.
- Collection author or active organization manager manages collections, collection items, donor groups, donor group members, and donor group items.
- Active organization manager manages branch items.
- Donor group invitations use `/api/v1/communications/invitations/` with `target_type="donor_group"`.
- Collection authors and organization managers manually set donor group parameters time with `POST /api/v1/collections/donor-groups/{id}/set-parameters-time/`.
- Collection authors and organization managers can also set place and time together with `POST /api/v1/collections/donor-groups/{id}/set-parameters/`. Legacy `schedule-meeting*` URLs remain as aliases.
- Poll endpoints are available under `/api/v1/collections/polls/`, `/poll-options/`, `/poll-votes/`, and `/meeting-place-proposals/`.
- Poll kinds are `text`, `date`, and `place`; poll statuses are `draft`, `open`, and `closed`.
- Donor group members can submit meeting place proposals and vote in donor group polls.
- Collection authors and organization managers create donor group polls, repost polls without zero-vote options, create place polls from meeting place proposals, and finalize date/place poll options into `DonorGroupParameters`.
- Donor group members can upload video reports attached directly to the donor group.
- News authors and organization managers can attach polls to news.
- New open donor group polls create notification records and push delivery tasks for donor group members.
- ������ ������������ push-����������� ��������� ���� � ���� �� �����.

The `collections` app has a public REST API now. Organization and donor group chats are implemented in `communications`. Poll-result finalization for donor group date/place parameters and donor group video reports are implemented. The platform does not currently implement a full item transfer accounting lifecycle.


## Frontend Rules

- �� ���������� ������� � ������ ����� public API; ����������� read-only ����������� � autocomplete.
- ��� ����� �������������� ������� ����������� `GeoData`, � �� ��������� ��������� ����.
- �� �������� ����������� online ������ �� `geodata=null`; ����������� `is_online`.
- ��� ���������������� �������� ���������� ����� ����� backend responses, �� � UI ��������� edit/delete ��� ��������� � ��-����������.
- ��� file fields ����������� `multipart/form-data`.
- Organization PDF reports are general organization activity reports. Do not attach them to collections or donor groups in frontend state.
- Donor group video reports are attached directly to `donor_group`; do not create extra frontend grouping unless the backend adds it later.
- ��� `401` ����������� refresh token flow, ��� `403` ����������� ���������� ����, ��� `400` ����������� field errors.

---

## Detailed Collections API

Base prefix: `/api/v1/collections/`.

## Endpoints

```http
GET /api/v1/collections/item-categories/
GET /api/v1/collections/item-categories/{id}/

GET    /api/v1/collections/user-items/
POST   /api/v1/collections/user-items/
GET    /api/v1/collections/user-items/{id}/
PATCH  /api/v1/collections/user-items/{id}/
DELETE /api/v1/collections/user-items/{id}/

GET    /api/v1/collections/collections/
POST   /api/v1/collections/collections/
GET    /api/v1/collections/collections/{id}/
PATCH  /api/v1/collections/collections/{id}/
DELETE /api/v1/collections/collections/{id}/

GET    /api/v1/collections/collection-items/
POST   /api/v1/collections/collection-items/
GET    /api/v1/collections/collection-items/{id}/
PATCH  /api/v1/collections/collection-items/{id}/
DELETE /api/v1/collections/collection-items/{id}/

GET    /api/v1/collections/branch-items/
POST   /api/v1/collections/branch-items/
GET    /api/v1/collections/branch-items/{id}/
PATCH  /api/v1/collections/branch-items/{id}/
DELETE /api/v1/collections/branch-items/{id}/

GET    /api/v1/collections/donor-groups/
POST   /api/v1/collections/donor-groups/
GET    /api/v1/collections/donor-groups/{id}/
PATCH  /api/v1/collections/donor-groups/{id}/
DELETE /api/v1/collections/donor-groups/{id}/
POST   /api/v1/collections/donor-groups/{id}/schedule-meeting-time/
POST   /api/v1/collections/donor-groups/{id}/schedule-meeting/
POST   /api/v1/collections/donor-groups/{id}/set-parameters-time/
POST   /api/v1/collections/donor-groups/{id}/set-parameters/

GET    /api/v1/collections/donor-group-members/
POST   /api/v1/collections/donor-group-members/
GET    /api/v1/collections/donor-group-members/{id}/
PATCH  /api/v1/collections/donor-group-members/{id}/
DELETE /api/v1/collections/donor-group-members/{id}/

GET    /api/v1/collections/donor-group-items/
POST   /api/v1/collections/donor-group-items/
GET    /api/v1/collections/donor-group-items/{id}/
PATCH  /api/v1/collections/donor-group-items/{id}/
DELETE /api/v1/collections/donor-group-items/{id}/

GET    /api/v1/collections/donor-group-video-reports/
GET    /api/v1/collections/donor-group-video-reports/?donor_group=1
POST   /api/v1/collections/donor-group-video-reports/
GET    /api/v1/collections/donor-group-video-reports/{id}/
PATCH  /api/v1/collections/donor-group-video-reports/{id}/
DELETE /api/v1/collections/donor-group-video-reports/{id}/

GET    /api/v1/collections/courier-profiles/
POST   /api/v1/collections/courier-profiles/
GET    /api/v1/collections/courier-profiles/{id}/
PATCH  /api/v1/collections/courier-profiles/{id}/
DELETE /api/v1/collections/courier-profiles/{id}/

GET    /api/v1/collections/meeting-place-proposals/
POST   /api/v1/collections/meeting-place-proposals/
GET    /api/v1/collections/meeting-place-proposals/{id}/
PATCH  /api/v1/collections/meeting-place-proposals/{id}/
DELETE /api/v1/collections/meeting-place-proposals/{id}/

GET    /api/v1/collections/polls/
POST   /api/v1/collections/polls/
GET    /api/v1/collections/polls/{id}/
PATCH  /api/v1/collections/polls/{id}/
DELETE /api/v1/collections/polls/{id}/
POST   /api/v1/collections/polls/{id}/repost/
POST   /api/v1/collections/polls/{id}/finalize/
POST   /api/v1/collections/polls/from-place-proposals/

GET    /api/v1/collections/poll-options/
POST   /api/v1/collections/poll-options/
GET    /api/v1/collections/poll-options/{id}/
PATCH  /api/v1/collections/poll-options/{id}/
DELETE /api/v1/collections/poll-options/{id}/

GET    /api/v1/collections/poll-votes/
POST   /api/v1/collections/poll-votes/
GET    /api/v1/collections/poll-votes/{id}/
PATCH  /api/v1/collections/poll-votes/{id}/
DELETE /api/v1/collections/poll-votes/{id}/
```

## Permissions

- Item categories: public read-only.
- User items: public read; authenticated users create their own items; only the owner updates or deletes.
- Collections: public read; active organization members create; the author or an active organization manager updates or deletes.
- Collection items: public read; the collection author or an active organization manager creates, updates, or deletes.
- Branch items: public read; only an active manager of the branch organization creates, updates, or deletes.
- Donor groups: public read; the collection author or an active organization manager creates, updates, or deletes.
- Donor group parameters time: the collection author or an active organization manager manually sets or updates the group's date/time through `set-parameters-time`. Legacy `schedule-meeting-time` remains available.
- Donor group parameters: the collection author or an active organization manager manually sets or updates the group's place and date/time through `set-parameters`. Legacy `schedule-meeting` remains available.
- Donor group members: public read; the collection author or an active organization manager manages members. Accepting a donor group invitation also creates membership.
- Donor group items: public read; the collection author or an active organization manager links user items and selected quantities.
- Donor group video reports: authenticated read for donor group members, the collection author, and active organization managers; donor group members upload; uploader or group manager edits/deletes.
- Invitations: use `/api/v1/communications/invitations/` with `target_type = "donor_group"`.
- Courier profiles: public read; authenticated users create their own profile; only the owner updates or deletes.
- Meeting place proposals: public read; donor group members create proposals; the proposal author, collection author, or organization manager updates or deletes.
- Polls: public read; donor group polls are managed by the collection author or organization manager; news polls are managed by the news author or organization manager.
- Poll finalization: collection author or organization manager chooses a `date` or `place` poll option with `POST /polls/{id}/finalize/`. This closes the poll and writes the selected date/place into `DonorGroupParameters`.
- Poll options: public read; only the corresponding poll manager creates, updates, or deletes options.
- Poll votes: authenticated users see and manage only their own votes; donor group polls accept votes only from donor group members.
- New open donor group polls create in-app notifications and push delivery tasks for donor group members.

## Payloads

User item:

```json
{
  "category": 1,
  "quantity": 2,
  "description": "Optional note"
}
```

User item responses include organizer selection aggregates:

```json
{
  "id": 1,
  "quantity": 7,
  "selected_quantity": 3,
  "available_quantity": 4
}
```

Pass `?collection=1` to scope `selected_quantity` and `available_quantity` to donor groups of a specific collection.

Collection:

```json
{
  "organization": 1,
  "branch": 1,
  "geodata": 1,
  "title": "Winter help",
  "description": "Warm clothes and blankets",
  "status": "draft",
  "starts_at": "2026-06-01T10:00:00+05:00",
  "ends_at": "2026-06-30T18:00:00+05:00"
}
```

Collection responses include frontend aggregates:

```json
{
  "items_count": 2,
  "quantity_required_total": 10,
  "quantity_selected_total": 3,
  "donor_groups_count": 1,
  "donor_group_members_count": 2,
  "donor_group_items_count": 1
}
```

Collection item:

```json
{
  "collection": 1,
  "category": 1,
  "quantity_required": 10,
  "description": "5 liter bottles preferred"
}
```

Collection item responses include `selected_quantity` and `remaining_quantity`, calculated from `DonorGroupItem` rows for the same collection/category.

Branch item:

```json
{
  "branch": 1,
  "category": 1,
  "description": "Accepted at this branch"
}
```

Donor group:

```json
{
  "collection": 1,
  "title": "Central pickup group"
}
```

Donor group responses include `parameters` when date/time/place parameters have been assigned:

```json
{
  "id": 1,
  "collection": 1,
  "created_by_member": 1,
  "title": "Central pickup group",
  "parameters": {
    "id": 1,
    "donor_group": 1,
    "geodata": 1,
    "street": "Lenina, 1",
    "description": "Main entrance",
    "starts_at": "2026-06-06T12:00:00+05:00",
    "ends_at": "2026-06-06T13:00:00+05:00",
    "finalized_by_member": 1,
    "finalized_at": "2026-05-09T12:00:00+05:00",
    "created_at": "2026-05-09T12:00:00+05:00",
    "updated_at": "2026-05-09T12:00:00+05:00"
  }
}
```

Set or update donor group parameters time only:

```http
POST /api/v1/collections/donor-groups/{id}/set-parameters-time/
```

```json
{
  "starts_at": "2026-06-06T12:00:00+05:00",
  "ends_at": "2026-06-06T13:00:00+05:00"
}
```

`starts_at` is required. `ends_at` is optional and cannot be earlier than `starts_at`. This endpoint does not require place data.

Parameter time assignment creates notifications for donor group members except the actor. Notification payload:

```json
{
  "target_type": "donor_group_parameters",
  "target_id": 1,
  "donor_group_id": 1,
  "event": "date_assigned"
}
```

Possible `event` values: `date_assigned`, `time_assigned`.

Set or update donor group parameters place and time:

```http
POST /api/v1/collections/donor-groups/{id}/set-parameters/
```

```json
{
  "geodata": 1,
  "street": "Lenina, 1",
  "description": "Main entrance",
  "starts_at": "2026-06-06T12:00:00+05:00",
  "ends_at": "2026-06-06T13:00:00+05:00"
}
```

`starts_at` is required. Provide at least one place field: `geodata`, `street`, or `description`. Reposting or finalizing polls is not required to set parameters.

Place and time assignment creates notifications for donor group members except the actor. Possible notification `payload.event` values: `date_assigned`, `time_assigned`, `place_assigned`.

Donor group invitation:

```json
{
  "target_type": "donor_group",
  "target_id": 1,
  "invited_user": 2,
  "send_email": false,
  "send_push": true
}
```

Donor group item:

```json
{
  "donor_group": 1,
  "user_item": 1,
  "quantity": 2
}
```

Donor group responses include `video_reports_count`.

Donor group video report:

```json
{
  "donor_group": 1,
  "title": "Pickup report",
  "description": "Optional note",
  "video": "<video file>"
}
```

Use `multipart/form-data`. Reports are attached directly to `donor_group`, without extra grouping.

Courier profile:

```json
{
  "car_name": "Lada Largus"
}
```

`CourierProfile` is a user/account extension internally. The endpoint remains under `/api/v1/collections/courier-profiles/` for compatibility.

Meeting place proposal:

```json
{
  "donor_group": 1,
  "geodata": 1,
  "street": "Lenina, 1",
  "description": "Main entrance"
}
```

Poll:

```json
{
  "donor_group": 1,
  "news": null,
  "title": "Pickup time",
  "description": "",
  "kind": "date",
  "status": "open",
  "closes_at": "2026-06-01T10:00:00+05:00"
}
```

`kind` values: `text`, `date`, `place`. `status` values: `draft`, `open`, `closed`.

Poll responses also expose finalization fields:

```json
{
  "finalized_option": 1,
  "finalized_by_member": 1,
  "finalized_at": "2026-05-09T12:00:00+05:00"
}
```

Poll option:

```json
{
  "poll": 1,
  "text": "Saturday",
  "starts_at": "2026-06-06T12:00:00+05:00",
  "ends_at": null,
  "geodata": null,
  "place_street": "",
  "place_description": "",
  "sort_order": 0
}
```

For `text` polls, `text` is required. For `date` polls, `starts_at` is required. For `place` polls, provide at least one place field: `geodata`, `place_street`, or `place_description`.

Vote:

```json
{
  "poll": 1,
  "option": 1
}
```

Repost poll without zero-vote options:

```http
POST /api/v1/collections/polls/{id}/repost/
```

```json
{
  "title": "Pickup time, second round",
  "status": "open",
  "closes_at": "2026-06-02T10:00:00+05:00"
}
```

Finalize a donor group date/place poll option into `DonorGroupParameters`:

```http
POST /api/v1/collections/polls/{id}/finalize/
```

```json
{
  "option": 1
}
```

For `date` polls, the selected option writes `starts_at`/`ends_at` to `DonorGroupParameters`. For `place` polls, it writes `geodata`/`place_street`/`place_description`. The poll becomes `closed`; parameter update notifications are created for donor group members except the actor.

Create a place poll from donor group proposals:

```http
POST /api/v1/collections/polls/from-place-proposals/
```

```json
{
  "donor_group": 1,
  "title": "Meeting place",
  "description": "",
  "status": "open",
  "proposal_ids": [1, 2, 3]
}
```

If `proposal_ids` is omitted, all proposals from the donor group become poll options.

---

## Detailed Push Notifications API

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

---

## API Testing Flow

## ������� ���������

������� URL ��� ���������� backend:

```text
http://127.0.0.1:8000
```

�������� � Postman environment:

| Variable | Initial value |
| --- | --- |
| `base_url` | `http://127.0.0.1:8000` |
| `access_token` | ����� |
| `refresh_token` | ����� |
| `region_id` | id �������, ������� ������������ ����� `import_russia_locations`, seed-�������� ��� �����-������� |
| `city_id` | id ������, ������� ������������ ����� `import_russia_locations`, seed-�������� ��� �����-������� |
| `geodata_id` | ����� |
| `organization_id` | ����� |
| `event_id` | ����� |

��� �������������� �������� ����������� header:

```text
Authorization: Bearer {{access_token}}
```

## 1. ����������� � ����

### �����������

```http
POST {{base_url}}/api/v1/accounts/register/
Content-Type: application/json
```

```json
{
  "username": "manager",
  "email": "manager@example.com",
  "password": "StrongPassword123!",
  "password_confirm": "StrongPassword123!",
  "first_name": "Manager",
  "last_name": "User"
}
```

����� ����������� ������������ ������ ����������� email ����� �� ������.

### ������������� email

```http
POST {{base_url}}/api/v1/accounts/verify-email/
Content-Type: application/json
```

```json
{
  "email": "manager@example.com",
  "code": "123456"
}
```

### �����

```http
POST {{base_url}}/api/v1/accounts/login/
Content-Type: application/json
```

```json
{
  "email": "manager@example.com",
  "password": "StrongPassword123!"
}
```

� Tests ������� Postman ����� ��������� ������:

```javascript
const json = pm.response.json();
pm.environment.set("access_token", json.access);
pm.environment.set("refresh_token", json.refresh);
```

## 2. ������ � ���������

��������� ��������� � ����� ������ `common`.

### �������� ������ ��������

```http
GET {{base_url}}/api/v1/common/regions/
```

������� ������ ��������� ����� ��������� API. ��� ������ �������:

```http
GET {{base_url}}/api/v1/common/regions/?search=sver
```

### �������� ������ �������

```http
GET {{base_url}}/api/v1/common/cities/
```

������ ������ ��������� ����� ��������� API. ��� ��������� ����� `import_russia_locations`, seed-�������� ��� ���������������� backend-�������. � ������ `region` - id �������, `region_name` - �������� ������� ��� �����������.

� dev/test ���� ����� migration �������� �������� ����� ������� �� ������ ������ ������: Kaliningrad, Murmansk, Saint Petersburg, Moscow, Sochi, Yekaterinburg, Novosibirsk, Yakutsk, Vladivostok, Petropavlovsk-Kamchatsky.

### ����� ����� ��� autocomplete

```http
GET {{base_url}}/api/v1/common/cities/?search=vlad
```

����� �������� �� `name`, `region_name`, `country_code`. ��� ���������� ������ ��������� `id` � ���������� `city_id`.

�������� `id` ������� ������ �� ������ � ��������� ��� � `city_id`.

### ������� geodata

��� ���� ��������������. ����� ������� ������ �����, ������ �����, ������ ���������� ��� ����� ����������.

```http
POST {{base_url}}/api/v1/common/geodata/
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

```json
{
  "city": "{{city_id}}",
  "street": "��. ������, 1",
  "latitude": "56.838011",
  "longitude": "60.597465"
}
```

��������� `id` � `geodata_id`.

## 3. ��������� ������������

```http
PATCH {{base_url}}/api/v1/accounts/profile/
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

```json
{
  "geodata": "{{geodata_id}}"
}
```

��������:

```http
GET {{base_url}}/api/v1/accounts/profile/
Authorization: Bearer {{access_token}}
```

## 4. ��������� �����������

����������� ������:

- `geodata` - ������ �� `/api/v1/common/geodata/`;
- `is_online` - ���� ������-�����������;
- `city` - ������ ��������� ����, ���� ��������� ��� �������� �������������;
- `max_url`, `vk_url`, `website_url` - ������ �� ���������� ����� ��� �������� �����������.

```http
POST {{base_url}}/api/v1/organizations/events/
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

```json
{
  "title": "���� �����",
  "content": "�������� �����������",
  "category": 1,
  "organization": "{{organization_id}}",
  "geodata": "{{geodata_id}}",
  "is_online": false,
  "starts_at": "2026-06-01T10:00:00+05:00",
  "max_url": "https://max.example.com/event-post",
  "vk_url": "https://vk.com/event-post",
  "website_url": "https://example.com/events/help"
}
```

��� ������-����������� ����� ���������:

```json
{
  "title": "������-������� ���������",
  "content": "������ �������",
  "category": 1,
  "organization": "{{organization_id}}",
  "is_online": true,
  "starts_at": "2026-06-01T10:00:00+05:00"
}
```

`geodata` ����� �� ���������.

## 5. �������� ������

### ���������� ������

```http
POST {{base_url}}/api/v1/common/geodata/
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

```json
{
  "latitude": "91.000000",
  "longitude": "60.000000"
}
```

��������� ���������: `400 Bad Request`, ������ �� ���� `latitude`.

### ���������� �������

```json
{
  "latitude": "56.000000",
  "longitude": "181.000000"
}
```

��������� ���������: `400 Bad Request`, ������ �� ���� `longitude`.
