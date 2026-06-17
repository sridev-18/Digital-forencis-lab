from django.urls import path
from . import views

app_name = "analysis"

urlpatterns = [
    path("case/<int:case_pk>/", views.analysis_list_view, name="list"),
    path("task/<int:pk>/", views.analysis_detail_view, name="detail"),
    path("task/<int:pk>/status/", views.task_status_view, name="status"),
    path("run/<int:evidence_pk>/", views.run_analysis_view, name="run"),
    path("timeline/<int:case_pk>/", views.timeline_view, name="timeline"),
]
