#!/usr/bin/env sh
set -eu

python manage.py check
python manage.py shell -c "
from django.test import Client
client = Client()
paths = ['/', '/en/', '/en/blog/', '/en/catalog/', '/api/schema/']
codes = {path: client.get(path).status_code for path in paths}
print(codes)
assert codes['/'] in (200, 302)
assert codes['/en/'] == 200
assert codes['/en/blog/'] == 200
assert codes['/en/catalog/'] == 200
assert codes['/api/schema/'] in (200, 302, 403)
"
