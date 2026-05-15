# urls.py
from django.urls import path

from . import views

urlpatterns = [
    # Follow system
    path("follow/<int:user_id>/", views.FollowView.as_view(), name="follow-user"),
    path(
        "followers/<int:user_id>/",
        views.FollowersListView.as_view(),
        name="user-followers",
    ),
    path(
        "following/<int:user_id>/",
        views.FollowingListView.as_view(),
        name="user-following",
    ),
]
