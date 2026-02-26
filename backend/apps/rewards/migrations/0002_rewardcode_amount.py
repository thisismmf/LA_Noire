from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rewards", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="rewardcode",
            name="amount",
            field=models.BigIntegerField(default=0),
        ),
    ]
