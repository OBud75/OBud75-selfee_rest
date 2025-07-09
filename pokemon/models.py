from django.conf import settings
from django.db.models import Index
from django.db.models.base import Model
from django.db.models.constraints import UniqueConstraint
from django.db.models.deletion import CASCADE
from django.db.models.fields import CharField, PositiveIntegerField
from django.db.models.fields.related import ForeignKey


class NamedModel(Model):
    name = CharField(max_length=255, unique=True)

    class Meta:
        abstract = True


class TypeGroup(NamedModel):
    pass


class Pokemon(NamedModel):
    number = PositiveIntegerField(unique=True)

    class Meta:
        indexes: list[Index] = [
            Index(fields=["number"], name="pokemon_number_idx")
        ]


class UserType(Model):
    user = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE
    )
    type_group = ForeignKey(
        "pokemon.TypeGroup",
        on_delete=CASCADE
    )

    class Meta:
        constraints: list[UniqueConstraint] = [
            UniqueConstraint(
                fields=["user", "type_group"],
                name="unique_user_type_group"
            )
        ]


class PokemonType(Model):
    pokemon = ForeignKey(
        "pokemon.Pokemon",
        on_delete=CASCADE
    )
    type_group = ForeignKey(
        "pokemon.TypeGroup",
        on_delete=CASCADE
    )

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["pokemon", "type_group"],
                name="unique_pokemon_type"
            )
        ]
