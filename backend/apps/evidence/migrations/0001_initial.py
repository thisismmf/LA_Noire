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
            name="Evidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("evidence_type", models.CharField(choices=[("witness_statement", "Witness Statement"), ("medical", "Medical"), ("vehicle", "Vehicle"), ("identity_document", "Identity Document"), ("other", "Other")], max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="evidence", to="cases.case")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="evidence_created", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="WitnessStatementEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("transcription", models.TextField()),
                ("evidence", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="witness_statement", to="evidence.evidence")),
            ],
        ),
        migrations.CreateModel(
            name="EvidenceMedia",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="evidence_media/")),
                ("media_type", models.CharField(blank=True, max_length=50)),
                ("witness_statement", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="media", to="evidence.witnessstatementevidence")),
            ],
        ),
        migrations.CreateModel(
            name="MedicalEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("forensic_result", models.TextField(blank=True)),
                ("identity_db_result", models.TextField(blank=True)),
                ("status", models.CharField(default="pending", max_length=50)),
                ("evidence", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="medical", to="evidence.evidence")),
            ],
        ),
        migrations.CreateModel(
            name="MedicalEvidenceImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="medical_evidence/")),
                ("medical_evidence", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="evidence.medicalevidence")),
            ],
        ),
        migrations.CreateModel(
            name="VehicleEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("model", models.CharField(max_length=255)),
                ("color", models.CharField(max_length=100)),
                ("license_plate", models.CharField(blank=True, max_length=50)),
                ("serial_number", models.CharField(blank=True, max_length=50)),
                ("evidence", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="vehicle", to="evidence.evidence")),
            ],
        ),
        migrations.CreateModel(
            name="IdentityDocumentEvidence",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("owner_full_name", models.CharField(max_length=255)),
                ("data", models.JSONField(blank=True, default=dict)),
                ("evidence", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="identity_document", to="evidence.evidence")),
            ],
        ),
    ]
