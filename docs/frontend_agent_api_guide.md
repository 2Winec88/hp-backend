# Frontend Agent API Guide

Документ описывает frontend-facing API проекта. Источник истины для точной схемы также доступен в OpenAPI:

- `GET /api/schema/`
- `GET /api/docs/`
- `GET /api/redoc/`

Базовый REST-префикс: `/api/v1/`.

Для авторизованных запросов используйте:

```text
Authorization: Bearer <access_token>
```

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

После регистрации пользователь неактивен до подтверждения email. Код отправляется backend-ом через Celery.

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

Response содержит `access`, `refresh`, `user`.

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

`common` содержит переиспользуемые справочники и геоданные.

### Regions

```http
GET /api/v1/common/regions/
GET /api/v1/common/regions/?search=сверд
GET /api/v1/common/regions/{id}/
```

Регионы read-only для публичного API. Создание, редактирование и удаление через frontend запрещены.

Response item:

```json
{
  "id": 1,
  "name": "Свердловская область",
  "geoname_id": null,
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
GET /api/v1/common/cities/?search=екат
GET /api/v1/common/cities/?search=екат&limit=10
GET /api/v1/common/cities/{id}/
```

Города read-only для публичного API. Для выбора города в адресе мероприятия или филиала используйте autocomplete через `search`. Backend ищет по названию города, названию региона и коду страны, приоритизирует совпадение с началом названия города и возвращает до `limit` записей. `limit` optional, по умолчанию `20`, максимум `100`.

Response item:

```json
{
  "id": 1,
  "name": "Екатеринбург",
  "geoname_id": null,
  "latitude": "56.838011",
  "longitude": "60.597465",
  "country_code": "RU",
  "region": 1,
  "region_name": "Свердловская область",
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

Все поля optional. Можно указать только город, только улицу, только координаты или пустую заготовку.

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
  "city_name": "Екатеринбург",
  "region_name": "Свердловская область",
  "street": "Lenina, 1",
  "latitude": "56.838011",
  "longitude": "60.597465",
  "created_at": "...",
  "updated_at": "..."
}
```

Coordinates validation: `latitude` от `-90` до `90`, `longitude` от `-180` до `180`.

## Organizations

### Organizations

```http
GET   /api/v1/organizations/organizations/
GET   /api/v1/organizations/organizations/{id}/
PATCH /api/v1/organizations/organizations/{id}/
```

Читать могут все. Редактировать может активный менеджер организации.

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

Организации создаются через заявку на регистрацию, а не прямым `POST /organizations/organizations/`.

### Registration Requests

```http
GET  /api/v1/organizations/organization-registration-requests/
POST /api/v1/organizations/organization-registration-requests/
GET  /api/v1/organizations/organization-registration-requests/{id}/
POST /api/v1/organizations/organization-registration-requests/{id}/approve/
POST /api/v1/organizations/organization-registration-requests/{id}/reject/
```

`POST` заявки отправляйте как `multipart/form-data`, потому что нужны документы.

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

Пользователь видит только свои заявки. Staff superuser видит все и может approve/reject.

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

Доступ только менеджеру организации. `DELETE` мягко исключает участника: запись остается, но `is_active=false`. Менеджер не может исключить себя и нельзя исключить последнего менеджера.

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

Категории read-only для frontend.

### Branches

```http
GET    /api/v1/organizations/branches/
GET    /api/v1/organizations/branches/?organization=1
POST   /api/v1/organizations/branches/
GET    /api/v1/organizations/branches/{id}/
PATCH  /api/v1/organizations/branches/{id}/
DELETE /api/v1/organizations/branches/{id}/
```

Филиалы принадлежат организации и используют `common.GeoData` для геолокации. Читать могут все. Создавать, редактировать и удалять филиалы может только активный менеджер организации. `organization` нельзя менять после создания.

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

Филиал может иметь несколько изображений через отдельный `branch-images` ресурс. Для `image` используйте `multipart/form-data`. Управлять изображениями может только активный менеджер организации филиала. Читать могут все. `branch` нельзя менять после создания.

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

Читать могут все. Создавать может только активный участник организации. Редактировать/удалять может автор или активный менеджер организации.

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

`ends_at` не может быть раньше `starts_at`. `geodata = null` не означает автоматически online; используйте отдельное поле `is_online`.

Старое текстовое поле `city` оставлено для совместимости. Новые экраны должны использовать `geodata`.

### Event Images

```http
GET    /api/v1/organizations/event-images/
GET    /api/v1/organizations/event-images/?event=1
POST   /api/v1/organizations/event-images/
GET    /api/v1/organizations/event-images/{id}/
PATCH  /api/v1/organizations/event-images/{id}/
DELETE /api/v1/organizations/event-images/{id}/
```

Для создания используйте `multipart/form-data`.

Fields:

```text
event
image
alt_text
sort_order
```

`event` нельзя менять после создания.

### News

```http
GET    /api/v1/organizations/news/
GET    /api/v1/organizations/news/?organization=1
POST   /api/v1/organizations/news/
GET    /api/v1/organizations/news/{id}/
PATCH  /api/v1/organizations/news/{id}/
DELETE /api/v1/organizations/news/{id}/
```

Новости принадлежат организации, не мероприятию. Detail-запрос увеличивает `views_count`.

Payload:

```json
{
  "organization": 1,
  "title": "News title",
  "text": "News text",
  "comments": ""
}
```

Для одиночного legacy-поля `image` используйте `multipart/form-data`. Для галереи используйте отдельный `news-images` endpoint. `organization` нельзя менять после создания. Response новости содержит read-only поля `images`, `images_count`, `comments_count` и `views_count`.

Alias для обратной совместимости:

```http
/api/v1/organizations/event-news/
```

Новый frontend должен использовать `/news/`.

### News Images

```http
GET    /api/v1/organizations/news-images/
GET    /api/v1/organizations/news-images/?news=1
POST   /api/v1/organizations/news-images/
GET    /api/v1/organizations/news-images/{id}/
PATCH  /api/v1/organizations/news-images/{id}/
DELETE /api/v1/organizations/news-images/{id}/
```

Новость может иметь несколько изображений через отдельный `news-images` ресурс. Для `image` используйте `multipart/form-data`. Добавлять, редактировать и удалять изображения может автор новости или активный менеджер организации. Читать могут все. `news` нельзя менять после создания.

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

Создавать комментарии может любой авторизованный пользователь. Редактировать/удалять может автор комментария или активный менеджер организации новости. `news` нельзя менять после создания.

Payload:

```json
{
  "news": 1,
  "text": "Comment text"
}
```

## Communications

### Notifications

```http
GET  /api/v1/communications/notifications/
GET  /api/v1/communications/notifications/?is_read=false
POST /api/v1/communications/notifications/
GET  /api/v1/communications/notifications/{id}/
POST /api/v1/communications/notifications/{id}/mark-read/
POST /api/v1/communications/notifications/mark-all-read/
```

Пользователь видит только свои уведомления.

Create payload:

```json
{
  "recipient": 2,
  "type": "text",
  "title": "Title",
  "body": "Body",
  "payload": {},
  "send_email": false
}
```

Allowed create types: `text`, `message`, `system`. Invitation notifications создаются через invitations API.

### Invitations

```http
GET  /api/v1/communications/invitations/
POST /api/v1/communications/invitations/
GET  /api/v1/communications/invitations/{id}/
POST /api/v1/communications/invitations/{id}/accept/
POST /api/v1/communications/invitations/{id}/decline/
POST /api/v1/communications/invitations/{id}/cancel/
```

Пользователь видит приглашения, где он приглашенный или приглашающий.

Create payload for organization invitation:

```json
{
  "target_type": "organization",
  "target_id": 1,
  "invited_user": 2,
  "role": "member",
  "send_email": true
}
```

Allowed organization roles: `manager`, `member`. Принимать приглашение может только invited user. Отменять может пользователь, который имеет право приглашать в target.

Сейчас поддержан `target_type="organization"`. Donor group invitations будут добавлены после реализации donor groups в `collections`.

## WebSocket

Channels подключен. Сейчас frontend-facing WebSocket endpoint:

```text
ws://<host>/ws/communications/health/
wss://<host>/ws/communications/health/
```

JWT middleware принимает token из query param:

```text
?token=<access_token>
```

или из header:

```text
Authorization: Bearer <access_token>
```

Текущий endpoint служит health-check. Полноценные чаты и live notifications будут добавляться отдельно. REST и база остаются источником истины; WebSocket не должен быть единственным способом получить важные данные.

## Collections

Приложение `collections` пока не имеет публичного REST API. В коде есть начальные модели справочника вещей, но сборы, донорские группы, голосования, передачи вещей и видеоотчеты еще не реализованы как frontend API.

## Frontend Rules

- Не создавайте регионы и города через public API; используйте read-only справочники и autocomplete.
- Для новых географических экранов используйте `GeoData`, а не отдельные текстовые поля.
- Не выводите мероприятие online только по `geodata=null`; используйте `is_online`.
- Для организационного контента проверяйте права через backend responses, но в UI скрывайте edit/delete для неавторов и не-менеджеров.
- Для file fields используйте `multipart/form-data`.
- При `401` отправляйте refresh token flow, при `403` показывайте отсутствие прав, при `400` показывайте field errors.
