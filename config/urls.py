from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("", include("apps.cases.urls")),
    path("evidence/", include("apps.evidence.urls")),
    path("analysis/", include("apps.analysis.urls")),
    path("reports/", include("apps.reports.urls")),
    path("audit/", include("apps.audit.urls")),

    # REST API endpoints
    path("api/accounts/", include("apps.accounts.api_urls")),
    path("api/cases/", include("apps.cases.api_urls")),
    path("api/evidence/", include("apps.evidence.api_urls")),
    path("api/analysis/", include("apps.analysis.api_urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
