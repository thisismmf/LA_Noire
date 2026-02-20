from django.conf import settings
from django.db import models


class Trial(models.Model):
    VERDICT_CHOICES = (
        ("guilty", "Guilty"),
        ("not_guilty", "Not Guilty"),
    )
    case = models.OneToOneField("cases.Case", on_delete=models.CASCADE, related_name="trial")
    judge = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="trials")
    verdict = models.CharField(max_length=20, choices=VERDICT_CHOICES)
    punishment_title = models.CharField(max_length=255, blank=True)
    punishment_description = models.TextField(blank=True)
    decided_at = models.DateTimeField(auto_now_add=True)
