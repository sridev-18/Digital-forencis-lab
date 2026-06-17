from django.urls import path
from rest_framework.routers import DefaultRouter
from .api_views import EvidenceViewSet

router = DefaultRouter()
router.register(r"", EvidenceViewSet, basename="evidence")
urlpatterns = router.urls
