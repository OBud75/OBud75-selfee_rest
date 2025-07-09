from django.urls import path

from pokemon.api_views import (
    PokemonOfUserTypeListAPIView,
    PokemonOfUserTypeRetrieveAPIView,
    UserTypeCreateAPIView,
    UserTypeDestroyAPIView
)


app_name = "pokemon"
urlpatterns = [
    path(
        route="group/<str:type_name>/add/",
        view=UserTypeCreateAPIView.as_view(),
        name="user-type-create"
    ),
    path(
        route="group/<str:type_name>/remove/",
        view=UserTypeDestroyAPIView.as_view(),
        name="user-type-destroy"
    ),
    path(
        route="pokemon/",
        view=PokemonOfUserTypeListAPIView.as_view(),
        name="of-user-type-list"),
    path(
        route="pokemon/<str:identifier>/",
        view=PokemonOfUserTypeRetrieveAPIView.as_view(),
        name="of-user-type-retrieve"
    )
]
