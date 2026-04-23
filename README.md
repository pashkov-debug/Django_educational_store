# Megano Django store

Единый проект интернет-магазина на Django с одним публичным фронтом, Docker/Poetry-деплоем и сохранённой инфраструктурой мониторинга (`loki`, `promtail`, `grafana`).

## Что внутри

- магазин: главная, каталог, карточка товара, корзина, checkout, оплата, профиль, история заказов;
- Django Admin;
- Docker + Docker Compose;
- Poetry без создания отдельного virtualenv внутри контейнера;
- мониторинг через `loki`, `promtail`, `grafana` по профилю `monitoring`;
- demo-данные из миграций/фикстур.

## Demo-учётки

- `admin / 123456`
- `buyer1 / 123456`
- `buyer2 / 123456`

## 1. Локальный запуск без Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install --no-root
cp .env.example .env
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Сайт: `http://127.0.0.1:8000/`  
Админка: `http://127.0.0.1:8000/admin/`

## 2. Локальный запуск через Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f web
```

Сайт: `http://127.0.0.1:8000/`  
Админка: `http://127.0.0.1:8000/admin/`

### Мониторинг локально

```bash
docker compose --profile monitoring up -d
```

После этого:
- Django: `http://127.0.0.1:8000/`
- Loki: `http://127.0.0.1:3100/`
- Grafana: `http://127.0.0.1:3000/`

## 3. Что нужно отредактировать перед деплоем на ВМ

Открой `.env` и проверь минимум эти поля:

```dotenv
DJANGO_SECRET_KEY=свой_секретный_ключ
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,89.232.176.127
DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1,http://localhost,http://89.232.176.127
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=сложный_пароль
```

Если IP или домен изменится — обнови `DJANGO_ALLOWED_HOSTS` и `DJANGO_CSRF_TRUSTED_ORIGINS`.

## 4. Деплой на ВМ по SSH

Ниже сценарий для случая, когда:
- ВМ уже создана;
- SSH-ключ уже есть;
- репозиторий уже залит на GitHub.

### 4.1. Подключение к серверу

С локальной машины:

```bash
chmod 600 ~/.ssh/id_rsa
ssh -i ~/.ssh/id_rsa ubuntu@89.232.176.127
```

Если у образа другой системный пользователь, замени `ubuntu` на нужного.

### 4.2. Установка Docker на Ubuntu-сервере

На сервере:

```bash
chmod +x scripts/install_docker_ubuntu.sh
./scripts/install_docker_ubuntu.sh
```

После установки лучше переподключиться по SSH.

Проверка:

```bash
docker --version
docker compose version
```

### 4.3. Клонирование проекта на сервер

На сервере:

```bash
git clone <URL_ТВОЕГО_REPO> myfistsite
cd myfistsite
cp .env.example .env
nano .env
```

Отредактируй `.env`:
- укажи корректный `DJANGO_SECRET_KEY`;
- проверь IP/домен в `DJANGO_ALLOWED_HOSTS` и `DJANGO_CSRF_TRUSTED_ORIGINS`;
- при необходимости поменяй пароль Grafana.

### 4.4. Запуск проекта

На сервере:

```bash
docker compose up -d --build
docker compose logs -f web
```

Сайт будет доступен по адресу:

- `http://89.232.176.127:8000/`

### 4.5. Запуск мониторинга

На сервере:

```bash
docker compose --profile monitoring up -d
```

После этого доступны:
- магазин: `http://89.232.176.127:8000/`
- grafana: `http://89.232.176.127:3000/`

## 5. Обновление проекта после пуша в GitHub

Вариант вручную на сервере:

```bash
cd ~/myfistsite
git pull
docker compose up -d --build
```

Вариант через скрипт с локальной машины:

```bash
chmod +x scripts/deploy_vm.sh

DEPLOY_HOST=89.232.176.127 \
DEPLOY_USER=ubuntu \
DEPLOY_PATH=/home/ubuntu/myfistsite \
REPO_URL=<URL_ТВОЕГО_REPO> \
BRANCH=main \
SSH_OPTS="-i ~/.ssh/id_rsa" \
./scripts/deploy_vm.sh
```

## 6. Smoke-check после запуска

На сервере или локально:

```bash
chmod +x scripts/smoke_check.sh
./scripts/smoke_check.sh
```

## 7. Что важно по ТЗ

Закрыто:
- Django-проект;
- переносимость через `.env` + миграции;
- Django Admin;
- demo-данные;
- один публичный фронт;
- Docker/Compose деплой;
- SSH/ВМ инструкции.

Осторожность:
- отдельная реальная очередь обработки платежей в фоне должна быть подтверждена отдельно, если куратор будет строго проверять именно очередь как отдельный worker-процесс.

## 8. Полезные команды

Остановить всё:

```bash
docker compose down
```

Остановить вместе с мониторингом:

```bash
docker compose --profile monitoring down
```

Пересобрать только web:

```bash
docker compose up -d --build web
```

Посмотреть контейнеры:

```bash
docker compose ps
```
