from django.shortcuts import render
from rest_framework.views import APIView

from authentification.views import IsAuthenticatedWithJWT


# Create your views here.

class CreateGameView(APIView):
    permission_classes = [] #IsAuthenticatedWithJWT]

    def post(self, request):

        # session Existante


        # Joueur Existant


        # Joueur Hôte de la session



        # Opérations

        # Créer partie

        # Créer round

        # Associer les joueurs
        pass