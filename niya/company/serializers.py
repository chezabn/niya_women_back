from rest_framework import serializers
from .models import Company

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        exclude = ("user",)

    def validate(self, data):
        request = self.context.get("request")
        user = request.user

        if request.method == "POST":
            if Company.objects.filter(user=user).exists():
                raise serializers.ValidationError("User has already a company")
            if not data.get("name"):
                raise serializers.ValidationError({"name": "This field is required"})
            if not data.get("description"):
                raise serializers.ValidationError({"description": "This field is required"})
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        return Company.objects.create(user=user, **validated_data)