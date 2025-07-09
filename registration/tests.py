from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.status import (
    HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
)
from rest_framework.test import APITestCase

from pokemon.models import TypeGroup, UserType


User = get_user_model()


class LoginToken(APITestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "secretpass"
        self.user = get_user_model().objects.create_user(
            username=self.username,
            password=self.password
        )
        self.url = reverse("registration:login")

    def test_login_success_returns_token(self):
        data = {"username": self.username, "password": self.password}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIn("token", response.data)
        token = self.user.auth_token
        self.assertEqual(response.data["token"], token.key)

    def test_login_fail(self):
        data = {"username": self.username, "password": "wrongpass"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", response.data)


class LoginAuthentication(APITestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "secretpass"
        self.user = get_user_model().objects.create_user(
            username=self.username, password=self.password
        )
        self.url = reverse("registration:login")
        self.me_url = reverse("registration:user-me")

    def test_success_login_authenticate_user(self):
        data = {"username": self.username, "password": self.password}
        resp = self.client.post(self.url, data)
        token = resp.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        me_resp = self.client.get(self.me_url)
        self.assertTrue(me_resp.wsgi_request.user.is_authenticated)


class UserMeTests(APITestCase):
    def setUp(self):
        self.url = reverse("registration:user-me")
        self.user = User.objects.create_user(
            username="ash", password="pikachu"
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.tg1 = TypeGroup.objects.create(name="fire")
        self.tg2 = TypeGroup.objects.create(name="water")
        UserType.objects.create(user=self.user, type_group=self.tg1)
        UserType.objects.create(user=self.user, type_group=self.tg2)

    def test_get_user_me_with_groups(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, HTTP_200_OK)
        data = resp.data
        self.assertEqual(data["username"], "ash")
        self.assertIn("id", data)
        groups = data.get("type_groups", [])
        self.assertIsInstance(groups, list)
        names = {g["name"] for g in groups}
        self.assertSetEqual(names, {"fire", "water"})

    def test_get_user_me_no_groups(self):
        user2 = User.objects.create_user(username="misty", password="staryu")
        token2 = Token.objects.create(user=user2)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token2.key}")
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, HTTP_200_OK)
        data = resp.data
        self.assertEqual(data["username"], "misty")
        self.assertEqual(data.get("type_groups"), [])

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, HTTP_401_UNAUTHORIZED)
