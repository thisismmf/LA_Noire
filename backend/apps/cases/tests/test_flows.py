from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.rbac.models import Role, UserRole
from apps.rbac.constants import (
    ROLE_BASE_USER,
    ROLE_DETECTIVE,
    ROLE_POLICE_OFFICER,
    ROLE_SERGEANT,
)
from apps.cases.models import Complaint, Case
from apps.cases.constants import ComplaintStatus, CrimeLevel, CaseStatus, CaseSourceType
from apps.cases.models import CaseAssignment
from apps.suspects.models import Person, WantedRecord
from apps.suspects.utils import compute_most_wanted
from apps.rewards.models import RewardCode
from apps.payments.models import Payment
from apps.payments.gateway import sign_payload


class CaseFlowTests(APITestCase):
    def setUp(self):
        for slug in [ROLE_BASE_USER, ROLE_DETECTIVE, ROLE_POLICE_OFFICER, ROLE_SERGEANT]:
            Role.objects.get_or_create(slug=slug, defaults={"name": slug, "is_system": True})

    def create_user(self, username, role_slug):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            phone=f"{username}123",
            national_id=f"{username}nid",
            password="Pass1234!",
            first_name="Test",
            last_name="User",
        )
        role = Role.objects.get(slug=role_slug)
        UserRole.objects.get_or_create(user=user, role=role)
        return user

    def test_complaint_three_strike_invalidation(self):
        user = self.create_user("complainant", ROLE_BASE_USER)
        self.client.force_authenticate(user=user)
        complaint = Complaint.objects.create(
            title="Test",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_3,
            location="Loc",
            status=ComplaintStatus.RETURNED_TO_COMPLAINANT,
            created_by=user,
        )
        for _ in range(2):
            res = self.client.post(f"/api/v1/cases/complaints/{complaint.id}/resubmit/", {"title": "Upd"}, format="json")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            complaint.refresh_from_db()
            complaint.status = ComplaintStatus.RETURNED_TO_COMPLAINANT
            complaint.save()
        res = self.client.post(f"/api/v1/cases/complaints/{complaint.id}/resubmit/", {"title": "Upd"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, ComplaintStatus.VOIDED)

    def test_vehicle_evidence_xor_validation(self):
        detective = self.create_user("detective", ROLE_DETECTIVE)
        self.client.force_authenticate(user=detective)
        case = Case.objects.create(
            title="Case",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_3,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective,
        )
        CaseAssignment.objects.create(case=case, user=detective, role_in_case="detective")
        payload = {
            "evidence_type": "vehicle",
            "title": "Vehicle",
            "vehicle": {"model": "M", "color": "Red", "license_plate": "ABC", "serial_number": "123"},
        }
        res = self.client.post(f"/api/v1/cases/{case.id}/evidence/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vehicle_evidence_requires_one_identifier(self):
        detective = self.create_user("detective2", ROLE_DETECTIVE)
        self.client.force_authenticate(user=detective)
        case = Case.objects.create(
            title="Case",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_3,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective,
        )
        CaseAssignment.objects.create(case=case, user=detective, role_in_case="detective")
        payload = {
            "evidence_type": "vehicle",
            "title": "Vehicle",
            "vehicle": {"model": "M", "color": "Red"},
        }
        res = self.client.post(f"/api/v1/cases/{case.id}/evidence/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_most_wanted_ranking_computation(self):
        person = Person.objects.create(full_name="John Doe")
        case = Case.objects.create(
            title="Case",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_1,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
        )
        record = WantedRecord.objects.create(person=person, case=case)
        record.started_at = timezone.now() - timedelta(days=40)
        record.save()
        results = compute_most_wanted()
        self.assertTrue(results)
        entry = results[0]
        self.assertEqual(entry["person"].id, person.id)
        self.assertEqual(entry["crime_degree"], 3)
        self.assertEqual(entry["ranking_score"], entry["days_wanted"] * entry["crime_degree"])

    def test_tip_flow_issues_reward_code(self):
        base_user = self.create_user("baseuser", ROLE_BASE_USER)
        officer = self.create_user("officer", ROLE_POLICE_OFFICER)
        detective = self.create_user("det3", ROLE_DETECTIVE)
        self.client.force_authenticate(user=base_user)
        tip_res = self.client.post("/api/v1/tips/", {"content": "Info"}, format="json")
        self.assertEqual(tip_res.status_code, status.HTTP_201_CREATED)
        tip_id = tip_res.data["id"]
        self.client.force_authenticate(user=officer)
        review_res = self.client.post(f"/api/v1/tips/{tip_id}/officer-review/", {"approve": True}, format="json")
        self.assertEqual(review_res.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=detective)
        det_res = self.client.post(f"/api/v1/tips/{tip_id}/detective-review/", {"approve": True}, format="json")
        self.assertEqual(det_res.status_code, status.HTTP_200_OK)
        self.assertTrue(RewardCode.objects.filter(tip_id=tip_id).exists())

    def test_payment_create_and_callback(self):
        sergeant = self.create_user("sergeant", ROLE_SERGEANT)
        self.client.force_authenticate(user=sergeant)
        case = Case.objects.create(
            title="Case",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=sergeant,
        )
        res = self.client.post(
            "/api/v1/payments/create/",
            {"case_id": case.id, "amount": 1000, "type": "bail"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        payment_id = res.data["payment"]["id"]
        signature = sign_payload(f"{payment_id}:1000:bail")
        callback = self.client.post(
            "/api/v1/payments/callback/",
            {"payment_id": payment_id, "status": "success", "signature": signature},
            format="json",
        )
        self.assertEqual(callback.status_code, status.HTTP_200_OK)
        payment = Payment.objects.get(id=payment_id)
        self.assertEqual(payment.status, "success")
