from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cases", "0001_initial"),
        ("suspects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tip",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()),
                ("status", models.CharField(choices=[("pending_officer", "Pending Officer"), ("pending_detective", "Pending Detective"), ("rejected", "Rejected"), ("accepted", "Accepted")], default="pending_officer", max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("case", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tips", to="cases.case")),
                ("detective_reviewer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tips_reviewed_detective", to=settings.AUTH_USER_MODEL)),
                ("officer_reviewer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tips_reviewed_officer", to=settings.AUTH_USER_MODEL)),
                ("person", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tips", to="suspects.person")),
                ("submitted_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tips", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="TipAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="tips/")),
                ("tip", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="rewards.tip")),
            ],
        ),
        migrations.CreateModel(
            name="RewardCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=32, unique=True)),
                ("issued_at", models.DateTimeField(auto_now_add=True)),
                ("redeemed_at", models.DateTimeField(blank=True, null=True)),
                ("tip", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="reward_code", to="rewards.tip")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reward_codes", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
