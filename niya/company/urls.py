from django.urls import path

from .views import CompanyView, CompanyNameView

urlpatterns = [
    path("company/", CompanyView.as_view(), name="company_api"),
    path("company/<str:name>/", CompanyNameView.as_view(), name="company_api"),
]
