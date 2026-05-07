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
    accept_cgu = serializers.BooleanField(required=True, write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password2",
            "first_name",
            "last_name",
            "accept_cgu",
        ]

    def validate(self, data):
        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError(
                "Ce nom d'utilisateur est déjà associée à un compte Niyya Women."
            )
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                "Cet adresse email est déjà associée à un compte Niyya Women."
            )
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        if not data["accept_cgu"]:
            raise serializers.ValidationError(
                "Les conditions générales d'utilisation doivent être acceptées"
            )
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
