import time
from datetime import datetime, UTC, timedelta
from typing import Optional

from django.shortcuts import render
import random
from rest_framework import status
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from authentification.models import Session, Player, Game, Domino, Round, HandPlayer
from authentification.views import IsAuthenticatedWithJWT


# Create your views here.


def verify_entry(data, need_to_be_hote=False):
    # - Validation des entrées :
    session_id = data.get("session_id")
    player_id = data.get("player_id")

    print(data)

    # session_id et player_id renseignés
    if not session_id:
        return Response(dict(code=400, message="session_id manquant", data=None), status=status.HTTP_400_BAD_REQUEST)

    if not player_id:
        return Response(dict(code=400, message="player_id manquant", data=None), status=status.HTTP_400_BAD_REQUEST)

    player = Player.objects.filter(id=player_id).first()
    session = Session.objects.filter(id=session_id).first()

    # Session et Joueur existants
    if not session:
        return Response(dict(code=404, message="session inexistante", data=None), status=status.HTTP_404_NOT_FOUND)
    if not player:
        return Response(dict(code=404, message="joueur inexistant", data=None), status=status.HTTP_404_NOT_FOUND)
    # Joueur pas hote de session

    print(session.hote.pseudo)
    print(player.pseudo)

    if need_to_be_hote and session.hote != player:
        return Response(dict(code=404, message="joueur non hote de la session", data=None),
                status=status.HTTP_404_NOT_FOUND)

    return None


class CreateGame(APIView):
    permission_classes = []

    # permission_classes = [IsAuthenticatedWithJWT]

    def post(self, request):
        data_request = request.data
        data_return = dict(code=201, message="Nouvelle partie lancée", data=None)

        # Vérifier les premières entrées
        response = verify_entry(data_request, need_to_be_hote=True)
        if response:
            return response

        player_hote = Player.objects.get(id=data_request.get("player_id")) # Vérifié

        # Vérifie si une partie n'est pas déjà en cours
        session = Session.objects.get(id=data_request.get("session_id"))
        if session.game_id:
            return Response(dict(code=400, message="Une partie est déjà en cours", data=None), status=status.HTTP_400_BAD_REQUEST)

        return Response(data_return, status=status.HTTP_201_CREATED)

        # Crée une partie
        game = Game.objects.create(session) # NE PAS OUBLIER LE STATUT

        # Crée un round
        round = Round.objects.create(game, session, table="[]")

        # Distribue 7 dominos pour chaque joueurs de la session

        player_id_list = json.loads(session.order) # Liste des joueurs
        domino_list = Domino.objects.all() # Liste des dominos

        # Le joueur qui a le domino le plus fort
        strongest_domino_owner = dict(player_id=0, domino_id=0)

        # Pour chacun des joueurs dans la partie
        for player_id in player_id_list:
            dominoes = []
            # Choisis 7 Dominos dans la liste
            for i in range(0, 7):
                new_domino = random.choice(domino_list)
                domino_list.remove(new_domino)
                dominoes.append(new_domino)
                if strongest_domino_owner["domino_id"] <= new_domino.domino_id:
                    strongest_domino_owner["domino_id"] = new_domino.domino_id
                    strongest_domino_owner["player_id"] = player_id
            # Lie les dominos au joueur
            HandPlayer.objects.create(round, session, player=Player.objects.get(id=player_id), dominoes=dominoes)

        player_hote_dominoes_value = json.loads(HandPlayer.objects.get(session=session, round=round.id, player=player_hote).dominoes)

        player_hote_dominoes = []
        for domino_id in player_hote_dominoes_value:
            player_hote_dominoes.append(Domino.objects.get(id=domino_id))

        # Première personne à jouer
        first_to_play = Player.objects.get(id=strongest_domino_owner.get("player_id"))


        # Son temps de reflexion
        reflexion_time_param = session.reflexion_time
        player_time_end = datetime.now(UTC) + timedelta(seconds=reflexion_time_param)

        #     8. **notifie tout les joueurs sauf hote via le websocket de la session**
        #         1. **renvoie les dominos qui ont été distribués aux joueurs**


        # Transmet à l’hôte ses dominos
        data_return["data"] = dict(round_id=round.id,
                                   dominoes=player_hote_dominoes,
                                   player_turn=first_to_play.pseudo,
                                   player_time_end=player_time_end)

        return Response(data_return, status=status.HTTP_201_CREATED)


class PlaceDomino(APIView):
    permission_classes = []

    # permission_classes = [IsAuthenticatedWithJWT]

    def post(self, request):
        data_request = request.data
        data_return = dict(code=201, message="Domino joué", data=None)

        # Vérifie les entrées communes
        response = verify_entry(data_request)
        if response:
            return response

        # Objets validés
        session = Session.objects.get(id=data_request.get("session_id"))
        player = Player.objects.get(id=data_request.get("player_id"))

        #   Vérifie les entrées
        round_id = data_request.get("round_id")
        domino_id = data_request.get("domino_id")
        side = data_request.get("side")

        if not round_id:
            return Response(dict(code=400, message="round_id manquant", data=None), status=status.HTTP_400_BAD_REQUEST)

        if not domino_id:
            return Response(dict(code=400, message="domino_id manquant", data=None), status=status.HTTP_400_BAD_REQUEST)

        if not side:
            return Response(dict(code=400, message="side (cote) manquant", data=None), status=status.HTTP_400_BAD_REQUEST)

        #   Vérifie l'existence des objets
        domino = Domino.objects.get(id=domino_id)
        round = Round.objects.get(id=round_id)

        # Round existante
        if not round:
            return Response(dict(code=404, message="Round inexistant", data=None), status=status.HTTP_404_NOT_FOUND)

        # Domino existant
        if not domino:
            return Response(dict(code=404, message="Domino inexistant", data=None), status=status.HTTP_404_NOT_FOUND)

        if side != "left" or side != "right":
            return Response(dict(code=400, message="side mal renseigné (left or right)", data=None), status=status.HTTP_400_BAD_REQUEST)

        # Dominoes du joueurs
        player_dominoes = HandPlayer.objects.get(player, round, session).dominoes


        if not player_dominoes:
            return Response(dict(code=404, message="Le joueur n'a pas de données dans ce round", data=None), status=status.HTTP_404_NOT_FOUND)

        player_dominoes = json.loads(HandPlayer.objects.get(player, round, session).dominoes)
        #  Vérifie qu’il possède bien le domino
        if domino.id in player_dominoes:
            return Response(dict(code=404, message="Le joueur ne possède pas le domino mentionné", data=None),
                            status=status.HTTP_404_NOT_FOUND)

        #  Vérifier que c’est bien son tour
        order = json.loads(session.order)
        last_player = round.last_player

        index_next_player = 0 if order.index(last_player) + 1 >= len(order) else order.index(last_player) + 1
        # Prochain joueur qui doit jouer
        next_player = Player.objects.get(id=order.get(index_next_player))

        if player == last_player or player != next_player:
            return Response(dict(code=400, message="Ce n'est pas ton tour", data=None), status=status.HTTP_400_BAD_REQUEST)

        # Dominos sur la table
        table_de_jeu = json.loads(round.table_de_jeu)

        # Valeur de gauche disponible
        domino_left = Domino.objects.get(id=table_de_jeu[0]["id"])
        domino_left = dict(id=domino_left.id, left=domino_left.left, right=domino_left.right,
                           orientation=table_de_jeu[0]["orientation"])

        if domino_left["orientation"] == "normal":
            value_left = domino_left["left"]
        else:
            value_left = domino_left["right"]

        # Valeur de droite disponible
        domino_right = table_de_jeu[len(table_de_jeu) - 1]["id"]
        domino_right = dict(id=domino_right.id, left=domino_right.left, right=domino_right.right,
                            orientation=table_de_jeu[len(table_de_jeu) - 1]["orientation"])

        if domino_right["orientation"] == "normal":
            value_right = domino_left["right"]
        else:
            value_right = domino_left["left"]


        # Domino bien jouable là ou il est placé
        if (side == "left" and (domino.left != value_left or domino.right != value_left)) or (side == "right" and (domino.left != value_right or domino.right != value_right)): # Domino non jouable
            return Response(dict(code=400, message="Domino non jouable", data=None), status=status.HTTP_400_BAD_REQUEST)




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
