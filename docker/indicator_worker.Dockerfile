FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY services/indicator_engine/requirements.txt /app/services/indicator_engine/requirements.txt
RUN pip install --no-cache-dir -r services/indicator_engine/requirements.txt

COPY . /app

CMD ["celery", "-A", "services.indicator_engine.tasks", "worker", "--loglevel=info"]