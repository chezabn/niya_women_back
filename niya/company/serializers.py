from rest_framework import serializers
from .models import Company


class CompanySerializer(serializers.ModelSerializer):
    """
    Serializer for the Company model.

    This serializer handles the serialization and deserialization of the Company model
    and includes validation logic for creating a company.

    Fields:
        All fields of the Company model are included except the 'user' field, which is
        automatically set to the authenticated user during creation.

    Validation:
        - Ensures that a user cannot create more than one company.
        - Ensures that 'name' and 'description' are provided on POST requests.

    Methods:
        - validate(data):
            Performs custom validation before creating a Company instance.
        - create(validated_data):
            Associates the new Company instance with the currently authenticated user.

    :param data: The initial data passed to the serializer.
    :type data: dict
    :raises serializers.ValidationError: If the user already has a company, or if required fields are missing.
    :return: A validated Company instance ready for creation or update.
    :rtype: CompanySerializer
    """

    class Meta:
        model = Company
        fields = ["id", "name", "description", "address", "phone", "email", "website", "logo"]

    def validate(self, data):
        request = self.context.get("request")
        user = request.user

        if request.method == "POST":
            if Company.objects.filter(user=user).exists():
                raise serializers.ValidationError("User has already a company")
            if not data.get("name"):
                raise serializers.ValidationError({"name": "This field is required"})
            if not data.get("description"):
                raise serializers.ValidationError(
                    {"description": "This field is required"}
                )
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        return Company.objects.create(user=user, **validated_data)
