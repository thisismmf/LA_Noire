from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.rbac.models import Role
from .constants import (
    CrimeLevel,
    CaseStatus,
    ComplaintStatus,
    CrimeSceneStatus,
    CaseSourceType,
    CaseAssignmentRole,
)


class Complaint(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    crime_level = models.IntegerField(choices=CrimeLevel.choices)
    location = models.CharField(max_length=255)
    incident_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=ComplaintStatus.choices, default=ComplaintStatus.PENDING_CADET_REVIEW)
    strike_count = models.PositiveIntegerField(default=0)
    last_message = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="complaints")
    assigned_cadet = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_cadet_complaints",
    )
    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_officer_complaints",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Complaint {self.id}"


class Case(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    crime_level = models.IntegerField(choices=CrimeLevel.choices)
    location = models.CharField(max_length=255)
    incident_datetime = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=CaseStatus.choices, default=CaseStatus.ACTIVE)
    source_type = models.CharField(max_length=50, choices=CaseSourceType.choices)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="created_cases")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    complaint = models.OneToOneField("Complaint", on_delete=models.SET_NULL, null=True, blank=True, related_name="case")

    def __str__(self):
        return f"Case {self.id}"


class CaseComplainant(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, null=True, blank=True, related_name="complainants")
    case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True, blank=True, related_name="complainants")
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    national_id = models.CharField(max_length=20)
    is_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    review_message = models.TextField(blank=True)

    def __str__(self):
        return self.full_name


class CaseReview(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="reviews")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    decision = models.CharField(max_length=50)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CrimeSceneReport(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name="crime_scene_report")
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="crime_scene_reports")
    scene_datetime = models.DateTimeField()
    status = models.CharField(max_length=50, choices=CrimeSceneStatus.choices, default=CrimeSceneStatus.PENDING_APPROVAL)
    required_approver_role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name="required_approvals")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="crime_scene_approvals")
    approved_at = models.DateTimeField(null=True, blank=True)


class CrimeSceneWitness(models.Model):
    report = models.ForeignKey(CrimeSceneReport, on_delete=models.CASCADE, related_name="witnesses")
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20)
    national_id = models.CharField(max_length=20)


class CaseAssignment(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="case_assignments")
    role_in_case = models.CharField(max_length=50, choices=CaseAssignmentRole.choices)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("case", "user", "role_in_case")


