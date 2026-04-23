# Megano Django store

Unified project: one public frontend based on the diploma layout, without duplicated storefront/layout directories.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

## Demo credentials

- admin / 123456
- buyer1 / 123456
- buyer2 / 123456

## Notes

- Public storefront templates: `shopapp/templates/frontend`
- Public storefront static files: `shopapp/static/frontend`
- Old duplicated frontend directories were removed.
- Demo products, categories and store settings are created by migration `0012_storefront_unification`.
