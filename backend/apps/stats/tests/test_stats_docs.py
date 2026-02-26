from drf_spectacular.generators import SchemaGenerator
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.cases.constants import CaseSourceType, CaseStatus, CrimeLevel
from apps.cases.models import Case
from apps.rbac.constants import ROLE_DETECTIVE
from apps.rbac.models import Role, UserRole


class StatsDocsTests(APITestCase):
    def setUp(self):
        Role.objects.get_or_create(slug=ROLE_DETECTIVE, defaults={"name": "detective", "is_system": True})

    def test_stats_overview_is_public_and_returns_counts(self):
        detective = User.objects.create_user(
            username="stats_detective",
            email="stats_detective@example.com",
            phone="5551000000",
            national_id="stats-detective",
            password="Pass1234!",
            first_name="Stats",
            last_name="Detective",
        )
        UserRole.objects.get_or_create(user=detective, role=Role.objects.get(slug=ROLE_DETECTIVE))
        Case.objects.create(
            title="Solved case",
            description="Closed investigation",
            crime_level=CrimeLevel.LEVEL_2,
            location="Downtown",
            status=CaseStatus.CLOSED_SOLVED,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective,
        )
        Case.objects.create(
            title="Active case",
            description="Open investigation",
            crime_level=CrimeLevel.LEVEL_1,
            location="Harbor",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.CRIME_SCENE,
            created_by=detective,
        )

        response = self.client.get("/api/v1/stats/overview/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "total_solved_cases": 1,
                "total_employees": 1,
                "active_cases": 1,
            },
        )

    def test_schema_describes_public_stats_route_and_real_examples(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        stats_get = schema["paths"]["/api/v1/stats/overview/"]["get"]
        response_examples = stats_get["responses"]["200"]["content"]["application/json"]["examples"]

        self.assertIn("Authentication: No JWT required.", stats_get["description"])
        self.assertEqual(
            response_examples["SuccessResponse"]["value"],
            {
                "total_solved_cases": 1,
                "total_employees": 1,
                "active_cases": 1,
            },
        )
        self.assertNotEqual(response_examples["SuccessResponse"]["value"], {"success": True})

    def test_login_schema_uses_structured_response_example(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        login_post = schema["paths"]["/api/v1/auth/login/"]["post"]
        response_examples = login_post["responses"]["200"]["content"]["application/json"]["examples"]

        self.assertIn("tokens", response_examples["SuccessResponse"]["value"])
        self.assertIn("user", response_examples["SuccessResponse"]["value"])
