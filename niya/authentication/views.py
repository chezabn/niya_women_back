from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import connections

from .models import User
from .serializers import UserSerializer, RegisterSerializer

__version__ = "1.0.0"


class Healthcheck(APIView):
    """
    Healthcheck endpoint for the Authentication API.

    Performs a simple check to ensure the application and database connection are operational.

    :param request: HTTP GET request
    :type request: rest_framework.request.Request
    :return: JSON response with API name, version, and database connection status
    :rtype: rest_framework.response.Response
    """

    def get(self, request):
        db_conn = connections["default"]
        try:
            cursor = db_conn.cursor()
        except Exception as e:
            return Response(
                {
                    "name": "Authentication API",
                    "version": __version__,
                    "status": "Database connection failed",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {
                "name": "Authentication API",
                "version": __version__,
                "status": "Database connection established",
            },
            status=status.HTTP_200_OK,
        )


class MyUserAPIView(APIView):
    """
    Authenticated user endpoint to retrieve, update, or delete the user account.

    Requires a valid JWT token in the Authorization header.

    GET:
        Retrieve the authenticated user's information.

    PATCH:
        Partially update the authenticated user's information.

    DELETE:
        Delete the authenticated user's account.

    :param request: HTTP request (GET, PATCH, DELETE)
    :type request: rest_framework.request.Request
    :return: JSON response with user data or confirmation message
    :rtype: rest_framework.response.Response
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        user.delete()
        return Response(
            {"message": "Account deleted"}, status=status.HTTP_204_NO_CONTENT
        )


class RegisterAPIView(APIView):
    """
    User registration endpoint.

    Accepts user registration data and creates a new user account.
    Returns access and refresh JWT tokens on successful registration.

    POST:
        Register a new user.

    :param request: HTTP POST request with user registration data
    :type request: rest_framework.request.Request
    :return: JSON response with tokens or validation errors
    :rtype: rest_framework.response.Response
    """

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh.access_token)
            return Response(
                {
                    "message": "User registered successfully",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsersAPIView(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
