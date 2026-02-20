from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.rbac.models import Role, UserRole
from apps.rbac.constants import ROLE_BASE_USER


class AuthTests(APITestCase):
    def setUp(self):
        Role.objects.get_or_create(slug=ROLE_BASE_USER, defaults={"name": "Base User", "is_system": True})

    def _register(self, username="user1", email="u1@example.com", phone="123", national_id="nid1"):
        url = "/api/v1/auth/register/"
        data = {
            "username": username,
            "email": email,
            "phone": phone,
            "national_id": national_id,
            "first_name": "A",
            "last_name": "B",
            "password": "Pass1234!",
        }
        return self.client.post(url, data, format="json")

    def _login(self, identifier, password="Pass1234!"):
        return self.client.post("/api/v1/auth/login/", {"identifier": identifier, "password": password}, format="json")

    def test_register_assigns_base_role(self):
        response = self._register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="user1")
        self.assertTrue(UserRole.objects.filter(user=user, role__slug=ROLE_BASE_USER).exists())

    def test_login_with_username(self):
        self._register()
        response = self._login("user1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)

    def test_login_with_email(self):
        self._register()
        response = self._login("u1@example.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_with_phone(self):
        self._register()
        response = self._login("123")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_with_national_id(self):
        self._register()
        response = self._login("nid1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_rbac_forbidden_for_base_user(self):
        self._register()
        user = User.objects.get(username="user1")
        self.client.force_authenticate(user=user)
        res = self.client.get("/api/v1/rbac/roles/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
