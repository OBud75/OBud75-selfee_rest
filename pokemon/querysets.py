from django.db.models import Prefetch, Q
from django.db.models.query import QuerySet


class PokemonQuerySet(QuerySet):
    def by_identifier(self, identifier):
        if identifier.isdigit():
            lookup = Q(number=int(identifier))
        else:
            lookup = Q(name__iexact=identifier)
        return self.filter(lookup)

    def for_user(self, user):
        return self._for_user(user=user)._prefetch_user_types(user=user)

    def _for_user(self, user):
        """As a fist optimiation solution, we use JOIN + DISTINCT.
        If real performance issues arise, other optimiations should be
        considered, such as using IN (Subquery) or annotate + exists."""
        return self.filter(
            pokemontype__type_group__usertype__user=user
        ).distinct()

    def _prefetch_user_types(self, user):
        from pokemon.models import PokemonType

        user_types = (
            PokemonType.objects
            .select_related("type_group")
            .filter(type_group__usertype__user=user)
        )
        return self.prefetch_related(
            Prefetch(
                lookup="pokemontype_set",
                queryset=user_types,
                to_attr="user_filtered_types"
            )
        )
