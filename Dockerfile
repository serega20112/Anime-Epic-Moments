# syntax=docker/dockerfile:1.7

# ============================================================
# Anime Epic Moments — образ приложения
# Зависимости ставит только uv (pyproject.toml + uv.lock).
# pip / requirements.txt в проекте не используются.
# ============================================================

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
# В pyproject.toml стоит python-preference = "only-managed" — это нужно для
# локальной разработки (uv сам заводит CPython 3.12 на машине разработчика).
# В контейнере нужно обратное: используем интерпретатор базового образа,
# иначе uv скачает свой managed CPython и он займёт место в образе.
ENV UV_PYTHON_PREFERENCE=only-system
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/

# Отдельным слоем — чтобы зависимости не переустанавливались при правках кода.
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project --no-cache

COPY src /app/src
COPY migrations /app/migrations
COPY scripts /app/scripts

# ----------------------------------------------------------------
# Финальный образ: только интерпретатор, venv и код. uv не нужен.
# ----------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/migrations /app/migrations
COPY --from=builder /app/scripts /app/scripts

RUN sed -i 's/\r$//' /app/scripts/entrypoint.sh && chmod +x /app/scripts/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["web"]
