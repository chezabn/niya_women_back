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
    INVALID_CODE,
    MISSING_CODE,
    EMAIL_VERIFIED,
    SUCCESSFUL_EMAIL,
    MISSING_EMAIL,
    CODE_SENT,
    PASSWORD_CHANGED,
    MISSING_INFORMATION,
    PASSWORD_NOT_SECURED,
    USER_OR_CODE_NOT_MATCH,
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
                "detail": "User registered successfully",
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
                    "detail": "User registered successfully",
                    "access": access_token,
                    "refresh": refresh_token,
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
    """
    Endpoint used to send an email verification code to the authenticated user.

    This endpoint allows authenticated users to request a verification
    code in order to confirm ownership of their email address.

    Before sending the code, several validations are performed:
        - The user must be authenticated
        - The email must not already be verified
        - The user account must contain a valid email address

    If validation succeeds:
        - A temporary verification code is generated
        - The code expiration time is set
        - An email containing the verification code is sent

    Security notes:
        - The verification code is temporary
        - The code expiration is handled at model level
        - Only authenticated users can access this endpoint

    Responses:
        - HTTP 200:
            Verification code successfully sent.

        - HTTP 400:
            Email already verified,
            missing email,
            or email sending failure.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Generate and send an email verification code.

        This method generates a temporary verification code for the
        authenticated user and sends it to the user's email address.

        Validation flow:
            1. Check whether the email is already verified
            2. Check whether the user has an email address
            3. Generate a verification code
            4. Send the verification email

        :param request:
            Incoming HTTP POST request.
        :type request:
            rest_framework.request.Request

        :return:
            JSON response containing a success or error message.
        :rtype:
            rest_framework.response.Response

        Success response example:
            {
                "detail": "Verification code sent successfully."
            }

        Error response examples:
            {
                "detail": "Email already verified."
            }

            {
                "detail": "No email associated with this account."
            }
        """
        user = request.user
        if user.email_verified:
            return Response(
                {"detail": EMAIL_VERIFIED},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not user.email:
            return Response(
                {"detail": MISSING_EMAIL},
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
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"detail": CODE_SENT},
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    """
    Endpoint used to verify a user's email address.

    This endpoint allows authenticated users to validate their email
    address using the verification code previously sent to them.

    Verification flow:
        1. Ensure a verification code is provided
        2. Validate the code and expiration date
        3. Mark the email as verified
        4. Remove the verification code from the database
        5. Send a confirmation email

    Security notes:
        - Verification codes are temporary
        - Expired codes are rejected
        - Only authenticated users can verify their email

    Responses:
        - HTTP 200:
            Email successfully verified.

        - HTTP 400:
            Missing code,
            invalid code,
            expired code,
            or email sending failure.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Verify the authenticated user's email address.

        This method validates the verification code provided by the user.
        If the code is valid:
            - The email is marked as verified
            - Verification fields are cleared
            - A confirmation email is sent

        :param request:
            Incoming HTTP POST request containing the verification code.
        :type request:
            rest_framework.request.Request

        :return:
            JSON response containing a success or error message.
        :rtype:
            rest_framework.response.Response

        Request body example:
            {
                "code": "123456"
            }

        Success response example:
            {
                "detail": "Email verified successfully."
            }

        Error response examples:
            {
                "detail": "No verification code provided."
            }

            {
                "detail": "Invalid or expired verification code."
            }
        """
        user = request.user
        code = request.data.get("code")
        if not code:
            return Response(
                {"detail": MISSING_CODE}, status=status.HTTP_400_BAD_REQUEST
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
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": SUCCESSFUL_EMAIL}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": INVALID_CODE}, status=status.HTTP_400_BAD_REQUEST
            )


# Views for reset password
class RequestPasswordResetView(APIView):
    """
    Endpoint used to request a password reset code.

    This endpoint allows users to request a temporary password reset
    code by providing their email address.

    Security behavior:
        - The endpoint always returns the same success response,
          even if the email does not exist.
        - This prevents user enumeration attacks.

    Password reset flow:
        1. Validate that an email is provided
        2. Search for the associated user
        3. Generate a temporary reset code
        4. Send the reset code by email

    Notes:
        - The reset code expiration is handled at model level
        - This endpoint is publicly accessible
        - Email sending failures are intentionally hidden from clients

    Responses:
        - HTTP 200:
            Generic success response.

        - HTTP 400:
            Missing email address.
    """

    permission_classes = []  # Accessible sans authentification

    def post(self, request):
        """
        Generate and send a password reset code.

        This method validates the provided email address and,
        if a matching user exists, generates a temporary reset code
        and sends it by email.

        For security reasons:
            - The response is always identical whether the user exists or not
            - Internal email sending errors are not exposed

        :param request:
            Incoming HTTP POST request containing the user's email.
        :type request:
            rest_framework.request.Request

        :return:
            JSON response containing a generic success or validation message.
        :rtype:
            rest_framework.response.Response

        Request body example:
            {
                "email": "user@example.com"
            }

        Success response example:
            {
                "detail": "If this email exists, a reset code has been sent."
            }

        Error response example:
            {
                "detail": "Email is required."
            }
        """

        email = request.data.get("email")
        if not email:
            return Response(
                {"detail": MISSING_EMAIL}, status=status.HTTP_400_BAD_REQUEST
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
            {"detail": CODE_SENT},
            status=status.HTTP_200_OK,
        )


class ConfirmPasswordResetView(APIView):
    """
    Endpoint used to confirm a password reset operation.

    This endpoint validates:
        - The user's email
        - The reset code
        - The new password

    If validation succeeds:
        - The user's password is updated
        - Reset codes are cleared
        - Failed login attempts are reset

    Security features:
        - Reset codes are temporary
        - Expired codes are rejected
        - Password complexity is validated
        - Login lock state is reset after success

    Responses:
        - HTTP 200:
            Password successfully updated.

        - HTTP 400:
            Missing fields,
            invalid code,
            invalid user,
            or insecure password.
    """

    permission_classes = []  # Accessible sans authentification

    def post(self, request):
        """
        Validate a password reset code and update the password.

        This method verifies the provided reset code and updates
        the user's password if all validations succeed.

        Validation flow:
            1. Validate required fields
            2. Validate password complexity
            3. Check that the user exists
            4. Validate the reset code
            5. Update the password
            6. Clear reset-related fields
            7. Reset failed login attempts

        :param request:
            Incoming HTTP POST request containing:
                - email
                - reset code
                - new password
        :type request:
            rest_framework.request.Request

        :return:
            JSON response containing a success or error message.
        :rtype:
            rest_framework.response.Response

        Request body example:
            {
                "email": "user@example.com",
                "code": "123456",
                "new_password": "StrongPassword123!"
            }

        Success response example:
            {
                "detail": "Password changed successfully."
            }

        Error response examples:
            {
                "detail": "Missing required information."
            }

            {
                "detail": "Password is not secure enough."
            }

            {
                "detail": "Invalid or expired code."
            }
        """
        email = request.data.get("email")
        code = request.data.get("code")
        new_password = request.data.get("new_password")

        # Validation des champs obligatoires
        if not all([email, code, new_password]):
            return Response(
                {"detail": MISSING_INFORMATION},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vérification de la complexité du mot de passe (optionnel mais recommandé)
        if len(new_password) < 8:
            return Response(
                {"detail": PASSWORD_NOT_SECURED},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email=email).first()

        if not user:
            return Response(
                {"detail": USER_OR_CODE_NOT_MATCH},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vérification du code
        if not user.is_password_reset_code_valid(code):
            return Response(
                {"detail": INVALID_CODE},
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
            {"detail": PASSWORD_CHANGED},
            status=status.HTTP_200_OK,
        )
