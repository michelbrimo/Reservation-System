from datetime import date, time

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
            role=Role.objects.get(name='Admin'),
            address='test address',
            phone_number='1234567890',
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.role, Role.objects.get(name='Admin'))

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
                role=Role.objects.get(name='Admin'),
                address='test address',
                phone_number='1234567890',
            )
            self.assertEqual(user.email, expected)

    def test_new_user_with_no_email(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email='',
                password='testpass123',
                role=Role.objects.get(name='Admin'),
                address='test address',
                phone_number='1234567890',
            )

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            email='test@example.com',
            password='testpass123',
            role=Role.objects.get(name='Admin'),
            address='test address',
            phone_number='1234567890',
            name='Admin'
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

    def test_create_reservation_successfully(self):
        doctor = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123',
            role=Role.objects.get(name='Doctor'),
            address='test address',
            phone_number='1234567890',
            name='Doctor'
        )

        patient = models.Patient.objects.create(
            name='test patient',
            phone_number='0123456789',
            birth_date=date(2015, 7, 23),
        )

        payload = {
            "patient_id": patient.id,
            "doctor_id": doctor.id,
            "date": date(2024, 7, 23),
            "time": time(15, 0),
            "description": 'teeth surgery',
            "requirements": 'prepare the surgery tools',
            "patient_reminder": time(10, 0),
            "doctor_reminder": time(14, 30),
        }

        res = models.Reservation.objects.create(**payload)

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(res, key))
