from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CommentViewSet, PublicationViewSet, PublicationLikeView,
                    PublicationReportView, AdminPublicationReportsView)

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
        path(
        "publications/<int:publication_id>/report/",
        PublicationReportView.as_view(),
        name="publication-report",
    ),
    path(
        "reports/all/",
        AdminPublicationReportsView.as_view(),
        name="admin_publication_reports",
    ),
]
