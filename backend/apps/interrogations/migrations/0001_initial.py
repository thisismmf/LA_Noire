from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("cases", "0001_initial"),
        ("suspects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Interrogation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("detective_score", models.IntegerField(blank=True, null=True)),
                ("sergeant_score", models.IntegerField(blank=True, null=True)),
                ("captain_decision", models.CharField(blank=True, max_length=50)),
                ("captain_notes", models.TextField(blank=True)),
                ("chief_decision", models.CharField(blank=True, max_length=50)),
                ("chief_notes", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("pending_detective", "Pending Detective"), ("pending_sergeant", "Pending Sergeant"), ("pending_captain", "Pending Captain"), ("pending_chief", "Pending Chief"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending_detective", max_length=50)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interrogations", to="cases.case")),
                ("suspect", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interrogations", to="suspects.person")),
            ],
        ),
    ]
