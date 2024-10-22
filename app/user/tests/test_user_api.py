from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from django.urls import reverse
from django.contrib.auth import get_user_model

from user.serializers import UserSerializer

from core.models import Role

USERS_CREATE_URL = reverse('user:user-create')
USERS_URL = reverse('user:user-list')
TOKEN_URL = reverse('user:user-token')


def user_detail_url(user_id):
    return reverse('user:user-detail', args=[user_id])


def create_user(**params):
    user_details = {
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'Test name',
        'role_id': 1,
    }
    user_details.update(params)

    return get_user_model().objects.create_user(**user_details)


class PublicUserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.role = Role.objects.create(id=1, name='Admin')

    def test_create_valid_user_success(self):
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test name',
            'role': self.role.id
        }

        res = self.client.post(USERS_CREATE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload['email'])
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)
        self.assertEqual(user.role_id, payload['role'])

    def test_email_taken(self):
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'test name',
            'role_id': self.role.id
        }

        create_user(**payload)
        res = self.client.post(USERS_CREATE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_short_passwords(self):
        payload = {
            'email': 'test@example.com',
            'password': 1234,
            'name': 'test name',
            'role': self.role.id
        }

        res = self.client.post(USERS_CREATE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user = get_user_model().objects.filter(email=payload['email'])
        self.assertFalse(user.exists())

    def test_create_user_no_role(self):
        payload = {
            'email': 'test@example.com',
            'password': 1234,
            'name': 'test name',
        }

        res = self.client.post(USERS_CREATE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user = get_user_model().objects.filter(email=payload['email'])
        self.assertFalse(user.exists())

    def test_create_token(self):
        user_details = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'role_id': self.role.id
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
            'role': self.role.id
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class PrivateUserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='admin@example.com')
        self.client.force_authenticate(user=self.user)
        self.role = Role.objects.create(id=1, name='Admin')

    def test_get_all_users(self):
        user2 = create_user(email='test2@example.com')

        res = self.client.get(USERS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

        serializer1 = UserSerializer(self.user)
        serializer2 = UserSerializer(user2)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)

    def test_get_my_profile(self):
        res = self.client.get(user_detail_url(self.user.id))
        serializer = UserSerializer(self.user)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_user_profile(self):
        other_user = create_user(email='test@example.com')

        res = self.client.get(user_detail_url(other_user.id))
        serializer = UserSerializer(other_user)

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
            'role': self.role.id
        }

        res = self.client.put(user_detail_url(other_user.id), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        other_user.refresh_from_db()
        serializer = UserSerializer(other_user)
        self.assertEqual(res.data, serializer.data)
