from django.urls import path

from .views import (
    Healthcheck,
    MyUserAPIView,
    UserDetailAPIView,
    UsersAPIView,
    UserSearchAPIView,
    BlockedUsersAPIView,
    UserBlockAPIView,
    UserReportAPIView,
    AdminUserReportsAPIView,
)

urlpatterns = [
    path(
        "healthcheck/",
        Healthcheck.as_view(),
        name="healthcheck_auth_api",
    ),
    path(
        "me/",
        MyUserAPIView.as_view(),
        name="my_user",
    ),
    path(
        "all/",
        UsersAPIView.as_view(),
        name="users",
    ),
    path(
        "search/",
        UserSearchAPIView.as_view(),
        name="search_user",
    ),
    path(
        "<int:pk>/",
        UserDetailAPIView.as_view(),
        name="user_detail",
    ),
    path("block/", BlockedUsersAPIView.as_view(), name="blocked_users"),
    path("<int:user_id>/block/", UserBlockAPIView.as_view(), name="user_block"),
    path("reports/", UserReportAPIView.as_view(), name="user_report"),
    path("reports/all/", AdminUserReportsAPIView.as_view(), name="admin_user_reports"),
]
