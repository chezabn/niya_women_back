from django.urls import path

from .views import MyCompanyView, CompanyIDView, CompaniesView

urlpatterns = [
    path("company/mine/", MyCompanyView.as_view(), name="my_company_api"),
    path("companies/", CompaniesView.as_view(), name="company_api"),
    path("companies/<int:company_id>/", CompanyIDView.as_view(), name="company_api_id"),
]
