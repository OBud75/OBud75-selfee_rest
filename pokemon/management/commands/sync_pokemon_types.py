import requests

from django.apps import apps
from django.core.management.base import BaseCommand


Pokemon = apps.get_model(app_label="pokemon", model_name="Pokemon")
TypeGroup = apps.get_model(app_label="pokemon", model_name="TypeGroup")


class Command(BaseCommand):
    help = "Synchronize Pokémon ↔ TypeGroup relations"
    POKEAPI_DETAIL_URL = "https://pokeapi.co/api/v2/pokemon/{name}/"

    def handle(self, *args, **options):
        created = 0
        deleted = 0
        self.stdout.write("Starting sync_pokemon_types")

        for poke in Pokemon.objects.all():
            resp = requests.get(
                self.POKEAPI_DETAIL_URL.format(name=poke.name)
            )
            if resp.status_code != 200:
                self.stderr.write(f"Error fetching details for {poke.name}")
                continue

            data = resp.json()
            desired_names = {t["type"]["name"] for t in data.get("types", [])}

            groups = TypeGroup.objects.filter(name__in=desired_names)
            desired_ids = {g.id for g in groups}

            poke_types = poke.pokemontype_set
            current_ids = set(poke_types.values_list("type_group_id", flat=True))

            to_delete = current_ids - desired_ids
            if to_delete:
                deleted_count, _ = poke_types.filter(type_group_id__in=to_delete).delete()
                deleted += deleted_count

            to_create = desired_ids - current_ids
            for tg_id in to_create:
                poke_types.create(type_group_id=tg_id)
                created += 1

            self.stdout.write(
                f"• {poke.id}/{poke.name} : +{len(to_create)}, -{len(to_delete)}"
            )

        self.stdout.write(self.style.SUCCESS(
            f"Relations sync complete: {created} created, {deleted} deleted."
        ))
