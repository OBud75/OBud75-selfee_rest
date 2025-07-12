from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_304_NOT_MODIFIED,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND
)
from rest_framework.test import APITestCase

from pokemon.models import (
    Pokemon, PokemonType, TypeGroup, UserType)


User = get_user_model()


class UserTypeAddTests(APITestCase):
    def setUp(self):
        self.view_name = "pokemon:user-type-create"
        self.user = User.objects.create_user(
            username="ash", password="pikachu"
        )
        token = Token.objects.create(user=self.user)
        self.auth_headers = {
            "HTTP_AUTHORIZATION": f"Token {token.key}"
        }

    def test_add_existing_type_returns_201(self):
        tg = TypeGroup.objects.create(name="fire")

        url = reverse(self.view_name, args=["fire"])
        resp = self.client.post(url, **self.auth_headers)

        self.assertEqual(resp.status_code, second=HTTP_201_CREATED)
        self.assertEqual(
            resp.data,
            {
                "user": {"username": "ash"},
                "type_group": {"name": "fire"}
            }
        )
        self.assertTrue(
            UserType.objects.filter(user=self.user, type_group=tg).exists()
        )

    def test_idempotent_add_returns_304(self):
        tg = TypeGroup.objects.create(name="grass")

        url = reverse(self.view_name, args=["grass"])
        resp1 = self.client.post(url, **self.auth_headers)
        resp2 = self.client.post(url, **self.auth_headers)

        self.assertEqual(resp1.status_code, HTTP_201_CREATED)
        self.assertEqual(resp2.status_code, HTTP_304_NOT_MODIFIED)
        self.assertEqual(
            UserType.objects.filter(user=self.user, type_group=tg).count(),
            1
        )

    def test_add_unknown_type_returns_400(self):
        url = reverse(self.view_name, args=["unknown"])
        resp = self.client.post(url, **self.auth_headers)

        self.assertEqual(resp.status_code, HTTP_400_BAD_REQUEST)
        self.assertIn("error", resp.data)

    def test_unauthenticated_returns_401(self):
        TypeGroup.objects.create(name="electric")
        url = reverse(self.view_name, args=["electric"])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, HTTP_401_UNAUTHORIZED)


class UserTypeDestroyTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="ash", password="pikachu")
        self.user2 = User.objects.create_user(username="misty", password="staryu")

        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

        self.tg = TypeGroup.objects.create(name="fire")
        self.ut2 = UserType.objects.create(user=self.user2, type_group=self.tg)

        self.url = lambda user, type_name: reverse(
            "pokemon:user-type-destroy", args=[type_name]
        )
        self.auth1 = {"HTTP_AUTHORIZATION": f"Token {self.token1.key}"}
        self.auth2 = {"HTTP_AUTHORIZATION": f"Token {self.token2.key}"}

    def test_delete_existing_relation_returns_200(self):
        UserType.objects.create(user=self.user1, type_group=self.tg)

        resp = self.client.delete(self.url(self.user1, "fire"), **self.auth1)
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(resp.data, {"removed": "fire"})
        self.assertFalse(
            UserType.objects.filter(user=self.user1, type_group=self.tg).exists()
        )

    def test_delete_nonexistent_relation_returns_404(self):
        resp = self.client.delete(self.url(self.user1, "fire"), **self.auth1)
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)

    def test_cannot_delete_other_user_relation(self):
        resp = self.client.delete(self.url(self.user1, "fire"), **self.auth1)
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)
        self.assertTrue(
            UserType.objects.filter(user=self.user2, type_group=self.tg).exists()
        )

    def test_unknown_type_returns_404(self):
        resp = self.client.delete(self.url(self.user1, "unknown"), **self.auth1)
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)

    def test_unauthenticated_returns_401(self):
        resp = self.client.delete(self.url(self.user1, "fire"))
        self.assertEqual(resp.status_code, HTTP_401_UNAUTHORIZED)


class PokemonOfUserTypeListTests(APITestCase):
    def setUp(self):
        self.url = reverse("pokemon:of-user-type-list")

        self.user = User.objects.create_user("ash", password="pikachu")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        fire  = TypeGroup.objects.create(name="fire")
        water = TypeGroup.objects.create(name="water")
        grass = TypeGroup.objects.create(name="grass")

        UserType.objects.create(user=self.user, type_group=fire)
        UserType.objects.create(user=self.user, type_group=water)

        char = Pokemon.objects.create(number=4, name="charmander")
        squ  = Pokemon.objects.create(number=7, name="squirtle")
        bul  = Pokemon.objects.create(number=1, name="bulbasaur")

        PokemonType.objects.create(pokemon=char, type_group=fire)
        PokemonType.objects.create(pokemon=squ,  type_group=water)
        PokemonType.objects.create(pokemon=bul,  type_group=grass)

    def test_list_only_allowed_pokemons(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, HTTP_200_OK)

        names = {p["name"] for p in resp.data}
        self.assertSetEqual(names, {"charmander", "squirtle"})

        for p in resp.data:
            self.assertIn("number", p)
            self.assertIn("name", p)
            self.assertIn("types", p)
            self.assertIsInstance(p["types"], list)

    def test_empty_if_no_types(self):
        user2 = User.objects.create_user("misty", password="staryu")
        token2 = Token.objects.create(user=user2)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token2.key}")

        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(resp.data, [])

    def test_unauthenticated_get_401(self):
        self.client.credentials()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, HTTP_401_UNAUTHORIZED)


class PokemonDetailTests(APITestCase):
    def setUp(self):
        self.url = lambda ident: reverse(
            "pokemon:of-user-type-retrieve", args=[ident]
        )

        self.user = User.objects.create_user(username="ash", password="pikachu")
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        fire  = TypeGroup.objects.create(name="fire")
        water = TypeGroup.objects.create(name="water")
        grass = TypeGroup.objects.create(name="grass")

        UserType.objects.create(user=self.user, type_group=fire)
        UserType.objects.create(user=self.user, type_group=water)

        self.char = Pokemon.objects.create(number=4, name="charmander")
        self.bulb = Pokemon.objects.create(number=1, name="bulbasaur")
        self.squir = Pokemon.objects.create(number=7, name="squirtle")

        PokemonType.objects.create(pokemon=self.char,  type_group=fire)
        PokemonType.objects.create(pokemon=self.bulb,  type_group=grass)
        PokemonType.objects.create(pokemon=self.squir, type_group=water)

    def test_retrieve_by_id_allowed(self):
        resp = self.client.get(self.url("4"))
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(resp.data["number"], 4)
        self.assertEqual(resp.data["name"], "charmander")
        self.assertListEqual(sorted(resp.data["types"]), ["fire"])

    def test_retrieve_by_name_allowed(self):
        resp = self.client.get(self.url("Squirtle"))  # case-insensitive
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(resp.data["number"], 7)
        self.assertEqual(resp.data["name"], "squirtle")
        self.assertListEqual(sorted(resp.data["types"]), ["water"])

    def test_cannot_access_unallowed_type(self):
        resp = self.client.get(self.url("1"))
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)

    def test_unknown_identifier_returns_404(self):
        resp1 = self.client.get(self.url("9999"))
        self.assertEqual(resp1.status_code, HTTP_404_NOT_FOUND)
        resp2 = self.client.get(self.url("missingno"))
        self.assertEqual(resp2.status_code, HTTP_404_NOT_FOUND)

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        resp = self.client.get(self.url("4"))
        self.assertEqual(resp.status_code, HTTP_401_UNAUTHORIZED)


class PokemonListWithFixturesTests(APITestCase):
    fixtures = [
        "users",
        "tokens",
        "typegroups",
        "usertypes",
        "pokemons",
        "pokemontypes"
    ]

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token testtoken")
        self.url = reverse(viewname="pokemon:of-user-type-list")

    def test_list_only_allowed_pokemons(self):
        with self.assertNumQueries(num=3):
            resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, HTTP_200_OK)

        names = {p["name"] for p in resp.data}
        self.assertEqual(names, {"charmander", "squirtle"})

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, HTTP_401_UNAUTHORIZED)


class PokemonDetailWithFixturesTests(APITestCase):
    fixtures = [
        "users",
        "tokens",
        "typegroups",
        "usertypes",
        "pokemons",
        "pokemontypes"
    ]

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token testtoken")
        self.detail_url = lambda ident: reverse(
            viewname="pokemon:of-user-type-retrieve", args=[ident])

    def test_retrieve_by_id_allowed(self):
        with self.assertNumQueries(num=3):
            resp = self.client.get(self.detail_url("4"))
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(resp.data["number"], 4)
        self.assertIn("fire", resp.data["types"])

    def test_retrieve_by_name_allowed(self):
        with self.assertNumQueries(num=3):
            resp = self.client.get(self.detail_url("Squirtle"))
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(resp.data["name"], "squirtle")
        self.assertIn("water", resp.data["types"])

    def test_unallowed_returns_404(self):
        with self.assertNumQueries(num=2):
            resp = self.client.get(self.detail_url("1"))
        self.assertEqual(resp.status_code, HTTP_404_NOT_FOUND)

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        resp = self.client.get(self.detail_url("4"))
        self.assertEqual(resp.status_code, HTTP_401_UNAUTHORIZED)
