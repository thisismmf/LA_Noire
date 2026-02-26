from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.rbac.models import Role, UserRole
from apps.rbac.constants import ROLE_BASE_USER, ROLE_SYSTEM_ADMIN


class AuthTests(APITestCase):
    def setUp(self):
        Role.objects.get_or_create(slug=ROLE_BASE_USER, defaults={"name": "Base User", "is_system": True})
        Role.objects.get_or_create(slug=ROLE_SYSTEM_ADMIN, defaults={"name": "System Admin", "is_system": True})

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

    def test_system_admin_can_list_users_with_filters(self):
        self._register()
        admin = User.objects.create_user(
            username="sysadmin",
            email="sysadmin@example.com",
            phone="999",
            national_id="nid999",
            password="Pass1234!",
            first_name="S",
            last_name="A",
        )
        UserRole.objects.get_or_create(user=admin, role=Role.objects.get(slug=ROLE_SYSTEM_ADMIN))
        self.client.force_authenticate(user=admin)
        res = self.client.get("/api/v1/users/?username=user1")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["username"], "user1")
        self.assertIn("roles", res.data[0])

    def test_system_roles_are_immutable(self):
        admin = User.objects.create_user(
            username="admin2",
            email="admin2@example.com",
            phone="998",
            national_id="nid998",
            password="Pass1234!",
            first_name="S",
            last_name="A",
        )
        UserRole.objects.get_or_create(user=admin, role=Role.objects.get(slug=ROLE_SYSTEM_ADMIN))
        base_role = Role.objects.get(slug=ROLE_BASE_USER)
        self.client.force_authenticate(user=admin)
        patch_res = self.client.patch(f"/api/v1/rbac/roles/{base_role.id}/", {"name": "Changed"}, format="json")
        self.assertEqual(patch_res.status_code, status.HTTP_403_FORBIDDEN)
        delete_res = self.client.delete(f"/api/v1/rbac/roles/{base_role.id}/")
        self.assertEqual(delete_res.status_code, status.HTTP_403_FORBIDDEN)
