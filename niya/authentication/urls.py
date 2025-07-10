# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from authentication.views import UserAPIView, RegisterAPIView, Healthcheck


urlpatterns = [
    path("users/", UserAPIView.as_view(), name="users_api"),
    path("register/", RegisterAPIView.as_view(), name="register_api"),
    path("login/", TokenObtainPairView.as_view(), name="login_api"),
    path("healthcheck/", Healthcheck.as_view(), name="healthcheck_auth_api"),
]
