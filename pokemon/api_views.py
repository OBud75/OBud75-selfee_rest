from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import permission_classes
from rest_framework.generics import (
    CreateAPIView, DestroyAPIView, ListAPIView, RetrieveAPIView)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK, HTTP_201_CREATED,
    HTTP_304_NOT_MODIFIED, HTTP_400_BAD_REQUEST
)

from pokemon.models import Pokemon, PokemonType, TypeGroup
from pokemon.serializers import (
    PokemonWithTypesSerialier, UserTypeOutputSerializer)


@permission_classes(permission_classes=[IsAuthenticated])
class UserTypeCreateAPIView(CreateAPIView):
    """
    Authorization: Token <your_token_here>

    Endpoint: POST /api/group/{type_name}/add/

    Path Parameters:
        type_name (string): TypeGroup to add (case-insensitive).

    Request Body: None

    Responses:
        201 Created: {
            "id": 12, 
            "user": 1,
            "type_group": { "name": "fire" }
        } The newly created UserType record.

        304 Not Modified: {
            "id": 12, 
            "user": 1,
            "type_group": { "name": "fire" }
        } The UserType record already exists for the user.

        400 Bad Request: {
            "error": "Type 'invalid_type' invalid"
        } The provided type_name does not match any TypeGroup.

        401 Unauthorized:
            Missing or invalid authentication token.
    """
    def create(self, request, *args, **kwargs):
        type_name = kwargs.get("type_name", "").lower()

        try:
            type_group = TypeGroup.objects.get(name=type_name)
        except TypeGroup.DoesNotExist:
            return Response(
                data={"error": f"Type {type_name!r} invalid"},
                status=HTTP_400_BAD_REQUEST
            )

        user_type, created = type_group.usertype_set.get_or_create(
            user=request.user
        )

        if created:
            status = HTTP_201_CREATED
        else:
            status = HTTP_304_NOT_MODIFIED

        output = UserTypeOutputSerializer(user_type)
        return Response(data=output.data, status=status)


@permission_classes(permission_classes=[IsAuthenticated])
class UserTypeDestroyAPIView(DestroyAPIView):
    """
    Authorization: Token <your_token_here>

    Endpoint: DELETE /api/group/{type_name}/remove/

    Path Parameters:
        type_name (string): TypeGroup to remove (case-insensitive).

    Responses:
        200 OK: {
            "removed": "fire"
        } The type was successfully removed from the user's types.

        404 Not Found: {
            "detail": "Not found."
        } The specified type_name does not exist for the user.

        401 Unauthorized:
            Missing or invalid authentication token.
    """
    def get_object(self):
        return get_object_or_404(
            klass=self.request.user.usertype_set,
            type_group__name=self.kwargs["type_name"].lower())

    def delete(self, request, *args, **kwargs):
        type_group  = self.get_object()
        type_name = type_group.type_group.name
        self.perform_destroy(instance=type_group)
        return Response(data={"removed": type_name}, status=HTTP_200_OK)


@permission_classes(permission_classes=[IsAuthenticated])
class PokemonOfUserTypeListAPIView(ListAPIView):
    """
    Authorization: Token <your_token_here>

    Endpoint: GET /api/pokemon/

    Query Parameters: None

    Request Body: None

    Responses:
        200 OK: [
            { "number": 4, "name": "charmander", "types": ["fire"] },
            { "number": 7, "name": "squirtle",   "types": ["water"] }
        ] A list of Pokémon belonging to the user's types, with its types.

        401 Unauthorized:
            Missing or invalid authentication token.
    """
    serializer_class = PokemonWithTypesSerialier

    def get_queryset(self):
        return (
            Pokemon.objects.filter(
                pokemontype__type_group__usertype__user=self.request.user
            ).distinct().prefetch_related(
                Prefetch(
                    lookup="pokemontype_set",
                    queryset=PokemonType.objects.select_related("type_group"))
            )
        )


@permission_classes(permission_classes=[IsAuthenticated])
class PokemonOfUserTypeRetrieveAPIView(RetrieveAPIView):
    """
    Authorization: Token <your_token_here>

    Endpoint: GET /api/pokemon/{identifier}/

    Path Parameters:
        identifier (string or int): The Pokémon's
        number or name (case-insensitive).

    Request Body: None

    Responses:
        200 OK: {
            "number": 4,
            "name": "charmander",
            "types": ["fire"]
        } Pokémon with its types, if it belongs to the user's types.

        404 Not Found: {
            "detail": "Not found."
        } Pokémon does not exist or does not belong to the user's types.

        401 Unauthorized:
            Missing or invalid authentication token.
    """
    serializer_class = PokemonWithTypesSerialier

    def get_object(self):
        user = self.request.user
        identifier = self.kwargs["identifier"]
        if identifier.isdigit():
            lookup = Q(number=int(identifier))
        else:
            lookup = Q(name__iexact=identifier)

        return get_object_or_404(
            Pokemon.objects.filter(
                lookup, pokemontype__type_group__usertype__user=user
            ).distinct().prefetch_related(
                Prefetch(
                    lookup="pokemontype_set",
                    queryset=PokemonType.objects.select_related("type_group")
                )
            )
        )
