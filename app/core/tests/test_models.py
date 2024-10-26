from datetime import date

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command


from core import models
from core.models import Role


class ModelTests(TestCase):
    def setUp(self):
        call_command('seeder')

    def test_create_user_with_email_successfully(self):
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            role_id=Role.objects.get(name='Admin').id,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.role_id, Role.objects.get(name='Admin').id)

    def test_new_user_email_normalized(self):
        emails = [
            ['Test1@example.com', 'Test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
        ]
        password = 'testpass123'

        for email, expected in emails:
            user = get_user_model().objects.create_user(
                email=email,
                password=password,
                role_id=Role.objects.get(name='Admin').id
            )
            self.assertEqual(user.email, expected)

    def test_new_user_with_no_email(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='',
                password='testpass123',
                role_id=Role.objects.get(name='Admin').id
            )

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='testpass123',
            role_id=Role.objects.get(name='Admin').id
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


    def test_create_patient_successfully(self):
        payload = {
            'name': 'test name',
            'relative': 'father',
            'relative_name': 'test relative name',
            'phone_number': '0123456789',
            'birth_date': date(2015, 7, 23)
        }

        res = models.Patient.objects.create(**payload)

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(res, key))
