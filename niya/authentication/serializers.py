from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving user profile information.

    :class:`UserSerializer` serializes basic user fields including:
    - ID
    - Username
    - Email
    - First name
    - Last name
    - Bio

    It is used for displaying user data in a secure, readable format.

    :Meta:
        model: :class:`User`
        fields: ``["id", "username", "email", "first_name", "last_name", "bio", "email_verified"]``
    """

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "bio",
            "email_verified",
        ]


class UserPreviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, label="Confirm Password")

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
        ]

    def validate_email(self, value):
        """
        Vérifie si l'email existe déjà dans la base de données.

        :param value: L'email soumis par l'utilisateur.
        :type value: str
        :raises serializers.ValidationError: Si l'email existe déjà.
        :return: L'email validé.
        :rtype: str
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Cet adresse email est déjà associée à un compte Niyya Women."
            )
        return value

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
