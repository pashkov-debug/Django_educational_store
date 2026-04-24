FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.5 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml /app/pyproject.toml

RUN poetry install --only main --no-root --no-ansi

COPY . /app/

RUN python manage.py compilemessages

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]