from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import (
    # Healthcheck
    Healthcheck,
    MyUserAPIView,
    # Authentication
    RegisterAPIView,
    LoginAPIView,
    UsersAPIView,
    SendVerificationCodeView,
    VerifyEmailView,
    UserDetailAPIView,
    ConfirmPasswordResetView,
    RequestPasswordResetView,
)

urlpatterns = [
    # Healthcheck
    path("healthcheck/", Healthcheck.as_view(), name="healthcheck_auth_api"),
    # Endpoints
    path("user/", MyUserAPIView.as_view(), name="my_user_api"),
    path("users/", UsersAPIView.as_view(), name="users_api"),
    path("users/<int:pk>/", UserDetailAPIView.as_view(), name="user_detail_api"),
    # Authentication (Register and Login)
    path("register/", RegisterAPIView.as_view(), name="register_api"),
    path("login/", LoginAPIView.as_view(), name="login_api"),
    # Email verification
    path(
        "send-verification-code/",
        SendVerificationCodeView.as_view(),
        name="send_verification_code",
    ),
    path("verify-email/", VerifyEmailView.as_view(), name="verify_email"),
    # Reset password
    path(
        "request-password-reset/",
        RequestPasswordResetView.as_view(),
        name="request_password_reset",
    ),
    path(
        "confirm-password-reset/",
        ConfirmPasswordResetView.as_view(),
        name="confirm_password_reset",
    ),
]
