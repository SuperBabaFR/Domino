"""
URL configuration for API_Domino project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from django.urls import path
import game
from game.views import CreateGame, PlaceDomino
from session.views import CreateSessionView, JoinSessionView

urlpatterns = [
    path('start', CreateGame.as_view(), name='start'),
    path('play', PlaceDomino.as_view(), name='play'),
    path('create', CreateSessionView.as_view(), name='create'),
    path('rejoindre', JoinSessionView.as_view(), name='rejoindre'),
]
