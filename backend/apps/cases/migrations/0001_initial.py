from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("rbac", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Complaint",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("crime_level", models.IntegerField(choices=[(1, "Level 3"), (2, "Level 2"), (3, "Level 1"), (4, "Critical")])),
                ("location", models.CharField(max_length=255)),
                ("incident_datetime", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("pending_cadet", "Pending Cadet Review"), ("returned_to_complainant", "Returned to Complainant"), ("pending_officer", "Pending Officer Review"), ("returned_to_cadet", "Returned to Cadet"), ("approved", "Approved"), ("voided", "Voided")], default="pending_cadet", max_length=50)),
                ("strike_count", models.PositiveIntegerField(default=0)),
                ("last_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="complaints", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Case",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("crime_level", models.IntegerField(choices=[(1, "Level 3"), (2, "Level 2"), (3, "Level 1"), (4, "Critical")])),
                ("location", models.CharField(max_length=255)),
                ("incident_datetime", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("pending_superior", "Pending Superior Approval"), ("active", "Active"), ("closed_solved", "Closed (Solved)"), ("closed_unsolved", "Closed (Unsolved)"), ("voided", "Voided")], default="active", max_length=50)),
                ("source_type", models.CharField(choices=[("complaint", "Complaint"), ("crime_scene", "Crime Scene")], max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("complaint", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="case", to="cases.complaint")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_cases", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="CaseComplainant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=255)),
                ("phone", models.CharField(max_length=20)),
                ("national_id", models.CharField(max_length=20)),
                ("is_verified", models.BooleanField(default=False)),
                ("case", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="complainants", to="cases.case")),
                ("complaint", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="complainants", to="cases.complaint")),
            ],
        ),
        migrations.CreateModel(
            name="CaseReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("decision", models.CharField(max_length=50)),
                ("message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("complaint", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="cases.complaint")),
                ("reviewer", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="CrimeSceneReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scene_datetime", models.DateTimeField()),
                ("status", models.CharField(choices=[("pending_approval", "Pending Approval"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending_approval", max_length=50)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crime_scene_approvals", to=settings.AUTH_USER_MODEL)),
                ("case", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="crime_scene_report", to="cases.case")),
                ("reported_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="crime_scene_reports", to=settings.AUTH_USER_MODEL)),
                ("required_approver_role", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="required_approvals", to="rbac.role")),
            ],
        ),
        migrations.CreateModel(
            name="CrimeSceneWitness",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(blank=True, max_length=255)),
                ("phone", models.CharField(max_length=20)),
                ("national_id", models.CharField(max_length=20)),
                ("report", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="witnesses", to="cases.crimescenereport")),
            ],
        ),
        migrations.CreateModel(
            name="CaseAssignment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role_in_case", models.CharField(choices=[("detective", "Detective"), ("officer", "Officer"), ("sergeant", "Sergeant")], max_length=50)),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="cases.case")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="case_assignments", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "unique_together": {("case", "user", "role_in_case")},
            },
        ),
    ]
