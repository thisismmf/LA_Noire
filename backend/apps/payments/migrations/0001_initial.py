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
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.PositiveBigIntegerField()),
                ("type", models.CharField(choices=[("bail", "Bail"), ("fine", "Fine")], max_length=10)),
                ("status", models.CharField(choices=[("created", "Created"), ("pending", "Pending"), ("success", "Success"), ("failed", "Failed")], default="created", max_length=20)),
                ("gateway_ref", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("verified_at", models.DateTimeField(blank=True, null=True)),
                ("case", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payments", to="cases.case")),
                ("payer", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payments", to=settings.AUTH_USER_MODEL)),
                ("person", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payments", to="suspects.person")),
            ],
        ),
    ]
