from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from backend.domain import RecommendationResult
from backend.infrastructure.cache.codec import (
    DATACLASS_MARKER,
    DATETIME_MARKER,
    FIELDS_MARKER,
    decode,
    deserialize,
    encode,
    resolve_class,
    serialize,
)

RECOMMENDATION_FIELDS = (
    "anime_id",
    "reason",
    "similarity_score",
    "title",
    "description",
    "image_url",
    "genres",
    "watch_url",
)


@pytest.mark.unit
class TestEncode:
    """Юнит-тесты сериализации значений кэша."""

    def test_marks_dataclass_with_qualified_name(self):
        """Что тестируем: кодирование доменного dataclass.
        Что передаём: рекомендацию со всеми полями.
        Что ожидаем: метки класса и полей, каждое поле закодировано.
        """
        encoded = encode(
            RecommendationResult(
                anime_id=1,
                reason="r",
                similarity_score=0.5,
                title="t",
                description="d",
                image_url=None,
            )
        )

        assert encoded[DATACLASS_MARKER].endswith("RecommendationResult")
        assert set(encoded[FIELDS_MARKER]) == set(RECOMMENDATION_FIELDS)
        assert encoded[FIELDS_MARKER]["anime_id"] == 1

    def test_marks_datetime_with_isoformat(self):
        """Что тестируем: кодирование даты и времени.
        Что передаём: aware-дату в UTC.
        Что ожидаем: метку datetime со значением isoformat.
        """
        moment = datetime(2026, 3, 21, 12, 30, tzinfo=UTC)

        assert encode(moment) == {DATETIME_MARKER: moment.isoformat()}

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (("a", "b"), ["a", "b"]),
            ({"x"}, ["x"]),
            (frozenset({"y"}), ["y"]),
            ({1: "a"}, {"1": "a"}),
            (None, None),
            (True, True),
        ],
    )
    def test_encodes_containers_and_scalars(self, value, expected):
        """Что тестируем: кодирование коллекций и простых значений.
        Что передаём: кортеж, множество, frozenset, словарь, None и флаг.
        Что ожидаем: JSON-совместимое представление без меток типов.
        """
        assert encode(value) == expected

    def test_rejects_unsupported_type(self):
        """Что тестируем: реакцию кодировщика на неизвестный тип.
        Что передаём: объект без представления в JSON.
        Что ожидаем: TypeError с именем типа вместо тихой порчи данных.
        """
        with pytest.raises(TypeError, match="cannot serialize value of type"):
            encode(object())


@pytest.mark.unit
class TestDecode:
    """Юнит-тесты восстановления значений из JSON."""

    def test_roundtrip_restores_recommendation(self):
        """Что тестируем: полный цикл сериализации рекомендации.

        Регрессия: RecommendationResult был обычным классом, кодировщик
        отказывался его писать, а хранилище из-за этого роняло Redis в память.
        Что передаём: рекомендацию, прогнанную через serialize и deserialize.
        Что ожидаем: равный исходному доменный объект.
        """
        original = RecommendationResult(
            anime_id=7,
            reason="Похожее на ваши избранные/хайлайты",
            similarity_score=1.234,
            title="Gintama",
            description="Комедия",
            image_url="https://example.com/cover.jpg",
            genres=["Action", "Comedy"],
            watch_url="/watch/7?episode=1",
        )

        restored = deserialize(serialize(original), default=None)

        assert restored == original

    def test_roundtrip_restores_nested_datetime(self):
        """Что тестируем: восстановление вложенной даты.
        Что передаём: словарь с датой внутри списка.
        Что ожидаем: тот же момент времени после цикла кодирования.
        """
        moment = datetime(2026, 3, 21, 12, 30)
        payload = decode(encode([{"created_at": moment}]))

        assert payload == [{"created_at": moment}]

    def test_deserialize_returns_default_on_corrupt_payload(self):
        """Что тестируем: чтение испорченной записи кэша.
        Что передаём: битый JSON и восстановимый JSON с отсутствующим классом.
        Что ожидаем: значение по умолчанию вместо исключения.
        """
        assert deserialize("{not-json", default="fallback") == "fallback"
        assert (
            deserialize('{"__dataclass__": "no.such.Module.Klass", "__fields__": {}}', "fallback")
            == "fallback"
        )


@pytest.mark.unit
class TestResolveClass:
    """Юнит-тесты разрешения имени класса для десериализации."""

    def test_resolves_nested_class_name(self):
        """Что тестируем: разбор имени класса с вложенным путём.
        Что передаём: полное имя dataclass из домена.
        Что ожидаем: сам класс.
        """
        assert resolve_class(RecommendationResult.__module__ + ".RecommendationResult") is (
            RecommendationResult
        )

    def test_rejects_name_without_module(self):
        """Что тестируем: имя без имени модуля.
        Что передаём: одиночное имя класса.
        Что ожидаем: ValueError вместо непонятного ImportError.
        """
        with pytest.raises(ValueError, match="does not name a module"):
            resolve_class("RecommendationResult")

    def test_rejects_non_class_name(self):
        """Что тестируем: имя, указывающее не на класс.
        Что передаём: имя модуля.
        Что ожидаем: TypeError.
        """
        with pytest.raises(TypeError, match="does not name a class"):
            resolve_class("backend.domain.value_objects.reaction")


@pytest.mark.unit
def test_recommendation_result_is_dataclass() -> None:
    """Что тестируем: пригодность рекомендации для кэша.
    Что передаём: сам класс.
    Что ожидаем: это dataclass, то есть кодировщик умеет его писать.
    """
    assert dataclasses.is_dataclass(RecommendationResult)
