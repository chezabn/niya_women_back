import random
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    phone = models.IntegerField(null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, null=True, blank=True)
    email_verification_code_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

    def generate_verification_code(self):
        """Génère un code à 6 chiffres valable 15 minutes"""
        self.email_verification_code = f"{random.randint(100000, 999999)}"
        self.email_verification_code_expires = timezone.now() + timezone.timedelta(minutes=15)
        self.save(update_fields=["email_verification_code", "email_verification_code_expires"])

    def is_verification_code_valid(self, code):
        """Vérifie si le code est correct et non expiré"""
        if not self.email_verification_code or not self.email_verification_code_expires:
            return False
        if timezone.now() > self.email_verification_code_expires:
            return False
        return self.email_verification_code == code