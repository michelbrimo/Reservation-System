from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from core.models import Role, Patient

from django.core.management import call_command

from patient.serializers import PatientSerializer

PATIENT_URL = reverse('patient:patient-list')


def patient_detail_url(patient_id):
    return reverse('patient:patient-detail', args=[patient_id])


def create_user(**params):
    user_details = {
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'Test name',
        'role_id': Role.objects.get(name='Admin').id,
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


class PublicPatientTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_crud_patients_auth_required(self):
        res = self.client.get(PATIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePatientTest(TestCase):
    def setUp(self):
        call_command('seeder')
        self.client = APIClient()
        self.user = create_user(email='admin@example.com', role_id=Role.objects.get(name='Admin').id)
        self.client.force_authenticate(self.user)

    def _check_patient_data(self, patient, payload):
        serializer = PatientSerializer(patient)

        for key in payload.keys():
            if key == 'birth_date':
                self.assertEqual(payload[key].isoformat(), serializer.data[key])
            else:
                self.assertEqual(payload[key], serializer.data[key])

    def test_crud_permission_denied(self):
        doctor = create_user(role_id=Role.objects.get(name='Doctor').id)
        self.client.force_authenticate(doctor)

        payload = {
            'name': 'patient name',
            'relative': 'father',
            'relative_name': 'test relative name',
            'phone_number': '0987654321',
            'birth_date': date(2015, 7, 23)
        }

        res = self.client.post(PATIENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Patient.objects.all().count(), 0)

    def test_create_patient_successfully(self):
        payload = {
            'name': 'patient name',
            'relative': 'father',
            'relative_name': 'test relative name',
            'phone_number': '0987654321',
            'birth_date': date(2015, 7, 23)
        }

        res = self.client.post(PATIENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        patient = Patient.objects.get(id=res.data['id'])
        self._check_patient_data(patient, payload)

    def test_create_patient_blank_name_failed(self):
        payload = {
            'name': '',
            'relative': 'father',
            'relative_name': 'test relative name',
            'phone_number': '0123456789',
            'birth_date': date(2015, 7, 23)
        }

        res = self.client.post(PATIENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Patient.objects.all().count(), 0)

    def test_create_patient_invalid_number(self):
        payload = {
            'name': 'test name',
            'relative': 'father',
            'relative_name': 'test relative name',
            'phone_number': 'not a number',
            'birth_date': date(2015, 7, 23)
        }

        res = self.client.post(PATIENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Patient.objects.all().count(), 0)

    def test_create_patient_with_no_relative_success(self):
        payload = {
            'name': 'test name',
            'phone_number': '0123456789',
            'birth_date': date(2015, 7, 23)
        }

        res = self.client.post(PATIENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Patient.objects.all().count(), 1)

        patient = Patient.objects.get(id=res.data['id'])
        self._check_patient_data(patient, payload)

    def test_get_all_patients_successfully(self):
        patient1 = create_patient()
        patient2 = create_patient()

        res = self.client.get(PATIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

        serializer1 = PatientSerializer(patient1)
        serializer2 = PatientSerializer(patient2)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)

    def test_get_patient_details(self):
        patient = create_patient()

        res = self.client.get(patient_detail_url(patient.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        serializer = PatientSerializer(patient)

        self.assertEqual(serializer.data, res.data)

    def test_partially_update_patient_successfully(self):
        patient = create_patient(name='old name')

        payload = {
            'name': 'new name',

        }
        res = self.client.patch(patient_detail_url(patient.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        patient.refresh_from_db()
        serializer = PatientSerializer(patient)

        self.assertEqual(patient.name, payload['name'])
        self.assertEqual(serializer.data, res.data)

    def test_fully_update_patient_successfully(self):
        patient = create_patient(name='old name')

        payload = {
            'name': 'new name',
            'relative': 'new relative',
            'relative_name': 'new relative name',
            'phone_number': '888888888',
            'birth_date': date(2001, 12, 12)
        }

        res = self.client.put(patient_detail_url(patient.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        patient.refresh_from_db()
        serializer = PatientSerializer(patient)

        self.assertEqual(res.data, serializer.data)

    def test_update_patient_blank_name_failed(self):
        patient = create_patient()

        payload = {
            'name': '',
        }

        res = self.client.patch(patient_detail_url(patient.id), payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_patient_no_relative_success(self):
        patient = create_patient()

        payload = {
            'name': 'new name',
            'relative': '',
            'relative_name': '',
            'phone_number': '0934621717',
            'birth_date': date(2001, 12, 12)
        }

        res = self.client.put(patient_detail_url(patient.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        patient.refresh_from_db()
        serializer = PatientSerializer(patient)
        self.assertEqual(res.data, serializer.data)

    def test_update_patient_invalid_phone_number(self):
        patient = create_patient()

        payload = {
            'name': 'new name',
            'relative': '',
            'relative_name': '',
            'phone_number': 'not a number',
            'birth_date': date(2001, 12, 12)
        }

        res = self.client.put(patient_detail_url(patient.id), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_patient_successfully(self):
        patient = create_patient()

        res = self.client.delete(patient_detail_url(patient.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Patient.objects.all().count(), 0)
