FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=0 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl \
  && curl -sSL https://install.python-poetry.org | python - \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN /opt/poetry/bin/poetry install --no-root --only main

COPY triggerflow_canvas ./triggerflow_canvas
COPY agently ./agently
COPY tests ./tests

EXPOSE 8000

CMD ["uvicorn", "triggerflow_canvas.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
