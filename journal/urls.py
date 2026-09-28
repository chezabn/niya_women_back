from django.urls import include
from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import JournalViewSet

router = DefaultRouter()

router.register(
    "journals",
    JournalViewSet,
    basename="journals",
)

urlpatterns = [
    path("", include(router.urls)),
]