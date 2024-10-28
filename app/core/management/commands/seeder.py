from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from core.models import Role, User
from django.contrib.auth.models import Group, Permission
from django.db.models import Q


class Command(BaseCommand):
    help = 'Seed Data into Database'

    def handle(self, *args, **options):
        # create roles
        Role.objects.get_or_create(name='Admin')
        Role.objects.get_or_create(name='Doctor')
        Role.objects.get_or_create(name='Receptionist')

        # create groups with its permission
        self.admins_group, created = Group.objects.get_or_create(name='admins_group')
        self.doctors_group, created = Group.objects.get_or_create(name='doctors_group')
        self.receptionist_group, created = Group.objects.get_or_create(name='receptionist_group')

        self.add_user_api_permissions()
        self.add_patient_api_permissions()

        # create super_user
        User.objects.create_superuser(
            email='superadmin123@example.com',
            password='goodpass123',
            name='Admin Name',
            role=Role.objects.get(name='Admin')
        )

    def add_user_api_permissions(self):
        user_content_type = ContentType.objects.filter(app_label='core', model='user').first()
        user_permissions = Permission.objects.filter(content_type_id=user_content_type.id)

        self.admins_group.permissions.add(*user_permissions)

    def add_patient_api_permissions(self):
        def give_admins_permissions():
            self.admins_group.permissions.add(*patient_permissions)

        def give_doctors_permissions():
            filtered_permissions = patient_permissions.filter(Q(codename__contains='view'))
            self.doctors_group.permissions.add(*filtered_permissions)

        def give_receptionist_permissions():
            filtered_permissions = patient_permissions.filter(
                Q(codename__contains='view') |
                Q(codename__contains='add') |
                Q(codename__contains='change')
            )

            self.receptionist_group.permissions.add(*filtered_permissions)

        patient_content_type = ContentType.objects.filter(app_label='core', model='patient').first()
        patient_permissions = Permission.objects.filter(content_type_id=patient_content_type.id)

        give_admins_permissions()
        give_doctors_permissions()
        give_receptionist_permissions()
