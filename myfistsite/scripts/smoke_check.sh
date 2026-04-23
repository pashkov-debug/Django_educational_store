#!/usr/bin/env sh
set -eu

python manage.py check
python manage.py shell -c "
from django.test import Client
client = Client()
paths = ['/', '/catalog/', '/cart/', '/sign-in/', '/admin/']
codes = {path: client.get(path).status_code for path in paths}
print(codes)
assert codes['/'] == 200
assert codes['/catalog/'] == 200
assert codes['/cart/'] == 200
assert codes['/sign-in/'] == 200
assert codes['/admin/'] in (200, 302)
"
