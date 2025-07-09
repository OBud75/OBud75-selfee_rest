from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from registration.api_views import UserMeAPIView


app_name = 'registration'
urlpatterns = [
    path('login/', obtain_auth_token, name='login'),
    path('user/me/', UserMeAPIView.as_view(), name='user-me'),
]
