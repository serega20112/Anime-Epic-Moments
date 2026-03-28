# API и маршруты

## Описание

Приложение сочетает серверный HTML-рендеринг и JSON-endpoint'ы. Маршруты сгруппированы по продуктовым областям: аутентификация, поиск аниме, избранное, хайлайты, просмотр, рекомендации и главная страница.

Состояние аутентификации в основном определяется по cookie `access_token`, которая разбирается в app factory и прокидывается в `g.user`.

## Как это работает

### Публичные и auth-маршруты

| Метод | Путь | Тип | Назначение |
| --- | --- | --- | --- |
| `GET` | `/` | HTML | Главная страница с сезонными тайтлами и рекомендациями |
| `GET` | `/auth/login` | HTML | Страница входа |
| `POST` | `/auth/login` | Redirect | Аутентификация пользователя и установка `access_token` |
| `GET` | `/auth/register` | HTML | Страница регистрации |
| `POST` | `/auth/register` | Redirect | Регистрация пользователя и установка `access_token` |
| `POST` | `/auth/logout` | Redirect | Очистка auth-cookie |
| `GET` | `/auth/profile` | HTML | Страница профиля текущего пользователя |
| `POST` | `/auth/profile` | Redirect | Обновление профиля |
| `GET` | `/auth/password-reset` | HTML | Страница запроса сброса пароля |
| `POST` | `/auth/password-reset` | Redirect | Отправка письма для сброса |
| `GET` | `/auth/password-reset/confirm` | HTML | Страница подтверждения сброса |
| `POST` | `/auth/password-reset/confirm` | Redirect | Сохранение нового пароля |

### Поиск аниме

| Метод | Путь | Тип | Назначение |
| --- | --- | --- | --- |
| `GET` | `/anime/search` | HTML | Страница поиска по названию |
| `GET` | `/anime/search/description` | HTML | Страница поиска по описанию |
| `GET` | `/anime/api/search` | JSON | Поиск аниме по названию |
| `GET` | `/anime/api/search/description` | JSON | Поиск по естественному описанию и фильтрам |
| `GET` | `/anime/api/autocomplete` | JSON | Подсказки автокомплита |
| `GET` | `/anime/api/season/popular` | JSON | Популярные аниме сезона |

### Избранное

| Метод | Путь | Тип | Назначение |
| --- | --- | --- | --- |
| `POST` | `/favorites/` | Пустой ответ | Добавление аниме в избранное со snapshot-метаданными |
| `DELETE` | `/favorites/` | Пустой ответ | Удаление аниме из избранного |
| `GET` | `/favorites/<user_id>` | HTML | Рендер страницы избранного и рекомендаций |

### Хайлайты

| Метод | Путь | Тип | Назначение |
| --- | --- | --- | --- |
| `POST` | `/highlights/` | Пустой ответ | Создание хайлайта |
| `GET` | `/highlights/<user_id>` | HTML | Дашборд пользовательских хайлайтов |
| `GET` | `/highlights/top` | HTML | Публичный топ хайлайтов |
| `PUT` | `/highlights/<highlight_id>` | Пустой ответ | Редактирование хайлайта |
| `DELETE` | `/highlights/<highlight_id>` | Пустой ответ | Удаление хайлайта |

### Просмотр

| Метод | Путь | Тип | Назначение |
| --- | --- | --- | --- |
| `GET` | `/watch/<anime_id>` | HTML | Страница просмотра с источниками, прогрессом и хайлайтами |
| `POST` | `/watch/<anime_id>/status` | JSON | Сохранение статуса аниме у пользователя |
| `POST` | `/watch/<anime_id>/sources` | JSON | Ручное создание источника отключено |
| `POST` | `/watch/<anime_id>/sources/discover` | JSON | Принудительный поиск источников для эпизода |
| `POST` | `/watch/<anime_id>/session` | JSON | Сохранение состояния плеера |
| `POST` | `/watch/<anime_id>/highlights` | JSON | Создание хайлайта прямо из плеера |
| `GET` | `/watch/open/<anime_id>` | Redirect | Вспомогательный редирект на страницу просмотра |

### Рекомендации

| Метод | Путь | Тип | Назначение |
| --- | --- | --- | --- |
| `POST` | `/api/v1/recommendations/generate/<user_id>` | JSON | Возврат кэшированных или свежих рекомендаций |
| `POST` | `/api/v1/recommendations/refresh/<user_id>` | JSON | Принудительная пересборка рекомендаций без кэша |

Важные детали интерфейса:

- избранное принимает как JSON, так и form-data и сохраняет локальный snapshot карточки
- мутации watch-слоя требуют аутентифицированного пользователя в `g.user`
- route-обработчики остаются тонкими и делегируют поведение в use case
- watch-страница HTML-ориентированная, а инкрементальные действия выполняются через JSON

## Почему это сделано так

- HTML-ответы позволяют не строить отдельный frontend-build pipeline.
- JSON-endpoint'ы используются там, где взаимодействие должно быть частичным и быстрым: поиск, состояние плеера, discovery, рекомендации.
- Группировка маршрутов по продуктовым областям упрощает навигацию, дебаг и тестирование.
- Cookie-based auth удобен для server-rendered интерфейса, при этом JSON-endpoint'ы остаются пригодными для browser-side скриптов.

## Где в коде

- `src/backend/create_app.py`
- `src/backend/delivery/api/v1/index_route.py`
- `src/backend/delivery/api/v1/auth_route.py`
- `src/backend/delivery/api/v1/anime_route.py`
- `src/backend/delivery/api/v1/favorite_route.py`
- `src/backend/delivery/api/v1/highlight_route.py`
- `src/backend/delivery/api/v1/watch_route.py`
- `src/backend/delivery/api/v1/recommendation_route.py`
- `src/frontend/templates`
- `src/frontend/static/js`

## Связанные документы

- [Обзор архитектуры](../architecture/overview.md)
- [Доменное ядро](../domain/core.md)
- [Безопасность](../security/security.md)
- [Пользовательские сценарии](../use-cases.md)
