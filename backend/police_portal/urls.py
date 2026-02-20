from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.rbac.urls")),
    path("api/v1/", include("apps.cases.urls")),
    path("api/v1/", include("apps.evidence.urls")),
    path("api/v1/", include("apps.board.urls")),
    path("api/v1/", include("apps.suspects.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.interrogations.urls")),
    path("api/v1/", include("apps.trials.urls")),
    path("api/v1/", include("apps.rewards.urls")),
    path("api/v1/", include("apps.payments.urls")),
    path("api/v1/", include("apps.stats.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

