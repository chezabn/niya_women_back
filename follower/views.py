from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import UserBlock
from users.serializers import UserPreviewSerializer
from notifications.models import Notification
from notifications.services import create_notification
from publication.pagination import FeedPagination

from .models import Follow
from .serializers import FollowStatusSerializer

User = get_user_model()


def paginated_user_response(request, users, view):
    paginator = FeedPagination()
    users = users.select_related("profile")
    page = paginator.paginate_queryset(users, request, view=view)
    serializer = UserPreviewSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


class FollowView(APIView):
    """
    Handle follow/unfollow actions between users.

    This view allows authenticated users to:
    - Follow another user (POST)
    - Unfollow another user (DELETE)
    - Check if they are following a specific user (GET)

    The relationship is unidirectional (follower → followed).
    Self-following is explicitly prohibited.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """
        Follow a user.

        Creates a follow relationship from the authenticated user (follower)
        to the target user (followed).

        :param request: The HTTP request object containing user authentication.
        :type request: rest_framework.request.Request
        :param user_id: The ID of the user to follow.
        :type user_id: int
        :return: A response indicating success or that the user is already followed.
        :rtype: rest_framework.response.Response
        :statuscode 201: User successfully followed.
        :statuscode 200: User was already being followed.
        :statuscode 400: Attempt to follow oneself.
        :statuscode 404: Target user does not exist.
        """
        target_user = get_object_or_404(User, id=user_id)
        if request.user == target_user:
            return Response(
                {"error": "You cannot follow yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if UserBlock.objects.filter(
            Q(blocker=request.user, blocked=target_user)
            | Q(blocker=target_user, blocked=request.user)
        ).exists():
            return Response(
                {"error": "Cette action n'est pas disponible."},
                status=status.HTTP_403_FORBIDDEN,
            )
        follow, created = Follow.objects.get_or_create(
            follower=request.user, followed=target_user
        )
        if created:
            create_notification(
                recipient=target_user,
                actor=request.user,
                notification_type=Notification.Type.FOLLOW,
            )
            return Response(
                {"message": "Now following"}, status=status.HTTP_201_CREATED
            )
        else:
            return Response({"message": "Already following"}, status=status.HTTP_200_OK)

    def delete(self, request, user_id):
        """
        Unfollow a user.

        Removes the follow relationship between the authenticated user and the target user.

        :param request: The HTTP request object containing user authentication.
        :type request: rest_framework.request.Request
        :param user_id: The ID of the user to unfollow.
        :type user_id: int
        :return: A success message upon unfollowing.
        :rtype: rest_framework.response.Response
        :statuscode 204: Successfully unfollowed (or was not following).
        :statuscode 404: Target user does not exist.
        """
        target_user = get_object_or_404(User, id=user_id)
        Follow.objects.filter(follower=request.user, followed=target_user).delete()
        return Response({"message": "Unfollowed"}, status=status.HTTP_204_NO_CONTENT)

    def get(self, request, user_id):
        """
        Check if the authenticated user is following a given user.

        :param request: The HTTP request object containing user authentication.
        :type request: rest_framework.request.Request
        :param user_id: The ID of the user to check.
        :type user_id: int
        :return: A JSON object with a boolean field ``is_following``.
        :rtype: rest_framework.response.Response
        :statuscode 200: Always returns 200 with the follow status.
        :statuscode 404: Target user does not exist.
        """
        target_user = get_object_or_404(User, id=user_id)
        is_following = Follow.objects.filter(
            follower=request.user, followed=target_user
        ).exists()
        serializer = FollowStatusSerializer(instance={"is_following": is_following})
        return Response(serializer.data)


class FollowersListView(APIView):
    """
    Retrieve the list of followers for a given user.

    Returns a paginated (if implemented) or full list of users who follow the specified user.
    Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """
        Get all followers of a user.

        Fetches all users who follow the user identified by ``user_id``.

        :param request: The HTTP request object.
        :type request: rest_framework.request.Request
        :param user_id: The ID of the user whose followers are to be retrieved.
        :type user_id: int
        :return: A list of user previews (id, username, etc.).
        :rtype: rest_framework.response.Response
        :statuscode 200: Successfully retrieved followers.
        :statuscode 404: User with given ID does not exist.
        """
        target_user = get_object_or_404(User, id=user_id)
        # The listed user is the follower; ``following`` is the reverse
        # relation from User to Follow.follower.
        users = User.objects.filter(following__followed=target_user).order_by("id")
        return paginated_user_response(request, users, self)

    def delete(self, request, user_id):
        """Remove the specified account from the authenticated user's followers."""
        follower = get_object_or_404(User, id=user_id)
        Follow.objects.filter(follower=follower, followed=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowingListView(APIView):
    """
    Retrieve the list of users that a given user is following.

    Returns all users followed by the specified user.
    Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """
        Get all users followed by a given user.

        Fetches all users that the user identified by ``user_id`` is following.

        :param request: The HTTP request object.
        :type request: rest_framework.request.Request
        :param user_id: The ID of the user whose following list is to be retrieved.
        :type user_id: int
        :return: A list of user previews (id, username, etc.).
        :rtype: rest_framework.response.Response
        :statuscode 200: Successfully retrieved following list.
        :statuscode 404: User with given ID does not exist.
        """
        target_user = get_object_or_404(User, id=user_id)
        # The listed user is the followed account; ``followers`` is the
        # reverse relation from User to Follow.followed.
        users = User.objects.filter(followers__follower=target_user).order_by("id")
        return paginated_user_response(request, users, self)
