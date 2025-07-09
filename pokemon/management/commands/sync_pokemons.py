import requests

from django.apps import apps
from django.core.management.base import BaseCommand


Pokemon = apps.get_model(app_label="pokemon", model_name="Pokemon")


class Command(BaseCommand):
    help = "Synchronize Pokémon entries from PokeAPI into Pokemon model"
    POKEAPI_LIST_URL   = "https://pokeapi.co/api/v2/pokemon?limit=100&offset={offset}"
    POKEAPI_DETAIL_URL = "https://pokeapi.co/api/v2/pokemon/{name}/"

    def handle(self, *args, **options):
        offset = 0
        created = updated = 0

        self.stdout.write("Starting sync_pokemon")

        while True:
            list_resp = requests.get(
                self.POKEAPI_LIST_URL.format(offset=offset)
            )
            if list_resp.status_code != 200:
                self.stderr.write("Error fetching Pokemon list")
                return

            data    = list_resp.json()
            results = data.get("results", [])

            if not results:
                break

            for entry in results:
                name = entry["name"]
                detail = requests.get(
                    self.POKEAPI_DETAIL_URL.format(name=name)
                )

                if detail.status_code != 200:
                    self.stderr.write(f"Error fetching {name} information")
                    continue

                info   = detail.json()
                number = info["id"]

                _, is_new = Pokemon.objects.update_or_create(
                    number=number,
                    defaults={"name": name, "number": number}
                )

                if is_new:
                    created += 1
                else:
                    updated += 1

                self.stdout.write(f"• {number}/{name}")

            if data.get("next"):
                offset += len(results)
            else:
                break

        self.stdout.write(self.style.SUCCESS(
            f"Pokemon sync: {created} created, {updated} updated."
        ))
