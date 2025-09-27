from django.contrib.auth import get_user_model
from .models import Company
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class CompanyAPITest(APITestCase):
    def setUp(self):
        self.company_url = reverse("company_api")

        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123",
            "password2": "TestPass123",
            "first_name": "Test",
            "last_name": "User",
        }

        self.user = User.objects.create_user(
            username="TestUser",
            email="usertest@example.com",
            password="password123",
        )

        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    def test_create_company_success(self):
        data = {
            "name": "Test Company",
            "description": "Company description",
        }
        response = self.client.post(
            self.company_url, data, format="json", **self.auth_headers
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Company.objects.count(), 1)
        self.assertEqual(Company.objects.first().name, data["name"])
        self.assertEqual(Company.objects.first().description, data["description"])

    def test_create_company_without_required_attribute(self):
        data = {
            "description": "Missing name",
        }
        response = self.client.post(
            self.company_url, data, format="json", **self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", response.json())

    def test_get_companies(self):
        Company.objects.create(user=self.user, name="Company1", description="desc")
        response = self.client.get(self.company_url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) >= 1)
        company = response.json()[0]
        self.assertEqual(company["name"], "Company1")
        self.assertEqual(company["description"], "desc")

    def test_get_company_with_name_or_description(self):
        user1 = User.objects.create_user(
            username="User1",
            email="user1@example.com",
            password="password123",
        )
        user2 = User.objects.create_user(
            username="User2",
            email="user2@example.com",
            password="password123",
        )
        Company.objects.create(user=self.user, name="New Company", description="Test description")
        Company.objects.create(user=user1, name="Saad Test", description="My first company")
        Company.objects.create(user=user2, name="An other", description="small description")

        response = self.client.get(self.company_url + "?search=Company", **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        companies = response.json()
        self.assertEqual(len(companies), 2)

    def test_get_company_by_id(self):
        company = Company.objects.create(
            user=self.user, name="Test Company", description="desc"
        )
        url = reverse("company_api_id", kwargs={"company_id": company.id})
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Test Company")
        self.assertEqual(response.json()["description"], "desc")

    def test_get_not_existing_company_by_name(self):
        Company.objects.create(user=self.user, name="Test Company", description="desc")
        url = reverse("company_api_id", kwargs={"company_id": 10000})
        response = self.client.get(url, **self.auth_headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "Company not found")

    def test_patch_companies(self):
        Company.objects.create(user=self.user, name="Company1", description="desc")
        data = {"name": "New Name", "description": "Change description"}
        response = self.client.patch(self.company_url, data, **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "New Name")
        self.assertEqual(response.json()["description"], "Change description")

    def test_patch_company_add_attribute(self):
        Company.objects.create(user=self.user, name="Company1", description="desc")
        data = {"email": "example@example.com"}
        response = self.client.patch(self.company_url, data, **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Company1")
        self.assertEqual(response.json()["description"], "desc")
        self.assertEqual(response.json()["email"], "example@example.com")

    def test_patch_company_remove_attribute(self):
        Company.objects.create(
            user=self.user,
            name="Company1",
            description="desc",
            email="example@example.com",
        )
        data = {"email": ""}
        response = self.client.patch(self.company_url, data, **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "")
        self.assertEqual(response.json()["name"], "Company1")
        self.assertEqual(response.json()["description"], "desc")

    def test_delete_company_without_confirm(self):
        Company.objects.create(user=self.user, name="Company test", description="desc")
        response = self.client.get(self.company_url, **self.auth_headers)
        self.assertTrue(len(response.json()) >= 1)
        response = self.client.delete(self.company_url, **self.auth_headers)
        self.assertEqual(response.status_code, 400)

    def test_delete_company_with_confirm(self):
        Company.objects.create(user=self.user, name="Company", description="desc")
        response = self.client.get(self.company_url, **self.auth_headers)
        self.assertTrue(len(response.json()) >= 1)
        confirmation = {"confirm": True}
        response = self.client.delete(
            self.company_url, confirmation, **self.auth_headers
        )
        self.assertEqual(response.status_code, 204)
