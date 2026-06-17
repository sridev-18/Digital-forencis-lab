from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import CaseViewSet

router = DefaultRouter()
router.register(r"", CaseViewSet, basename="case")
urlpatterns = router.urls
