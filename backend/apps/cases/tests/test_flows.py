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
    ROLE_SYSTEM_ADMIN,
    ROLE_JUDGE,
)
from apps.cases.models import Complaint, Case, CaseComplainant
from apps.cases.constants import ComplaintStatus, CrimeLevel, CaseStatus, CaseSourceType
from apps.cases.models import CaseAssignment
from apps.suspects.models import Person, WantedRecord, SuspectCandidate
from apps.suspects.utils import compute_most_wanted
from apps.rewards.models import RewardCode
from apps.payments.models import Payment
from apps.payments.gateway import sign_payload
from apps.interrogations.models import Interrogation
from apps.notifications.models import Notification


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
            ROLE_SYSTEM_ADMIN,
            ROLE_JUDGE,
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
        cadet = self.create_user("cadet_strike", ROLE_CADET)
        complaint = Complaint.objects.create(
            title="Test",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_3,
            location="Loc",
            status=ComplaintStatus.PENDING_CADET_REVIEW,
            created_by=user,
        )
        self.client.force_authenticate(user=cadet)
        for index in range(3):
            res = self.client.post(
                f"/api/v1/cases/complaints/{complaint.id}/cadet-review/",
                {"action": "return", "message": f"Issue {index + 1}"},
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            complaint.refresh_from_db()
            if index < 2:
                self.assertEqual(complaint.status, ComplaintStatus.RETURNED_TO_COMPLAINANT)
                self.client.force_authenticate(user=user)
                resubmit = self.client.post(
                    f"/api/v1/cases/complaints/{complaint.id}/resubmit/",
                    {"title": "Updated"},
                    format="json",
                )
                self.assertEqual(resubmit.status_code, status.HTTP_200_OK)
                self.client.force_authenticate(user=cadet)
        complaint.refresh_from_db()
        self.assertEqual(complaint.strike_count, 3)
        self.assertEqual(complaint.status, ComplaintStatus.VOIDED)
        self.assertTrue(Notification.objects.filter(user=user, type="complaint_voided").exists())

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

    def test_cadet_approve_requires_officer_selection(self):
        base_user = self.create_user("baseu2a", ROLE_BASE_USER)
        cadet = self.create_user("cadet1a", ROLE_CADET)
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
            {"action": "approve"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_officer_can_only_review_assigned_complaint(self):
        base_user = self.create_user("baseu2b", ROLE_BASE_USER)
        cadet = self.create_user("cadet1b", ROLE_CADET)
        officer_assigned = self.create_user("officer_assigned", ROLE_POLICE_OFFICER)
        officer_other = self.create_user("officer_other", ROLE_POLICE_OFFICER)
        complaint = Complaint.objects.create(
            title="Test",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_3,
            location="Loc",
            status=ComplaintStatus.PENDING_OFFICER_REVIEW,
            created_by=base_user,
            assigned_cadet=cadet,
            assigned_officer=officer_assigned,
        )
        self.client.force_authenticate(user=officer_other)
        res = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/officer-review/",
            {"action": "return_to_cadet", "message": "Needs correction"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.client.force_authenticate(user=officer_assigned)
        success_res = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/officer-review/",
            {"action": "return_to_cadet", "message": "Needs correction"},
            format="json",
        )
        self.assertEqual(success_res.status_code, status.HTTP_200_OK)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, ComplaintStatus.RETURNED_TO_CADET)

    def test_only_assigned_cadet_can_review_returned_complaint(self):
        base_user = self.create_user("baseu2c", ROLE_BASE_USER)
        cadet_assigned = self.create_user("cadet_assigned", ROLE_CADET)
        cadet_other = self.create_user("cadet_other", ROLE_CADET)
        officer = self.create_user("officer2c", ROLE_POLICE_OFFICER)
        complaint = Complaint.objects.create(
            title="Test",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_3,
            location="Loc",
            status=ComplaintStatus.RETURNED_TO_CADET,
            created_by=base_user,
            assigned_cadet=cadet_assigned,
            assigned_officer=officer,
        )
        self.client.force_authenticate(user=cadet_other)
        res = self.client.post(
            f"/api/v1/cases/complaints/{complaint.id}/cadet-review/",
            {"action": "return", "message": "Wrong user"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

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
            assigned_officer=officer,
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
            assigned_cadet=cadet,
            assigned_officer=officer,
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

    def test_cadet_added_case_complainants_are_auto_approved(self):
        cadet = self.create_user("cadet_case_comp", ROLE_CADET)
        officer = self.create_user("officer_case_comp", ROLE_POLICE_OFFICER)
        case = Case.objects.create(
            title="Case",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_3,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=officer,
        )
        self.client.force_authenticate(user=cadet)
        add_res = self.client.post(
            f"/api/v1/cases/{case.id}/add-complainant/",
            {"full_name": "Extra", "phone": "12345", "national_id": "nid-extra"},
            format="json",
        )
        self.assertEqual(add_res.status_code, status.HTTP_200_OK)
        created = CaseComplainant.objects.get(case=case, full_name="Extra")
        self.assertEqual(created.verification_status, CaseComplainant.VerificationStatus.APPROVED)
        self.assertTrue(created.is_verified)
        review_res = self.client.post(
            f"/api/v1/cases/complainants/{created.id}/review/",
            {"action": "reject", "message": "Not needed"},
            format="json",
        )
        self.assertEqual(review_res.status_code, status.HTTP_400_BAD_REQUEST)

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
        person = Person.objects.create(full_name="Payment Target")
        WantedRecord.objects.create(case=case, person=person, status="wanted")
        res = self.client.post(
            "/api/v1/payments/create/",
            {"case_id": case.id, "person_id": person.id, "amount": 1000, "type": "bail"},
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
        witness = User.objects.create_user(
            username="witness_cs",
            email="witness_cs@example.com",
            phone="999",
            national_id="nid-999",
            password="Pass1234!",
            first_name="W",
            last_name="User",
        )
        self.client.force_authenticate(user=officer)
        create_res = self.client.post(
            "/api/v1/cases/crime-scene/",
            {
                "title": "Crime Scene Case",
                "description": "Desc",
                "crime_level": CrimeLevel.LEVEL_2,
                "location": "Loc",
                "scene_datetime": timezone.now().isoformat().replace("+00:00", "Z"),
                "witnesses": [{"full_name": "W User", "phone": witness.phone, "national_id": witness.national_id}],
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

    def test_crime_scene_witness_must_match_registered_user(self):
        officer = self.create_user("officer5b", ROLE_POLICE_OFFICER)
        witness = User.objects.create_user(
            username="witness_bad",
            email="witness_bad@example.com",
            phone="11111",
            national_id="nid-11111",
            password="Pass1234!",
            first_name="Real",
            last_name="Witness",
        )
        self.client.force_authenticate(user=officer)
        bad_phone = self.client.post(
            "/api/v1/cases/crime-scene/",
            {
                "title": "Crime Scene Case",
                "description": "Desc",
                "crime_level": CrimeLevel.LEVEL_2,
                "location": "Loc",
                "scene_datetime": timezone.now().isoformat().replace("+00:00", "Z"),
                "witnesses": [{"full_name": "Real Witness", "phone": "99999", "national_id": witness.national_id}],
            },
            format="json",
        )
        self.assertEqual(bad_phone.status_code, status.HTTP_400_BAD_REQUEST)

    def test_complaint_queue_filters_by_role(self):
        creator = self.create_user("compl_creator", ROLE_BASE_USER)
        cadet = self.create_user("cadet_queue", ROLE_CADET)
        officer = self.create_user("officer_queue", ROLE_POLICE_OFFICER)
        admin = self.create_user("admin_queue", ROLE_SYSTEM_ADMIN)
        Complaint.objects.create(
            title="C1",
            description="D",
            crime_level=CrimeLevel.LEVEL_3,
            location="L",
            status=ComplaintStatus.PENDING_CADET_REVIEW,
            created_by=creator,
        )
        Complaint.objects.create(
            title="C2",
            description="D",
            crime_level=CrimeLevel.LEVEL_3,
            location="L",
            status=ComplaintStatus.RETURNED_TO_CADET,
            created_by=creator,
            assigned_cadet=cadet,
        )
        Complaint.objects.create(
            title="C3",
            description="D",
            crime_level=CrimeLevel.LEVEL_3,
            location="L",
            status=ComplaintStatus.PENDING_OFFICER_REVIEW,
            created_by=creator,
            assigned_officer=officer,
        )
        self.client.force_authenticate(user=cadet)
        cadet_res = self.client.get("/api/v1/cases/complaints/queue/")
        self.assertEqual(cadet_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(cadet_res.data), 2)
        self.client.force_authenticate(user=officer)
        officer_res = self.client.get("/api/v1/cases/complaints/queue/")
        self.assertEqual(officer_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(officer_res.data), 1)
        self.client.force_authenticate(user=admin)
        admin_res = self.client.get("/api/v1/cases/complaints/queue/?status=pending_officer")
        self.assertEqual(admin_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(admin_res.data), 1)

    def test_case_visibility_follows_complaint_and_crime_scene_rules(self):
        cadet = self.create_user("cadet_vis", ROLE_CADET)
        officer = self.create_user("officer_vis", ROLE_POLICE_OFFICER)
        patrol = self.create_user("patrol_vis", ROLE_PATROL_OFFICER)
        sergeant = self.create_user("sergeant_vis", ROLE_SERGEANT)

        complaint_case = Case.objects.create(
            title="ComplaintCase",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=officer,
        )
        crime_scene_pending = Case.objects.create(
            title="CrimePending",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.PENDING_SUPERIOR_APPROVAL,
            source_type=CaseSourceType.CRIME_SCENE,
            created_by=officer,
        )
        crime_scene_active = Case.objects.create(
            title="CrimeActive",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.CRIME_SCENE,
            created_by=officer,
        )

        self.client.force_authenticate(user=cadet)
        cadet_res = self.client.get("/api/v1/cases/")
        cadet_ids = {row["id"] for row in cadet_res.data}
        self.assertIn(complaint_case.id, cadet_ids)
        self.assertNotIn(crime_scene_pending.id, cadet_ids)
        self.assertNotIn(crime_scene_active.id, cadet_ids)

        self.client.force_authenticate(user=patrol)
        patrol_res = self.client.get("/api/v1/cases/")
        patrol_ids = {row["id"] for row in patrol_res.data}
        self.assertIn(complaint_case.id, patrol_ids)
        self.assertIn(crime_scene_active.id, patrol_ids)
        self.assertNotIn(crime_scene_pending.id, patrol_ids)

        self.client.force_authenticate(user=sergeant)
        sergeant_res = self.client.get("/api/v1/cases/")
        sergeant_ids = {row["id"] for row in sergeant_res.data}
        self.assertIn(complaint_case.id, sergeant_ids)
        self.assertIn(crime_scene_active.id, sergeant_ids)
        self.assertIn(crime_scene_pending.id, sergeant_ids)

    def test_tip_review_queue_filters_by_role(self):
        base_user = self.create_user("tip_base", ROLE_BASE_USER)
        officer = self.create_user("tip_officer", ROLE_POLICE_OFFICER)
        detective = self.create_user("tip_detective", ROLE_DETECTIVE)
        admin = self.create_user("tip_admin", ROLE_SYSTEM_ADMIN)
        self.client.force_authenticate(user=base_user)
        tip1 = self.client.post("/api/v1/tips/", {"content": "tip1"}, format="json").data["id"]
        tip2 = self.client.post("/api/v1/tips/", {"content": "tip2"}, format="json").data["id"]
        self.client.force_authenticate(user=officer)
        self.client.post(f"/api/v1/tips/{tip1}/officer-review/", {"approve": True}, format="json")
        officer_queue = self.client.get("/api/v1/tips/review-queue/")
        self.assertEqual(officer_queue.status_code, status.HTTP_200_OK)
        self.assertEqual(len(officer_queue.data), 1)
        self.assertEqual(officer_queue.data[0]["id"], tip2)
        self.client.force_authenticate(user=detective)
        detective_queue = self.client.get("/api/v1/tips/review-queue/")
        self.assertEqual(detective_queue.status_code, status.HTTP_200_OK)
        self.assertEqual(len(detective_queue.data), 1)
        self.assertEqual(detective_queue.data[0]["id"], tip1)
        self.client.force_authenticate(user=admin)
        admin_queue = self.client.get("/api/v1/tips/review-queue/")
        self.assertEqual(admin_queue.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(admin_queue.data), 2)

    def test_sergeant_cannot_decide_suspect_for_unrelated_case(self):
        detective = self.create_user("det_unrel", ROLE_DETECTIVE)
        sergeant = self.create_user("sgt_unrel", ROLE_SERGEANT)
        case = Case.objects.create(
            title="Case",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective,
        )
        CaseAssignment.objects.create(case=case, user=detective, role_in_case="detective")
        person = Person.objects.create(full_name="Suspect")
        candidate = SuspectCandidate.objects.create(
            case=case,
            person=person,
            proposed_by_detective=detective,
            rationale="R",
        )
        self.client.force_authenticate(user=sergeant)
        res = self.client.post(
            f"/api/v1/cases/{case.id}/suspects/{candidate.id}/sergeant-decision/",
            {"approve": True},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_sergeant_rejection_of_suspect_requires_message(self):
        detective = self.create_user("det_rel", ROLE_DETECTIVE)
        sergeant = self.create_user("sgt_rel", ROLE_SERGEANT)
        case = Case.objects.create(
            title="Case",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective,
        )
        CaseAssignment.objects.create(case=case, user=detective, role_in_case="detective")
        CaseAssignment.objects.create(case=case, user=sergeant, role_in_case="sergeant")
        person = Person.objects.create(full_name="Suspect")
        candidate = SuspectCandidate.objects.create(
            case=case,
            person=person,
            proposed_by_detective=detective,
            rationale="R",
        )
        self.client.force_authenticate(user=sergeant)
        res = self.client.post(
            f"/api/v1/cases/{case.id}/suspects/{candidate.id}/sergeant-decision/",
            {"approve": False},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detective_cannot_score_interrogation_for_unrelated_case(self):
        detective_assigned = self.create_user("det_assigned", ROLE_DETECTIVE)
        detective_other = self.create_user("det_other", ROLE_DETECTIVE)
        case = Case.objects.create(
            title="Case",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective_assigned,
        )
        CaseAssignment.objects.create(case=case, user=detective_assigned, role_in_case="detective")
        person = Person.objects.create(full_name="P")
        interrogation = Interrogation.objects.create(case=case, suspect=person, status="pending_sergeant")
        self.client.force_authenticate(user=detective_other)
        res = self.client.patch(
            f"/api/v1/interrogations/{interrogation.id}/detective-score/",
            {"score": 7},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_captain_can_approve_only_one_offender_per_case(self):
        captain = self.create_user("captain_interro", ROLE_CAPTAIN)
        case = Case.objects.create(
            title="Case",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=captain,
        )
        suspect_one = Person.objects.create(full_name="S1")
        suspect_two = Person.objects.create(full_name="S2")
        first = Interrogation.objects.create(case=case, suspect=suspect_one, status="pending_captain")
        second = Interrogation.objects.create(case=case, suspect=suspect_two, status="pending_captain")
        self.client.force_authenticate(user=captain)
        first_res = self.client.post(
            f"/api/v1/interrogations/{first.id}/captain-decision/",
            {"decision": "approve"},
            format="json",
        )
        self.assertEqual(first_res.status_code, status.HTTP_200_OK)
        second_res = self.client.post(
            f"/api/v1/interrogations/{second.id}/captain-decision/",
            {"decision": "approve"},
            format="json",
        )
        self.assertEqual(second_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_chief_rejection_sends_interrogation_back_to_captain(self):
        captain = self.create_user("captain_loop", ROLE_CAPTAIN)
        chief = self.create_user("chief_loop", ROLE_POLICE_CHIEF)
        case = Case.objects.create(
            title="Critical Case",
            description="Desc",
            crime_level=CrimeLevel.CRITICAL,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=captain,
        )
        suspect = Person.objects.create(full_name="Critical Suspect")
        interrogation = Interrogation.objects.create(
            case=case,
            suspect=suspect,
            status="pending_chief",
            captain_decision="approve",
            captain_reviewed_by=captain,
        )
        self.client.force_authenticate(user=chief)
        res = self.client.post(
            f"/api/v1/interrogations/{interrogation.id}/chief-decision/",
            {"decision": "reject", "notes": "Insufficient evidence"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        interrogation.refresh_from_db()
        self.assertEqual(interrogation.status, "pending_captain")
        self.assertTrue(
            Notification.objects.filter(
                user=captain,
                case=case,
                type="chief_rejected_interrogation_decision",
            ).exists()
        )

    def test_case_report_requires_case_access(self):
        detective = self.create_user("det_report", ROLE_DETECTIVE)
        judge = self.create_user("judge_report", ROLE_JUDGE)
        case = Case.objects.create(
            title="Case",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_1,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective,
        )
        self.client.force_authenticate(user=judge)
        res = self.client.get(f"/api/v1/cases/{case.id}/report/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_board_disallows_cross_case_evidence_reference(self):
        detective = self.create_user("det_board", ROLE_DETECTIVE)
        self.client.force_authenticate(user=detective)
        case_a = Case.objects.create(
            title="A",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective,
        )
        case_b = Case.objects.create(
            title="B",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective,
        )
        CaseAssignment.objects.create(case=case_a, user=detective, role_in_case="detective")
        ev_res = self.client.post(
            f"/api/v1/cases/{case_a.id}/evidence/",
            {"evidence_type": "other", "title": "E", "description": "Desc"},
            format="json",
        )
        self.assertEqual(ev_res.status_code, status.HTTP_201_CREATED)
        evidence_id = ev_res.data["id"]
        board_item_res = self.client.post(
            f"/api/v1/cases/{case_b.id}/board/items/",
            {"item_type": "EVIDENCE_REF", "evidence": evidence_id},
            format="json",
        )
        self.assertEqual(board_item_res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detective_board_is_not_accessible_to_non_detective_roles(self):
        detective = self.create_user("det_board_only", ROLE_DETECTIVE)
        sergeant = self.create_user("sgt_board_only", ROLE_SERGEANT)
        case = Case.objects.create(
            title="BoardCase",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective,
        )
        CaseAssignment.objects.create(case=case, user=detective, role_in_case="detective")
        self.client.force_authenticate(user=sergeant)
        res = self.client.get(f"/api/v1/cases/{case.id}/board/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_evidence_description_is_required(self):
        detective = self.create_user("det_desc", ROLE_DETECTIVE)
        self.client.force_authenticate(user=detective)
        case = Case.objects.create(
            title="Case",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=detective,
        )
        CaseAssignment.objects.create(case=case, user=detective, role_in_case="detective")
        res = self.client.post(
            f"/api/v1/cases/{case.id}/evidence/",
            {"evidence_type": "other", "title": "No Desc"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reward_lookup_uses_stored_amount(self):
        base_user = self.create_user("reward_base", ROLE_BASE_USER)
        officer = self.create_user("reward_officer", ROLE_POLICE_OFFICER)
        detective = self.create_user("reward_det", ROLE_DETECTIVE)
        case = Case.objects.create(
            title="RewardCase",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_1,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=officer,
        )
        person = Person.objects.create(full_name="RewardPerson")
        record = WantedRecord.objects.create(case=case, person=person, status="wanted")
        record.started_at = timezone.now() - timedelta(days=40)
        record.save(update_fields=["started_at"])
        self.client.force_authenticate(user=base_user)
        tip_res = self.client.post(
            "/api/v1/tips/",
            {"content": "Useful", "person": person.id},
            format="json",
        )
        tip_id = tip_res.data["id"]
        self.client.force_authenticate(user=officer)
        self.client.post(f"/api/v1/tips/{tip_id}/officer-review/", {"approve": True}, format="json")
        self.client.force_authenticate(user=detective)
        self.client.post(f"/api/v1/tips/{tip_id}/detective-review/", {"approve": True}, format="json")
        reward = RewardCode.objects.get(tip_id=tip_id)
        self.assertGreater(reward.amount, 0)
        record.status = "cleared"
        record.ended_at = timezone.now()
        record.save(update_fields=["status", "ended_at"])
        self.client.force_authenticate(user=officer)
        lookup = self.client.get(f"/api/v1/rewards/lookup/?national_id={base_user.national_id}&code={reward.code}")
        self.assertEqual(lookup.status_code, status.HTTP_200_OK)
        self.assertEqual(lookup.data["reward"]["amount"], reward.amount)

    def test_payment_validation_requires_person_and_case_status(self):
        sergeant = self.create_user("sgt_payment_rules", ROLE_SERGEANT)
        self.client.force_authenticate(user=sergeant)
        case_lvl2 = Case.objects.create(
            title="C2",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_2,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=sergeant,
        )
        person = Person.objects.create(full_name="NoLink")
        missing_person = self.client.post(
            "/api/v1/payments/create/",
            {"case_id": case_lvl2.id, "amount": 1000, "type": "bail"},
            format="json",
        )
        self.assertEqual(missing_person.status_code, status.HTTP_400_BAD_REQUEST)
        not_linked = self.client.post(
            "/api/v1/payments/create/",
            {"case_id": case_lvl2.id, "person_id": person.id, "amount": 1000, "type": "bail"},
            format="json",
        )
        self.assertEqual(not_linked.status_code, status.HTTP_400_BAD_REQUEST)
        record = WantedRecord.objects.create(case=case_lvl2, person=person, status="cleared")
        invalid_status = self.client.post(
            "/api/v1/payments/create/",
            {"case_id": case_lvl2.id, "person_id": person.id, "amount": 1000, "type": "bail"},
            format="json",
        )
        self.assertEqual(invalid_status.status_code, status.HTTP_400_BAD_REQUEST)
        record.status = "wanted"
        record.save(update_fields=["status"])
        valid_bail = self.client.post(
            "/api/v1/payments/create/",
            {"case_id": case_lvl2.id, "person_id": person.id, "amount": 1000, "type": "bail"},
            format="json",
        )
        self.assertEqual(valid_bail.status_code, status.HTTP_201_CREATED)
        case_lvl3 = Case.objects.create(
            title="C3",
            description="Desc",
            crime_level=CrimeLevel.LEVEL_3,
            location="Loc",
            status=CaseStatus.ACTIVE,
            source_type=CaseSourceType.COMPLAINT,
            created_by=sergeant,
        )
        record_fine = WantedRecord.objects.create(case=case_lvl3, person=person, status="wanted")
        fine_invalid = self.client.post(
            "/api/v1/payments/create/",
            {"case_id": case_lvl3.id, "person_id": person.id, "amount": 2000, "type": "fine"},
            format="json",
        )
        self.assertEqual(fine_invalid.status_code, status.HTTP_400_BAD_REQUEST)
        record_fine.status = "arrested"
        record_fine.save(update_fields=["status"])
        fine_valid = self.client.post(
            "/api/v1/payments/create/",
            {"case_id": case_lvl3.id, "person_id": person.id, "amount": 2000, "type": "fine"},
            format="json",
        )
        self.assertEqual(fine_valid.status_code, status.HTTP_201_CREATED)
