from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from .views import (
    # Healthcheck
    Healthcheck,
    # Verification identity
    SubmitIdentityVerificationView,
    AdminReviewIdentityView,
)

urlpatterns = [
    # Healthcheck
    path("healthcheck/", Healthcheck.as_view(), name="healthcheck_auth_api"),
    path('identity/submit/', SubmitIdentityVerificationView.as_view(), name='submit_identity'),
    path('admin/identity/<int:pk>/review/', AdminReviewIdentityView.as_view(), name='admin_review_identity'),
]
