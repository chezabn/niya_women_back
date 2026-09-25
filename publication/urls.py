from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, PublicationViewSet, PublicationLikeView

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
    path(
        "publications/<int:publication_id>/like/",
        PublicationLikeView.as_view(),
        name="publication-like",
    ),
]