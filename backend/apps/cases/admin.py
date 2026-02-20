from django.contrib import admin
from .models import Complaint, Case, CaseComplainant, CaseReview, CrimeSceneReport, CrimeSceneWitness, CaseAssignment


admin.site.register(Complaint)
admin.site.register(Case)
admin.site.register(CaseComplainant)
admin.site.register(CaseReview)
admin.site.register(CrimeSceneReport)
admin.site.register(CrimeSceneWitness)
admin.site.register(CaseAssignment)
