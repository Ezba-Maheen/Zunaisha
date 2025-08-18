from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates a temporary superuser to regain access to the admin panel.'

    def handle(self, *args, **options):
        if not User.objects.filter(username='tempadmin').exists():
            User.objects.create_superuser('tempadmin', 'tempadmin@example.com', 'secure_temporary_password_123')
            self.stdout.write(self.style.SUCCESS('Successfully created temporary superuser "tempadmin".'))
        else:
            self.stdout.write(self.style.SUCCESS('Superuser "tempadmin" already exists.'))