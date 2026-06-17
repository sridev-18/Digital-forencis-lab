from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("case/<int:case_pk>/", views.report_view, name="view"),
    path("case/<int:case_pk>/pdf/", views.export_pdf_view, name="pdf"),
]
