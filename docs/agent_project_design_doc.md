# Agent Project Design Doc

Этот документ предназначен для агента, который продолжает backend-разработку проекта. Он описывает не только продуктовую идею, но и фактическое состояние репозитория, принятые архитектурные решения, API-контракты и правила дальнейшей реализации.

## 1. Суть проекта

Проект `hp-backend` — backend веб-платформы для координации гуманитарной помощи.

Платформа нужна для:

- регистрации пользователей и организаций;
- регистрации и проверки организаций;
- управления членством в организациях;
- создания сборов гуманитарной помощи;
- добавления вещей пользователями;
- формирования донорских групп;
- координации передачи вещей;
- организации чатов и уведомлений;
- публикации мероприятий и новостей организаций;
- хранения филиалов организаций и мест передачи;
- хранения видеоотчётов о передаче вещей.

Важное бизнес-решение: платформа не делает автоматическое сопоставление помощи. Координация выполняется вручную пользователями, организациями, организаторами сборов и курьерами-добровольцами.

## 2. Технологический стек

- Python `>=3.13`
- Django `>=6.0.4`
- Django REST Framework
- PostgreSQL
- Redis
- Celery
- Django Channels
- Daphne
- channels-redis
- Simple JWT
- drf-spectacular
- Docker
- Nginx
- uv

Проект — модульный монолит. Все домены живут в одном Django-проекте, но разделены по приложениям в `apps/`.

## 3. Основные приложения

### `apps.accounts`

Отвечает за:

- кастомную модель пользователя;
- регистрацию;
- email verification;
- login/logout;
- JWT;
- профиль пользователя;
- заготовку геоданных пользователя.

Ключевые модели:

- `User`
- `EmailVerificationCode`

`User`:

- наследуется от `AbstractUser`;
- использует `email` как `USERNAME_FIELD`;
- имеет `avatar`, `bio`, `is_email_verified`;
- имеет nullable `geodata` на `common.GeoData`.

Ключевые endpoints:

- `POST /api/v1/accounts/register/`
- `POST /api/v1/accounts/verify-email/`
- `POST /api/v1/accounts/login/`
- `POST /api/v1/accounts/logout/`
- `GET/PATCH/PUT /api/v1/accounts/profile/`
- `POST /api/v1/accounts/token/refresh/`

Email verification отправляется через Celery-задачу `send_email_verification_code`.

### `apps.common`

Общий модуль. Здесь должны жить переиспользуемые сущности, не принадлежащие одному бизнес-домену.

Принятое правило: всё общее и потенциально переиспользуемое добавлять сюда, а не размазывать по доменным приложениям.

Сейчас содержит географические сущности:

- `Region`
- `City`
- `GeoData`

`Region`:

- справочник регионов;
- будет наполняться через GeoNames;
- не создаётся через публичный API;
- поддерживает autocomplete через `GET /api/v1/common/regions/?search=...`;
- содержит `name`, `geoname_id`, координаты региона, `country_code`.

`City`:

- справочник городов;
- будет наполняться через GeoNames;
- не создаётся через публичный API;
- поддерживает autocomplete через `GET /api/v1/common/cities/?search=...`;
- содержит `name`, `geoname_id`, координаты города, `country_code`, ссылку на `Region`.

`GeoData`:

- переиспользуемая геолокация;
- содержит ссылку на `City`, `street`, `latitude`, `longitude`;
- все поля необязательные;
- можно сохранить только город, только улицу, только координаты или пустую заготовку.

Ключевые endpoints:

- `GET /api/v1/common/cities/`
- `GET /api/v1/common/cities/?search=...`
- `GET /api/v1/common/cities/{id}/`
- `GET /api/v1/common/regions/`
- `GET /api/v1/common/regions/?search=...`
- `GET /api/v1/common/regions/{id}/`
- `GET/POST/PATCH/DELETE /api/v1/common/geodata/`

Важно: `Region` и `City` read-only для публичного API. Регионы и города должны заводиться импортом из GeoNames или административным backend-процессом.

В dev/test базу через migration загружен небольшой тестовый набор городов из разных частей России: Kaliningrad, Murmansk, Saint Petersburg, Moscow, Sochi, Yekaterinburg, Novosibirsk, Yakutsk, Vladivostok, Petropavlovsk-Kamchatsky.

### `apps.organizations`

Отвечает за:

- организации;
- участников организаций;
- заявки на регистрацию организаций;
- мероприятия организаций;
- новости организаций;
- комментарии к новостям;
- будущие филиалы организаций.

Ключевые модели:

- `Category`
- `Organization`
- `OrganizationMember`
- `Event`
- `EventImage`
- `OrganizationNews`
- `OrganizationNewsComment`
- `OrganizationRegistrationRequest`

`Organization`:

- юридическая и контактная информация;
- `created_by`;
- ссылки организации: `max_url`, `vk_url`, `website_url`;
- после одобрения заявки создатель становится `OrganizationMember` с ролью `manager`.

`OrganizationMember`:

- связывает пользователя и организацию;
- роли: `manager`, `member`;
- уникальность: один membership на пару organization/user.

`Event`:

- организационный контент;
- принадлежит `Organization`;
- создаётся участником организации;
- имеет `created_by_member`;
- имеет `geodata` на `common.GeoData`;
- имеет `is_online`;
- старое текстовое поле `city` пока оставлено для совместимости, но новые экраны должны использовать `geodata`;
- имеет внешние ссылки на конкретные посты/страницы мероприятия: `max_url`, `vk_url`, `website_url`.

`OrganizationNews`:

- новость организации, не мероприятия;
- принадлежит `Organization`;
- создаётся участником организации;
- имеет `created_by_member`;
- имеет `comments` как текстовое поле и отдельные `OrganizationNewsComment`;
- имеет `views_count`;
- detail endpoint увеличивает `views_count`.

`OrganizationNewsComment`:

- отдельные комментарии к новости;
- может быть создан авторизованным пользователем;
- автор или менеджер организации может редактировать/удалять.

Ключевые endpoints:

- `GET/DELETE /api/v1/organizations/members/`
- `GET/POST/PATCH/DELETE /api/v1/organizations/events/`
- `GET/POST/PATCH/DELETE /api/v1/organizations/news/`
- `GET/POST/PATCH/DELETE /api/v1/organizations/news-comments/`
- `GET/POST /api/v1/organizations/organization-registration-requests/`
- `POST /api/v1/organizations/organization-registration-requests/{id}/approve/`
- `POST /api/v1/organizations/organization-registration-requests/{id}/reject/`

`/api/v1/organizations/event-news/` оставлен как alias на новости организации для обратной совместимости. Новый frontend должен использовать `/news/`.

Права:

- читать мероприятия и новости могут все;
- создавать может авторизованный пользователь, являющийся участником организации;
- автор может редактировать/удалять свой контент;
- менеджер организации может редактировать/удалять контент участников своей организации;
- менеджер может исключать участников через members API;
- менеджер не может удалить самого себя из организации;
- нельзя удалить последнего менеджера организации.

### `apps.communications`

Отвечает за:

- уведомления;
- приглашения;
- websocket routing;
- JWT auth для websocket;
- будущие чаты организаций и донорских групп.

Ключевые модели:

- `Notification`
- `Invitation`

`Notification`:

- универсальное in-app уведомление;
- типы: `invitation`, `message`, `system`, `text`;
- хранит `recipient`, `actor`, `title`, `body`, `payload`, `is_read`, `email_sent_at`;
- может использоваться не только для приглашений, но и для текстов, системных событий, сообщений.

`Invitation`:

- универсальное приглашение;
- использует `ContentType` + `object_id`, чтобы приглашать в разные типы целей;
- сейчас поддержан `target_type="organization"`;
- позже добавить `donor_group` через новый handler;
- статусы: `pending`, `accepted`, `declined`, `expired`, `cancelled`;
- связано с `Notification`;
- при accept для организации создаёт `OrganizationMember`.

Ключевые endpoints:

- `GET/POST /api/v1/communications/notifications/`
- `POST /api/v1/communications/notifications/{id}/mark-read/`
- `POST /api/v1/communications/notifications/mark-all-read/`
- `GET/POST /api/v1/communications/invitations/`
- `POST /api/v1/communications/invitations/{id}/accept/`
- `POST /api/v1/communications/invitations/{id}/decline/`
- `POST /api/v1/communications/invitations/{id}/cancel/`

Celery:

- `send_notification_delivery(notification_id)` отправляет внешнюю доставку, сейчас email.
- Уведомление и приглашение сохраняются синхронно в БД.
- Email отправляется через `transaction.on_commit(...)`.

WebSocket:

- ASGI подключён через Channels.
- Есть health endpoint: `/ws/communications/health/`.
- JWT middleware принимает token из query param `?token=...` или header `Authorization: Bearer ...`.

Важно: бизнес-логика приглашений не зависит от websocket. WebSocket — только realtime-слой.

### `apps.collections`

Пока реализован только начальный справочник вещей.

Ключевые модели:

- `ItemCategory`
- `Item`

Будущий главный бизнес-модуль должен покрыть:

- сборы гуманитарной помощи;
- вещи пользователей;
- донорские группы;
- голосования;
- передачу вещей;
- видеоотчёты.

Ожидаемый доменный сценарий:

1. Организация создаёт сбор с перечнем необходимых вещей.
2. Пользователь добавляет свои вещи в сбор.
3. Формируется донорская группа или выбирается самостоятельная передача через филиал.
4. Для донорской группы создаётся чат и голосования.
5. Курьер-доброволец принимает вещи.
6. Загружается видеоотчёт.
7. Участники получают уведомления.

## 4. Роли проекта

### Пользователь

- просматривает сборы;
- добавляет свои вещи;
- участвует в донорских группах;
- передаёт вещи через филиалы организаций;
- получает уведомления;
- может иметь `geodata` в профиле.

### Организатор

- член организации, создавший сбор;
- управляет своим сбором;
- координирует донорскую группу;
- создаёт голосования;
- просматривает видеоотчёты.

### Менеджер организации

- управляет организацией;
- приглашает участников;
- исключает участников;
- модерирует организационный контент;
- создаёт мероприятия;
- управляет филиалами организации.

### Курьер-доброволец

- принимает вещи;
- подтверждает передачу;
- загружает видеоотчёты.

### Администратор

- проверяет заявки на регистрацию организаций;
- модерирует платформу;
- управляет контентом;
- блокирует пользователей.

## 5. Геоданные

Архитектурное решение: геоданные не должны жить отдельными полями в каждой модели. Они вынесены в `common.GeoData`.

Использование сейчас:

- `User.geodata`
- `Event.geodata`

Ожидаемое использование позже:

- филиалы организаций;
- точки передачи вещей;
- варианты места в голосованиях донорской группы;
- адреса самостоятельной передачи через филиал.

`is_online` остаётся на сущности мероприятия. Не выводить онлайн только по `geodata = null`: отсутствие геоданных может означать незаполненное место, черновик или офлайн без точного адреса.

Правила:

- `City` — read-only API, импортируется из GeoNames.
- `GeoData` можно создавать через API.
- `latitude` допустима от `-90` до `90`.
- `longitude` допустима от `-180` до `180`.
- Все поля `GeoData` optional.

## 6. API-префиксы

Основной REST API:

- `/api/v1/accounts/`
- `/api/v1/common/`
- `/api/v1/communications/`
- `/api/v1/organizations/`

Документация OpenAPI:

- `/api/schema/`
- `/api/docs/`
- `/api/redoc/`

Debug toolbar в `DEBUG`:

- `/__debug__/`

## 7. Асинхронность

Celery используется для фоновых задач:

- email verification;
- email-доставка уведомлений;
- будущие системные фоновые задачи.

Правило: бизнес-факт сохраняется синхронно в БД, внешняя доставка уходит в Celery после `transaction.on_commit`.

Пример:

```python
with transaction.atomic():
    invitation = Invitation.objects.create(...)
    notification = Notification.objects.create(...)

transaction.on_commit(
    lambda: send_notification_delivery.delay(notification.pk)
)
```

## 8. Realtime

Channels подключён, но не должен быть фундаментом бизнес-логики.

Использовать websocket для:

- live notifications;
- чатов организации;
- чатов донорской группы;
- presence/typing позже, если потребуется.

Не использовать websocket как единственный источник данных. Всё важное должно сохраняться в БД и читаться через REST.

## 9. Docker и инфраструктура

Docker compose содержит:

- PostgreSQL
- Redis
- web
- nginx
- celery
- mailpit

Nginx настроен на WebSocket upgrade.

Redis используется:

- Celery broker/result backend;
- Channels layer.

## 10. Тестирование

Основные команды:

```bash
uv run python manage.py check
uv run python manage.py test apps.common apps.accounts apps.organizations
uv run python manage.py test apps.communications
```

Для проверки миграций:

```bash
uv run python manage.py makemigrations --check --dry-run
```

Текущие тесты покрывают:

- registration/email verification/login;
- profile geodata;
- common City/GeoData API;
- organization registration request approve/reject;
- organization membership admin;
- event/news manager permissions;
- organization news comments/views;
- communications notifications/invitations;
- websocket health endpoint.

## 11. Документация в `docs`

- `agent_project_design_doc.md` — этот агентский диздок.
- `frontend_agent_api_guide.md` — общий frontend-facing API guide по всем текущим endpoints.
- `postman_api_testing_guide.md` — инструкция для Postman.
- `frontend_agent_geodata_instructions.md` — инструкция для frontend-агента по geodata.
- `accounts_views_diagram.md` — диаграмма views модуля accounts.

## 12. Важные архитектурные решения

1. `common` — место для всего общего и переиспользуемого.
2. Города не создаются через публичный API. Источник городов — GeoNames.
3. `GeoData` — общая модель местоположения.
4. `is_online` — свойство мероприятия, не свойство геоданных.
5. Организационные новости принадлежат организации, не мероприятию.
6. Организационный контент должен иметь `organization` и `created_by_member`.
7. Для организационного контента использовать общий permission: автор или менеджер организации.
8. Уведомления универсальны и не завязаны только на приглашения.
9. Приглашения универсальны через `ContentType` и handler registry.
10. Сохранение бизнес-данных синхронное, внешняя доставка через Celery.
11. WebSocket — realtime-слой, REST/БД — источник истины.

## 13. Что реализовывать дальше

Приоритетные направления:

1. Филиалы организаций.
   - Использовать `GeoData`.
   - Добавить описание, контакты, изображения, график работы.
   - Менеджеры организации управляют филиалами.

2. Полноценный `collections`.
   - Сборы гуманитарной помощи.
   - Позиции необходимых вещей.
   - Вещи пользователей.
   - Донорские группы.
   - Голосования.
   - Передачи вещей.
   - Видеоотчёты.

3. Чаты.
   - Чат организации.
   - Чат донорской группы.
   - Доступ только участникам соответствующего контекста.
   - REST history + websocket realtime.

4. Donor group invitations.
   - Добавить handler в `communications.invitation_handlers`.
   - Не переписывать общий invitation API.

5. GeoNames import.
   - Реализовать management command.
   - Загружать города в `common.City`.
   - Не открывать публичный POST для городов.

## 14. Предупреждения для агента

- Не удалять старые alias endpoints без явного решения пользователя.
- Не смешивать отсутствие `geodata` с онлайн-форматом.
- Не создавать отдельные city/address поля в новых доменах, если можно использовать `GeoData`.
- Не отправлять email/внешние уведомления до commit транзакции.
- Не делать websocket единственным способом получить уведомление или сообщение.
- Не откатывать незнакомые изменения в рабочем дереве.
- Перед изменениями в моделях всегда создавать миграции и проверять `makemigrations --check --dry-run`.
