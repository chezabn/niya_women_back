from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import UserPreviewSerializer
from .models import Follow, Friendship

User = get_user_model()


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
        return Response({"is_following": is_following})


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
        followers = target_user.followers.all().select_related("follower")
        users = [f.follower for f in followers]
        serializer = UserPreviewSerializer(users, many=True)
        return Response(serializer.data)


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
        following = target_user.following.all().select_related("followed")
        users = [f.followed for f in following]
        serializer = UserPreviewSerializer(users, many=True)
        return Response(serializer.data)


class FriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        recipient = get_object_or_404(User, pk=user_id)
        if recipient == request.user:
            return Response({"error": "You cannot add yourself"}, status=400)

        # An incoming request can be accepted by sending a request back.
        incoming = Friendship.objects.filter(
            requester=recipient, recipient=request.user
        ).first()
        if incoming:
            if incoming.status == Friendship.PENDING:
                incoming.status = Friendship.ACCEPTED
                incoming.save(update_fields=["status"])
                return Response({"status": Friendship.ACCEPTED}, status=200)
            return Response({"status": incoming.status}, status=200)

        friendship, created = Friendship.objects.get_or_create(
            requester=request.user, recipient=recipient
        )
        return Response(
            {"status": friendship.status},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def patch(self, request, user_id):
        requester = get_object_or_404(User, pk=user_id)
        friendship = get_object_or_404(
            Friendship, requester=requester, recipient=request.user
        )
        if friendship.status != Friendship.ACCEPTED:
            friendship.status = Friendship.ACCEPTED
            friendship.save(update_fields=["status"])
        return Response({"status": friendship.status})

    def delete(self, request, user_id):
        other_user = get_object_or_404(User, pk=user_id)
        Friendship.objects.filter(
            requester=request.user, recipient=other_user
        ).delete()
        Friendship.objects.filter(
            requester=other_user, recipient=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, user_id):
        other_user = get_object_or_404(User, pk=user_id)
        friendship = Friendship.objects.filter(
            requester=request.user, recipient=other_user
        ).first() or Friendship.objects.filter(
            requester=other_user, recipient=request.user
        ).first()
        return Response({"status": friendship.status if friendship else None})


class FriendsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accepted = Friendship.objects.filter(status=Friendship.ACCEPTED).filter(
            Q(requester=request.user) | Q(recipient=request.user)
        ).select_related("requester", "recipient")
        friends = [
            row.recipient if row.requester_id == request.user.id else row.requester
            for row in accepted
        ]
        return Response(UserPreviewSerializer(friends, many=True).data)


class FriendRequestsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        requests = Friendship.objects.filter(
            recipient=request.user, status=Friendship.PENDING
        ).select_related("requester")
        return Response(
            UserPreviewSerializer([row.requester for row in requests], many=True).data
        )
