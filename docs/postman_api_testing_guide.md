# Руководство по тестированию API через Postman

## Базовые настройки

Базовый URL для локального backend:

```text
http://127.0.0.1:8000
```

Создайте в Postman environment:

| Variable | Initial value |
| --- | --- |
| `base_url` | `http://127.0.0.1:8000` |
| `access_token` | пусто |
| `refresh_token` | пусто |
| `region_id` | id региона, заранее загруженного из GeoNames |
| `city_id` | id города, заранее загруженного из GeoNames |
| `geodata_id` | пусто |
| `organization_id` | пусто |
| `event_id` | пусто |

Для авторизованных запросов используйте header:

```text
Authorization: Bearer {{access_token}}
```

## 1. Регистрация и вход

### Регистрация

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

После регистрации пользователь должен подтвердить email кодом из письма.

### Подтверждение email

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

### Логин

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

В Tests вкладке Postman можно сохранить токены:

```javascript
const json = pm.response.json();
pm.environment.set("access_token", json.access);
pm.environment.set("refresh_token", json.refresh);
```

## 2. Города и геоданные

Геоданные находятся в общем модуле `common`.

### Получить список регионов

```http
GET {{base_url}}/api/v1/common/regions/
```

Регионы нельзя создавать через публичный API. Для поиска региона:

```http
GET {{base_url}}/api/v1/common/regions/?search=sver
```

### Получить список городов

```http
GET {{base_url}}/api/v1/common/cities/
```

Города нельзя создавать через публичный API. Они заводятся через импорт из GeoNames или через административный backend-процесс. В ответе `region` - id региона, `region_name` - название региона для отображения.

В dev/test базу через migration загружен тестовый набор городов из разных частей России: Kaliningrad, Murmansk, Saint Petersburg, Moscow, Sochi, Yekaterinburg, Novosibirsk, Yakutsk, Vladivostok, Petropavlovsk-Kamchatsky.

### Найти город для autocomplete

```http
GET {{base_url}}/api/v1/common/cities/?search=vlad
```

Поиск работает по `name`, `region_name`, `country_code`. Для выбранного города сохраните `id` в переменную `city_id`.

Возьмите `id` нужного города из ответа и сохраните его в `city_id`.

### Создать geodata

Все поля необязательные. Можно указать только город, только улицу, только координаты или любую комбинацию.

```http
POST {{base_url}}/api/v1/common/geodata/
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

```json
{
  "city": "{{city_id}}",
  "street": "ул. Ленина, 1",
  "latitude": "56.838011",
  "longitude": "60.597465"
}
```

Сохраните `id` в `geodata_id`.

## 3. Геоданные пользователя

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

Проверка:

```http
GET {{base_url}}/api/v1/accounts/profile/
Authorization: Bearer {{access_token}}
```

## 4. Геоданные мероприятия

Мероприятие хранит:

- `geodata` - ссылка на `/api/v1/common/geodata/`;
- `is_online` - флаг онлайн-мероприятия;
- `city` - старое текстовое поле, пока оставлено для обратной совместимости;
- `max_url`, `vk_url`, `website_url` - ссылки на конкретные посты или страницу мероприятия.

```http
POST {{base_url}}/api/v1/organizations/events/
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

```json
{
  "title": "Сбор вещей",
  "content": "Описание мероприятия",
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

Для онлайн-мероприятия можно отправить:

```json
{
  "title": "Онлайн-встреча волонтёров",
  "content": "Созвон команды",
  "category": 1,
  "organization": "{{organization_id}}",
  "is_online": true,
  "starts_at": "2026-06-01T10:00:00+05:00"
}
```

`geodata` можно не указывать.

## 5. Проверки ошибок

### Невалидная широта

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

Ожидаемый результат: `400 Bad Request`, ошибка по полю `latitude`.

### Невалидная долгота

```json
{
  "latitude": "56.000000",
  "longitude": "181.000000"
}
```

Ожидаемый результат: `400 Bad Request`, ошибка по полю `longitude`.
