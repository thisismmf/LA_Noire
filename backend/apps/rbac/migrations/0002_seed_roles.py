from django.db import migrations
from apps.rbac.constants import (
    ROLE_SYSTEM_ADMIN,
    ROLE_POLICE_CHIEF,
    ROLE_CAPTAIN,
    ROLE_SERGEANT,
    ROLE_DETECTIVE,
    ROLE_POLICE_OFFICER,
    ROLE_PATROL_OFFICER,
    ROLE_CADET,
    ROLE_COMPLAINANT,
    ROLE_WITNESS,
    ROLE_SUSPECT,
    ROLE_CRIMINAL,
    ROLE_JUDGE,
    ROLE_CORONER,
    ROLE_BASE_USER,
)


ROLE_DEFINITIONS = [
    (ROLE_SYSTEM_ADMIN, "System Administrator (مدیر کل سامانه)"),
    (ROLE_POLICE_CHIEF, "Police Chief (رئیس پلیس)"),
    (ROLE_CAPTAIN, "Captain (کاپیتان)"),
    (ROLE_SERGEANT, "Sergeant (گروهبان)"),
    (ROLE_DETECTIVE, "Detective (کارآگاه)"),
    (ROLE_POLICE_OFFICER, "Police Officer (مامور پلیس)"),
    (ROLE_PATROL_OFFICER, "Patrol Officer (افسر گشت)"),
    (ROLE_CADET, "Cadet (کارآموز)"),
    (ROLE_COMPLAINANT, "Complainant (شاکی)"),
    (ROLE_WITNESS, "Witness (شاهد)"),
    (ROLE_SUSPECT, "Suspect (متهم)"),
    (ROLE_CRIMINAL, "Criminal (مجرم)"),
    (ROLE_JUDGE, "Judge (قاضی)"),
    (ROLE_CORONER, "Coroner/Forensic Doctor (پزشک قانونی)"),
    (ROLE_BASE_USER, "Base User / کاربر عادی"),
]


def seed_roles(apps, schema_editor):
    Role = apps.get_model("rbac", "Role")
    for slug, name in ROLE_DEFINITIONS:
        Role.objects.get_or_create(slug=slug, defaults={"name": name, "description": name, "is_system": True})


def remove_roles(apps, schema_editor):
    Role = apps.get_model("rbac", "Role")
    Role.objects.filter(slug__in=[slug for slug, _ in ROLE_DEFINITIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("rbac", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles, remove_roles),
    ]
