#!/bin/sh
set -e
echo "Menunggu PostgreSQL di $POSTGRES_HOST:$POSTGRES_PORT..."
until python -c "import socket,os; s=socket.socket(); s.connect((os.environ['POSTGRES_HOST'], int(os.environ['POSTGRES_PORT']))); s.close()" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL siap."

python manage.py makemigrations kobo_mce --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput || true

if [ "$DJANGO_DEBUG" = "1" ]; then
  echo "Mode pengembangan (runserver)."
  exec python manage.py runserver 0.0.0.0:8000
else
  echo "Mode produksi (gunicorn)."
  exec gunicorn ahp_mce.wsgi:application --bind 0.0.0.0:8000 --workers 3
fi
