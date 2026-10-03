from django.urls import path

from .views import ReportProblemView


urlpatterns = [
    path("", ReportProblemView.as_view(), name="report-problem"),
]