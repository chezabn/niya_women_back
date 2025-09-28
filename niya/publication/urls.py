from django.urls import path
from .views import PublicationDetailAPIView, PublicationAPIView

urlpatterns = [
    path("publications/", PublicationAPIView.as_view(), name="publication"),
    path(
        "publications/<int:pk>/",
        PublicationDetailAPIView.as_view(),
        name="publication-detail",
    ),
]
