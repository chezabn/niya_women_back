from datetime import datetime

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.serializers import UserPreviewSerializer
from .models import Publication, Comment
from .serializers import PublicationSerializer, CommentSerializer


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

    def get_object(self, request, pk):
        try:
            return Publication.objects.get(pk=pk)
        except Publication.DoesNotExist:
            return None

    def get(self, request, pk):
        publication = self.get_object(request, pk)
        if not publication:
            return Response(
                {"message": "Publication not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = PublicationSerializer(publication)
        return Response(serializer.data)

    def patch(self, request, pk):
        publication = self.get_object(request, pk)
        if not publication:
            return Response(
                {"message": "Publication not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if publication.author != request.user:
            return Response(
                {"message": "You are not the author of this publication"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = PublicationSerializer(publication, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        publication = self.get_object(request, pk)
        if not publication:
            return Response(
                {"message": "Publication not found"}, status=status.HTTP_404_NOT_FOUND
            )
        if publication.author != request.user:
            return Response(
                {"message": "You are not the author of this publication"},
                status=status.HTTP_403_FORBIDDEN,
            )
        publication.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublicationLikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, publication_id):
        """Ajouter un like à une publication"""
        publication = get_object_or_404(Publication, pk=publication_id)
        user = request.user

        if user in publication.likes.all():
            return Response(
                {"detail": "You are already liked"}, status=status.HTTP_200_OK
            )

        publication.likes.add(user)
        return Response({"detail": "publication liked"}, status=status.HTTP_200_OK)

    def get(self, request, publication_id):
        """Lister tous les utilisateurs ayant liké la publication"""
        publication = get_object_or_404(Publication, pk=publication_id)
        users = publication.likes.all()
        serializer = UserPreviewSerializer(users, many=True)
        return Response({"users": serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, publication_id):
        """Enelever son like de la publication"""
        publication = get_object_or_404(Publication, pk=publication_id)
        user = request.user
        if user not in publication.likes.all():
            return Response(
                {"detail": "You are not liked"}, status=status.HTTP_404_NOT_FOUND
            )
        publication.likes.remove(user)
        return Response({"detail": "Publication unliked"}, status=status.HTTP_200_OK)


class PublicationCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, publication_id):
        """Ajouter un commentaire à une publication"""
        publication = get_object_or_404(Publication, pk=publication_id)
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                author=request.user, created_at=datetime.now(), publication=publication
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, publication_id):
        """Voir la liste de tous les commentaires d'une publicaiton"""
        publication = get_object_or_404(Publication, pk=publication_id)
        comments = publication.comments.filter(publication=publication).order_by(
            "-created_at"
        )
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


class PublicationCommentDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_comment(self, request, publication_id):
        return get_object_or_404(Comment, pk=publication_id)

    def patch(self, request, comment_id):
        """Modifier un commentaire d'une publication"""
        comment = self.get_comment(request, comment_id)
        if comment.author != request.user:
            return Response(
                {"message": "You are not the author of this comment"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, comment_id):
        """Supprimer un commentaire d'une publication"""
        comment = self.get_comment(request, comment_id)
        user = request.user
        if comment.author != user and user != comment.publication.author:
            return Response(
                {"message": "You are not the author of this comment"},
                status=status.HTTP_403_FORBIDDEN,
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
