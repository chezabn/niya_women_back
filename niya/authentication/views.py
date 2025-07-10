from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import connections
from authentication.serializers import UserSerializer, RegisterSerializer

__version__ = "1.0.0"


class Healthcheck(APIView):
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


class UserAPIView(APIView):
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
