from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Role",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, unique=True)),
                ("slug", models.SlugField(max_length=150, unique=True)),
                ("description", models.TextField(blank=True)),
                ("is_system", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="UserRole",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="role_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="role_users", to="rbac.role"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_roles", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "unique_together": {("user", "role")},
            },
        ),
    ]
