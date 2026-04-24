#!/usr/bin/env sh
set -eu

if ! command -v msgfmt >/dev/null 2>&1; then
  echo "Ошибка: не найден msgfmt."
  echo "Установи gettext: sudo apt update && sudo apt install -y gettext"
  exit 1
fi

python manage.py compilemessages
python manage.py test