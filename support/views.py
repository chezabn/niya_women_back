from django.conf import settings
from django.core.mail import send_mail

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ReportProblemSerializer


class ReportProblemView(APIView):
    def post(self, request):
        serializer = ReportProblemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        subject = serializer.validated_data["subject"]
        message = serializer.validated_data["message"]

        try:
            send_mail(
                subject=f"[Niyya Women] {subject}",
                message=f"Email de l'utilisatrice : {email}\n\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=["contact@niyya-women.com"],
                fail_silently=False,
            )
        except Exception as e:
            return Response(
                {"detail": f"Impossible d'envoyer le message: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"detail": "Message envoyé."},
            status=status.HTTP_200_OK,
        )