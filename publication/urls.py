from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PublicationViewSet

router = DefaultRouter()

router.register(
    "publications",
    PublicationViewSet,
    basename="publications",
)

urlpatterns = [
    path("", include(router.urls)),
]
