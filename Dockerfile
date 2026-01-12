FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache -r uv.lock

COPY src/ ./src/

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["python", "-m", "app.api.main"]

