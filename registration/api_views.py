from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from registration.serializers import UserMeSerializer


@permission_classes(permission_classes=[IsAuthenticated])
class UserMeAPIView(APIView):
    """
    Authorization: Token <your_token_here>

    Endpoint: GET /api/user/me/

    Path Parameters: None

    Request Body: None

    Responses:
        200 OK: {
            "id": 1,
            "username": "ash",
            "type_groups": [
                { "name": "fire" },
                { "name": "water" }
            ]
        } The authenticated user's profile plus
        the list of TypeGroup names they belong to.

        401 Unauthorized:
            Missing or invalid authentication token.
    """
    def get(self, request) -> Response:
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data, status=HTTP_200_OK)
