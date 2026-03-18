from django.urls import path

from .views import (
    PublicationDetailAPIView,
    PublicationAPIView,
    PublicationLikeAPIView,
    PublicationCommentAPIView,
    PublicationCommentDetailAPIView,
)

urlpatterns = [
    # Logique d'une publication
    path("publications/", PublicationAPIView.as_view(), name="publication"),
    path(
        "publications/<int:pk>/",
        PublicationDetailAPIView.as_view(),
        name="publication-detail",
    ),
    # Url pour like une publication
    path(
        "publications/<int:publication_id>/likes/",
        PublicationLikeAPIView.as_view(),
        name="publication-like",
    ),
    # Url pour voir tous les commentaires d'une publication
    path(
        "publications/<int:publication_id>/comments/",
        PublicationCommentAPIView.as_view(),
        name="publication-comment",
    ),
    # Url pour consulter un commentaire d'une publication
    path(
        "comments/<int:comment_id>/",
        PublicationCommentDetailAPIView.as_view(),
        name="comment-detail",
    ),
]
