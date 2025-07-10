from django.urls import path 
from flame.views import home

from . import views

app_name = "flame"

urlpatterns = [
    path("", views.home, name= "home")
]