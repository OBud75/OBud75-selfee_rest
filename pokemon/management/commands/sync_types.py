import requests

from django.apps import apps
from django.core.management.base import BaseCommand


TypeGroup = apps.get_model(app_label="pokemon", model_name="TypeGroup")


class Command(BaseCommand):
    help = "Synchronize all Pokémon types from PokeAPI into TypeGroup"
    POKEAPI_LIST_URL = "https://pokeapi.co/api/v2/type"

    def handle(self, *args, **options):
        resp = requests.get(self.POKEAPI_LIST_URL)
        if resp.status_code != 200:
            self.stderr.write(
                self.style.ERROR(
                    f"Error fetching PokeAPI types list: {resp.content}"
                )
            )
            return

        data = resp.json().get("results", [])
        total, created = 0, 0

        for item in data:
            name = item.get("name")

            if not name:
                continue

            total += 1
            _, is_new = TypeGroup.objects.get_or_create(
                name=name
            )

            if is_new:
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Sync finished: {total} types visited, {created} created."
        ))
