# Руководство по тестированию API в Postman

## Основная информация

В этом проекте маршруты API для аккаунтов доступны по пути:

`/api/v1/accounts/`

Источник: [hp_backend/urls.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/hp_backend/urls.py:18)

Перед тестированием запустите сервер разработки:

```powershell
uv run python manage.py runserver
```

Базовый URL для Postman:

```text
http://127.0.0.1:8000/api/v1/accounts
```

## 1. Создание коллекции в Postman

Создайте коллекцию, например:

`HP Backend API`

Добавьте переменные коллекции:

- `base_url` = `http://127.0.0.1:8000/api/v1/accounts`
- `access_token` = пусто
- `refresh_token` = пусто

После этого используйте URL в таком виде:

```text
{{base_url}}/register/
```

## 2. Общая настройка запросов

Для JSON-запросов:

- Заголовок: `Content-Type: application/json`

Для защищённых эндпоинтов:

- Тип авторизации: `Bearer Token`
- Токен: `{{access_token}}`

JWT-аутентификация настроена в:

[hp_backend/settings.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/hp_backend/settings.py:82)

## 3. Рекомендуемый порядок тестирования

Тестируйте API в таком порядке:

1. `register`
2. `login`
3. `profile GET`
4. `profile PATCH`
5. `token refresh`
6. `logout`

## 4. Регистрация пользователя

Запрос:

- Метод: `POST`
- URL: `{{base_url}}/register/`

Тело запроса:

```json
{
  "username": "harry",
  "email": "harry@example.com",
  "password": "StrongPassword123!",
  "password_confirm": "StrongPassword123!",
  "first_name": "Harry",
  "last_name": "Potter"
}
```

Ожидаемый результат:

- Статус: `201 Created`
- Ответ должен содержать данные пользователя и JWT-токены

Пример структуры ответа:

```json
{
  "user": {
    "id": 1,
    "username": "harry",
    "email": "harry@example.com"
  },
  "refresh": "refresh_token_here",
  "access": "access_token_here",
  "message": "User registered successfully"
}
```

Сохраните эти значения в переменные Postman:

- `access` -> `access_token`
- `refresh` -> `refresh_token`

Связанный код:

- [apps/accounts/views.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/views.py:17)
- [apps/accounts/serializers.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/serializers.py:53)

## 5. Вход в систему

Запрос:

- Метод: `POST`
- URL: `{{base_url}}/login/`

Тело запроса:

```json
{
  "email": "harry@example.com",
  "password": "StrongPassword123!"
}
```

Ожидаемый результат:

- Статус: `200 OK`
- Ответ должен содержать новые токены `access` и `refresh`

Связанный код:

- [apps/accounts/views.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/views.py:31)
- [apps/accounts/serializers.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/serializers.py:65)

## 6. Получение профиля текущего пользователя

Запрос:

- Метод: `GET`
- URL: `{{base_url}}/profile/`
- Авторизация: `Bearer {{access_token}}`

Ожидаемый результат:

- Статус: `200 OK`
- Ответ должен содержать профиль текущего пользователя

Пример:

```json
{
  "id": 1,
  "username": "harry",
  "email": "harry@example.com",
  "first_name": "Harry",
  "last_name": "Potter",
  "full_name": "Harry Potter",
  "avatar": null,
  "bio": "",
  "is_courier": false,
  "is_moderator": false
}
```

Связанный код:

- [apps/accounts/views.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/views.py:46)
- [apps/accounts/serializers.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/serializers.py:6)

## 7. Обновление профиля текущего пользователя

Запрос:

- Метод: `PATCH`
- URL: `{{base_url}}/profile/`
- Авторизация: `Bearer {{access_token}}`

Для текстовых полей используйте JSON:

```json
{
  "first_name": "Harry",
  "last_name": "James Potter",
  "bio": "Wizard"
}
```

Ожидаемый результат:

- Статус: `200 OK`

Если хотите протестировать поле `avatar`, используйте `form-data`, потому что это файловое поле.

Связанный код:

- [apps/accounts/views.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/views.py:52)
- [apps/accounts/serializers.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/serializers.py:27)

## 8. Обновление access-токена

Запрос:

- Метод: `POST`
- URL: `{{base_url}}/token/refresh/`

Тело запроса:

```json
{
  "refresh": "{{refresh_token}}"
}
```

Ожидаемый результат:

- Статус: `200 OK`
- Ответ должен содержать новый access-токен

Пример:

```json
{
  "access": "new_access_token_here"
}
```

Источник маршрута:

[apps/accounts/urls.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/urls.py:11)

## 9. Выход из системы

Запрос:

- Метод: `POST`
- URL: `{{base_url}}/logout/`
- Авторизация: `Bearer {{access_token}}`

Тело запроса:

```json
{
  "refresh_token": "{{refresh_token}}"
}
```

Ожидаемый результат:

- Статус: `200 OK`
- Ответ с сообщением об успешном выходе

Связанный код:

[apps/accounts/views.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/views.py:63)

## 10. Полезные негативные тесты

Также проверьте невалидные сценарии.

Для `register`:

- отсутствует `email`
- слабый пароль
- разные значения `password` и `password_confirm`
- дублирующийся `email`

Для `login`:

- неверный пароль
- неизвестный `email`

Для `profile`:

- запрос без Bearer-токена
- запрос с истёкшим токеном

Для `token refresh`:

- невалидный refresh-токен

## 11. Автосохранение токенов в Postman

Во вкладке `Tests` для `register` и `login` можно добавить:

```javascript
const jsonData = pm.response.json();

if (jsonData.access) {
    pm.collectionVariables.set("access_token", jsonData.access);
}

if (jsonData.refresh) {
    pm.collectionVariables.set("refresh_token", jsonData.refresh);
}
```

Это позволит автоматически обновлять переменные коллекции.

## 12. Важные замечания по текущему коду

Некоторые запросы могут завершаться ошибкой из-за проблем в текущей реализации backend, а не из-за настроек Postman.

Обнаруженные проблемы:

- В [apps/accounts/views.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/views.py:14) `User = get_user_model` должно быть `User = get_user_model()`.
- В [apps/accounts/views.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/views.py:22) `self.get_serializer(request.data)` должно быть `self.get_serializer(data=request.data)`.
- В [apps/accounts/serializers.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/serializers.py:60) сериализатор регистрации сейчас использует `super().create(validated_data)`, что рискованно для обработки пароля и поля `password_confirm`.
- В [apps/accounts/views.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/views.py:64) `permissions.isAuthenticated` должно быть `permissions.IsAuthenticated`.
- Выход из системы использует `token.blacklist()`, но `rest_framework_simplejwt.token_blacklist` отсутствует в `INSTALLED_APPS` в [hp_backend/settings.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/hp_backend/settings.py:29), поэтому logout может не работать.
- Ответ при обновлении профиля сейчас возвращает сообщение, связанное с паролем, в [apps/accounts/views.py](/c:/VScodeprojects/PythonProjects/hp-backend/hp-backend/apps/accounts/views.py:58).

## 13. Минимальный чек-лист для smoke test

Если нужен только быстрый smoke test, выполните такие запросы:

1. `POST {{base_url}}/register/`
2. `POST {{base_url}}/login/`
3. `GET {{base_url}}/profile/`
4. `POST {{base_url}}/token/refresh/`
5. `POST {{base_url}}/logout/`
