from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, PublicationViewSet


router = DefaultRouter()

router.register(
    "publications",
    PublicationViewSet,
    basename="publications",
)

router.register(
    "comments",
    CommentViewSet,
    basename="comments",
)


urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
]