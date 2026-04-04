FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY src /app/src
COPY build /app/build

RUN sed -i 's/\r$//' /app/build/scripts/entrypoint.sh && chmod +x /app/build/scripts/entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["/app/build/scripts/entrypoint.sh"]
CMD ["web"]
