from django.conf import settings
from django.db import models


class EvidenceType(models.TextChoices):
    WITNESS_STATEMENT = "witness_statement", "Witness Statement"
    MEDICAL = "medical", "Medical"
    VEHICLE = "vehicle", "Vehicle"
    IDENTITY_DOCUMENT = "identity_document", "Identity Document"
    OTHER = "other", "Other"


class Evidence(models.Model):
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, related_name="evidence")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    evidence_type = models.CharField(max_length=50, choices=EvidenceType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="evidence_created")

    def __str__(self):
        return f"Evidence {self.id}"


class WitnessStatementEvidence(models.Model):
    evidence = models.OneToOneField(Evidence, on_delete=models.CASCADE, related_name="witness_statement")
    transcription = models.TextField()


class EvidenceMedia(models.Model):
    witness_statement = models.ForeignKey(WitnessStatementEvidence, on_delete=models.CASCADE, related_name="media")
    file = models.FileField(upload_to="evidence_media/")
    media_type = models.CharField(max_length=50, blank=True)


class MedicalEvidence(models.Model):
    evidence = models.OneToOneField(Evidence, on_delete=models.CASCADE, related_name="medical")
    forensic_result = models.TextField(blank=True)
    identity_db_result = models.TextField(blank=True)
    status = models.CharField(max_length=50, default="pending")


class MedicalEvidenceImage(models.Model):
    medical_evidence = models.ForeignKey(MedicalEvidence, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="medical_evidence/")


class VehicleEvidence(models.Model):
    evidence = models.OneToOneField(Evidence, on_delete=models.CASCADE, related_name="vehicle")
    model = models.CharField(max_length=255)
    color = models.CharField(max_length=100)
    license_plate = models.CharField(max_length=50, blank=True)
    serial_number = models.CharField(max_length=50, blank=True)


class IdentityDocumentEvidence(models.Model):
    evidence = models.OneToOneField(Evidence, on_delete=models.CASCADE, related_name="identity_document")
    owner_full_name = models.CharField(max_length=255)
    data = models.JSONField(blank=True, default=dict)


