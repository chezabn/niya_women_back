# urls.py
from django.urls import path

from . import views

urlpatterns = [
    path("friends/", views.FriendsListView.as_view(), name="user-friends"),
    path("friend-requests/", views.FriendRequestsListView.as_view(), name="friend-requests"),
    path("friends/<int:user_id>/", views.FriendRequestView.as_view(), name="friend-request"),
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
