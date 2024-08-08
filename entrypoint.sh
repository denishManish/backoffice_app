#!/bin/bash
set -e

cd ./BackofficeApp

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

exec "$@"
