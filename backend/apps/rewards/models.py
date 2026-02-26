import uuid
from django.conf import settings
from django.db import models


class Tip(models.Model):
    STATUS_CHOICES = (
        ("pending_officer", "Pending Officer"),
        ("pending_detective", "Pending Detective"),
        ("rejected", "Rejected"),
        ("accepted", "Accepted"),
    )
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tips")
    case = models.ForeignKey("cases.Case", on_delete=models.SET_NULL, null=True, blank=True, related_name="tips")
    person = models.ForeignKey("suspects.Person", on_delete=models.SET_NULL, null=True, blank=True, related_name="tips")
    content = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending_officer")
    officer_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="tips_reviewed_officer")
    detective_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="tips_reviewed_detective")
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)


class TipAttachment(models.Model):
    tip = models.ForeignKey(Tip, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="tips/")


class RewardCode(models.Model):
    code = models.CharField(max_length=32, unique=True)
    tip = models.OneToOneField(Tip, on_delete=models.CASCADE, related_name="reward_code")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reward_codes")
    amount = models.BigIntegerField(default=0)
    issued_at = models.DateTimeField(auto_now_add=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def generate_code():
        return uuid.uuid4().hex[:12]
