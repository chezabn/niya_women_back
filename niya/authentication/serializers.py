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

    It is used for displaying user data in a secure, readable format.

    :Meta:
        model: :class:`User`
        fields: ``["id", "username", "email", "first_name", "last_name"]``
    """

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    This serializer handles the creation of a new user, including:
    - Validating that both password fields match
    - Hashing the password before saving
    - Returning only safe fields

    Fields:
        - ``username``: required, unique
        - ``email``: required, unique
        - ``password``: required, write-only
        - ``password2``: confirmation, write-only
        - ``first_name``: optional
        - ``last_name``: optional

    :Meta:
        model: :class:`User`
        fields:
            ``["username", "email", "password", "password2", "first_name", "last_name"]``

    :raises serializers.ValidationError:
        If the two passwords do not match.
    """

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

    def validate(self, data):
        """
        Validates that both passwords match.

        :param data: Input data from the request
        :type data: dict
        :raises serializers.ValidationError: If passwords do not match
        :return: Validated data
        :rtype: dict
        """
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        """
        Creates and returns a new user instance with hashed password.

        :param validated_data: Validated user data (password2 excluded)
        :type validated_data: dict
        :return: Newly created User object
        :rtype: User
        """
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
