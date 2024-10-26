from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from core.models import Role, User
from django.contrib.auth.models import Group, Permission



class Command(BaseCommand):
    help = 'Seed Data into Database'

    def handle(self, *args, **options):
        Role.objects.get_or_create(name='Admin')
        Role.objects.get_or_create(name='Doctor')
        Role.objects.get_or_create(name='Receptionist')

        admins_group, created = Group.objects.get_or_create(name='admins_group')
        doctors_group, created = Group.objects.get_or_create(name='doctors_group')
        receptionist_group, created = Group.objects.get_or_create(name='receptionist_group')

        user_content_type = ContentType.objects.filter(app_label='core', model='user').first()
        permissions = Permission.objects.filter(content_type_id=user_content_type.id)

        for permission in permissions:
            admins_group.permissions.add(permission)

        User.objects.create_superuser(
            email='superadmin123@example.com',
            password='goodpass123',
            name='Admin Name',
            role=Role.objects.get(name='Admin')
        )







