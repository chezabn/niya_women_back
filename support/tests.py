from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.conf import settings
from django.urls import reverse
from rest_framework.test import APITestCase


class ReportProblemAPITests(APITestCase):
    def setUp(self):
        self.url = reverse("report-problem")
        self.payload = {
            "email": "member@example.com",
            "subject": "Aide",
            "message": "Je ne peux pas accéder à mon compte.",
        }

    @patch("support.views.send_mail")
    def test_report_sends_email_without_authentication(self, send_mail):
        response = self.client.post(self.url, self.payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"detail": "Message envoyé."})
        send_mail.assert_called_once_with(
            subject="[Niyya Women] Aide",
            message=(
                "Email de l'utilisatrice : member@example.com\n\n"
                "Je ne peux pas accéder à mon compte."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["contact@niyya-women.com"],
            fail_silently=False,
        )

    def test_report_rejects_invalid_or_missing_fields(self):
        for payload in (
            {**self.payload, "email": "not-an-email"},
            {key: value for key, value in self.payload.items() if key != "message"},
            {**self.payload, "subject": "s" * 201},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post(self.url, payload).status_code, 400)

    @patch("support.views.send_mail", side_effect=RuntimeError("mail unavailable"))
    def test_report_returns_server_error_when_email_fails(self, send_mail):
        response = self.client.post(self.url, self.payload)

        self.assertEqual(response.status_code, 500)
        self.assertIn("Impossible d'envoyer le message", response.data["detail"])
        send_mail.assert_called_once()
