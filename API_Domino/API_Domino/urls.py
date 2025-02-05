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
from authentification.views import *
from session.views import CreateSessionView, JoinSessionView, LeaveSessionView

urlpatterns = [
    # Authentification
    path('token/refresh', tokenRefreshView.as_view(), name='tokenRefresh'),
    path('signup', SignupView.as_view(), name='signup'),
    path('login', LoginView.as_view(), name='login'),
    # Session
    path('create', CreateSessionView.as_view(), name='create'),
    path('join', JoinSessionView.as_view(), name='join'),
    path('kill',LeaveSessionView.as_view(), name='kill'),
    # Partie
    path('start', CreateGame.as_view(), name='start'),
    path('play', PlaceDomino.as_view(), name='play'),

]
