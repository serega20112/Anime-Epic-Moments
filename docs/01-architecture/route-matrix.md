# Матрица роутов

## Описание

Инвентарь всех HTTP-маршрутов **AEM**: для каждого зафиксировано, требуется ли
аутентификация, откуда берётся `user_id` и где проверяется владелец ресурса.
Механические колонки (путь, методы, обработчик, источник `user_id`)
воспроизводятся из кода:

```bash
uv run python scripts/export_route_matrix.py
```

Смысловые колонки — «Требует auth» и «Проверка владельца» — заполнены по
результатам чтения обработчиков и сценариев. Менять их нужно вместе с изменением
семантики роута: скрипт эти колонки не знает и не проверяет.

## Как это работает

### Легенда

| Метка | Смысл |
| --- | --- |
| **сессия** | `user_id` берётся из аутентифицированной сессии; её наполняет `load_user` |
| **путь** | `user_id` приходит в URL и сверяется с сессией через `require_self` |
| **тело** | `user_id` приходит в теле запроса и не используется как решающий |
| **цель** | `user_id` в пути — это *другой* пользователь (публичный профиль, подписка), сравнивать с сессией не нужно |
| **нет** | идентификатор пользователя не используется вовсе |

Проверка владельца означает одно из:

| Метка | Поведение |
| --- | --- |
| **require_self** | 401 для анонима, 403 при несовпадении пути и сессии |
| **use case** | Сценарий проверяет автора (`is_owned_by`, `ensure_owned_by`) или читает scoped-запросом по `user_id` |
| **публ. фильтр** | Репозиторий отдаёт только публичное (`is_public`) |

### Каталог и поиск — публичные

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/` | GET | нет | нет | — |
| `/anime/catalog` | GET | нет | нет | — |
| `/anime/search` | GET | нет | нет | — |
| `/anime/search/description` | GET | нет | нет | — |
| `/anime/api/autocomplete` | GET | нет | нет | — |
| `/anime/api/catalog` | GET | нет | нет | — |
| `/anime/api/search` | GET | нет | нет | — |
| `/anime/api/search/description` | GET | нет | нет | — |
| `/anime/api/season/popular` | GET | нет | нет | — |

### Рекомендации — приватные

Данные пользователя и платный вызов LLM; `user_id` из пути не доверяется
клиенту.

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/api/v1/recommendations/generate/{user_id}` | POST | да | путь + сессия | require_self, 401/403 |
| `/api/v1/recommendations/refresh/{user_id}` | POST | да | путь + сессия | require_self, 401/403 |
| `/api/v1/recommendations/ask/{user_id}` | POST | да | путь + сессия | require_self, 401/403 |

Тесты: `tests/integration/presentation/test_route_ownership.py`.

### Мобильный JSON API

| Путь | Методы | Требует auth | Источник user_id | Комментарий |
| --- | --- | --- | --- | --- |
| `/api/v1/auth/token` | POST | нет (сам выдаёт) | — | Выпуск пары токенов; CSRF-exempt, rate limit `auth_login` по IP |
| `/api/v1/auth/token/refresh` | POST | нет (по refresh-токену) | из payload refresh-токена | Ротация: старый токен однократно потребляется `TokenBlocklist`; CSRF-exempt |
| `/api/v1/auth/token/revoke` | POST | да (Bearer) | заголовок `Authorization` | Без Bearer — 401; отзывает access и refresh |
| `/api/v1/config` | GET | нет | — | Только фиче-флаги, персональных данных не отдаёт |

Тесты: `tests/integration/presentation/test_api_auth.py` (выпуск, ротация, отзыв,
отсутствие Bearer) и `tests/unit/presentation/test_security_helpers.py` (разбор
`Authorization`, CSRF-исключения).

### Аутентификация

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/auth/login` | GET, POST | нет | нет | — (вход по email и паролю) |
| `/auth/register` | GET, POST | нет | нет | — |
| `/auth/verify-email` | GET, POST | нет | нет | — (по токену письма) |
| `/auth/verify-email/resend` | POST | нет | нет | — (rate limit по IP) |
| `/auth/password-reset` | GET, POST | нет | нет | — (по email) |
| `/auth/password-reset/confirm` | GET, POST | нет | нет | — (по токену письма) |
| `/auth/logout` | POST | да (cookie-токен) | нет | Токен из cookie |
| `/auth/refresh` | POST | да (refresh-cookie) | нет | Токен из cookie |
| `/auth/profile` | GET, POST | да | сессия | use case |

### Избранное — приватное

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/favorites/` | POST, DELETE | да | сессия | поле `user_id` клиента игнорируется |
| `/favorites/ids/{user_id}` | GET | да | путь + сессия | require_self, 401/403 |
| `/favorites/{user_id}` | GET | да | путь + сессия | require_self, 401/403 |

Тесты: `tests/integration/presentation/test_route_ownership.py`.

### Коллекции

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/collections` | GET, POST | да | сессия | use case |
| `/collections/api/mine` | GET | да | сессия | use case |
| `/collections/{collection_id}/items` | POST | да | сессия | `ensure_owned_by` → 403 |
| `/collections/{collection_id}/items/remove` | POST | да | сессия | `ensure_owned_by` → 403 |
| `/collections/share/{collection_id}` | GET | нет | нет | публ. фильтр `is_public` |

### Хайлайты: публичные ленты

Хайлайт — публичная запись: отдельного флага видимости у сущности в домене нет,
он отображается в общей ленте, в топе и по ссылке. Скрытым от неавторизованных
зрителей остаётся только спойлерный контент (`include_spoilers`). Доступ гостя
здесь — ожидаемое поведение, а не пробел; изменится вместе с флагом видимости.

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/highlights/feed` | GET | нет (сессия улучшает выдачу) | сессия | публичный контент |
| `/highlights/top` | GET | нет (сессия улучшает выдачу) | сессия | публичный контент |
| `/highlights/share/{highlight_id}` | GET | нет (сессия улучшает выдачу) | сессия | публичный контент |
| `/highlights/{user_id}` | GET | нет (сессия улучшает выдачу) | цель | публичный контент автора |

### Хайлайты: приватные списки и операции

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/highlights/saved` | GET | да | сессия | use case |
| `/highlights/liked` | GET | да | сессия | use case |
| `/highlights/following` | GET | да | сессия | use case |
| `/highlights/notifications` | GET | да | сессия | use case |
| `/highlights/` | POST | да | сессия | автор — пользователь сессии |
| `/highlights/{highlight_id}` | PUT, DELETE | да | сессия | `is_owned_by` → 403 |
| `/highlights/{highlight_id}/likes` | POST, DELETE | да | сессия | use case |
| `/highlights/{highlight_id}/likes` | GET | нет | нет | публичный список лайкнувших |
| `/highlights/{highlight_id}/save` | POST, DELETE | да | сессия | use case |
| `/highlights/{highlight_id}/comments` | POST | да | сессия | автор — пользователь сессии |
| `/highlights/{highlight_id}/comments` | GET | нет | нет | публичные комментарии |

Обработчики `highlight_likes`, `set_saved_highlight` и `highlight_comments`
обслуживают по несколько методов: ветка `GET` публичная, ветки записи требуют
сессию и отвечают 401. Экспортёр помечает такие строки как «нет», потому что
читает один исходник; классификацию по методам нужно смотреть здесь.

### Моменты просмотра

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/moments` | GET | да | сессия | use case |
| `/moments/{moment_id}` | DELETE | да | сессия | scoped-запрос `(moment_id, user_id)` |
| `/moments/{moment_id}/publish` | POST | да | сессия | use case |
| `/watch/{anime_id}/moments` | POST | да | сессия | use case |

### Профили и подписки

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/users/{user_id}` | GET | нет (сессия уточняет спойлеры) | цель | публичный профиль |
| `/users/{user_id}/follow` | POST | да | сессия + цель | Инициатор из сессии; гость: 401 для JSON, 303 для страницы |
| `/users/{user_id}/unfollow` | POST | да | сессия + цель | То же |

### Просмотр и реакции

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/watch/{anime_id}` | GET | нет (сессия добавляет прогресс) | сессия | — |
| `/watch/open/{anime_id}` | GET | нет | нет | — |
| `/watch/proxy` | GET, HEAD | нет | нет | SSRF-allowlist хостов CDN |
| `/watch/{anime_id}/session` | POST | да | сессия | use case |
| `/watch/{anime_id}/status` | POST | да | сессия | use case |
| `/watch/{anime_id}/episode/complete` | POST | да | сессия | use case |
| `/watch/{anime_id}/highlights` | POST | да | сессия | use case |
| `/watch/{anime_id}/reactions` | GET, POST | да | сессия | use case |
| `/watch/{anime_id}/discussion` | POST | да | сессия | автор — пользователь сессии |
| `/watch/discussion/comments/{comment_id}/likes` | POST, DELETE | да | сессия | use case |
| `/watch/{anime_id}/sources` | POST | да | нет | Ручное создание источников отключено, всегда 403 |
| `/watch/{anime_id}/sources/discover` | POST | нет | нет | Техническая синхронизация провайдеров |
| `/ratings/` | POST | да | сессия | use case |

### Поддержка

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/support` | GET | нет | нет | — |
| `/support` | POST | нет (гость возможен) | сессия либо форма | E-mail гостя нормализуется, авторизованный пользователь не подделывается |

### Служебные

| Путь | Методы | Требует auth | Источник user_id | Проверка владельца |
| --- | --- | --- | --- | --- |
| `/health` | GET | нет | нет | — |
| `/ready` | GET | нет | нет | — |
| `/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect` | GET, HEAD | нет | нет | Доступны и в продакшене — открытая задача, см. [безопасность](security.md) |
| `/static/*` | GET | нет | нет | CSRF-exempt |

## Почему это сделано так

- Таблица нужна потому, что `user_id` из URL легко принять за доверенное
  значение: проверка владельца — единственное, что отделяет приватные данные
  одного пользователя от другого. Инвентарь делает пропуск видимым на ревью.
- Механические колонки генерируются, потому что ручная правка после добавления
  роута неизбежно отстаёт. Смысловые остаются ручными: скрипт не знает, публичен
  ли ресурс по продуктовому замыслу.
- Публичность хайлайтов зафиксирована письменно, чтобы её не «починили» как
  уязвимость: у сущности нет флага приватности, и поведение соответствует модели.
- Колонка «источник user_id» — статический сигнал по коду обработчика, а не
  гарантия: проверка владельца может жить в сценарии, и тогда её видно по метке
  «use case».

## Где в коде

- `scripts/export_route_matrix.py` — генератор механических колонок
- `src/backend/presentation/app_factory.py` — полный список подключённых роутеров
- `src/backend/presentation/dependencies/auth.py` — `require_self`
- `src/backend/presentation/api/helpers.py` — `get_current_user`
- `tests/integration/presentation/test_route_ownership.py` — проверки владельца
- `tests/integration/presentation/test_api_auth.py` — проверки Bearer-схемы

## Связанные документы

- [Безопасность](security.md)
- [Поток запроса](data-flow.md)
- [Обзор архитектуры](overview.md)
- [Baseline нарушений границ слоёв](importlinter-baseline.md)
