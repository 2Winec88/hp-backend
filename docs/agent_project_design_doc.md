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
- `CourierProfile`

`User`:

- наследуется от `AbstractUser`;
- использует `email` как `USERNAME_FIELD`;
- имеет `avatar`, `bio`, `is_email_verified`;
- имеет nullable `geodata` на `common.GeoData`.

`CourierProfile`:

- профиль пользователя как курьера-добровольца;
- находится в `apps.accounts`, потому что является расширением пользователя;
- сейчас хранит `car_name`;
- API для обратной совместимости остаётся в `/api/v1/collections/courier-profiles/`;
- физическая таблица сохранена как `collections_courierprofile`, чтобы перенос модели не терял существующие данные.

Ключевые endpoints:

- `POST /api/v1/accounts/register/`
- `POST /api/v1/accounts/verify-email/`
- `POST /api/v1/accounts/login/`
- `POST /api/v1/accounts/logout/`
- `GET/PATCH/PUT /api/v1/accounts/profile/`
- `POST /api/v1/accounts/token/refresh/`

Email verification отправляется через Celery-задачу `send_email_verification_code`.

### `apps.common`

Current geodata note, 2026-05-08:

- `Region` and `City` no longer store `geoname_id`.
- Current production import path is the Russian JSON dataset handled by `import_russia_locations`.
- `Region` and `City` remain read-only in public API.
- `GeoData` is still the reusable location record for users, branches, events, and collections.

Общий модуль. Здесь должны жить переиспользуемые сущности, не принадлежащие одному бизнес-домену.

Принятое правило: всё общее и потенциально переиспользуемое добавлять сюда, а не размазывать по доменным приложениям.

Сейчас содержит географические сущности:

- `Region`
- `City`
- `GeoData`

`Region`:

- справочник регионов;
- наполняется через русскоязычный JSON import командой `import_russia_locations` или административным backend-процессом;
- не создаётся через публичный API;
- поддерживает autocomplete через `GET /api/v1/common/regions/?search=...`;
- содержит `name`, координаты региона, `country_code`;
- `geoname_id` удалён и не является частью текущего API.

`City`:

- справочник городов;
- наполняется через русскоязычный JSON import командой `import_russia_locations` или административным backend-процессом;
- не создаётся через публичный API;
- поддерживает autocomplete через `GET /api/v1/common/cities/?search=...`;
- содержит `name`, координаты города, `country_code`, ссылку на `Region`;
- `geoname_id` удалён и не является частью текущего API.

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

Важно: `Region` и `City` read-only для публичного API. Регионы и города должны заводиться через `import_russia_locations`, миграции seed-данных или административный backend-процесс.

В dev/test базу через migration загружен небольшой тестовый набор городов из разных частей России: Kaliningrad, Murmansk, Saint Petersburg, Moscow, Sochi, Yekaterinburg, Novosibirsk, Yakutsk, Vladivostok, Petropavlovsk-Kamchatsky.

## File Upload Policy

File validation is centralized in `apps.common.file_validators`.

Current limits:

- Images and user avatars: `jpg`, `jpeg`, `png`, `webp`, `gif`; MIME `image/jpeg`, `image/png`, `image/webp`, `image/gif`; max `5 MB`.
- PDF documents for organization registration and organization activity reports: `pdf`; MIME `application/pdf`; max `25 MB`; PDF signature is checked.
- Donor group video reports: `mp4`, `mov`, `webm`; MIME `video/mp4`, `video/quicktime`, `video/webm`; max `500 MB`.

These rules are model-level validators and are also surfaced through DRF serializers as `400` responses on the corresponding file field.

### `apps.organizations`

Отвечает за:

- организации;
- участников организаций;
- заявки на регистрацию организаций;
- мероприятия организаций;
- новости организаций;
- комментарии к новостям;
- филиалы организаций и изображения филиалов.

Ключевые модели:

- `Category`
- `Organization`
- `OrganizationMember`
- `OrganizationBranch`
- `OrganizationBranchImage`
- `Event`
- `EventImage`
- `OrganizationNews`
- `OrganizationNewsImage`
- `OrganizationNewsComment`
- `OrganizationReportDocument`
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

`OrganizationBranch`:

- филиал или точка приёма организации;
- принадлежит `Organization`;
- использует nullable `geodata` на `common.GeoData`;
- хранит описание, телефон, email, график работы и `is_active`;
- управляется активным менеджером организации.

`OrganizationBranchImage`:

- галерея изображений филиала;
- хранит `image`, `alt_text`, `sort_order`.

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

`OrganizationReportDocument`:

- public PDF report for general organization activity;
- belongs to `Organization`, not to `Collection` or `DonorGroup`;
- has `created_by_member`;
- stores `title`, `description`, and `document`;
- creation requires an active organization manager; update/delete uses the common organization content author-or-manager permission.

Ключевые endpoints:

- `GET/DELETE /api/v1/organizations/members/`
- `GET/POST/PATCH/DELETE /api/v1/organizations/branches/`
- `GET/POST/PATCH/DELETE /api/v1/organizations/branch-images/`
- `GET/POST/PATCH/DELETE /api/v1/organizations/events/`
- `GET/POST/PATCH/DELETE /api/v1/organizations/news/`
- `GET/POST/PATCH/DELETE /api/v1/organizations/news-images/`
- `GET/POST/PATCH/DELETE /api/v1/organizations/news-comments/`
- `GET/POST/PATCH/DELETE /api/v1/organizations/report-documents/`
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
- поддерживает push-доставку через связанные `NotificationDelivery`;
- может использоваться не только для приглашений, но и для текстов, системных событий, сообщений.

`UserDevice`:

- устройство пользователя для push-доставки;
- поддерживает providers `fcm`, `apns`, `webpush`, `custom`;
- хранит provider token, device_id, platform, app_version, is_active.

`NotificationDelivery`:

- аудит внешней доставки уведомлений;
- каналы: `email`, `push`;
- статусы: `pending`, `sent`, `failed`, `skipped`;
- для push может ссылаться на `UserDevice`.

`OrganizationMessage`:

- сообщение чата организации;
- принадлежит `Organization`;
- автором является пользователь;
- доступ на чтение/запись основан на активном `OrganizationMember`;
- автор может редактировать/удалять своё сообщение, менеджер организации может модерировать;
- `DELETE` мягкий через `deleted_at`.

`DonorGroupMessage`:

- сообщение чата донорской группы;
- принадлежит `collections.DonorGroup`;
- автором является пользователь;
- доступ на чтение/запись основан на `DonorGroupMember`;
- автор может редактировать/удалять своё сообщение, автор сбора или менеджер организации может модерировать;
- `DELETE` мягкий через `deleted_at`.

`Invitation`:

- универсальное приглашение;
- использует `ContentType` + `object_id`, чтобы приглашать в разные типы целей;
- сейчас поддержаны `target_type="organization"` и `target_type="donor_group"`;
- статусы: `pending`, `accepted`, `declined`, `expired`, `cancelled`;
- связано с `Notification`;
- при accept для организации создаёт `OrganizationMember`;
- при accept для donor group создаёт `DonorGroupMember`.

Ключевые endpoints:

- `GET/POST /api/v1/communications/notifications/`
- `POST /api/v1/communications/notifications/{id}/mark-read/`
- `POST /api/v1/communications/notifications/mark-all-read/`
- `GET/POST/PATCH/DELETE /api/v1/communications/devices/`
- `GET /api/v1/communications/notification-deliveries/`
- `GET/POST/PATCH/DELETE /api/v1/communications/organization-messages/`
- `GET/POST/PATCH/DELETE /api/v1/communications/donor-group-messages/`
- `GET/POST /api/v1/communications/invitations/`
- `POST /api/v1/communications/invitations/{id}/accept/`
- `POST /api/v1/communications/invitations/{id}/decline/`
- `POST /api/v1/communications/invitations/{id}/cancel/`

Celery:

- `send_notification_delivery(notification_id)` отправляет email-доставку.
- `send_notification_push_delivery(notification_id)` отправляет push-доставку через настроенный HTTP provider.
- Уведомление и приглашение сохраняются синхронно в БД.
- Email и push отправляются через `transaction.on_commit(...)`.

WebSocket:

- ASGI подключён через Channels.
- Есть health endpoint: `/ws/communications/health/`.
- JWT middleware принимает token из query param `?token=...` или header `Authorization: Bearer ...`.

Важно: бизнес-логика приглашений не зависит от websocket. WebSocket — только realtime-слой.

### `apps.collections`

Реализует публичный REST API для сборов гуманитарной помощи, вещей пользователей, донорских групп, голосований, встреч и видеоотчётов. Endpoint курьерских профилей пока остаётся здесь для обратной совместимости, но модель `CourierProfile` принадлежит `apps.accounts`. Платформа не ведёт полный складской цикл учёта вещей; `UserItem` нужен как подсказка организатору, у кого что потенциально есть. Финальный выбор даты/места по голосованию реализован как явное действие организатора.

Ключевые модели:

- `ItemCategory`
- `Item`
- `UserItem`
- `Collection`
- `CollectionItem`
- `BranchItem`
- `DonorGroup`
- `DonorGroupParameters`
- `DonorGroupMember`
- `DonorGroupItem`
- `DonorGroupVideoReport`
- `MeetingPlaceProposal`
- `Poll`
- `PollOption`
- `PollVote`

Текущее решение для MVP: `ItemCategory` используется как конкретный тип вещи/потребности, например "Зубная гигиена", "Питьевая вода", "Куртки". Поле `description` хранит примеры содержимого категории. Не дублировать это описание в будущих связующих моделях вроде `UserItem` и `CollectionItem`; там должны жить контекстные поля пользователя или сбора.

Сейчас реализован слой сборов: пользовательские вещи, сборы организаций с `geodata`, позиции сборов, вещи, принимаемые филиалами, донорские группы, предложения мест встречи и голосования. `CollectionUserItem` намеренно не добавлен: организатор пока вручную смотрит публичные `UserItem` и координирует передачу вне автоматического матчинга.

Донорские группы привязаны к `Collection`. `DonorGroupMember` связывает пользователей с группой, `DonorGroupItem` хранит выбранный организатором `UserItem` и количество вещей пользователя для этой группы. Приглашения в донорскую группу идут через общий механизм `communications.Invitation` с `target_type="donor_group"` и при accept создают membership.

`DonorGroupParameters` хранит вручную назначенные параметры донорской группы: дату/время и, опционально, место сбора. Время можно назначить отдельно через `POST /api/v1/collections/donor-groups/{id}/set-parameters-time/`; место и время вместе можно назначить через `POST /api/v1/collections/donor-groups/{id}/set-parameters/`. Старые `schedule-meeting*` URLs остаются alias-ручками для совместимости. Эти действия не привязаны к итогам голосований.

Фронтовые агрегаты реализованы без отдельного полного цикла передачи вещей:

- `Collection` отдаёт `quantity_required_total`, `quantity_selected_total`, `donor_groups_count`, `donor_group_members_count`, `donor_group_items_count`;
- `CollectionItem` отдаёт `selected_quantity` и `remaining_quantity` по категории внутри сбора;
- `UserItem` отдаёт `selected_quantity` и `available_quantity`; query param `collection` ограничивает расчёт выбранными вещами в донорских группах конкретного сбора.

`DonorGroupVideoReport` хранит видеоотчёт, загруженный участником donor group, и привязан напрямую к `DonorGroup` без дополнительной группировки. Читать отчёты могут участники группы, автор сбора и менеджеры организации; загружать могут участники группы.

Назначение даты, времени и места создаёт существующие `communications.Notification` для участников donor group, кроме пользователя, который выполнил действие. В `payload` используется `target_type="donor_group_parameters"` и `event`: `date_assigned`, `time_assigned`, `place_assigned`.

Голосования поддерживают:

- типы `text`, `date`, `place`;
- статусы `draft`, `open`, `closed`;
- варианты `PollOption`;
- один голос пользователя на один poll;
- place polls из предложений места встречи;
- repost poll без вариантов с нулём голосов;
- финализацию `date`/`place` poll option через `POST /api/v1/collections/polls/{id}/finalize/`;
- push/in-app уведомления участникам donor group при создании открытого donor group poll.

Дальнейшая часть `collections` должна покрыть улучшение координации donor group без автоматического matching и складского учёта, а также возможные вложения/метаданные к отчётам, если они понадобятся.

Ожидаемый доменный сценарий:

1. Организация создаёт сбор с перечнем необходимых вещей.
2. Пользователь добавляет свои вещи в сбор.
3. Формируется донорская группа или выбирается самостоятельная передача через филиал.
4. Для донорской группы создаются голосования и вручную назначается встреча.
5. Позже добавляется чат donor group.
6. Курьер-доброволец принимает вещи.
7. Загружается видеоотчёт.
8. Участники получают уведомления.

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
- `OrganizationBranch.geodata`
- `Collection.geodata`
- `DonorGroupParameters.geodata`
- `MeetingPlaceProposal.geodata`
- `PollOption.geodata`

Ожидаемое использование позже:

- дополнительные точки координации, если появятся новые сущности встреч или отчётов.

`is_online` остаётся на сущности мероприятия. Не выводить онлайн только по `geodata = null`: отсутствие геоданных может означать незаполненное место, черновик или офлайн без точного адреса.

Правила:

- `City` — read-only API, импортируется через `import_russia_locations` или административный backend-процесс.
- `GeoData` можно создавать через API.
- `latitude` допустима от `-90` до `90`.
- `longitude` допустима от `-180` до `180`.
- Все поля `GeoData` optional.

## 6. API-префиксы

Основной REST API:

- `/api/v1/accounts/`
- `/api/v1/common/`
- `/api/v1/communications/`
- `/api/v1/collections/`
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
- push-доставка уведомлений;
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

Использовать websocket сейчас для:

- чатов организации;
- чатов донорской группы.

Не использовать websocket для in-app notification list на текущем этапе. Уведомления читаются через REST, обновляются через refetch/polling на frontend и при необходимости доставляются внешне через push.

Optional realtime позже:

- presence/typing;
- live notification badge, если REST polling и push окажутся недостаточными.

Не использовать websocket как единственный источник данных. Всё важное должно сохраняться в БД и читаться через REST.

Текущие chat websocket endpoints:

- `/ws/communications/organizations/{organization_id}/chat/`
- `/ws/communications/donor-groups/{donor_group_id}/chat/`

Они создают сообщения в БД и рассылают live event участникам соответствующего контекста. История и восстановление после reconnect идут через REST message endpoints.

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
uv run python manage.py test apps.collections
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
- communications devices/push delivery audit;
- organization and donor group chat messages;
- collections CRUD, donor groups, parameters, proposals, polls, aggregate fields, and video reports;
- websocket health endpoint.

## 11. Документация в `docs`

- `agent_project_design_doc.md` — этот агентский диздок.
- `frontend_agent_api_guide.md` — общий frontend-facing API guide по всем текущим endpoints.
- Postman/API testing flow хранится в `frontend_agent_api_guide.md`.
- `frontend_agent_geodata_instructions.md` — инструкция для frontend-агента по geodata.
- `accounts_views_diagram.md` — диаграмма views модуля accounts.

## 12. Важные архитектурные решения

1. `common` — место для всего общего и переиспользуемого.
2. Города не создаются через публичный API. Источник городов — JSON import `import_russia_locations`, seed-миграции или административный backend-процесс.
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

Current implementation note, 2026-05-09:

- Organization branches are implemented.
- Core collections CRUD is implemented: collections, user items, collection items, branch items, donor groups, donor group members, donor group items, frontend aggregate fields, and donor group video reports. Courier profile API remains exposed under collections for compatibility, while the model belongs to accounts.
- Donor group invitations are implemented through `communications.Invitation` with `target_type="donor_group"`.
- Donor group parameters scheduling is implemented: collection authors and organization managers manually set a donor group's date/time through `set-parameters-time`, or place and date/time through `set-parameters`; legacy `schedule-meeting*` aliases remain for compatibility.
- Push delivery is implemented as an additional `Notification` delivery channel.
- Voting base is implemented: text/date/place polls, poll options, one vote per user per poll, meeting place proposals, place-poll creation from proposals, poll reposting without zero-vote options, explicit finalization of date/place poll options into `DonorGroupParameters`, and push notifications for new open donor group polls.
- Organization PDF report documents are implemented under `/api/v1/organizations/report-documents/`.

Приоритетные направления:

1. Report improvements.
   - Optional metadata, moderation status, thumbnails, or file-size limits for donor group video reports.
   - Optional organization report categories if PDF reports grow beyond a flat list.
   - Keep video reports tied to donor groups and PDF reports tied to organizations, not to collection-level item accounting.

2. Chat improvements.
   - Read state / last read marker.
   - Attachments.
   - Optional push notification rules for mentions or important messages.

3. Meeting/poll UX improvements.
   - Better frontend flows around already implemented `poll.finalize`.
   - Keep manual `set-parameters` available as a separate organizer action.

4. Location import maintenance.
   - Русскоязычный JSON import: `uv run python manage.py import_russia_locations`.
   - Загружать регионы в `common.Region`.
   - Загружать города в `common.City`.
   - Не менять текущую схему `GeoData`: адресная строка остается optional, координаты хранятся отдельно.
   - Не открывать публичный POST для городов.

## 14. Предупреждения для агента

- Не удалять старые alias endpoints без явного решения пользователя.
- Не смешивать отсутствие `geodata` с онлайн-форматом.
- Не создавать отдельные city/address поля в новых доменах, если можно использовать `GeoData`.
- Не отправлять email/внешние уведомления до commit транзакции.
- Не делать websocket единственным способом получить сообщение.
- Не добавлять websocket-уведомления без явной продуктовой необходимости; для списка уведомлений достаточно REST/refetch/polling и push-доставки.
- Не откатывать незнакомые изменения в рабочем дереве.
- Перед изменениями в моделях всегда создавать миграции и проверять `makemigrations --check --dry-run`.
