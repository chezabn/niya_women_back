from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CompanySerializer
from .models import Company


class CompanyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CompanySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        companies = Company.objects.all()
        serializer = CompanySerializer(companies, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """
        Partially update the company associated with the authenticated user.

        This method allows the authenticated user to update one or more fields of
        their company profile. The user is not allowed to update the `user` field.
        The request context is passed to the serializer to allow validation logic
        to access the current user.

        :param request: The HTTP request containing the update data.
        :type request: rest_framework.request.Request

        :return: A Response object containing the updated data or error messages.
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
    permission_classes = [IsAuthenticated]

    def get(self, request, name):
        try:
            company = Company.objects.get(name=name)
            serializer = CompanySerializer(company)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Company.DoesNotExist:
            return Response(
                {"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND
            )
