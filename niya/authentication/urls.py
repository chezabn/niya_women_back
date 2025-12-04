from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import MyUserAPIView, RegisterAPIView, Healthcheck, UsersAPIView

urlpatterns = [
    path("user/", MyUserAPIView.as_view(), name="my_user_api"),
    path("users/", UsersAPIView.as_view(), name="users_api"),
    path("register/", RegisterAPIView.as_view(), name="register_api"),
    path("login/", TokenObtainPairView.as_view(), name="login_api"),
    path("healthcheck/", Healthcheck.as_view(), name="healthcheck_auth_api"),
]
