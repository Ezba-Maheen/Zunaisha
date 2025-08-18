import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zunaisha.settings")
django.setup()

from django.contrib.auth.models import User
from django.db import connection

def create_temporary_superuser():
    with connection.cursor() as cursor:
        if not User.objects.filter(username='tempadmin').exists():
            User.objects.create_superuser('tempadmin', 'tempadmin@example.com', 'secure_temporary_password_123')
            print('Successfully created temporary superuser "tempadmin".')
        else:
            print('Superuser "tempadmin" already exists.')

if __name__ == "__main__":
    create_temporary_superuser()