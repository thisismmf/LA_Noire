from django.conf import settings
from django.db import models


class Payment(models.Model):
    TYPE_CHOICES = (
        ("bail", "Bail"),
        ("fine", "Fine"),
    )
    STATUS_CHOICES = (
        ("created", "Created"),
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    )
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    case = models.ForeignKey("cases.Case", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    person = models.ForeignKey("suspects.Person", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    amount = models.PositiveBigIntegerField()
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    gateway_ref = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
