from datetime import date, time

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from core.models import Role, User, Patient, Reservation
from reservation.serializers import ReservationSerializer, ReservationDetailSerializer

RESERVATION_URL = reverse('reservation:reservation-list')


def reservation_detail_url(reservation_id):
    return reverse('reservation:reservation-detail', args=[reservation_id])


def create_user(**params):
    user_details = {
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'Test name',
        'role': Role.objects.get(name='Admin'),
        'address': 'test address',
        'phone_number': '1234567890',
    }
    user_details.update(params)

    return get_user_model().objects.create_user(**user_details)


def create_patient(**params):
    patient_details = {
        'name': 'patient name',
        'relative': 'father',
        'relative_name': 'test relative name',
        'phone_number': '0987654321',
        'birth_date': date(2015, 7, 23)
    }

    patient_details.update(params)

    return Patient.objects.create(**patient_details)


def create_reservation(**params):
    reservation_details = {
        "patient": Patient.objects.first(),
        "doctor": User.objects.first(),
        "date": date(2024, 7, 23),
        "time": time(15, 0),
        "description": 'teeth surgery',
        "requirements": 'prepare the surgery tools',
        "patient_reminder": time(10, 0),
        "doctor_reminder": time(14, 30),
    }

    reservation_details.update(params)
    return Reservation.objects.create(**reservation_details)


class PublicReservationAPITests(TestCase):
    def setUp(self):
        call_command('seeder')
        self.client = APIClient()

    def test_crud_patients_auth_required(self):
        res = self.client.get(RESERVATION_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateReservationAPITests(TestCase):
    def setUp(self):
        call_command('seeder')
        self.client = APIClient()
        self.admin = create_user(
            email='admin@example.com',
            role=Role.objects.get(name='Admin'),
            name='Admin'
        )
        self.client.force_authenticate(self.admin)
        self.patient = create_patient()
        self.doctor = create_user(
            email='doctor@example.com',
            role=Role.objects.get(name='Doctor'),
            name='Doctor'
        )

    def test_create_reservation_successfully(self):
        payload = {
            "patient": self.patient.id,
            "doctor": self.doctor.id,
            "date": date(2024, 7, 23),
            "time": time(15, 0),
            "description": 'teeth surgery',
            "requirements": 'prepare the surgery tools',
            "patient_reminder": time(10, 0),
            "doctor_reminder": time(14, 30),
        }

        res = self.client.post(RESERVATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        reservation = Reservation.objects.get(id=res.data['id'])
        serializer = ReservationDetailSerializer(reservation)

        for key in payload.keys():
            if key in ['date', 'time', 'patient_reminder', 'doctor_reminder']:
                self.assertEqual(payload[key].isoformat(), serializer.data[key])
            else:
                self.assertEqual(payload[key], serializer.data[key])

    def test_create_reservation_user_is_not_doctor(self):
        payload = {
            "patient": self.patient.id,
            "doctor": self.admin.id,
            "date": date(2024, 7, 23),
            "time": time(15, 0),
            "description": 'teeth surgery',
            "requirements": 'prepare the surgery tools',
            "patient_reminder": time(10, 0),
            "doctor_reminder": time(14, 30),
        }

        res = self.client.post(RESERVATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_create_reservation_no_requirements_and_reminders(self):
        payload = {
            'patient': self.patient.id,
            "doctor": self.doctor.id,
            "date": date(2024, 7, 23),
            "time": time(15, 0),
            "description": 'simple checkup',
        }

        res = self.client.post(RESERVATION_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        reservation = Reservation.objects.get(id=res.data['id'])
        serializer = ReservationDetailSerializer(reservation)

        for key in payload.keys():
            if key in ['date', 'time']:
                self.assertEqual(payload[key].isoformat(), serializer.data[key])
            else:
                self.assertEqual(payload[key], serializer.data[key])

    def test_get_all_doctors_day_reservations(self):
        other_doctor = create_user(email='doctor2@example.com', role=Role.objects.get(name='Doctor'))
        reservation1 = create_reservation(date=date(2022, 5, 17), doctor=self.doctor, patient=self.patient)
        reservation2 = create_reservation(date=date(2022, 5, 17), doctor=other_doctor, patient=self.patient)
        reservation3 = create_reservation(date=date(2015, 1, 1), doctor=other_doctor, patient=self.patient)

        res = self.client.get(RESERVATION_URL, {'date': date(2022, 5, 17)})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

        serializer1 = ReservationSerializer(reservation1)
        serializer2 = ReservationSerializer(reservation2)
        serializer3 = ReservationSerializer(reservation3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_get_my_day_reservations(self):
        other_doctor = create_user(email='doctor2@example.com', role=Role.objects.get(name='Doctor'))

        self.client.force_authenticate(self.doctor)

        reservation1 = create_reservation(date=date(2022, 5, 17), doctor=self.doctor, patient=self.patient)
        reservation2 = create_reservation(date=date(2022, 5, 17), doctor=other_doctor, patient=self.patient)
        reservation3 = create_reservation(date=date(2022, 5, 20), doctor=self.doctor, patient=self.patient)

        res = self.client.get(RESERVATION_URL, {'date': date(2022, 5, 17)})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

        serializer1 = ReservationSerializer(reservation1)
        serializer2 = ReservationSerializer(reservation2)
        serializer3 = ReservationSerializer(reservation3)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_get_doctors_reservations(self):
        other_doctor = create_user(email='doctor2@example.com', role=Role.objects.get(name='Doctor'))

        create_reservation(date=date(2022, 5, 17), doctor=self.doctor, patient=self.patient)
        create_reservation(date=date(2022, 5, 17), doctor=other_doctor, patient=self.patient)
        create_reservation(date=date(2022, 5, 17), doctor=self.doctor, patient=self.patient)

        res = self.client.get(RESERVATION_URL, {'date': date(2022, 5, 17), 'doctor': self.doctor.id})
        self.assertEqual(len(res.data), 2)


    def test_get_reservation_details(self):
        reservation = create_reservation(date=date(2022, 5, 17), doctor=self.doctor)

        res = self.client.get(reservation_detail_url(reservation.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        serializer = ReservationDetailSerializer(reservation)
        self.assertEqual(serializer.data, res.data)

    def test_partial_update_reservation(self):
        reservation = create_reservation(date=date(2022, 5, 17), doctor=self.doctor)

        res = self.client.patch(reservation_detail_url(reservation.id), {'date': date(2022, 5, 23)})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        reservation.refresh_from_db()
        serializer = ReservationDetailSerializer(reservation)
        self.assertEqual(serializer.data, res.data)

    def test_full_update_reservation(self):
        reservation = create_reservation(date=date(2022, 5, 17), doctor=self.doctor)

        payload = {
            "patient": Patient.objects.first().id,
            "doctor": self.doctor.id,
            "date": date(2002, 5, 5),
            "time": time(20, 0),
            "description": 'simple check',
            "requirements": '',
            "patient_reminder": '',
            "doctor_reminder": '',
        }

        res = self.client.put(reservation_detail_url(reservation.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        reservation.refresh_from_db()
        serializer = ReservationDetailSerializer(reservation)
        self.assertEqual(serializer.data, res.data)

    def test_delete_reservation(self):
        reservation = create_reservation(date=date(2022, 5, 17), doctor=self.doctor)
        res = self.client.delete(reservation_detail_url(reservation.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Reservation.objects.count(), 0)

    def test_crud_permission_denied(self):
        self.client.force_authenticate(self.doctor)
        reservation = create_reservation(date=date(2022, 5, 17), doctor=self.doctor)

        res = self.client.patch(reservation_detail_url(reservation.id), {'date': date(2022, 5, 23)})

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
