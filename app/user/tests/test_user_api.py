from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from django.urls import reverse
from django.contrib.auth import get_user_model

from user.serializers import UserSerializer, UserDetailSerializer

from core.models import Role
from django.core.management import call_command


USERS_URL = reverse('user:user-list')
TOKEN_URL = reverse('user:user-token')


def user_detail_url(user_id):
    return reverse('user:user-detail', args=[user_id])


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


class PublicUserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        call_command('seeder')

    def test_crud_users_auth_required(self):
        res = self.client.get(USERS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token(self):
        user_details = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'role': Role.objects.get(name='Admin')
        }
        create_user(**user_details)

        payload = {
            'email': user_details['email'],
            'password': user_details['password'],
        }
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        create_user()

        payload = {
            'email': 'WrongEmail@example.com',
            'password': 'wrong password',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_user(self):
        payload = {
            'email': 'NoUser@example.com',
            'password': '',
            'name': 'Test name',
            'role': Role.objects.get(name='Admin').id,
            'address': 'test address',
            'phone_number': '1234567890',
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class PrivateUserTests(TestCase):
    def setUp(self):
        call_command('seeder')
        self.client = APIClient()
        self.user = create_user(email='admin@example.com', role=Role.objects.get(name='Admin'))
        self.client.force_authenticate(user=self.user)

    def _change_client_user(self, **params):
        self.not_admin_user = create_user(**params)
        self.client.force_authenticate(user=self.not_admin_user)

    def test_create_valid_user_success(self):
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test name',
            'role': Role.objects.get(name='Doctor').id,
            'address': 'test address',
            'phone_number': '1234567890',
        }

        res = self.client.post(USERS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)
        self.assertEqual(user.role.id, payload['role'])

    def test_email_taken(self):
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'test name',
            'role': Role.objects.get(name='Admin'),
            'address': 'test address',
            'phone_number': '1234567890',
        }

        create_user(**payload)

        payload['role'] = Role.objects.get(name='Admin').id
        res = self.client.post(USERS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_short_passwords(self):
        payload = {
            'email': 'test@example.com',
            'password': 1234,
            'name': 'test name',
            'role': Role.objects.get(name='Admin').id,
            'address': 'test address',
            'phone_number': '1234567890',
        }

        res = self.client.post(USERS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user = get_user_model().objects.filter(email=payload['email'])
        self.assertFalse(user.exists())

    def test_create_user_no_role(self):
        payload = {
            'email': 'test@example.com',
            'password': 1234,
            'name': 'test name',
            'address': 'test address',
            'phone_number': '1234567890',
        }

        res = self.client.post(USERS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user = get_user_model().objects.filter(email=payload['email'])
        self.assertFalse(user.exists())

    def test_create_user_invalid_number(self):
        payload = {
            'email': 'test@example.com',
            'password': 1234,
            'name': 'test name',
            'address': 'test address',
            'phone_number': '1234567890',
        }

        res = self.client.post(USERS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_all_users(self):
        user2 = create_user(email='test2@example.com')

        res = self.client.get(USERS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # 3 Users (the Client User, the New User and the Admin)
        self.assertEqual(len(res.data), 3)

        serializer1 = UserSerializer(self.user)
        serializer2 = UserSerializer(user2)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)

    def test_get_users_based_on_role_id(self):
        doctor1 = create_user(email='doctor@example.com', role=Role.objects.get(name='Doctor'))
        doctor2 = create_user(email='doctor2@example.com', role=Role.objects.get(name='Doctor'))
        admin2 = create_user(email='admin2@example.com', role=Role.objects.get(name='Admin'))

        res = self.client.get(USERS_URL, {'role': doctor1.role.name})

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(res.data), 2)

        doctor1_serializer = UserSerializer(doctor1)
        doctor2_serializer = UserSerializer(doctor2)
        admin1_serializer = UserSerializer(self.user)
        admin2_serializer = UserSerializer(admin2)

        self.assertIn(doctor1_serializer.data, res.data)
        self.assertIn(doctor2_serializer.data, res.data)

        self.assertNotIn(admin1_serializer.data, res.data)
        self.assertNotIn(admin2_serializer.data, res.data)

    def test_get_users_name_starts_with_x(self):
        create_user(email='doctor@example.com', role=Role.objects.get(name='Doctor'), name='Lara')
        create_user(email='receptionist@example.com', role=Role.objects.get(name='Receptionist'), name='Laman')

        res = self.client.get(USERS_URL, {'name': 'La'})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_get_my_profile(self):
        res = self.client.get(user_detail_url(self.user.id))
        serializer = UserDetailSerializer(self.user)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_user_profile(self):
        other_user = create_user(email='test@example.com')

        res = self.client.get(user_detail_url(other_user.id))
        serializer = UserDetailSerializer(other_user)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_delete_user_profile(self):
        other_user = create_user(email='test@example.com')
        res = self.client.delete(user_detail_url(other_user.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(get_user_model().objects.filter(id=other_user.id).exists())

    def test_partial_update_user_profile(self):
        other_user = create_user(email='test@example.com')
        payload = {
            'name': "new name",
        }

        res = self.client.patch(user_detail_url(other_user.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], payload['name'])

    def test_full_update_user_profile(self):
        other_user = create_user(email='test@example.com')
        payload = {
            'email': "NewEmail@example.com",
            'password': "NewPass@123",
            'name': "New name",
            'role': Role.objects.get(name='Admin').id,
            'address': 'test address',
            'phone_number': '1234567890',
        }

        res = self.client.put(user_detail_url(other_user.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        other_user.refresh_from_db()
        serializer = UserDetailSerializer(other_user)
        serializer = UserDetailSerializer(other_user)
        self.assertEqual(res.data, serializer.data)

    def test_create_user_permission_denied(self):
        self._change_client_user(email='NotAdmin@example.com', role=Role.objects.get(name='Doctor'))

        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test name',
            'role': Role.objects.get(name='Doctor').id,
            'address': 'test address',
            'phone_number': '1234567890',
        }

        res = self.client.post(USERS_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        user = get_user_model().objects.filter(email=payload['email'])
        self.assertFalse(user.exists())

    def test_update_user_permission_denied(self):
        self._change_client_user(email='NotAdmin@example.com', role=Role.objects.get(name='Doctor'))

        payload = {
            'name': 'New Name',
        }

        user = create_user()

        res = self.client.patch(user_detail_url(user.id), payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(user.name, payload['name'])

    def test_delete_user_permission_denied(self):
        self._change_client_user(email='NotAdmin@example.com', role=Role.objects.get(name='Doctor'))

        user = create_user()

        res = self.client.delete(user_detail_url(user.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        user = get_user_model().objects.filter(id=user.id)
        self.assertTrue(user.exists())

    def test_view_user_permission_denied(self):
        self._change_client_user(email='NotAdmin@example.com', role=Role.objects.get(name='Doctor'))
        res = self.client.get(USERS_URL)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_user_details_permission_denied(self):
        self._change_client_user(email='NotAdmin@example.com', role=Role.objects.get(name='Doctor'))
        user = create_user()

        res = self.client.get(user_detail_url(user.id))

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
