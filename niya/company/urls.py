from django.urls import path

from .views import CompanyView, CompanyIDView

urlpatterns = [
    path("company/", CompanyView.as_view(), name="company_api"),
    path("company/<int:company_id>/", CompanyIDView.as_view(), name="company_api_id"),
]
