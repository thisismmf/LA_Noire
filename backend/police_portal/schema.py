import inspect
from collections.abc import Mapping

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.settings import api_settings


GENERIC_ERROR_EXAMPLE = OpenApiExample(
    "Error Response",
    value={
        "error": {
            "code": "validation_error",
            "message": "Readable message",
            "details": {"field": ["This field is required."]},
        }
    },
    response_only=True,
)

FIELD_NAME_EXAMPLES = {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
    "action": "approve",
    "amount": 1000,
    "assigned_at": "2026-02-26T16:20:00Z",
    "approve": True,
    "case_id": 1,
    "captain_notes": "Evidence supports moving forward with prosecution.",
    "code": "RW-1024",
    "color": "Black",
    "content": "Citizen tip about suspect location",
    "created_at": "2026-02-26T16:00:00Z",
    "crime_level": 2,
    "crime_degree": 3,
    "crime_scene_report_id": 8,
    "decided_at": "2026-02-26T18:30:00Z",
    "decision": "approve",
    "description": "Detailed operational note for investigators.",
    "days_wanted": 42,
    "email": "officer@example.com",
    "evidence_id": 3,
    "first_name": "Cole",
    "forensic_result": "Fingerprint match pending confirmation.",
    "from_item": 4,
    "full_name": "John Doe",
    "gateway_ref": "S000000000000000000000000000000000",
    "id": 1,
    "identifier": "officer@example.com",
    "identity_db_result": "Record matched in identity database.",
    "incident_datetime": "2026-02-26T10:30:00Z",
    "issued_at": "2026-02-26T17:45:00Z",
    "item_type": "NOTE",
    "last_name": "Phelps",
    "license_plate": "LAPD-1024",
    "location": "Downtown Los Angeles",
    "message": "Approved after supervisor review.",
    "media_type": "audio",
    "model": "Buick Eight",
    "national_id": "A123456789",
    "notes": "Known alias: Black Dahlia lead.",
    "owner_full_name": "John Doe",
    "password": "Pass1234!",
    "payload": {"evidence_id": 3, "evidence_type": "medical"},
    "payment_id": 1,
    "person_id": 1,
    "phone": "5551234567",
    "photo": "/media/suspects/john-doe.jpg",
    "punishment_description": "Five years imprisonment and post-release supervision.",
    "punishment_title": "Prison sentence",
    "read_at": None,
    "ranking_score": 120,
    "redeemed_at": None,
    "redirect_url": "https://sandbox.zarinpal.com/pg/StartPay/S000000000000000000000000000000000",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
    "rationale": "Witness testimony and vehicle footage point to this suspect.",
    "reported_by": 5,
    "reported_by_id": 5,
    "reported_at": "2026-02-26T16:10:00Z",
    "role": "detective",
    "role_in_case": "detective",
    "scene_datetime": "2026-02-26T10:15:00Z",
    "score": 8,
    "serial_number": "VIN123456789",
    "authority": "S000000000000000000000000000000000",
    "ref_id": 201,
    "status": "pending",
    "suspect_id": 1,
    "title": "Armed robbery investigation",
    "to_item": 5,
    "transcription": "Witness states the suspect fled in a dark sedan.",
    "type": "bail",
    "updated_at": "2026-02-26T16:25:00Z",
    "username": "detective_01",
    "verdict": "guilty",
    "x": 320,
    "y": 180,
}

SERIALIZER_REQUEST_EXAMPLES = {
    "apps.accounts.serializers.RegisterSerializer": {
        "username": "new_user_01",
        "email": "new_user_01@example.com",
        "phone": "5551234567",
        "national_id": "A123456789",
        "first_name": "Cole",
        "last_name": "Phelps",
        "password": "Pass1234!",
    },
    "apps.accounts.serializers.LoginSerializer": {
        "identifier": "officer@example.com",
        "password": "Pass1234!",
    },
    "apps.rbac.serializers.RoleSerializer": {
        "name": "Detective",
        "slug": "detective",
        "description": "Investigates active cases, evidence, and suspect link analysis.",
    },
    "apps.rbac.serializers.AssignRoleSerializer": {
        "role_slug": "detective",
    },
    "apps.cases.serializers.ComplaintSerializer": {
        "title": "Home burglary on Olive Street",
        "description": "Front door forced open and jewelry missing from the bedroom.",
        "crime_level": 2,
        "location": "Olive Street, Los Angeles",
        "incident_datetime": "2026-02-25T22:10:00Z",
        "complainants": [
            {
                "full_name": "Mary Hudson",
                "phone": "5551112233",
                "national_id": "MH-0001",
            }
        ],
    },
    "apps.cases.serializers.ComplaintResubmitSerializer": {
        "description": "Updated complaint with corrected witness and timeline details.",
        "location": "Olive Street, Los Angeles",
        "incident_datetime": "2026-02-25T22:10:00Z",
    },
    "apps.cases.serializers.CadetReviewSerializer": {
        "action": "return",
        "message": "Please add a valid national ID for the complainant.",
    },
    "apps.cases.serializers.OfficerReviewSerializer": {
        "action": "approve",
    },
    "apps.cases.serializers.CrimeSceneReportSerializer": {
        "title": "Warehouse assault",
        "description": "Officers found signs of struggle and blood traces near the loading dock.",
        "crime_level": 1,
        "location": "Harbor warehouse district",
        "incident_datetime": "2026-02-26T09:55:00Z",
        "scene_datetime": "2026-02-26T10:15:00Z",
        "witnesses": [
            {
                "full_name": "Evelyn Shaw",
                "phone": "5552003344",
                "national_id": "ES-4401",
            }
        ],
    },
    "apps.cases.serializers.CrimeSceneApproveSerializer": {
        "approve": True,
    },
    "apps.cases.serializers.AddComplainantSerializer": {
        "full_name": "Robert Miller",
        "phone": "5558881122",
        "national_id": "RM-0099",
    },
    "apps.cases.serializers.ComplainantReviewSerializer": {
        "action": "reject",
        "message": "Submitted contact details could not be verified.",
    },
    "apps.cases.serializers.CaseAssignmentUpsertSerializer": {
        "user_id": 7,
        "role_in_case": "detective",
    },
    "apps.evidence.serializers.EvidenceCreateSerializer": {
        "evidence_type": "witness_statement",
        "title": "Dock worker testimony",
        "description": "Statement from the worker who saw the suspect vehicle leave the scene.",
        "witness_statement": {
            "transcription": "I saw a dark sedan leaving the warehouse right after the shouting stopped.",
            "media": [
                {
                    "file": "statement-audio.mp3",
                    "media_type": "audio",
                }
            ],
        },
    },
    "apps.board.serializers.BoardItemSerializer": {
        "item_type": "NOTE",
        "title": "Timeline",
        "text": "Suspect vehicle appears on camera at 21:10 and exits at 21:18.",
        "x": 320,
        "y": 180,
    },
    "apps.board.serializers.BoardConnectionSerializer": {
        "from_item": 4,
        "to_item": 5,
    },
    "apps.suspects.serializers.SuspectProposalSerializer": {
        "suspects": [
            {
                "full_name": "John Doe",
                "national_id": "JD-3001",
                "phone": "5553131313",
                "notes": "Seen near the warehouse entrance on CCTV.",
            }
        ],
        "rationale": "Vehicle footage and witness testimony place the suspect at the scene.",
    },
    "apps.suspects.serializers.SergeantDecisionSerializer": {
        "approve": True,
        "message": "Evidence supports issuing an arrest order.",
    },
    "apps.suspects.serializers.SuspectStatusUpdateSerializer": {
        "case_id": 1,
        "status": "arrested",
    },
    "apps.interrogations.serializers.InterrogationCreateSerializer": {
        "suspect_id": 1,
        "detective_score": 7,
    },
    "apps.interrogations.serializers.ScoreSerializer": {
        "score": 8,
    },
    "apps.interrogations.serializers.CaptainDecisionSerializer": {
        "decision": "approve",
        "notes": "Forward to prosecution based on aligned evidence and interview scores.",
    },
    "apps.interrogations.serializers.ChiefDecisionSerializer": {
        "decision": "approve",
        "notes": "Critical case approved for judiciary referral.",
    },
    "apps.trials.serializers.TrialDecisionSerializer": {
        "verdict": "guilty",
        "punishment_title": "Prison sentence",
        "punishment_description": "Five years imprisonment and post-release supervision.",
    },
    "apps.rewards.serializers.TipSerializer": {
        "case": 1,
        "person": 2,
        "content": "The suspect is hiding near the harbor warehouse after midnight.",
        "attachments": [],
    },
    "apps.rewards.serializers.OfficerReviewSerializer": {
        "approve": True,
        "message": "Credible tip forwarded to the assigned detective.",
    },
    "apps.rewards.serializers.DetectiveReviewSerializer": {
        "approve": True,
        "message": "Tip matched existing evidence and was operationally useful.",
    },
    "apps.payments.serializers.PaymentCreateSerializer": {
        "case_id": 1,
        "person_id": 2,
        "amount": 1000,
        "type": "bail",
    },
    "apps.payments.serializers.PaymentCallbackSerializer": {
        "payment_id": 1,
        "authority": "S000000000000000000000000000000000",
        "status": "OK",
    },
}

SERIALIZER_RESPONSE_EXAMPLES = {
    "apps.accounts.serializers.UserWithRolesSerializer": {
        "id": 1,
        "username": "detective_01",
        "email": "detective@example.com",
        "phone": "5551234567",
        "national_id": "A123456789",
        "first_name": "Cole",
        "last_name": "Phelps",
        "roles": ["detective"],
    },
    "apps.accounts.serializers.LoginResponseSerializer": {
        "tokens": {
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh",
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access",
        },
        "user": {
            "id": 1,
            "username": "detective_01",
            "email": "detective@example.com",
            "phone": "5551234567",
            "national_id": "A123456789",
            "first_name": "Cole",
            "last_name": "Phelps",
        },
    },
    "apps.rbac.serializers.RoleSerializer": {
        "id": 5,
        "name": "Detective",
        "slug": "detective",
        "description": "Investigates active cases, evidence, and suspect link analysis.",
        "is_system": True,
    },
    "apps.cases.serializers.ComplaintSerializer": {
        "id": 12,
        "title": "Home burglary on Olive Street",
        "description": "Front door forced open and jewelry missing from the bedroom.",
        "crime_level": 2,
        "location": "Olive Street, Los Angeles",
        "incident_datetime": "2026-02-25T22:10:00Z",
        "status": "pending_cadet",
        "strike_count": 0,
        "last_message": "",
        "complainants": [
            {
                "id": 4,
                "full_name": "Mary Hudson",
                "phone": "5551112233",
                "national_id": "MH-0001",
                "is_verified": False,
                "verification_status": "pending",
                "review_message": "",
            }
        ],
        "created_at": "2026-02-26T16:00:00Z",
    },
    "apps.cases.serializers.CrimeSceneActionResponseSerializer": {
        "case": {
            "id": 21,
            "title": "Warehouse assault",
            "description": "Officers found signs of struggle and blood traces near the loading dock.",
            "crime_level": 1,
            "location": "Harbor warehouse district",
            "incident_datetime": "2026-02-26T09:55:00Z",
            "status": "pending_superior",
            "source_type": "crime_scene",
            "created_at": "2026-02-26T16:00:00Z",
            "complainants": [],
        },
        "crime_scene_report_id": 8,
    },
    "apps.cases.serializers.CaseSerializer": {
        "id": 21,
        "title": "Warehouse assault",
        "description": "Officers found signs of struggle and blood traces near the loading dock.",
        "crime_level": 1,
        "location": "Harbor warehouse district",
        "incident_datetime": "2026-02-26T09:55:00Z",
        "status": "active",
        "source_type": "crime_scene",
        "created_at": "2026-02-26T16:00:00Z",
        "complainants": [],
    },
    "apps.cases.serializers.CaseAssignmentSerializer": {
        "id": 6,
        "case": 21,
        "user": 7,
        "role_in_case": "detective",
        "assigned_at": "2026-02-26T16:20:00Z",
    },
    "apps.evidence.serializers.EvidenceSerializer": {
        "id": 3,
        "case": 21,
        "title": "Dock worker testimony",
        "description": "Statement from the worker who saw the suspect vehicle leave the scene.",
        "evidence_type": "witness_statement",
        "created_at": "2026-02-26T16:25:00Z",
        "created_by": 7,
        "witness_statement": {
            "transcription": "I saw a dark sedan leaving the warehouse right after the shouting stopped.",
            "media": [
                {
                    "id": 2,
                    "file": "statement-audio.mp3",
                    "media_type": "audio",
                }
            ],
        },
    },
    "apps.board.serializers.BoardItemSerializer": {
        "id": 4,
        "item_type": "NOTE",
        "evidence": None,
        "title": "Timeline",
        "text": "Suspect vehicle appears on camera at 21:10 and exits at 21:18.",
        "x": 320,
        "y": 180,
        "updated_at": "2026-02-26T16:25:00Z",
    },
    "apps.board.serializers.BoardConnectionSerializer": {
        "id": 9,
        "from_item": 4,
        "to_item": 5,
        "created_at": "2026-02-26T16:30:00Z",
    },
    "apps.board.serializers.DetectiveBoardSerializer": {
        "id": 2,
        "case": 21,
        "items": [
            {
                "id": 4,
                "item_type": "NOTE",
                "evidence": None,
                "title": "Timeline",
                "text": "Suspect vehicle appears on camera at 21:10 and exits at 21:18.",
                "x": 320,
                "y": 180,
                "updated_at": "2026-02-26T16:25:00Z",
            }
        ],
        "connections": [
            {
                "id": 9,
                "from_item": 4,
                "to_item": 5,
                "created_at": "2026-02-26T16:30:00Z",
            }
        ],
        "updated_at": "2026-02-26T16:35:00Z",
    },
    "apps.suspects.serializers.SuspectCandidateSerializer": {
        "id": 14,
        "case": 21,
        "person": {
            "id": 2,
            "full_name": "John Doe",
            "national_id": "JD-3001",
            "phone": "5553131313",
            "photo": "/media/suspects/john-doe.jpg",
            "notes": "Seen near the warehouse entrance on CCTV.",
        },
        "rationale": "Vehicle footage and witness testimony place the suspect at the scene.",
        "status": "approved",
        "sergeant_message": "Evidence supports issuing an arrest order.",
        "decided_at": "2026-02-26T18:30:00Z",
    },
    "apps.suspects.serializers.MostWantedSerializer": {
        "person": {
            "id": 2,
            "full_name": "John Doe",
            "national_id": "JD-3001",
            "phone": "5553131313",
            "photo": "/media/suspects/john-doe.jpg",
            "notes": "Seen near the warehouse entrance on CCTV.",
        },
        "days_wanted": 42,
        "crime_degree": 3,
        "ranking_score": 126,
        "reward_amount": 2520000000,
    },
    "apps.notifications.serializers.NotificationSerializer": {
        "id": 11,
        "case": 21,
        "type": "new_evidence",
        "payload": {"evidence_id": 3, "evidence_type": "medical"},
        "created_at": "2026-02-26T16:40:00Z",
        "read_at": None,
    },
    "apps.interrogations.serializers.InterrogationSerializer": {
        "id": 5,
        "case": 21,
        "suspect": 2,
        "detective_score": 7,
        "sergeant_score": 8,
        "captain_decision": "approve",
        "captain_notes": "Evidence supports moving forward with prosecution.",
        "chief_decision": None,
        "chief_notes": "",
        "status": "approved",
    },
    "apps.trials.serializers.TrialSerializer": {
        "id": 3,
        "case": 21,
        "judge": 9,
        "verdict": "guilty",
        "punishment_title": "Prison sentence",
        "punishment_description": "Five years imprisonment and post-release supervision.",
        "decided_at": "2026-02-26T20:00:00Z",
    },
    "apps.trials.serializers.CaseReportResponseSerializer": {
        "case": {
            "id": 21,
            "title": "Warehouse assault",
            "status": "active",
            "crime_level": 1,
        },
        "complaint": None,
        "crime_scene_report": {
            "id": 8,
            "status": "approved",
            "scene_datetime": "2026-02-26T10:15:00Z",
            "reported_by": 5,
            "approved_by": 6,
            "approved_at": "2026-02-26T11:00:00Z",
            "witnesses": [
                {
                    "full_name": "Evelyn Shaw",
                    "phone": "5552003344",
                    "national_id": "ES-4401",
                }
            ],
        },
        "reviews": [],
        "evidence": [
            {
                "id": 3,
                "title": "Dock worker testimony",
                "evidence_type": "witness_statement",
            }
        ],
        "suspects": [
            {
                "id": 14,
                "status": "approved",
                "rationale": "Vehicle footage and witness testimony place the suspect at the scene.",
            }
        ],
        "interrogations": [
            {
                "id": 5,
                "detective_score": 7,
                "sergeant_score": 8,
                "status": "approved",
            }
        ],
        "assignments": [
            {
                "user": {
                    "id": 7,
                    "username": "detective_01",
                    "first_name": "Cole",
                    "last_name": "Phelps",
                    "national_id": "A123456789",
                    "roles": ["detective"],
                },
                "role_in_case": "detective",
                "assigned_at": "2026-02-26T16:20:00Z",
            }
        ],
    },
    "apps.rewards.serializers.TipSerializer": {
        "id": 17,
        "case": 21,
        "person": 2,
        "content": "The suspect is hiding near the harbor warehouse after midnight.",
        "status": "pending_officer",
        "created_at": "2026-02-26T17:10:00Z",
        "attachments": [],
    },
    "apps.rewards.serializers.RewardLookupResponseSerializer": {
        "user": {
            "id": 15,
            "username": "citizen_tipster",
            "national_id": "CI-1001",
        },
        "tip": {
            "id": 17,
            "content": "The suspect is hiding near the harbor warehouse after midnight.",
            "status": "accepted",
        },
        "reward": {
            "code": "RW-1024",
            "issued_at": "2026-02-26T17:45:00Z",
            "redeemed_at": None,
            "status": "issued",
            "amount": 2520000000,
        },
    },
    "apps.payments.serializers.PaymentSerializer": {
        "id": 1,
        "payer": None,
        "case": 21,
        "person": 2,
        "amount": 1000,
        "type": "bail",
        "status": "pending",
        "gateway_ref": "S000000000000000000000000000000000",
        "created_at": "2026-02-26T17:30:00Z",
        "verified_at": None,
    },
    "apps.payments.serializers.PaymentCreateResponseSerializer": {
        "payment": {
            "id": 1,
            "payer": None,
            "case": 21,
            "person": 2,
            "amount": 1000,
            "type": "bail",
            "status": "pending",
            "gateway_ref": "S000000000000000000000000000000000",
            "created_at": "2026-02-26T17:30:00Z",
            "verified_at": None,
        },
        "redirect_url": "https://sandbox.zarinpal.com/pg/StartPay/S000000000000000000000000000000000",
        "authority": "S000000000000000000000000000000000",
    },
    "apps.stats.views.StatsOverviewSerializer": {
        "total_solved_cases": 1,
        "total_employees": 15,
        "active_cases": 4,
    },
}


def _instantiate_serializer(serializer_like):
    if serializer_like in (None, OpenApiTypes.NONE):
        return None
    if inspect.isclass(serializer_like) and issubclass(serializer_like, serializers.BaseSerializer):
        return serializer_like()
    return serializer_like


def _serializer_key(serializer_like):
    return f"{serializer_like.__class__.__module__}.{serializer_like.__class__.__name__}"


def _first_choice(field):
    choices = getattr(field, "choices", None)
    if not choices:
        return None
    if isinstance(choices, Mapping):
        return next(iter(choices.keys()), None)
    return next(iter(choices), None)


def _string_example(field_name):
    if field_name in FIELD_NAME_EXAMPLES:
        return FIELD_NAME_EXAMPLES[field_name]
    if field_name.endswith("_url"):
        return "https://example.com/resource"
    if field_name.endswith("_at") or field_name.endswith("_datetime"):
        return "2026-02-26T10:30:00Z"
    if field_name.endswith("_date"):
        return "2026-02-26"
    if field_name.endswith("_id"):
        return 1
    return "example"


def _build_field_example(field_name, field, *, include_read_only):
    if isinstance(field, serializers.HiddenField):
        return None
    choice_value = _first_choice(field)
    if choice_value is not None:
        return choice_value
    if isinstance(field, serializers.ListSerializer):
        child_example = _build_serializer_example(field.child, include_read_only=include_read_only)
        return [] if child_example is None else [child_example]
    if isinstance(field, serializers.ListField):
        child_example = _build_field_example(field_name, field.child, include_read_only=include_read_only)
        return [] if child_example is None else [child_example]
    if isinstance(field, serializers.DictField):
        return {"key": "value"}
    if isinstance(field, serializers.SerializerMethodField):
        return _string_example(field_name)
    if isinstance(field, serializers.BaseSerializer):
        return _build_serializer_example(field, include_read_only=include_read_only)
    if isinstance(field, serializers.BooleanField):
        return True
    if isinstance(field, (serializers.IntegerField, serializers.PrimaryKeyRelatedField)):
        return FIELD_NAME_EXAMPLES.get(field_name, 1)
    if isinstance(field, serializers.FloatField):
        return 1.5
    if isinstance(field, serializers.DecimalField):
        return "1000.00"
    if isinstance(field, serializers.DateTimeField):
        return "2026-02-26T10:30:00Z"
    if isinstance(field, serializers.DateField):
        return "2026-02-26"
    if isinstance(field, serializers.TimeField):
        return "10:30:00"
    if isinstance(field, serializers.EmailField):
        return "officer@example.com"
    if isinstance(field, serializers.URLField):
        return "https://example.com/resource"
    if isinstance(field, serializers.UUIDField):
        return "123e4567-e89b-12d3-a456-426614174000"
    if isinstance(field, serializers.JSONField):
        return {"key": "value"}
    if isinstance(field, serializers.CharField):
        return _string_example(field_name)
    return _string_example(field_name)


def _build_serializer_example(serializer_like, *, include_read_only):
    serializer_like = _instantiate_serializer(serializer_like)
    if serializer_like is None:
        return None
    if serializer_like == OpenApiTypes.STR:
        return "example"
    if isinstance(serializer_like, serializers.ListSerializer):
        child_example = _build_serializer_example(serializer_like.child, include_read_only=include_read_only)
        return [] if child_example is None else [child_example]
    if not isinstance(serializer_like, serializers.BaseSerializer):
        return None
    if not hasattr(serializer_like, "fields"):
        return None

    serializer_examples = SERIALIZER_RESPONSE_EXAMPLES if include_read_only else SERIALIZER_REQUEST_EXAMPLES
    serializer_key = _serializer_key(serializer_like)
    if serializer_key in serializer_examples:
        return serializer_examples[serializer_key]

    example = {}
    for field_name, field in serializer_like.fields.items():
        if include_read_only and getattr(field, "write_only", False):
            continue
        if not include_read_only and getattr(field, "read_only", False):
            continue
        value = _build_field_example(field_name, field, include_read_only=include_read_only)
        if value is not None:
            example[field_name] = value
    return example or None


def _pick_success_response_serializer(response_serializers):
    if isinstance(response_serializers, Mapping):
        for code in ("200", 200, "201", 201, "202", 202):
            if code in response_serializers:
                return response_serializers[code]
        for code, serializer_like in response_serializers.items():
            if str(code).startswith("2"):
                return serializer_like
        return next(iter(response_serializers.values()), None)
    return response_serializers


class PoliceAutoSchema(AutoSchema):
    def _allows_anonymous(self):
        permission_classes = getattr(self.view, "permission_classes", None) or api_settings.DEFAULT_PERMISSION_CLASSES
        for permission_class in permission_classes:
            if inspect.isclass(permission_class) and issubclass(permission_class, AllowAny):
                return True
        return False

    def get_description(self):
        base_description = super().get_description() or ""
        handler = getattr(self.view, self.method.lower(), None)
        doc_description = inspect.getdoc(handler) or inspect.getdoc(self.view) or ""

        description_parts = []
        if base_description.strip():
            description_parts.append(base_description.strip())
        elif doc_description.strip():
            description_parts.append(doc_description.strip())

        auth_text = "Authentication: No JWT required." if self._allows_anonymous() else "Authentication: Bearer JWT access token required."
        description_parts.append(auth_text)

        roles = getattr(self.view, "required_roles", None)
        if roles:
            description_parts.append(f"Required roles: {', '.join(roles)}")

        description_parts.append("Errors use the envelope `{error: {code, message, details}}`.")
        return "\n\n".join(description_parts)

    def get_examples(self):
        examples = list(super().get_examples() or [])
        has_request = any(getattr(example, "request_only", False) for example in examples)
        has_response = any(getattr(example, "response_only", False) for example in examples)

        if not has_request:
            request_example = _build_serializer_example(self.get_request_serializer(), include_read_only=False)
            if request_example is not None:
                examples.append(OpenApiExample("Request Example", value=request_example, request_only=True))

        if not has_response:
            response_serializer = _pick_success_response_serializer(self.get_response_serializers())
            response_example = _build_serializer_example(response_serializer, include_read_only=True)
            if response_example is not None:
                examples.append(OpenApiExample("Success Response", value=response_example, response_only=True))

        if not any(getattr(example, "response_only", False) and example.name == GENERIC_ERROR_EXAMPLE.name for example in examples):
            examples.append(GENERIC_ERROR_EXAMPLE)
        return examples
