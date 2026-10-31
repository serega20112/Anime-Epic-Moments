# Unit-тесты

## Описание

Канон модульного теста **AEM**: проверяется чистая логика слоёв `domain/` и
`application/` — инварианты сущностей, доменные политики, value objects и
сценарии использования на двойниках портов. У этого уровня нет базы, сети, диска
и контейнера зависимостей: есть только объект, правило и утверждение.

Границы уровня заданы в [стратегии](01-testing-strategy.md); происхождение
фикстур — в [фикстурах и изоляции](05-fixtures-and-isolation.md).

## Как это работает

### Правила

| № | Правило | Формулировка |
| --- | --- | --- |
| 1 | Ноль побочных эффектов | Нет обращений к диску, сети, базе и Redis. Единственный вводимый вход — двойники портов |
| 2 | Нет локальных фикстур | В файле теста запрещено объявлять `@pytest.fixture`; фикстура только принимается в аргументы |
| 3 | Докстринг модуля | Первой строкой файла — строка документирования модуля на русском, до импортов |
| 4 | `starlette.status` | HTTP-коды берутся из `starlette.status`, магические числа в утверждениях запрещены |
| 5 | Класс-контекст с маркером | Тесты сгруппированы в классе `Test<Компонент>` с декоратором `@pytest.mark.unit` над классом |
| 6 | `ids` у параметров | Каждая параметризация обязана задавать `ids=` — отчёт о падении читается без разбора кортежей |
| 7 | Докстринг теста в три части | `Что тестируем` / `Что передаём` / `Что ожидаем` |
| 8 | AAA | Тело строится блоками Arrange → Act → Assert, блоки разделяются пустой строкой, перемешивание запрещено |

### Скелет файла

```python
"""Инварианты хайлайта: таймкоды принадлежат одной серии."""

from __future__ import annotations

import pytest

from backend.domain.aggregates.highlight.highlight import Highlight
from backend.domain.exceptions import ValidationError


@pytest.mark.unit
class TestHighlightInvariants:
    """Проверка правил, которые сущность не даёт обойти."""

    def test_constructor_rejects_inverted_timecodes(self) -> None:
        """Что тестируем: инвариант порядка таймкодов хайлайта.
        Что передаём: начало позже конца в одной серии.
        Что ожидаем: ValidationError с указанием нарушенного правила.
        """
        with pytest.raises(ValidationError, match="таймкоды"):
            Highlight(
                user_id=1,
                anime_id=101,
                episode=3,
                start_timestamp=120.0,
                end_timestamp=95.0,
                title="Финальный заезд",
            )

    def test_constructor_rejects_zero_episode(self) -> None:
        """Что тестируем: инвариант номера серии.
        Что передаём: корректные таймкоды и серию с номером 0.
        Что ожидаем: ValidationError, потому что серии начинаются с единицы.
        """
        with pytest.raises(ValidationError, match="серии"):
            Highlight(
                user_id=1,
                anime_id=101,
                episode=0,
                start_timestamp=95.0,
                end_timestamp=120.0,
                title="Финальный заезд",
            )
```

### Сценарий на двойниках портов

Сценарий вызывается так, как его вызовет представление: одной командой или
запросом через `execute`. Проверяются три вещи: результат, аргументы, попавшие в
порт, и побочние действия внутри границ сценария (сброс кэша, коммит).

```python
"""Сценарий добавления тайтла в избранное: snapshot и сброс кэшей."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.application.dto.favorite import AddFavoriteCommand
from backend.application.interface.repositories.favorite_repository import (
    FavoriteRepository,
)
from backend.application.use_cases.favorite.add_favorite import AddFavoriteUseCase
from tests.support.fakes import FakeUnitOfWork


@pytest.mark.unit
class TestAddFavoriteUseCase:
    """Проверка оркестрации сценария на двойниках портов."""

    @pytest.mark.parametrize(
        ("genres_input", "expected_genres"),
        [
            ([" Action ", "Comedy"], ["Action", "Comedy"]),
            ('["Drama", "Mystery"]', ["Drama", "Mystery"]),
            ("Action, Comedy", ["Action", "Comedy"]),
        ],
        ids=["список-с-пробелами", "json-строка", "csv-строка"],
    )
    async def test_normalizes_snapshot_and_invalidates_caches(
        self,
        genres_input: list[str] | str,
        expected_genres: list[str],
        favorite_repository: AsyncMock,
        recommendation_service: AsyncMock,
        profile_overview_cache: AsyncMock,
    ) -> None:
        """Что тестируем: нормализцию snapshot-полей и сброс кэшей после записи.
        Что передаём: жанры в трёх формах, которые приходят из формы и JSON.
        Что ожидаем: жанры приведены к списку без пустых значений, запись
        ушла в репозиторий, рекомендации и обзор профиля сброшены один раз.
        """
        command = AddFavoriteCommand(
            user_id=5,
            anime_id=10,
            title="  Initial D  ",
            genres=genres_input,
        )
        use_case = AddFavoriteUseCase(
            FakeUnitOfWork(FavoriteRepository=favorite_repository),
            recommendation_service,
            profile_overview_cache,
        )

        result = await use_case.execute(command)

        assert result.genres == expected_genres
        favorite_repository.add.assert_awaited_once()
        recommendation_service.invalidate_user.assert_awaited_once_with(5)
        profile_overview_cache.invalidate_user.assert_awaited_once_with(
            5, include_ai_summary=True
        )
```

Двойник отдаётся через `FakeUnitOfWork(FavoriteRepository=favorite_repository)`:
ключ — имя класса порта. Если сценарий запросит порт, для которого двойник не
подготовлен, `FakeUnitOfWork` поднимет `LookupError` с именем порта — тест
сообщит, какую зависимость забыли описать, вместо молчаливого `AsyncMock`.

### Утверждения об HTTP-кодах

Код ответа сравнивается с константой, а не с числом:

```python
from starlette import status

assert result.status_code == status.HTTP_404_NOT_FOUND
assert result.error == "moment_not_found"
```

### Что проверяется в домене

| Объект | Обязательные проверки |
| --- | --- |
| Сущность | каждое правило конструктора: нарушение → конкретный тип исключения; допустимая граница (минимум, максимум) проходит |
| Value object | нормализация входа, производные свойства, неизменяемость |
| Политика | граничные значения лимита, поведение при пустом и мусорном входе, отсутствие побочного эффекта |
| Сценарий | успех; каждая ветвь отказа; какие порты вызваны и с чем; что NOT вызвано (например, LLM не вызывается, пока возрастный gate не пройден) |

Проверка «не вызван» обязательна там, где вызов стоит денег или приватности:
обращение к внешнему API, к LLM, отправка письма, сброс кэша.

### Чего в Unit-тесте быть не должно

| Антипаттерн | Чем заменяется |
| --- | --- |
| Реальная сессия SQLAlchemy, `sqlite://`, патч драйвера | двойник порта; SQL-поведение — уровень Integration |
| `httpx`, `TestClient`, вызов маршрута | сценарий вызывается напрямую; HTTP — уровень E2E |
| `AsyncMock` вместо сущности домена | настоящий объект: сущность дешёвая, её подмена скрывает ошибку правила |
| Мокирование проверяемого объекта | мокируются только зависимости; тестируемый объект строится реальным |
| `asyncio.run` внутри теста | `async def`-тест: `asyncio_mode = "auto"` |
| Цикл `for` с `assert` внутри вместо параметризации | `@pytest.mark.parametrize` с `ids=` |
| Один тест на три правила | тест на одно правило; имя теста говорит, на какое |
| Утверждение «не упало» | утверждение о конкретном результате или `pytest.raises` с `match` |
| Числовой HTTP-код | константа `starlette.status` |
| Локальная фикстура данных | фабрика из `tests/unit/fixtures/` |

### Скорость

Unit-прогон остаётся быстрым и без внешних зависимостей: файл не импортирует
`backend.infrastructure`, не читает `.env` и не создаёт файлов. Появившаяся в
Unit-тесте строка `import sqlalchemy` означает, что тест относится к уровню
Integration и должен быть переложен.

## Почему это сделано так

Инварианты проверяются в домене, потому что они единственное, что гарантирует
корректность данных: репозиторий можно заменить, маршрут переписать, а правило
`start < end` обязано оставаться невыполнимым в обход конструктора.

Двойник порта вместо реальной базы нужен не для скорости самой по себе, а для
выразительности: в Unit-тесте видно, какую ветвь выбрал сценарий и с каким
аргументом, тогда как на реальной базе тот же провал выглядит как «строка не
найдена» и требует разбора транзакции.

`ids` в параметризации — требование к читаемости падения. Без них отчёт печатает
`test_x[parametrize-2]`, и чтобы понять, какой из трёх форматов жанров сломался,
приходится перезапускать с `-v` и читать кортеж аргументов.

Трёхчастный докстринг держит тест у границы «один тест — одно правило»: блок
`Что ожидаем` невозможно сформулировать, если проверка охватывает три разных
поведения, — и тест распадается на три.

## Где в коде

- `tests/unit/domain/` — инварианты, value objects, политики
- `tests/unit/application/use_cases/` — сценарии на двойниках
- `tests/support/fakes.py` — `FakeUnitOfWork`
- `pyproject.toml` — `asyncio_mode = "auto"`, маркер `unit`

## Связанные документы

- [Стратегия тестирования](01-testing-strategy.md)
- [Integration-тесты](03-integration-testing.md)
- [Фикстуры и изоляция](05-fixtures-and-isolation.md)
- [Соглашения кодовой базы](../04-dev-guide/conventions.md)
- [Модель предметной области](../01-architecture/domain-model.md)
