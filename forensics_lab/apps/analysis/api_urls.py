from django.urls import path
from . import views

urlpatterns = [
    path("task/<int:pk>/status/", views.task_status_view, name="task_status"),
    path("run/<int:evidence_pk>/", views.run_analysis_view, name="run_analysis"),
]
