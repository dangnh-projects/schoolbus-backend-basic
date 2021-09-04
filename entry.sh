#!/bin/bash
cd ischoolbus
export DJANGO_SETTINGS_MODULE=ischoolbus.production

exec gunicorn ischoolbus.wsgi:application \
    --name ischoolbus_backend \
    --bind 0.0.0.0:8000 \
    --workers 5 \
"$@"
