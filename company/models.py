from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class CompanyManager(models.Manager):
    """
    Custom manager for the Company model.

    Provides additional helper methods, including:

    - get_company_by_name(name): Fetches a company instance by its name.

    :param name: The name of the company to retrieve.
    :type name: str
    :return: A Company instance matching the given name.
    :rtype: Company
    :raises: Company.DoesNotExist if no company is found with the given name.
    """

    def get_company_by_name(self, name):
        return self.get(name=name)


class Company(models.Model):
    """
    Model representing a company owned by a user.

    Fields:
        - name (str): Name of the company (required).
        - description (str): Short description of the company (required).
        - address (str): Optional physical address.
        - phone (str): Optional phone number.
        - email (str): Optional email address.
        - website (str): Optional website URL.
        - logo (str): Optional path or URL to the company logo.
        - user (User): One-to-one relation to the Django user owning the company.

    Methods:
        - __str__: Returns the name of the company as its string representation.
    """

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    address = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    website = models.CharField(max_length=200, blank=True, null=True)
    logo = models.CharField(max_length=500, blank=True, null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
