import os

from django.db import connections
from django.db.models.query_utils import Q
from rest_framework import status
from rest_framework import serializers, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.core.mail import send_mail
from niya import settings
from follower.models import Follow
from .models import UserBlock, UserReport

__version__ = "1.0.0"
__name__ = "Users API"

from .serializers import UserSerializer, UserUpdateSerializer, UserPreviewSerializer, UserReportSerializer, UserReportDetailSerializer, ExpoPushTokenSerializer
from django.contrib.auth import get_user_model

from libs.errors import ACCOUNT_DEACTIVATED
from libs.permissions import IsFullyAuthenticated
from publication.pagination import FeedPagination
from notifications.models import ExpoPushToken

User = get_user_model()


class Healthcheck(APIView):
    """
    Healthcheck endpoint for the Authentication API.

    This endpoint is used to verify that:
        - The API service is running correctly
        - The database connection is operational

    It performs a simple database connection test and returns
    information about the current application state.

    Typical use cases:
        - Monitoring
        - Load balancer health probes
        - Docker/Kubernetes health checks
        - CI/CD validation
        - Service uptime verification

    Responses:
        - HTTP 200:
            Application and database are operational.

        - HTTP 500:
            Database connection failed.
    """

    def get(self, _):
        """
        Perform a healthcheck on the application and database.

        This method attempts to establish a connection with the default
        configured database. If the connection succeeds, the API is
        considered healthy.

        :param _:
            Incoming HTTP GET request.
        :type Any:
            rest_framework.request.Request

        :return:
            JSON response containing:
                - application name
                - API version
                - current environment
                - database connection status
        :rtype:
            rest_framework.response.Response

        Success response example:
            {
                "name": "Users API",
                "version": "1.0.0",
                "environment": "dev",
                "status": "Database connection established"
            }

        Error response example:
            {
                "name": "Users API",
                "version": "1.0.0",
                "environment": "dev",
                "status": "Database connection failed"
            }
        """
        db_conn = connections["default"]
        try:
            _ = db_conn.cursor()
        except Exception as e:
            return Response(
                {
                    "name": __name__,
                    "version": __version__,
                    "environment": os.getenv("ENVIRONMENT", "dev"),
                    "status": "Database connection failed",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {
                "name": __name__,
                "version": __version__,
                "environment": os.getenv("ENVIRONMENT", "dev"),
                "status": "Database connection established",
            },
            status=status.HTTP_200_OK,
        )


class MyUserAPIView(APIView):
    """
    Retrieve, update or delete the authenticated user's account.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserUpdateSerializer(
            instance=request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                UserSerializer(request.user).data, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        user.is_active = False
        user.account_deactivated_by_user = True
        user.save()
        return Response(
            {"details": ACCOUNT_DEACTIVATED}, status=status.HTTP_204_NO_CONTENT
        )


class ExpoPushTokenAPIView(APIView):
    permission_classes = [IsFullyAuthenticated]

    def post(self, request):
        serializer = ExpoPushTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ExpoPushToken.objects.update_or_create(
            token=serializer.validated_data["push_token"],
            defaults={"user": request.user},
        )
        return Response({"detail": "Jeton push enregistré."}, status=status.HTTP_200_OK)


class UsersAPIView(ListAPIView):
    serializer_class = UserPreviewSerializer
    permission_classes = [IsFullyAuthenticated]

    def get_queryset(self):
        return visible_users(self.request.user).exclude(pk=self.request.user.pk)


class UserSearchAPIView(ListAPIView):
    """
    Search users by username or bia.
    """

    serializer_class = UserPreviewSerializer
    permission_classes = [IsFullyAuthenticated]

    def get_queryset(self):
        queryset = visible_users(self.request.user).exclude(pk=self.request.user.pk)
        query = self.request.query_params.get("q")
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) | Q(profile__bio__icontains=query)
            )
        return queryset


class UserDetailAPIView(RetrieveAPIView):
    """
    Retrieve the profile of a user by their ID.
    """

    serializer_class = UserSerializer
    permission_classes = [IsFullyAuthenticated]

    def get_queryset(self):
        return visible_users(self.request.user)


def visible_users(user):
    blocked_ids = UserBlock.objects.filter(
        Q(blocker=user) | Q(blocked=user)
    ).values_list("blocked_id", "blocker_id")
    ids = {pk for pair in blocked_ids for pk in pair}
    # Keep the authenticated user's own profile accessible even when they
    # participate in a block relationship.
    ids.discard(user.pk)
    return User.objects.filter(is_superuser=False, is_active=True).exclude(pk__in=ids)


class BlockedUsersAPIView(APIView):
    permission_classes = [IsFullyAuthenticated]

    def get(self, request):
        users = (
            User.objects.filter(
                blocked_by_users__blocker=request.user
            )
            .select_related("profile")
            .distinct()
        )

        paginator = FeedPagination()
        page = paginator.paginate_queryset(users, request, view=self)

        serializer = UserPreviewSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)

class UserBlockAPIView(APIView):
    permission_classes = [IsFullyAuthenticated]

    def post(self, request, user_id):
        target = get_object_or_404(User, pk=user_id, is_active=True, is_superuser=False)
        if target == request.user:
            return Response({"detail": "Vous ne pouvez pas bloquer votre propre compte."}, status=status.HTTP_400_BAD_REQUEST)
        _, created = UserBlock.objects.get_or_create(blocker=request.user, blocked=target)
        Follow.objects.filter(
            Q(follower=request.user, followed=target) | Q(follower=target, followed=request.user)
        ).delete()
        return Response({"blocked": True}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, user_id):
        UserBlock.objects.filter(blocker=request.user, blocked_id=user_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserReportAPIView(APIView):
    permission_classes = [IsFullyAuthenticated]

    def post(self, request):
        serializer = UserReportSerializer(
            data=request.data,
            context={"request": request},
        )

        if not serializer.is_valid():
            user_id = request.data.get("user_id")

            detail = next(
                (
                    str(error)
                    for errors in serializer.errors.values()
                    for error in errors
                ),
                "Impossible de transmettre le signalement.",
            )

            return Response(
                {
                    "id": user_id,
                    "detail": detail,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        target = User.objects.get(
            pk=serializer.validated_data["user_id"],
        )

        report = UserReport.objects.create(
            reporter=request.user,
            reported=target,
            reason=serializer.validated_data["reason"],
        )

        staff_emails = list(
            User.objects.filter(is_staff=True)
            .exclude(email="")
            .values_list("email", flat=True)
        )
        if staff_emails:
            send_mail(
                subject="Nouveau signalement sur Niya",
                message=(
                    f"Un nouveau signalement a été transmis par {request.user.username}.\n"
                    f"Compte signalé : {target.username}.\n"
                    f"Motif : {report.reason}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=staff_emails,
                fail_silently=True,
            )

        return Response(
            {
                "id": report.id,
                "detail": "Signalement transmis.",
            },
            status=status.HTTP_201_CREATED,
        )


class AdminUserReportsAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserReportDetailSerializer
    pagination_class = FeedPagination
    queryset = UserReport.objects.select_related("reporter", "reported").all()
