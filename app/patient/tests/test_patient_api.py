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
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def _check_patient_data(self, patient, payload):
        serializer = PatientSerializer(patient)

        for key in payload.keys():
            if key == 'birth_date':
                self.assertEqual(payload[key].isoformat(), serializer.data[key])
            else:
                self.assertEqual(payload[key], serializer.data[key])


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
