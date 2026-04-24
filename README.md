# Учебный интернет-магазин на Django

Учебный проект интернет-магазина на Django с каталогом товаров, корзиной, оформлением заказа, фоновой обработкой платежей, личным кабинетом, историей заказов, 
Docker Compose и наблюдаемостью через Loki/Grafana.

Проект подготовлен для локального запуска, запуска через Docker Compose и публикации на виртуальной машине.

## Цели практической работы

Проект закрывает практическую работу по публикации Django-приложения:

- работа с SSH;
- публикация кода в публичном репозитории;
- управление зависимостями через Poetry или Pipenv;
- сборка Docker-образа приложения;
- запуск приложения через Docker Compose;
- автоматический перезапуск сервисов через `restart: always`;
- публикация приложения на виртуальной машине;
- запуск с `DJANGO_DEBUG=1`, чтобы статика работала без отдельной production-настройки static-сервера.

## Основные возможности сайта

### Storefront

- Главная страница магазина.
- Каталог товаров.
- Фильтрация и сортировка товаров.
- Карточка товара.
- Страница скидок.
- Страница «О магазине».
- Поиск по товарам.
- Переключение языка интерфейса через `/ru/` и `/en/`.

### Корзина

- Добавление товара в корзину.
- Изменение количества.
- Удаление позиции из корзины.
- Поддержка гостевой корзины через сессию.
- Поддержка корзины авторизованного пользователя.
- Объединение гостевой корзины с пользовательской после входа.
- Сохранение цены товара на момент добавления в корзину.

### Оформление заказа

Оформление заказа реализовано пошагово:

1. Данные покупателя.
2. Способ доставки.
3. Способ оплаты.
4. Подтверждение заказа.

После подтверждения:

- создаётся заказ;
- создаются позиции заказа `OrderItem`;
- фиксируются цены и количество товаров;
- корзина очищается;
- пользователь переходит к оплате.

### Оплата

Оплата реализована через учебную очередь платежей.

- `/payment/` создаёт платёж со статусом `pending`.
- `/progress-payment/` показывает статус платежа.
- `process_payments` обрабатывает ожидающие платежи.
- `payment-worker` в Docker Compose запускает обработку автоматически.
- Успешный платёж переводит заказ в статус оплаты `paid`.
- Ошибочный платёж переводит заказ в статус оплаты `failed`.
- Для ошибочных платежей доступна повторная оплата.

Правила учебного платёжного сервиса:

- чётный номер счёта, который не заканчивается на `0`, считается успешным;
- нечётный номер или номер, который заканчивается на `0`, считается ошибочным;
- номер должен состоять только из цифр и быть не длиннее 8 символов.

Примеры:

```text
22222222 → успешная оплата
22222220 → ошибка оплаты
11111111 → ошибка оплаты
```

### Личный кабинет

- Просмотр данных пользователя.
- Профиль пользователя.
- Аватар пользователя.
- История заказов.
- Детальная страница заказа.
- Повторная оплата неоплаченного или ошибочного заказа.

### Админка

В проекте используется стандартная Django admin-панель.

Админка доступна по адресу:

```text
/admin/
```

### Наблюдаемость

В Docker Compose подключены:

- Loki;
- Promtail;
- Grafana.

Grafana используется для просмотра логов контейнеров.

## Что переводится

Интерфейс сайта поддерживает русский и английский языки.

Переводится:

- меню;
- кнопки;
- заголовки;
- системные сообщения;
- формы;
- страницы storefront.

Не переводится автоматически:

- названия товаров;
- описания товаров;
- категории из базы данных;
- производители из базы данных;
- пользовательские адреса;
- комментарии к заказам.

Перевод товарного контента не входит в текущие требования и оставлен как точка расширения.

## Стек

- Python
- Django
- Django REST Framework
- SQLite
- Docker
- Docker Compose
- Loki
- Promtail
- Grafana
- Poetry или Pipenv для управления зависимостями

## Структура проекта

Ключевые части проекта:

```text
shopapp/
  cart.py                 # сервис корзины
  checkout.py             # пошаговое оформление заказа
  payment.py              # создание платежей и progress page
  order_history.py        # история заказов пользователя
  content_pages.py        # about/sale/legacy redirects
  models.py               # Product, Cart, Order, OrderItem, Payment
  forms.py                # формы каталога, checkout, заказов
  views.py                # основные storefront/admin-like views
  management/
    commands/
      seed_demo.py
      process_payments.py
  templates/
    shopapp/
      storefront/

accounts/
  templates/
    accounts/
```

Старые layout-шаблоны больше не используются как источник рабочих страниц. Если в URL names встречается `layout_*`, это legacy-имя маршрута для обратной совместимости старых ссылок, а не использование старой папки `layout`.

## Переменные окружения

Пример `.env` хранится в `.env.example`.

Основные переменные:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000

APP_PORT=8000
GRAFANA_PORT=3000
LOKI_PORT=3100

GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

Для публикации на виртуальной машине добавьте IP сервера:

```env
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0,<IP_ВМ>
CSRF_TRUSTED_ORIGINS=http://<IP_ВМ>:8000,http://<IP_ВМ>:3000
```

По условию практической работы приложение запускается с:

```env
DJANGO_DEBUG=1
```

Это нужно, чтобы статика работала без отдельной production-настройки static-сервера.

## Локальный запуск без Docker

Создайте файл `.env` на основе примера:

```bash
cp .env.example .env
```

### Установка зависимостей

Если в проекте используется Poetry:

```bash
poetry install
poetry shell
```

Если в проекте используется Pipenv:

```bash
pipenv install --dev
pipenv shell
```

### Подготовка базы данных

Примените миграции:

```bash
python manage.py migrate
```

Соберите переводы:

```bash
python manage.py compilemessages
```

Создайте демо-данные:

```bash
python manage.py seed_demo
```

Запустите сервер:

```bash
python manage.py runserver
```

Откройте сайт:

```text
http://127.0.0.1:8000/
```

## Локальный запуск через Docker Compose

Создайте `.env`:

```bash
cp .env.example .env
```

Запустите проект:

```bash
docker compose up -d --build
```

Проверьте контейнеры:

```bash
docker compose ps
```

Проверьте логи приложения:

```bash
docker compose logs -f web
```

Проверьте worker платежей:

```bash
docker compose logs -f payment-worker
```

Откройте сайт:

```text
http://127.0.0.1:8000/
```

Откройте Grafana:

```text
http://127.0.0.1:3000/
```

Если в `.env` не указаны другие значения, стандартные доступы Grafana:

```text
admin / admin
```

## Проверка оплаты в Docker

1. Откройте каталог.
2. Добавьте товар в корзину.
3. Оформите заказ.
4. На странице оплаты введите:

```text
22222222
```

5. Откроется страница статуса платежа.
6. Через несколько секунд `payment-worker` обработает платёж.
7. Обновите страницу статуса.
8. Статус должен измениться на успешный.

Для проверки ошибки оплаты используйте:

```text
22222220
```

или:

```text
11111111
```

## Демо-данные

Команда для заполнения сайта:

```bash
python manage.py seed_demo
```

Пересоздать демо-данные:

```bash
python manage.py seed_demo --reset
```

Демо-доступы:

```text
admin_demo / admin123456
buyer_demo_1 / 123456
buyer_demo_2 / 123456
buyer_demo_3 / 123456
```

## Тесты

Запуск всех тестов:

```bash
python manage.py test
```

Запуск отдельных групп:

```bash
python manage.py test shopapp.tests.test_cart
python manage.py test shopapp.tests.test_checkout
python manage.py test shopapp.tests.test_payment
python manage.py test shopapp.tests.test_order_history
python manage.py test shopapp.tests.test_i18n_ui
```

## Полезные команды Django

Проверка проекта:

```bash
python manage.py check
```

Миграции:

```bash
python manage.py makemigrations
python manage.py migrate
```

Переводы:

```bash
python manage.py makemessages -l en -l ru
python manage.py compilemessages
```

Заполнение демо-данными:

```bash
python manage.py seed_demo
```

Обработка платежей вручную:

```bash
python manage.py process_payments
```

Циклическая обработка платежей:

```bash
python manage.py process_payments --loop --sleep 5
```

## Полезные команды Docker

Остановить проект:

```bash
docker compose down
```

Остановить проект с удалением volumes:

```bash
docker compose down -v
```

Пересобрать:

```bash
docker compose up -d --build
```

Посмотреть логи:

```bash
docker compose logs -f web
docker compose logs -f payment-worker
docker compose logs -f grafana
```

Зайти в контейнер приложения:

```bash
docker compose exec web sh
```

Выполнить миграции вручную:

```bash
docker compose exec web python manage.py migrate
```

Создать демо-данные вручную:

```bash
docker compose exec web python manage.py seed_demo
```

Обработать платежи вручную:

```bash
docker compose exec web python manage.py process_payments
```

Запустить тесты внутри контейнера:

```bash
docker compose exec web python manage.py test
```

## Публикация на виртуальной машине

### 1. Подключение по SSH

```bash
ssh <user>@<IP_ВМ>
```

### 2. Установка Docker и Docker Compose

Проверьте Docker:

```bash
docker --version
docker compose version
```

### 3. Клонирование проекта

```bash
git clone <URL_РЕПОЗИТОРИЯ>
cd <PROJECT_DIR>
```

### 4. Создание `.env`

```bash
cp .env.example .env
nano .env
```

В `.env` укажите IP виртуальной машины:

```env
DJANGO_ALLOWED_HOSTS=<IP_ВМ>,127.0.0.1,localhost,0.0.0.0
CSRF_TRUSTED_ORIGINS=http://<IP_ВМ>:8000,http://<IP_ВМ>:3000
DJANGO_DEBUG=1
```

### 5. Запуск

```bash
docker compose up -d --build
```

### 6. Проверка контейнеров

```bash
docker compose ps
```

Должны быть запущены:

```text
web
payment-worker
loki
promtail
grafana
```

### 7. Проверка логов

```bash
docker compose logs --tail=100 web
docker compose logs --tail=100 payment-worker
docker compose logs --tail=100 grafana
```

### 8. Проверка сайта

```text
http://<IP_ВМ>:8000/
```

Grafana:

```text
http://<IP_ВМ>:3000/
```

Loki:

```text
http://<IP_ВМ>:3100/
```

## Проверка после деплоя

После запуска на ВМ проверьте:

```text
http://<IP_ВМ>:8000/
http://<IP_ВМ>:8000/ru/
http://<IP_ВМ>:8000/en/
http://<IP_ВМ>:8000/admin/
http://<IP_ВМ>:3000/
http://<IP_ВМ>:3100/
```

Smoke-сценарий:

1. Открыть сайт.
2. Перейти в каталог.
3. Добавить товар в корзину.
4. Оформить заказ.
5. Создать платёж.
6. Дождаться обработки через `payment-worker`.
7. Проверить страницу заказа.
8. Проверить историю заказов.
9. Проверить логи в Grafana.

## Важное про Dockerfile

Для Poetry внутри Docker автоматическое создание virtualenv должно быть отключено:

```dockerfile
RUN poetry config virtualenvs.create false
```

Для Pipenv установка должна идти в системное окружение контейнера:

```dockerfile
RUN pipenv install --system --deploy
```

Docker-образ сам является изолированной средой выполнения, поэтому отдельное Python virtualenv внутри контейнера не требуется.

## Безопасность

- Реальный `DJANGO_SECRET_KEY` хранится только в `.env`.
- `.env` не должен попадать в репозиторий.
- В `.env.example` должны быть только примерные значения.
- Для публичной ВМ нужно указать IP в `DJANGO_ALLOWED_HOSTS`.
- Для форм с POST-запросами нужно указать IP в `CSRF_TRUSTED_ORIGINS`.

## Точка расширения

В проект можно добавить:

- PostgreSQL;
- nginx;
- Celery/Redis;
- email-уведомления;
- отзывы к товарам;
- мультиязычный товарный контент;
- CI/CD;
- домен и HTTPS.
