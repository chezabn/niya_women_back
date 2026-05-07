import os

from django.conf import settings
from django.core.mail import send_mail
from django.db import connections
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .constantes import (
    EMAIL_SUBJECT_VERIFICATION,
    EMAIL_BODY_VERIFICATION,
    APP_NAME,
    EMAIL_SUBJECT_PASSWORD_RESET,
    EMAIL_BODY_PASSWORD_RESET,
    EMAIL_BODY_EMAIL_VERIFIED,
    EMAIL_SUBJECT_EMAIL_VERIFIED,
)
from .models import User
from .permissions import IsActiveOrPendingVerification
from .serializers import UserSerializer, RegisterSerializer

__version__ = "1.0.0"
__name__ = "Authentication API"


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
                    "name": APP_NAME.format(service=__name__),
                    "version": __version__,
                    "environment": os.getenv("ENVIRONMENT", "dev"),
                    "status": "Database connection failed",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {
                "name": APP_NAME.format(service=__name__),
                "version": __version__,
                "environment": os.getenv("ENVIRONMENT", "dev"),
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


# Views for authentication: Registration and Login
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


class LoginAPIView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")

        # Check if username exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:  # TODO Erreur génériques
            return Response(
                {"message": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if account is locked
        if user.is_account_locked():
            minutes_remaining = (
                int((user.locked_until - timezone.now()).total_seconds() / 60) + 1
            )
            return Response(  # TODO Ajouter des erreurs génériques
                {
                    "detail": f"Compte temporairement bloqué pour sécurité. Réessayez dans {minutes_remaining} minutes.",
                    "locked_until": user.locked_until,
                },
                status=status.HTTP_423_LOCKED,
            )

        # Check if account is active
        if not user.is_active:
            if not user.email_verified:
                # TODO Ajouter une fonction qui permet de relancer la vérification de mail ?
                pass
            if not user.identity_verified:
                # TODO Ajouter une fonction qui permet de relancer la vérification de l'identité ?
                pass
            return Response(
                {
                    "detail": "Votre compte n'est pas encore activé. Veuillez vérifier vos emails ou attendre la validation administrative."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # If all is good, user can log in
        try:
            response = super().post(request, *args, **kwargs)
            if response.status_code == 200:
                user.reset_login_attempts()
            return response

        except Exception as e:
            # Check if account is locked with this attempt
            user.add_failed_login_attempt()
            if user.is_account_locked():
                return Response(
                    {
                        "detail": "Trop de tentatives échouées. Compte verrouillé pour 10 minutes."
                    },
                    status=status.HTTP_423_LOCKED,
                )

            return Response(
                {"detail": f"Nom d'utilisateur ou mot de passe incorrect: {e}"},
                status=status.HTTP_401_UNAUTHORIZED,
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


# Views for verification email
class SendVerificationCodeView(APIView):
    permission_classes = [IsActiveOrPendingVerification]

    def post(self, request):
        user = request.user
        if user.email_verified:
            return Response(
                {"message": "Email already verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.email:
            return Response(
                {"message": "No email associated with this account"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.generate_verification_code()
        try:
            send_mail(
                subject=EMAIL_SUBJECT_VERIFICATION,
                message=EMAIL_BODY_VERIFICATION.format(
                    code=user.email_verification_code
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"message": "Code envoyé vers votre adresse mail"},
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        code = request.data.get("code")
        if not code:
            return Response(
                {"message": "No code provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        if user.is_verification_code_valid(code):
            user.email_verified = True
            user.email_verification_code = None
            user.email_verification_code_expires = None
            user.save(
                update_fields=[
                    "email_verified",
                    "email_verification_code",
                    "email_verification_code_expires",
                ]
            )
            try:
                send_mail(
                    subject=EMAIL_SUBJECT_EMAIL_VERIFIED,
                    message=EMAIL_BODY_EMAIL_VERIFIED.format(
                        first_name=user.first_name
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {"message": "Email verified successfully"}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": "Code invalide"}, status=status.HTTP_400_BAD_REQUEST
            )


# Views for reset password
class RequestPasswordResetView(APIView):
    """
    Endpoint pour demander la réinitialisation du mot de passe.

    Accepte une adresse email, vérifie si l'utilisateur existe,
    génère un code de sécurité et l'envoie par email.

    NOTE DE SÉCURITÉ : Pour éviter l'énumération d'utilisateurs,
    cette API renvoie toujours un succès même si l'email n'existe pas,
    mais n'envoie l'email que si l'utilisateur existe.

    POST:
        {"email": "utilisateur@example.com"}

    :param request: HTTP POST request
    :type request: rest_framework.request.Request
    :return: Message de succès générique
    :rtype: rest_framework.response.Response
    """

    permission_classes = []  # Accessible sans authentification

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"message": "Email est requis"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Recherche de l'utilisateur
        user = User.objects.filter(email=email).first()

        if user:
            # Génération et envoi du code uniquement si l'utilisateur existe
            user.generate_password_reset_code()
            try:
                send_mail(
                    subject=EMAIL_SUBJECT_PASSWORD_RESET,
                    message=EMAIL_BODY_PASSWORD_RESET.format(
                        first_name=user.first_name or user.username,
                        code=user.password_reset_code,
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except Exception as e:
                # En cas d'erreur d'envoi, on loggue mais on ne révèle pas l'erreur technique au client
                # Dans un vrai prod, il faudrait logger cela proprement
                pass

                # Réponse générique pour ne pas révéler si l'email existe ou non
        return Response(
            {
                "message": "Si cet email est enregistré chez nous, vous recevrez un code de réinitialisation sous peu."
            },
            status=status.HTTP_200_OK,
        )


class ConfirmPasswordResetView(APIView):
    """
    Endpoint pour confirmer le code et définir le nouveau mot de passe.

    Vérifie le code reçu par email et met à jour le mot de passe si valide.

    POST:
        {
            "email": "utilisateur@example.com",
            "code": "123456",
            "new_password": "NouveauMotDePasseSecurise"
        }

    :param request: HTTP POST request
    :type request: rest_framework.request.Request
    :return: Succès ou erreurs de validation
    :rtype: rest_framework.response.Response
    """

    permission_classes = []  # Accessible sans authentification

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        new_password = request.data.get("new_password")

        # Validation des champs obligatoires
        if not all([email, code, new_password]):
            return Response(
                {"message": "Tous les champs (email, code, new_password) sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vérification de la complexité du mot de passe (optionnel mais recommandé)
        if len(new_password) < 8:
            return Response(
                {"message": "Le mot de passe doit contenir au moins 8 caractères."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email=email).first()

        if not user:
            return Response(
                {"message": "Utilisateur non trouvé ou code invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vérification du code
        if not user.is_password_reset_code_valid(code):
            return Response(
                {
                    "message": "Code invalide ou expiré. Veuillez recommencer la demande."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mise à jour du mot de passe
        user.set_password(new_password)
        user.password_reset_code = None
        user.password_reset_code_expires = None
        user.reset_login_attempts()  # Reset des tentatives de login échouées aussi
        user.save(
            update_fields=[
                "password",
                "password_reset_code",
                "password_reset_code_expires",
                "failed_login_attempts",
                "locked_until",
                "require_password_reset",
                "last_failed_login",
            ]
        )

        return Response(
            {
                "message": "Mot de passe réinitialisé avec succès. Vous pouvez maintenant vous connecter."
            },
            status=status.HTTP_200_OK,
        )
