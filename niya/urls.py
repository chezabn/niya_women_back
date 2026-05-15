from django.contrib import admin
from django.urls import include
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.urls")),
    path("api/identification/", include("identity_verification.urls")),
    path("api/users/", include("users.urls")),
    path("api/company/", include("company.urls")),
    path("api/publications/", include("publication.urls")),
    path("api/followers/", include("follower.urls")),
]
