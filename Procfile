web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && python -m gunicorn the_80_percent_bill.wsgi --bind 0.0.0.0:${PORT:-8000}
