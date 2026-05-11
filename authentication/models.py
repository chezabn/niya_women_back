import random

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    accept_cgu = models.BooleanField(default=False)
    # Attribut pour la vérification d'identitié
    identity_verified = models.BooleanField(default=False)
    identity_requested = models.BooleanField(default=False)
    # Attribut pour la verification du compte
    email_verified = models.BooleanField(default=False)
    email_verification_code = models.CharField(max_length=6, null=True, blank=True)
    email_verification_code_expires = models.DateTimeField(null=True, blank=True)

    # Attribut pour la limitation des tentatives
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True, default=None)
    locked_until = models.DateTimeField(null=True, blank=True)
    require_password_reset = models.BooleanField(default=False)

    # Attribut pour la réinitialisation du mot de passe
    password_reset_code = models.CharField(max_length=6, null=True, blank=True)
    password_reset_code_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

    # Methode pour la vérification du compte
    def generate_verification_code(self):
        """Génère un code à 6 chiffres valable 15 minutes"""
        self.email_verification_code = f"{random.randint(100000, 999999)}"
        self.email_verification_code_expires = timezone.now() + timezone.timedelta(
            minutes=15
        )
        self.save(
            update_fields=["email_verification_code", "email_verification_code_expires"]
        )

    def is_verification_code_valid(self, code):
        """Vérifie si le code est correct et non expiré"""
        if not self.email_verification_code or not self.email_verification_code_expires:
            return False
        if timezone.now() > self.email_verification_code_expires:
            return False
        return self.email_verification_code == code

    # Méthodes pour la limitation des tentatives de connexion
    def add_failed_login_attempt(self):
        """Incrémente les tentatives et gère le blocage"""
        now = timezone.now()
        self.failed_login_attempts += 1
        self.last_failed_login = now

        if self.failed_login_attempts >= 10:
            self.require_password_reset = True
        elif self.failed_login_attempts >= 5:
            self.locked_until = now + timezone.timedelta(minutes=10)
        else:
            self.locked_until = None

        self.save(
            update_fields=[
                "failed_login_attempts",
                "last_failed_login",
                "locked_until",
                "require_password_reset",
            ]
        )

    def reset_login_attempts(self):
        """Réinitialise les tentatives après login réussi ou réinit mot de passe"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.require_password_reset = False
        self.last_failed_login = None
        self.save(
            update_fields=[
                "failed_login_attempts",
                "locked_until",
                "require_password_reset",
                "last_failed_login",
            ]
        )

    def is_account_locked(self):
        """Vérifie si le compte est temporairement bloqué"""
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False

    def is_password_reset_required(self):
        """Vérifie si une réinitialisation est obligatoire"""
        return self.require_password_reset

    # Méthodes pour la réinitialisation du mot de passe
    def generate_password_reset_code(self):
        """
        Génère un code de réinitialisation de mot de passe à 6 chiffres valable 30 minutes.
        """
        self.password_reset_code = f"{random.randint(100000, 999999)}"
        self.password_reset_code_expires = timezone.now() + timezone.timedelta(
            minutes=30
        )
        self.save(update_fields=["password_reset_code", "password_reset_code_expires"])

    def is_password_reset_code_valid(self, code):
        """
        Vérifie si le code de réinitialisation est correct et non expiré.

        :param code: Le code fourni par l'utilisatrice.
        :type code: str
        :return: True si valide, False sinon.
        :rtype: bool
        """
        if not self.password_reset_code or not self.password_reset_code_expires:
            return False
        if timezone.now() > self.password_reset_code_expires:
            # Optionnel : Nettoyer le code expiré
            self.password_reset_code = None
            self.password_reset_code_expires = None
            self.save(
                update_fields=["password_reset_code", "password_reset_code_expires"]
            )
            return False
        return self.password_reset_code == code
