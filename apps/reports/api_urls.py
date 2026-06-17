from django.urls import path
from . import views

urlpatterns = [
    path("case/<int:case_pk>/pdf/", views.export_pdf_view, name="api_report_pdf"),
]
