from django.urls import path
from .views import *

urlpatterns = [
    path("check/", UserCheckView.as_view(), name="user-check"),
    path("", UserCreateView.as_view(), name="user-create"),
    path("my/", ProfileView.as_view(), name="user-profile"),
]
