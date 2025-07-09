from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    ModelSerializer, SerializerMethodField)

from pokemon.models import Pokemon, TypeGroup, UserType


User = get_user_model()


class UserTypeOutputSerializer(ModelSerializer):
    class UserSerializer(ModelSerializer):
        class Meta:
            model = User
            fields = ["username"]

    class TypeGroupSerializer(ModelSerializer):
        class Meta:
            model = TypeGroup
            fields = ["name"]

    user = UserSerializer(read_only=True)
    type_group = TypeGroupSerializer(read_only=True)

    class Meta:
        model = UserType
        fields = ["user", "type_group"]


class PokemonWithTypesSerialier(ModelSerializer):
    types = SerializerMethodField()

    class Meta:
        model = Pokemon
        fields = ["number", "name", "types"]

    def get_types(self, obj):
        return [
            pokemon_type.type_group.name for
            pokemon_type in obj.pokemontype_set.all()]
