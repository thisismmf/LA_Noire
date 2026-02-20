from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cases", "0001_initial"),
        ("evidence", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DetectiveBoard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("case", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="board", to="cases.case")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="boards_created", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="BoardItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("item_type", models.CharField(choices=[("EVIDENCE_REF", "Evidence Ref"), ("NOTE", "Note")], max_length=20)),
                ("title", models.CharField(blank=True, max_length=255)),
                ("text", models.TextField(blank=True)),
                ("x", models.FloatField(default=0)),
                ("y", models.FloatField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("board", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="board.detectiveboard")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="board_items_created", to=settings.AUTH_USER_MODEL)),
                ("evidence", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="board_items", to="evidence.evidence")),
            ],
        ),
        migrations.CreateModel(
            name="BoardConnection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("board", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="connections", to="board.detectiveboard")),
                ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="board_connections_created", to=settings.AUTH_USER_MODEL)),
                ("from_item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="connections_from", to="board.boarditem")),
                ("to_item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="connections_to", to="board.boarditem")),
            ],
        ),
    ]
