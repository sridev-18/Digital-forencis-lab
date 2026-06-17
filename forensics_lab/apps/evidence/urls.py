from django.urls import path
from . import views

app_name = "evidence"

urlpatterns = [
    path("upload/<int:case_pk>/", views.evidence_upload_view, name="upload"),
    path("<int:pk>/", views.evidence_detail_view, name="detail"),
    path("<int:pk>/verify/", views.verify_hash_view, name="verify_hash"),
]
