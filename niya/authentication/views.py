import os

from django.conf import settings
from django.core.mail import send_mail
from django.db import connections
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .constants import (
    EMAIL_SUBJECT_VERIFICATION,
    EMAIL_BODY_VERIFICATION,
    APP_NAME,
    EMAIL_SUBJECT_PASSWORD_RESET,
    EMAIL_BODY_PASSWORD_RESET,
    EMAIL_BODY_EMAIL_VERIFIED,
    EMAIL_SUBJECT_EMAIL_VERIFIED,
)
from .models import User
from .serializers import RegisterSerializer

__version__ = "1.0.0"
__name__ = "Authentication API"

from libs.errors import (
    USER_NOT_FOUND,
    ACCOUNT_BLOCKED,
    ACCOUNT_BAN,
    ACCOUNT_LOCKED,
    PASSWORD_FAILED,
)


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

    def get(self, request):
        """
        Perform a healthcheck on the application and database.

        This method attempts to establish a connection with the default
        configured database. If the connection succeeds, the API is
        considered healthy.

        :param request:
            Incoming HTTP GET request.
        :type request:
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
                "name": "Authentication API",
                "version": "1.0.0",
                "environment": "dev",
                "status": "Database connection established"
            }

        Error response example:
            {
                "name": "Authentication API",
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


# Views for authentication: Registration and Login
class RegisterAPIView(APIView):
    """
    User registration endpoint.

    This endpoint allows new users to create an account in the system.

    During the registration process:
        - User data is validated using RegisterSerializer
        - A new user account is created
        - JWT access and refresh tokens are generated
        - Tokens are returned immediately after successful registration

    Typical registration fields may include:
        - username
        - email
        - password
        - additional profile information

    Responses:
        - HTTP 201:
            User successfully registered.

        - HTTP 400:
            Validation failed or invalid input data.
    """

    def post(self, request):
        """
        Register a new user account and generate JWT tokens.

        This method validates the incoming registration data using
        RegisterSerializer. If validation succeeds:
            - A new user is created
            - JWT refresh and access tokens are generated
            - Authentication tokens are returned to the client

        :param request:
            Incoming HTTP POST request containing registration data.
        :type request:
            rest_framework.request.Request

        :return:
            JSON response containing:
                - success message
                - JWT access token
                - JWT refresh token
            or validation errors if registration fails.
        :rtype:
            rest_framework.response.Response

        Success response example:
            {
                "message": "User registered successfully",
                "access_token": "<jwt_access_token>",
                "refresh_token": "<jwt_refresh_token>"
            }

        Error response example:
            {
                "email": [
                    "This field must be unique."
                ]
            }
        """
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
    """
    Authentication endpoint used to log users into the application.

    This endpoint extends SimpleJWT's TokenObtainPairView in order to
    provide custom authentication behaviors such as:

    - Checking whether the username exists
    - Limiting failed login attempts
    - Temporarily locking accounts after multiple failures
    - Detecting banned or disabled accounts
    - Resetting failed login attempts after a successful login
    - Returning custom API error messages

    If authentication succeeds, a JWT access token and refresh token
    are returned to the client.

    Authentication flow:
        1. Verify that the username exists
        2. Check whether the account is temporarily locked
        3. Check whether the account is banned/inactive
        4. Authenticate the user credentials
        5. Reset failed attempts if login succeeds
        6. Increment failed attempts if authentication fails

    Returns:
        HTTP 200:
            JWT access and refresh tokens

        HTTP 401:
            Invalid credentials

        HTTP 403:
            Account banned or disabled

        HTTP 404:
            User not found

        HTTP 423:
            Account temporarily locked
    """

    def post(self, request, *args, **kwargs):
        """
        Authenticate a user and generate JWT tokens.

        This method overrides the default SimpleJWT login behavior
        to add advanced security checks and custom error handling.

        Security features implemented:
            - Username existence validation
            - Temporary account lock mechanism
            - Failed login attempt tracking
            - Ban/inactive account detection
            - Automatic reset of failed attempts on success

        Request body:
            {
                "username": "example_user",
                "password": "secure_password"
            }

        :param request:
            Incoming HTTP request containing authentication credentials.
        :type request:
            rest_framework.request.Request

        :param args:
            Additional positional arguments.
        :type args:
            tuple

        :param kwargs:
            Additional keyword arguments.
        :type kwargs:
            dict

        :return:
            A JSON response containing JWT tokens or an error message.
        :rtype:
            rest_framework.response.Response

        Possible responses:
            - 200 OK:
                Authentication successful.

            - 401 Unauthorized:
                Incorrect password or invalid credentials.

            - 403 Forbidden:
                User account is banned or disabled.

            - 404 Not Found:
                Username does not exist.

            - 423 Locked:
                Account temporarily locked after multiple failed attempts.
        """
        username = request.data.get("username")

        # Check if username exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"detail": USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if account is locked
        if user.is_account_locked():
            minutes_remaining = (
                int((user.locked_until - timezone.now()).total_seconds() / 60) + 1
            )
            return Response(
                {
                    "detail": ACCOUNT_BLOCKED.format(
                        minutes_remaining=minutes_remaining
                    ),
                    "locked_until": user.locked_until,
                },
                status=status.HTTP_423_LOCKED,
            )

        # Check if account is active
        if not user.is_active:
            if user.email_verified and getattr(user, "identity_verified", False):
                return Response(
                    {
                        "detail": ACCOUNT_BAN,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            pass

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
                        "detail": ACCOUNT_LOCKED,
                    },
                    status=status.HTTP_423_LOCKED,
                )

            return Response(
                {"detail": PASSWORD_FAILED.format(e=e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )


# Views for verification email
class SendVerificationCodeView(APIView):
    permission_classes = [IsAuthenticated]

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
