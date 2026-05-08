import os

from django.db import connections
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

__version__ = "1.0.0"
__name__ = "Users API"


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

# Other
class UsersAPIView(APIView):
    def get(self, request):
        users = User.objects.filter(is_superuser=False)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class UserDetailAPIView(APIView):
    """
    Endpoint pour récupérer les détails d'une utilisatrice spécifique par son ID.

    Cette vue permet à tout utilisateur (connecté ou non) de consulter le profil public
    d'une autre utilisatrice. Si l'utilisateur consulte son propre profil, il pourrait
    potentiellement avoir accès à des champs supplémentaires (à gérer dans le sérialiseur).

    URL Pattern: /users/<int:pk>/
    Method: GET

    :param request: HTTP GET request
    :type request: rest_framework.request.Request
    :param pk: Primary Key (ID) de l'utilisatrice cible
    :type pk: int
    :return: JSON response contenant les données de l'utilisatrice ou une erreur 404
    :rtype: rest_framework.response.Response
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk: int) -> Response:
        """
        Récupère une instance utilisateur basée sur l'ID fourni.

        Utilise get_object_or_404 pour renvoyer automatiquement une 404 propre
        si l'utilisateur n'existe pas, évitant ainsi de révéler des informations
        sur la structure de la base de données.

        :param request: La requête HTTP.
        :param pk: L'identifiant unique de l'utilisatrice.
        :return: Les données sérialisées de l'utilisatrice.
        """
        # Récupération sécurisée de l'objet ou levée d'une exception 404
        user = get_object_or_404(User, pk=pk)

        serializer = UserSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)
