import os
from django.contrib.auth import get_user_model

username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')

if username and password:
    User = get_user_model()
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, password=password, email=email)
        print(f"Superuser '{username}' created successfully.")
    else:
        print(f"Superuser '{username}' already exists.")