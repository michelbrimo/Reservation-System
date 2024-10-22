from django.core.management.base import BaseCommand
from core.models import Role


class Command(BaseCommand):
    help = 'Description of my custom command'

    def handle(self, *args, **options):
        Role.objects.create(name='Admin2')
        Role.objects.create(name='Doctor2')
        Role.objects.create(name='Receptionist2')
