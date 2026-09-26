from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from publication.pagination import FeedPagination
from users.serializers import UserPreviewSerializer

from .models import Follow, Friendship
from .serializers import (
    FollowStatusSerializer,
    FriendTargetSerializer,
    FriendshipStatusSerializer,
)

User = get_user_model()


def paginated_user_response(request, users, view):
    paginator = FeedPagination()
    users = users.select_related("profile")
    page = paginator.paginate_queryset(users, request, view=view)
    serializer = UserPreviewSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


def validate_friend_target(request, user_id):
    serializer = FriendTargetSerializer(
        data={"user_id": user_id}, context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data["user_id"]


def friendship_status_response(friendship, http_status=status.HTTP_200_OK):
    serializer = FriendshipStatusSerializer(
        instance={"status": friendship.status if friendship else None}
    )
    return Response(serializer.data, status=http_status)


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
        follow, created = Follow.objects.get_or_create(
            follower=request.user, followed=target_user
        )
        if created:
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
        users = User.objects.filter(followers__followed=target_user).order_by("id")
        return paginated_user_response(request, users, self)


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
        users = User.objects.filter(following__follower=target_user).order_by("id")
        return paginated_user_response(request, users, self)


class FriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        recipient = validate_friend_target(request, user_id)

        # An incoming request can be accepted by sending a request back.
        incoming = Friendship.objects.filter(
            requester=recipient, recipient=request.user
        ).first()
        if incoming:
            if incoming.status == Friendship.PENDING:
                incoming.status = Friendship.ACCEPTED
                incoming.save(update_fields=["status"])
                return friendship_status_response(incoming)
            return friendship_status_response(incoming)

        friendship, created = Friendship.objects.get_or_create(
            requester=request.user, recipient=recipient
        )
        return friendship_status_response(
            friendship,
            http_status=(
                status.HTTP_201_CREATED if created else status.HTTP_200_OK
            ),
        )

    def patch(self, request, user_id):
        requester = validate_friend_target(request, user_id)
        friendship = get_object_or_404(
            Friendship, requester=requester, recipient=request.user
        )
        if friendship.status != Friendship.ACCEPTED:
            friendship.status = Friendship.ACCEPTED
            friendship.save(update_fields=["status"])
        return friendship_status_response(friendship)

    def delete(self, request, user_id):
        other_user = validate_friend_target(request, user_id)
        Friendship.objects.filter(
            requester=request.user, recipient=other_user
        ).delete()
        Friendship.objects.filter(
            requester=other_user, recipient=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, user_id):
        other_user = validate_friend_target(request, user_id)
        friendship = Friendship.objects.filter(
            requester=request.user, recipient=other_user
        ).first() or Friendship.objects.filter(
            requester=other_user, recipient=request.user
        ).first()
        return friendship_status_response(friendship)


class FriendsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        friends = User.objects.filter(
            Q(
                friend_requests_received__requester=request.user,
                friend_requests_received__status=Friendship.ACCEPTED,
            )
            | Q(
                friend_requests_sent__recipient=request.user,
                friend_requests_sent__status=Friendship.ACCEPTED,
            )
        ).distinct().order_by("id")
        return paginated_user_response(request, friends, self)


class FriendRequestsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.filter(
            friend_requests_sent__recipient=request.user,
            friend_requests_sent__status=Friendship.PENDING,
        ).order_by("id")
        return paginated_user_response(request, users, self)
