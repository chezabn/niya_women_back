from django.urls import path

from .views import (
    Healthcheck,
    SubmitIdentityVerificationView,
    AdminReviewIdentityView,
    ReviewIdentityView,
    IdentityVerificationStatusView,
)

urlpatterns = [
    path(
        "healthcheck/",
        Healthcheck.as_view(),
        name="healthcheck_auth_api",
    ),

    path(
        "identity/submit/",
        SubmitIdentityVerificationView.as_view(),
        name="submit_identity",
    ),

    path(
        "identity/status/",
        IdentityVerificationStatusView.as_view(),
        name="identity_verification_status",
    ),

    path(
        "admin/identity/<int:pk>/review/",
        AdminReviewIdentityView.as_view(),
        name="admin_review_identity",
    ),

    path(
        "identity/<int:pk>/",
        ReviewIdentityView.as_view(),
        name="review_identity",
    ),
]