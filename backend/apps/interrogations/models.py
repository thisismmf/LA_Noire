from django.db import models
from django.conf import settings


class Interrogation(models.Model):
    STATUS_CHOICES = (
        ("pending_detective", "Pending Detective"),
        ("pending_sergeant", "Pending Sergeant"),
        ("pending_captain", "Pending Captain"),
        ("pending_chief", "Pending Chief"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, related_name="interrogations")
    suspect = models.ForeignKey("suspects.Person", on_delete=models.CASCADE, related_name="interrogations")
    detective_score = models.IntegerField(null=True, blank=True)
    sergeant_score = models.IntegerField(null=True, blank=True)
    captain_decision = models.CharField(max_length=50, blank=True)
    captain_notes = models.TextField(blank=True)
    captain_reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="captain_interrogation_decisions",
    )
    chief_decision = models.CharField(max_length=50, blank=True)
    chief_notes = models.TextField(blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending_detective")

