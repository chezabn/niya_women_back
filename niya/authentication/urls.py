from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import (
    MyUserAPIView,
    RegisterAPIView,
    Healthcheck,
    UsersAPIView,
    SendVerificationCodeView,
    VerifyEmailView, UserDetailAPIView,
)

urlpatterns = [
    path("user/", MyUserAPIView.as_view(), name="my_user_api"),
    path("users/", UsersAPIView.as_view(), name="users_api"),
    path("users/<int:pk>/", UserDetailAPIView.as_view(), name="user_detail_api"),

    path("register/", RegisterAPIView.as_view(), name="register_api"),
    path("login/", TokenObtainPairView.as_view(), name="login_api"),
    path("healthcheck/", Healthcheck.as_view(), name="healthcheck_auth_api"),
    # Email verification
    path(
        "send-verification-code/",
        SendVerificationCodeView.as_view(),
        name="send_verification_code",
    ),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
]
