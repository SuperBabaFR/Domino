from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentification.models import Session, Player, Game, Domino, Round
from authentification.views import IsAuthenticatedWithJWT


# Create your views here.


def verify_entry(data, need_to_be_hote=False):
    # - Validation des entrées :
    session_id = data.get("session_id")
    player_id = data.get("player_id")

    # session_id et player_id renseignés
    if not session_id:
        return Response(dict(code=400, message="session_id manquant", data=None), status=status.HTTP_400_BAD_REQUEST)

    if not player_id:
        return Response(dict(code=400, message="player_id manquant", data=None), status=status.HTTP_400_BAD_REQUEST)

    session = Session.objects.get(id=session_id)
    player = Player.objects.get(id=player_id)

    # Session et Joueur existants
    if not session:
        return Response(dict(code=404, message="session inexistante", data=None), status=status.HTTP_404_NOT_FOUND)
    if not player:
        return Response(dict(code=404, message="joueur inexistant", data=None), status=status.HTTP_404_NOT_FOUND)
    # Joueur pas hote de session
    if need_to_be_hote and session.hote != player:
        return Response(dict(code=404, message="joueur non hote de la session", data=None), status=status.HTTP_404_NOT_FOUND)





class CreateGame(APIView):
    permission_classes = []

    # permission_classes = [IsAuthenticatedWithJWT]

    def post(self, request):
        data_request = request.data
        data_return = dict(code=201, message="Nouvelle partie lancée", data=None)

        # Vérifier les premières entrées
        verify_entry(data_return, need_to_be_hote=True)


        # Joueur Hôte de la session

        # Opérations

        # Créer partie

        # Créer round

        # Associer les joueurs

        return Response(data_return, status=status.HTTP_201_CREATED)


class PlaceDomino(APIView):
    permission_classes = []

    # permission_classes = [IsAuthenticatedWithJWT]

    def post(self, request):
        data_request = request.data
        data_return = dict(code=201, message="Domino joué", data=None)

        verify_entry(data_return)
        # Objets validés
        session = Session.objects.get(id=data_request.get("session_id"))
        player = Player.objects.get(id=data_request.get("player_id"))

        #   Vérifie les entrées
        game_id = data_request.get("game_id")
        domino_id = data_request.get("domino_id")
        side = data_request.get("side")

        if not game_id:
            return Response(dict(code=400, message="game_id manquant", data=None), status=status.HTTP_400_BAD_REQUEST)

        if not domino_id:
            return Response(dict(code=400, message="domino_id manquant", data=None), status=status.HTTP_400_BAD_REQUEST)

        if not side:
            return Response(dict(code=400, message="domino_id manquant", data=None), status=status.HTTP_400_BAD_REQUEST)

        #   Vérifie l'existence des objets
        domino = Domino.objects.get(id=domino_id)
        game = Game.objects.get(id=game_id)

        # Partie existante
        if not game:
            return Response(dict(code=404, message="Partie inexistante", data=None), status=status.HTTP_404_NOT_FOUND)

        # Domino existant
        if not domino:
            return Response(dict(code=404, message="Domino inexistant", data=None), status=status.HTTP_404_NOT_FOUND)

        round = Round.objects.get(game=game, session=session, player=player)

        # Données de Manche pour le joueur existants
        if not round:
            return Response(dict(code=404, message="Pas de données de manche pour le joueur", data=None), status=status.HTTP_404_NOT_FOUND)

        #  Vérifie qu’il possède bien le domino
        if not round.dominos.contains(domino.id):
            return Response(dict(code=404, message="Le joueur ne possède pas le domino mentionné", data=None), status=status.HTTP_404_NOT_FOUND)

        #      - Vérifier que c’est bien son tour (on récupère l’ordre de passage et l’id du dernier joueur qui a joué)
        table_de_jeu = Gametable.objects.get(game=game, session=session, player=player)

        if not table_de_jeu:
            pass


        #      - Domino bien jouable là ou il est placé (ex : vérifie si y’a un 3 à gauche donc il peut jouer son 2/3)

        #  - **Opérations réalisées :**
        #      1. Ajoute l’id du domino au début ou à la fin du champ table en fonction de si il est joué à gauche ou a droite de la table
        #      2. Change idLastPlayer qui a joué par lui
        #      3. Regarde a qui le tour et si il est boudé
        #      4. Transmet au joueur le domino qu’il a joué

        return Response(data_return, status=status.HTTP_201_CREATED)

    #      5. **notifie tout les joueurs via le websocket de la session**
    #          1. du domino qui a été joué
    #              1. par qui
    #              2. ou (left or right)
    #          2. de la nouvelle personne qui doit jouer
    #              1. d’à quelle heure il verra son temps de reflexion s’écouler
    #      6. notifie la personne qui doit jouer
    #          1. du domino qui a été joué
    #              1. par qui
    #              2. ou
    #          2. des dominos qu’il peut jouer | si il est boudé aucun
    #          3. d’à quelle heure il verra son temps de réflexion s’écouler
