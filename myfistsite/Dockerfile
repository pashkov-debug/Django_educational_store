FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.4 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.toml /app/
RUN poetry install --no-root

COPY . /app/

RUN chmod +x /app/entrypoint.sh /app/scripts/smoke_check.sh

EXPOSE 8000

CMD ["sh", "/app/entrypoint.sh"]
