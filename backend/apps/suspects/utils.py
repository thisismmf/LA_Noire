from django.utils import timezone
from apps.cases.constants import CRIME_LEVEL_TO_DEGREE, CaseStatus
from .models import WantedRecord


def compute_most_wanted():
    now = timezone.now()
    persons = {}
    records = WantedRecord.objects.select_related("case", "person").all()
    for record in records:
        person = record.person
        if person.id not in persons:
            persons[person.id] = {
                "person": person,
                "days_wanted": 0,
                "crime_degree": 0,
            }
        info = persons[person.id]
        degree = CRIME_LEVEL_TO_DEGREE.get(record.case.crime_level, 0)
        if degree > info["crime_degree"]:
            info["crime_degree"] = degree
        if record.status == "wanted" and record.case.status in [CaseStatus.ACTIVE, CaseStatus.PENDING_SUPERIOR_APPROVAL]:
            delta_days = (now - record.started_at).days
            if delta_days > info["days_wanted"]:
                info["days_wanted"] = delta_days
    results = []
    for info in persons.values():
        if info["days_wanted"] < 30:
            continue
        ranking_score = info["days_wanted"] * info["crime_degree"]
        reward_amount = ranking_score * 20000000
        results.append({
            "person": info["person"],
            "days_wanted": info["days_wanted"],
            "crime_degree": info["crime_degree"],
            "ranking_score": ranking_score,
            "reward_amount": reward_amount,
        })
    results.sort(key=lambda x: x["ranking_score"], reverse=True)
    return results
