#!/bin/bash

cd /srv/backend
docker compose exec backend sh -c "cd BackofficeApp && python manage.py flushexpiredtokens"