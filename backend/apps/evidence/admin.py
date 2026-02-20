from django.contrib import admin
from .models import Evidence, WitnessStatementEvidence, EvidenceMedia, MedicalEvidence, MedicalEvidenceImage, VehicleEvidence, IdentityDocumentEvidence

admin.site.register(Evidence)
admin.site.register(WitnessStatementEvidence)
admin.site.register(EvidenceMedia)
admin.site.register(MedicalEvidence)
admin.site.register(MedicalEvidenceImage)
admin.site.register(VehicleEvidence)
admin.site.register(IdentityDocumentEvidence)
