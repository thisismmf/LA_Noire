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
            name="Trial",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("verdict", models.CharField(choices=[("guilty", "Guilty"), ("not_guilty", "Not Guilty")], max_length=20)),
                ("punishment_title", models.CharField(blank=True, max_length=255)),
                ("punishment_description", models.TextField(blank=True)),
                ("decided_at", models.DateTimeField(auto_now_add=True)),
                ("case", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="trial", to="cases.case")),
                ("judge", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="trials", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
