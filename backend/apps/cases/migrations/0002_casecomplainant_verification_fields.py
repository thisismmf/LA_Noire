from django.db import migrations, models


def set_initial_verification_status(apps, schema_editor):
    CaseComplainant = apps.get_model("cases", "CaseComplainant")
    CaseComplainant.objects.filter(is_verified=True).update(verification_status="approved")
    CaseComplainant.objects.filter(is_verified=False).update(verification_status="pending")


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="casecomplainant",
            name="review_message",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="casecomplainant",
            name="verification_status",
            field=models.CharField(
                choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.RunPython(set_initial_verification_status, migrations.RunPython.noop),
    ]
