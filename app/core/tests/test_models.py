from datetime import date

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_patient(**kwargs):
    return models.Patient.objects.create(**kwargs)

class ModelTests(TestCase):
    def setUp(self):
        self.role = models.Role.objects.create(id=1, name='Admin')

    def test_create_user_with_email_successful(self):
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            role_id=self.role.id
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.role_id, self.role.id)

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
                role_id=self.role.id
            )
            self.assertEqual(user.email, expected)

    def test_new_user_with_no_email(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='',
                password='testpass123',
                role_id=self.role.id
            )

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='testpass123',
            role_id=self.role.id
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)




# class ModelTests(TestCase):
#     def test_create_patient(self):
#         payload = {
#             'name': 'test name',
#             'relative': 'father',
#             'relative_name': 'test relative name',
#             'phone_number': '0123456789',
#             'birth_date': date(2015, 7, 23)
#         }
#
#         res = models.Patient.objects.create(**payload)
#
#         self.assertEqual(res.name, payload['name'])
#         self.assertEqual(res.relative, payload['relative'])
#         self.assertEqual(res.relative_name, payload['relative_name'])
#         self.assertEqual(res.phone_number, payload['phone_number'])
#         self.assertEqual(res.birth_date, payload['birth_date'])
