"""Разбор тел форм в типизированные модели запросов."""

from __future__ import annotations

from fastapi import Request
from pydantic import BaseModel, ValidationError


async def read_form_model[ModelT: BaseModel](
    request: Request, model_type: type[ModelT]
) -> ModelT | None:
    """Собрать модель запроса из тела формы.

    Из формы берутся только поля модели: лишние ключи (например, ``user_id``,
    который присылает клиент) намеренно не попадают в запрос.

    Args:
        request: Текущий HTTP-запрос с телом формы.
        model_type: Модель запроса, которую нужно заполнить.

    Returns:
        ModelT | None: Заполненная модель либо None, если форма не прошла проверку.
    """
    form = await request.form()
    data = {name: form.get(name) for name in model_type.model_fields}
    try:
        return model_type.model_validate(data)
    except ValidationError:
        return None
