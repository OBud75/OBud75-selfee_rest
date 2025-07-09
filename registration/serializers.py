from django.contrib.auth import get_user_model
from rest_framework.serializers import (
    CharField, IntegerField,
    ModelSerializer, Serializer,
    SerializerMethodField
)

from pokemon.models import TypeGroup


User = get_user_model()


class UserMeSerializer(Serializer):
    class TypeGroupSerializer(ModelSerializer):
        class Meta:
            model = TypeGroup
            fields = ["name"]

    id = IntegerField(read_only=True)
    username = CharField(read_only=True)
    type_groups = SerializerMethodField()

    def get_type_groups(self, user):
        user_types_qs = user.usertype_set.select_related("type_group")
        user_type_groups = [ut.type_group for ut in user_types_qs]
        serializer = self.TypeGroupSerializer(user_type_groups, many=True)
        return serializer.data

    def to_representation(self, user):
        return {
            "id": user.id,
            "username": user.username,
            "type_groups": self.get_type_groups(user=user)
        }
