from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CompanySerializer
from .models import Company


class CompanyView(APIView):
    """
    API endpoint for managing companies.

    Provides methods to create, retrieve, update, and delete a company
    associated with the authenticated user.

    :permission_classes: Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Create a new company associated with the authenticated user.

        Validates the input data using CompanySerializer. If valid, saves
        the new company and returns the serialized data with HTTP 201 status.
        Otherwise, returns validation errors with HTTP 400 status.

        :param request: HTTP request containing company data.
        :type request: rest_framework.request.Request

        :return: Serialized company data or validation errors.
        :rtype: rest_framework.response.Response
        """
        serializer = CompanySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        Retrieve a list of all companies.

        Serializes and returns all companies in the database with HTTP 200 status.

        :param request: HTTP request.
        :type request: rest_framework.request.Request

        :return: List of serialized companies.
        :rtype: rest_framework.response.Response
        """
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """
        Partially update the company associated with the authenticated user.

        Allows updating one or more fields except the 'user' field.
        Returns the updated company data if successful,
        or error details with HTTP 400 status if validation fails.
        Returns HTTP 404 if the company does not exist.

        :param request: HTTP request containing fields to update.
        :type request: rest_framework.request.Request

        :return: Updated serialized company data or error messages.
        :rtype: rest_framework.response.Response
        """
        try:
            company = Company.objects.get(user=request.user)
        except Company.DoesNotExist:
            return Response(
                {"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = CompanySerializer(
            company, data=request.data, partial=True, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        Delete the company associated with the authenticated user.

        Requires confirmation via 'confirm' field in the request data.
        Returns HTTP 204 status on success,
        HTTP 400 if confirmation is missing,
        or HTTP 404 if the company does not exist.

        :param request: HTTP request possibly containing 'confirm'.
        :type request: rest_framework.request.Request

        :return: Success message or error details.
        :rtype: rest_framework.response.Response
        """
        try:
            company = Company.objects.get(user=request.user)
        except Company.DoesNotExist:
            return Response(
                {"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND
            )

        confirmation = request.data.get("confirm", False)
        if not confirmation:
            return Response(
                {"error": "Confirm required"}, status=status.HTTP_400_BAD_REQUEST
            )

        company.delete()
        return Response(
            {"message": "Company deleted"}, status=status.HTTP_204_NO_CONTENT
        )


class CompanyNameView(APIView):
    """
    API endpoint to retrieve a company by its name.
    """

    def get(self, request, name):
        """
        Retrieve a company by its name.

        :param request: HTTP request.
        :type request: rest_framework.request.Request
        :param name: Name of the company to retrieve.
        :type name: str

        :return: Serialized company data or error message.
        :rtype: rest_framework.response.Response
        """
        try:
            company = Company.objects.get(name=name)
            serializer = CompanySerializer(company)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Company.DoesNotExist:
            return Response(
                {"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND
            )
