#!/usr/bin/env bash

# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run database migrations
python manage.py migrate

# Create a superuser
python -c 'import os; from django.contrib.auth import get_user_model; User = get_user_model(); username=os.environ.get("DJANGO_SUPERUSER_USERNAME"); password=os.environ.get("DJANGO_SUPERUSER_PASSWORD"); email=os.environ.get("DJANGO_SUPERUSER_EMAIL"); if username and password: User.objects.create_superuser(username=username, password=password, email=email)'