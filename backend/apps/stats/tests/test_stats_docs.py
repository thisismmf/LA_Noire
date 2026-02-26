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
                "total_employees": 15,
                "active_cases": 4,
            },
        )
        self.assertNotEqual(response_examples["SuccessResponse"]["value"], {"success": True})

    def test_login_schema_uses_structured_response_example(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)
        login_post = schema["paths"]["/api/v1/auth/login/"]["post"]
        response_examples = login_post["responses"]["200"]["content"]["application/json"]["examples"]

        self.assertIn("tokens", response_examples["SuccessResponse"]["value"])
        self.assertIn("user", response_examples["SuccessResponse"]["value"])

    def test_all_operations_have_descriptions_and_json_examples(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        for path, operations in schema["paths"].items():
            for method, operation in operations.items():
                self.assertTrue(operation.get("description"), f"{method.upper()} {path} is missing a description")

                request_body = operation.get("requestBody", {})
                request_content = request_body.get("content", {})
                if "application/json" in request_content:
                    self.assertTrue(
                        request_content["application/json"].get("examples"),
                        f"{method.upper()} {path} is missing request examples",
                    )

                for status_code, response in operation.get("responses", {}).items():
                    if not str(status_code).startswith("2"):
                        continue
                    content = response.get("content", {})
                    if "application/json" not in content:
                        continue
                    examples = content["application/json"].get("examples")
                    self.assertTrue(examples, f"{method.upper()} {path} is missing success response examples")
                    for example in examples.values():
                        self.assertNotEqual(example["value"], {"success": True})
                        self.assertNotEqual(example["value"], {"example": "value"})
                    break

    def test_complex_workflow_examples_are_domain_specific(self):
        schema = SchemaGenerator().get_schema(request=None, public=True)

        complaint_post = schema["paths"]["/api/v1/cases/complaints/"]["post"]
        complaint_example = complaint_post["requestBody"]["content"]["application/json"]["examples"]["RequestExample"]["value"]
        self.assertIn("complainants", complaint_example)
        self.assertEqual(complaint_example["complainants"][0]["full_name"], "Mary Hudson")

        evidence_post = schema["paths"]["/api/v1/cases/{case_id}/evidence/"]["post"]
        evidence_example = evidence_post["requestBody"]["content"]["application/json"]["examples"]["RequestExample"]["value"]
        self.assertEqual(evidence_example["evidence_type"], "witness_statement")
        self.assertIn("witness_statement", evidence_example)

        report_get = schema["paths"]["/api/v1/cases/{case_id}/report/"]["get"]
        report_example = report_get["responses"]["200"]["content"]["application/json"]["examples"]["SuccessResponse"]["value"]
        self.assertIn("assignments", report_example)
        self.assertIn("evidence", report_example)
