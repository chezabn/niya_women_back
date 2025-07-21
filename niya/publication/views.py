from datetime import datetime

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Publication
from .serializers import PublicationSerializer


class PublicationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        publications = Publication.objects.all()
        serializer = PublicationSerializer(publications, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PublicationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, created_at=datetime.now())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Publication.objects.get(pk=pk)
        except Publication.DoesNotExist:
            return None

    def get(self, request, pk):
        publication = self.get_object(pk)
        if not publication:
            return Response(
                {"message": "Publication not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = PublicationSerializer(publication)
        return Response(serializer.data)

    def patch(self, request, pk):
        publication = self.get_object(pk)
        if not publication:
            return Response(
                {"message": "Publication not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = PublicationSerializer(publication, data=request.data, patch=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        publication = self.get_object(pk)
        if not publication:
            return Response(
                {"message": "Publication not found"}, status=status.HTTP_404_NOT_FOUND
            )
        publication.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
