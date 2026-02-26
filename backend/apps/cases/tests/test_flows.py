from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from apps.accounts.models import User
from apps.rbac.models import Role, UserRole
from apps.rbac.constants import (
    ROLE_BASE_USER,
    ROLE_CADET,
    ROLE_DETECTIVE,
    ROLE_PATROL_OFFICER,
    ROLE_POLICE_OFFICER,
    ROLE_POLICE_CHIEF,
    ROLE_CAPTAIN,
    ROLE_CORONER,
    ROLE_SERGEANT,
)
from apps.cases.models import Complaint, Case, CaseComplainant
from apps.cases.constants import ComplaintStatus, CrimeLevel, CaseStatus, CaseSourceType
from apps.cases.models import CaseAssignment
from apps.suspects.models import Person, WantedRecord
from apps.suspects.utils import compute_most_wanted
from apps.rewards.models import RewardCode
from apps.payments.models import Payment
from apps.payments.gateway import sign_payload


class CaseFlowTests(APITestCase):
    def setUp(self):
        for slug in [
            ROLE_BASE_USER,
            ROLE_CADET,
            ROLE_DETECTIVE,
            ROLE_POLICE_OFFICER,
            ROLE_PATROL_OFFICER,
            ROLE_SERGEANT,
            ROLE_CAPTAIN,
            ROLE_POLICE_CHIEF,
            ROLE_CORONER,
        ]:
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

    def test_cadet_return_requires_message(self):
        base_user = self.create_user("baseu2", ROLE_BASE_USER)
        cadet = self.create_user("cadet1", ROLE_CADET)
        complaint = Complaint.objects.create(
            title="Test",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_3,
            location="Loc",
            status=ComplaintStatus.PENDING_CADET_REVIEW,
            created_by=base_user,
        )
        self.client.force_authenticate(user=cadet)
        res = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/cadet-review/",
            {"action": "return"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_officer_cannot_approve_when_complainants_pending(self):
        base_user = self.create_user("baseu3", ROLE_BASE_USER)
        officer = self.create_user("officer2", ROLE_POLICE_OFFICER)
        complaint = Complaint.objects.create(
            title="Test",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_3,
            location="Loc",
            status=ComplaintStatus.PENDING_OFFICER_REVIEW,
            created_by=base_user,
        )
        CaseComplainant.objects.create(
            complaint=complaint,
            full_name="Comp One",
            phone="22222",
            national_id="nid-22222",
        )
        self.client.force_authenticate(user=officer)
        res = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/officer-review/",
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complainant_review_then_officer_approval_forms_case(self):
        base_user = self.create_user("baseu4", ROLE_BASE_USER)
        cadet = self.create_user("cadet2", ROLE_CADET)
        officer = self.create_user("officer3", ROLE_POLICE_OFFICER)
        complaint = Complaint.objects.create(
            title="Approved Complaint",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_3,
            location="Loc",
            status=ComplaintStatus.PENDING_OFFICER_REVIEW,
            created_by=base_user,
        )
        complainant = CaseComplainant.objects.create(
            complaint=complaint,
            full_name="Comp Two",
            phone="33333",
            national_id="nid-33333",
        )
        self.client.force_authenticate(user=cadet)
        review_res = self.client.post(
            f"/api/v1/cases/complainants/{complainant.id}/review/",
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(review_res.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=officer)
        approve_res = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/officer-review/",
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(approve_res.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, ComplaintStatus.APPROVED)
        self.assertTrue(Case.objects.filter(complaint=complaint).exists())

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

    def test_case_assignment_api_allows_manager_to_assign_detective(self):
        sergeant = self.create_user("sergeant2", ROLE_SERGEANT)
        detective = self.create_user("detective3", ROLE_DETECTIVE)
        case = Case.objects.create(
            title="CaseAssign",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.CRIME_SCENE,
            created_by=sergeant,
        )
        self.client.force_authenticate(user=sergeant)
        create_res = self.client.post(
            f"/api/v1/cases/{case.id}/assignments/",
            {"user_id": detective.id, "role_in_case": "detective"},
            format="json",
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            CaseAssignment.objects.filter(case=case, user=detective, role_in_case="detective").exists()
        )

    def test_unrelated_police_role_cannot_get_evidence_by_id(self):
        detective = self.create_user("detective4", ROLE_DETECTIVE)
        officer = self.create_user("officer4", ROLE_POLICE_OFFICER)
        case = Case.objects.create(
            title="EvCase",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective,
        )
        CaseAssignment.objects.create(case=case, user=detective, role_in_case="detective")
        self.client.force_authenticate(user=detective)
        create_res = self.client.post(
            f"/api/v1/cases/{case.id}/evidence/",
            {
                "evidence_type": "other",
                "title": "Simple evidence",
                "description": "desc",
            },
            format="json",
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        evidence_id = create_res.data["id"]
        self.client.force_authenticate(user=officer)
        get_res = self.client.get(f"/api/v1/evidence/{evidence_id}/")
        self.assertEqual(get_res.status_code, status.HTTP_403_FORBIDDEN)

    def test_crime_scene_create_returns_report_id_and_case_approve_route_works(self):
        officer = self.create_user("officer5", ROLE_POLICE_OFFICER)
        sergeant = self.create_user("sergeant3", ROLE_SERGEANT)
        self.client.force_authenticate(user=officer)
        create_res = self.client.post(
            "/api/v1/cases/crime-scene/",
            {
                "title": "Crime Scene Case",
                "description": "Desc",
                "crime_level": CrimeLevel.LEVEL_2,
                "location": "Loc",
                "scene_datetime": timezone.now().isoformat().replace("+00:00", "Z"),
                "witnesses": [{"full_name": "W", "phone": "999", "national_id": "nid-999"}],
            },
            format="json",
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        self.assertIn("crime_scene_report_id", create_res.data)
        case_id = create_res.data["case"]["id"]
        self.client.force_authenticate(user=sergeant)
        approve_res = self.client.post(
            f"/api/v1/cases/{case_id}/crime-scene/approve/",
            {"approve": True},
            format="json",
        )
        self.assertEqual(approve_res.status_code, status.HTTP_200_OK)
