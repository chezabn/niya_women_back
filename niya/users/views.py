import os

from django.db import connections
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

__version__ = "1.0.0"
__name__ = "Users API"

from .serializers import UserSerializer, UserUpdateSerializer
from django.contrib.auth import get_user_model

from libs.errors import ACCOUNT_DEACTIVATED

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
        user.save()
        return Response(
            {"details": ACCOUNT_DEACTIVATED}, status=status.HTTP_204_NO_CONTENT
        )


# Other
class UsersAPIView(APIView):
    def get(self, request):
        users = User.objects.filter(is_superuser=False)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class UserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int) -> Response:
        # Récupération sécurisée de l'objet ou levée d'une exception 404
        user = get_object_or_404(User, pk=pk)

        serializer = UserSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)
