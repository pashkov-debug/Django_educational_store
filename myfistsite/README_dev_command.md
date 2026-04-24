# Что бы было...

## 1. Применить миграции
```bash
python manage.py migrate
```

## 2. Создать администратора
```bash
python manage.py createsuperuser
```

## 3. Заполнить БД товарами
```bash
python manage.py create_products
```

## 4. Заполнить БД заказами
```bash
python manage.py create_orders
```
## 5. Запустить тесты
```bash
python manage.py test
```

Если нужно запустить только тесты магазина:
```bash
python manage.py test shopapp
```

---

## 6. Запустить сервер
```bash
python manage.py runserver
```

---

## 7. Очистить данные без удаления схемы
```bash
python manage.py flush --no-input
```

После этого нужно заново:
```bash
python manage.py createsuperuser
python manage.py create_products
python manage.py create_orders

```

## 8. Полностью пересоздать локальную SQLite-БД
### Linux / macOS
```bash
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
python manage.py create_products
python manage.py create_orders
python manage.py runserver
```

### Windows PowerShell
```powershell
Remove-Item .\db.sqlite3 -Force
python manage.py migrate
python manage.py createsuperuser
python manage.py create_products
python manage.py create_orders
python manage.py runserver
```

### Фикстуры
```
python manage.py dumpdata auth.user --indent 2 > shopapp/fixtures/users.json
python manage.py dumpdata shopapp.product --indent 2 > shopapp/fixtures/products.json
python manage.py dumpdata shopapp.order --indent 2 > shopapp/fixtures/orders.json
```

### Схема для OpenAPI
```
python manage.py spectacular --file schema.yaml --validate --fail-on-warn
```

### Докер
```
docker compose config
для амд 64
docker plugin install grafana/loki-docker-driver:3.7.0-amd64 --alias loki --grant-all-permissions
для арм64
docker plugin install grafana/loki-docker-driver:3.7.0-arm64 --alias loki --grant-all-permissions

docker plugin ls
docker compose up --build -d
docker compose ps

docker compose exec web python manage.py check

docker compose logs -f web
docker compose logs -f

docker compose down
начисто:
docker compose down -v

полная пересборка без кэша:
docker compose build --no-cache web
docker compose up -d
```

### Локи/графан
```
http://127.0.0.1:3100/ready
http://127.0.0.1:3100/loki/api/v1/status/buildinfo
{service="web",project="myfistsite"}

http://127.0.0.1:3000/login
admin/admin xD
```