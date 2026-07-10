FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /app/apps/api/requirements.txt
COPY ai/requirements.txt /app/ai/requirements.txt
COPY services/indicator_engine/requirements.txt /app/services/indicator_engine/requirements.txt

RUN pip install --no-cache-dir -r apps/api/requirements.txt && \
    pip install --no-cache-dir -r ai/requirements.txt && \
    pip install --no-cache-dir -r services/indicator_engine/requirements.txt

COPY . /app

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
