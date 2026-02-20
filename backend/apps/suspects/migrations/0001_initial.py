from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cases", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Person",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=255)),
                ("national_id", models.CharField(blank=True, max_length=20)),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("photo", models.ImageField(blank=True, null=True, upload_to="persons/")),
                ("notes", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="SuspectCandidate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rationale", models.TextField()),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=20)),
                ("sergeant_message", models.TextField(blank=True)),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="suspect_candidates", to="cases.case")),
                ("person", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="suspect_candidates", to="suspects.person")),
                ("proposed_by_detective", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="suspects_proposed", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="WantedRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("wanted", "Wanted"), ("arrested", "Arrested"), ("cleared", "Cleared")], default="wanted", max_length=20)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wanted_records", to="cases.case")),
                ("person", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="wanted_records", to="suspects.person")),
            ],
        ),
    ]
