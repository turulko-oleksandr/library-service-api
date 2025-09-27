from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

CREATE_USER_URL = reverse("library_service_users:create")
TOKEN_URL = reverse("library_service_users:token_obtain_pair")
ME_URL = reverse("library_service_users:manage")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class UserModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = "test@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        email = "test@EXAMPLE.COM"
        user = get_user_model().objects.create_user(email, "test123")

        self.assertEqual(user.email, email.lower())

    def test_new_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, "test123")

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(
            "super@example.com",
            "superpass123"
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


class PublicUserApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_exists(self):
        payload = {"email": "test@example.com", "password": "testpass123"}
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = {"email": "test@example.com", "password": "pw"}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload["email"]
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        user_details = {"email": "test@example.com", "password": "testpass123"}
        create_user(**user_details)

        res = self.client.post(TOKEN_URL, user_details)

        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        create_user(email="test@example.com", password="goodpass")
        payload = {"email": "test@example.com", "password": "badpass"}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("access", res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token_no_user(self):
        payload = {"email": "test@example.com", "password": "testpass123"}
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):

    def setUp(self):
        self.user = create_user(
            email="test@example.com",
            password="testpass123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {
                "id": self.user.id,
                "email": self.user.email,
                "is_staff": self.user.is_staff,
            },
        )

    def test_post_me_not_allowed(self):
        res = self.client.post(ME_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {"password": "newpassword123"}
        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
