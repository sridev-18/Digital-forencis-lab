from django.urls import path
from . import views

app_name = "cases"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("cases/", views.case_list_view, name="list"),
    path("cases/new/", views.case_create_view, name="create"),
    path("cases/<int:pk>/", views.case_detail_view, name="detail"),
    path("cases/<int:pk>/edit/", views.case_update_view, name="update"),
    path("cases/<int:pk>/notes/", views.add_note_view, name="add_note"),
]
