from . import views
from django.urls import path, include

urlpatterns = [
    path('dashboard', views.Dashboard.as_view(), name="dashboard"),
    path('edit/<slug:slug>', views.EditAppointment.as_view(), name="edit-appointment")
]