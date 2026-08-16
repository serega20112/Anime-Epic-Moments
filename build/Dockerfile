FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY src /app/src
COPY build /app/build

RUN sed -i 's/\r$//' /app/build/scripts/entrypoint.sh && chmod +x /app/build/scripts/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/app/build/scripts/entrypoint.sh"]
CMD ["web"]