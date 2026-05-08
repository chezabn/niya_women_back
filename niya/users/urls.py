from django.urls import path

from .views import (
    Healthcheck,
    MyUserAPIView
)

urlpatterns = [
    path("healthcheck/", Healthcheck.as_view(), name="healthcheck_auth_api"),
    path("me/", MyUserAPIView.as_view(), name="my_user"),
]
