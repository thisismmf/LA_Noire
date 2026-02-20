from django.db import models


class CrimeLevel(models.IntegerChoices):
    LEVEL_3 = 1, "Level 3"
    LEVEL_2 = 2, "Level 2"
    LEVEL_1 = 3, "Level 1"
    CRITICAL = 4, "Critical"


CRIME_LEVEL_TO_DEGREE = {
    CrimeLevel.LEVEL_3: 1,
    CrimeLevel.LEVEL_2: 2,
    CrimeLevel.LEVEL_1: 3,
    CrimeLevel.CRITICAL: 4,
}


class CaseStatus(models.TextChoices):
    PENDING_SUPERIOR_APPROVAL = "pending_superior", "Pending Superior Approval"
    ACTIVE = "active", "Active"
    CLOSED_SOLVED = "closed_solved", "Closed (Solved)"
    CLOSED_UNSOLVED = "closed_unsolved", "Closed (Unsolved)"
    VOIDED = "voided", "Voided"


class ComplaintStatus(models.TextChoices):
    PENDING_CADET_REVIEW = "pending_cadet", "Pending Cadet Review"
    RETURNED_TO_COMPLAINANT = "returned_to_complainant", "Returned to Complainant"
    PENDING_OFFICER_REVIEW = "pending_officer", "Pending Officer Review"
    RETURNED_TO_CADET = "returned_to_cadet", "Returned to Cadet"
    APPROVED = "approved", "Approved"
    VOIDED = "voided", "Voided"


class CrimeSceneStatus(models.TextChoices):
    PENDING_APPROVAL = "pending_approval", "Pending Approval"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class CaseSourceType(models.TextChoices):
    COMPLAINT = "complaint", "Complaint"
    CRIME_SCENE = "crime_scene", "Crime Scene"


class CaseAssignmentRole(models.TextChoices):
    DETECTIVE = "detective", "Detective"
    OFFICER = "officer", "Officer"
    SERGEANT = "sergeant", "Sergeant"
