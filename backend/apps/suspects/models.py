from django.db import models
from django.conf import settings


class Person(models.Model):
    full_name = models.CharField(max_length=255)
    national_id = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to="persons/", blank=True, null=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.full_name


class SuspectCandidate(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, related_name="suspect_candidates")
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="suspect_candidates")
    proposed_by_detective = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="suspects_proposed")
    rationale = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    sergeant_message = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)


class WantedRecord(models.Model):
    STATUS_CHOICES = (
        ("wanted", "Wanted"),
        ("arrested", "Arrested"),
        ("cleared", "Cleared"),
    )
    person = models.ForeignKey(Person, on_delete=models.CASCADE, related_name="wanted_records")
    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, related_name="wanted_records")
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="wanted")

