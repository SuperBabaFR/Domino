from datetime import datetime, UTC, timedelta
import random
from rest_framework import status
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from authentification.models import Session, Player, Game, Domino, Round, HandPlayer, Statut, Infosession


# Create your views here.
def verify_values(data, keys):
    for key in keys:
        value = data.get(key)
        if not value:
            return Response(dict(code=400, message=f'{key} manquant', data=None), status=status.HTTP_400_BAD_REQUEST)
    return None


def verify_objets(objets):
    for (key, obj) in objets.items():
        if not obj:
            return Response(dict(code=400, message=f'{key} inexistant', data=None), status=status.HTTP_400_BAD_REQUEST)
    return None


def domino_playable(domino, table_de_jeu, side):
    # si y'a qu'un domino
    if len(table_de_jeu) == 1:
        domino_one = Domino.objects.get(id=table_de_jeu[0]["id"])
        if (side == "left" and domino_one.left not in [domino.left, domino.right]) or (
                side == "right" and domino_one.right not in [domino.left, domino.right]):
            return False
        return dict(left=domino_one.left, right=domino_one.right)

    # Domino tout à gauche
    domino_left = Domino.objects.get(id=table_de_jeu[0]["id"])
    domino_left = dict(left=domino_left.left, right=domino_left.right, orientation=table_de_jeu[0]["orientation"])
    # Valeur de gauche disponible
    value_left = domino_left["left"] if domino_left["orientation"] == "normal" else domino_left["right"]

    # Domino tout à droite
    domino_right = Domino.objects.get(id=table_de_jeu[len(table_de_jeu) - 1]["id"])
    domino_right = dict(left=domino_right.left, right=domino_right.right,
                        orientation=table_de_jeu[len(table_de_jeu) - 1]["orientation"])
    # Valeur de droite disponible
    value_right = domino_right["right"] if domino_right["orientation"] == "normal" else domino_right["left"]

    # Domino bien jouable là ou il est placé
    if (side == "left" and value_left not in [domino.left, domino.right]) or (
            side == "right" and value_right not in [domino.left, domino.right]):
        return False
    return dict(left=value_left, right=value_right)


class CreateGame(APIView):
    permission_classes = []

    # permission_classes = [IsAuthenticatedWithJWT]

    def post(self, request):
        data_request = request.data
        data_return = dict(code=201, message="Nouvelle partie lancée", data=None)

        # Vérifie l'existance des keys dans le body
        keys = ["session_id", "player_id"]

        response = verify_values(data_request, keys)
        if response:
            return response

        # Objets
        session = Session.objects.filter(id=data_request.get("session_id")).first()
        player_hote = Player.objects.filter(id=data_request.get("player_id")).first()

        # Vérifie l'existence des objets
        objets_list = dict(session=session, player=player_hote)
        response = verify_objets(objets_list)
        if response:
            return response

        session = Session.objects.get(id=data_request.get("session_id"))
        player_hote = Player.objects.get(id=data_request.get("player_id"))  # Vérifié

        # Joueur pas hote de session
        if session.hote != player_hote:
            return Response(dict(code=404, message="joueur non hote de la session", data=None),
                            status=status.HTTP_404_NOT_FOUND)

        player_id_list = json.loads(session.order)  # Liste des joueurs

        # Vérifie qu'il y a au moins deux joueurs
        if len(player_id_list) < 2:
            return Response(dict(code=400, message="Il n'y a pas assez de joueurs dans la session", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        # Vérifie si une partie n'est pas déjà en cours
        if session.game_id:
            return Response(dict(code=400, message="Une partie est déjà en cours", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        # Si un joueur n'est pas prêt on crée pas de partie
        for player_id in player_id_list:
            info_player = Infosession.objects.get(session=session, player=Player.objects.get(id=player_id))

            if info_player.statut.name == "player.not_ready":
                return Response(dict(code=400, message="Tout les joueurs ne sont pas prêts", data=None),
                                status=status.HTTP_400_BAD_REQUEST)

        # Crée une partie
        game = Game.objects.create(session_id=session, statut=Statut.objects.get(id=1))  # NE PAS OUBLIER LE STATUT
        session.game_id = game
        session.save()

        # Crée un round
        round = Round.objects.create(game=game, session=session, table="[]", statut=Statut.objects.get(id=11))

        # Distribue 7 dominos pour chaque joueurs de la session
        domino_list = list(Domino.objects.all())  # Liste des dominos

        # Le joueur qui a le domino le plus fort
        strongest_domino_owner = dict(player_id=0, domino_id=0)

        # Pour chacun des joueurs dans la partie
        for player_id in player_id_list:
            dominoes = []
            # Choisis 7 Dominos dans la liste
            for i in range(0, 7):
                new_domino = random.choice(domino_list)
                domino_list.remove(new_domino)
                dominoes.append(new_domino.id)
                if strongest_domino_owner["domino_id"] <= new_domino.id:
                    strongest_domino_owner["domino_id"] = new_domino.id
                    strongest_domino_owner["player_id"] = player_id
            # Lie les dominos au joueur
            HandPlayer.objects.create(round=round, session=session, player=Player.objects.get(id=player_id),
                                      dominoes=dominoes)

        player_hote_dominoes_value = json.loads(
            HandPlayer.objects.get(session=session, round=round.id, player=player_hote).dominoes)

        player_hote_dominoes = []
        for domino_id in player_hote_dominoes_value:
            domino = Domino.objects.get(id=domino_id)
            domino_data = dict(id=domino.id, left=domino.left, right=domino.right)
            player_hote_dominoes.append(domino_data)

        # Première personne à jouer
        first_to_play = Player.objects.get(id=strongest_domino_owner.get("player_id"))
        # Ecrit dans la base a qui le tour
        round.player_turn(first_to_play)

        # Son temps de reflexion
        reflexion_time_param = session.reflexion_time
        player_time_end = datetime.now(UTC) + timedelta(seconds=reflexion_time_param)

        #     8. **notifie tout les joueurs sauf hote via le websocket de la session**
        #         1. **renvoie les dominos qui ont été distribués aux joueurs*
        # Un timer pour la fin du tour du joueur

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
        data_return = dict(code=200, message="Domino joué", data=None)

        # Vérifie l'existance des keys dans le body
        keys = ["session_id", "player_id", "round_id", "domino_id", "side"]

        response = verify_values(data_request, keys)
        if response:
            return response

        # Objets
        session = Session.objects.filter(id=data_request.get("session_id")).first()
        player = Player.objects.filter(id=data_request.get("player_id")).first()
        domino = Domino.objects.filter(id=data_request.get("domino_id")).first()
        round = Round.objects.filter(id=data_request.get("round_id")).first()

        # Valeurs
        side = data_request.get("side")

        # Vérifie l'existence des objets
        objets_list = dict(session=session, player=player, domino=domino, round=round)
        response = verify_objets(objets_list)
        if response:
            return response

        # Side bien renseigné
        if not (side == "left" or side == "right"):
            return Response(dict(code=400, message="side mal renseigné (left or right)", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        #  Vérifier que c’est bien son tour
        if player != round.player_turn:
            return Response(dict(code=400, message="Ce n'est pas ton tour", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        # Dominos du joueurs
        hand_player = HandPlayer.objects.filter(player=player, round=round, session=session).first()

        if not hand_player:
            return Response(dict(code=404, message="Le joueur n'a pas de données dans ce round", data=None),
                            status=status.HTTP_404_NOT_FOUND)

        player_dominoes: list = json.loads(hand_player.dominoes)
        #  Vérifie qu’il possède bien le domino
        if domino.id not in player_dominoes:
            return Response(dict(code=404, message="Le joueur ne possède pas le domino mentionné", data=None),
                            status=status.HTTP_404_NOT_FOUND)

        # Dominos sur la table
        table_de_jeu: list = json.loads(round.table)

        # Vérifie si le joueur qui commence joue bien son plus gros domino
        if len(table_de_jeu) == 0 and max(player_dominoes) != domino.id:
            return Response(dict(code=400, message="Le joueur doit jouer son plus gros domino", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        # Si ce n'est pas le premier domino à poser, on vérifie qu'il est bien jouable
        playable_values = domino_playable(domino, table_de_jeu, side)
        if len(table_de_jeu) > 0 and playable_values == False:
            return Response(dict(code=400, message="Domino non jouable", data=None),
                            status=status.HTTP_400_BAD_REQUEST)  # Domino non jouable

        #  - **Opérations réalisées :**

        # Détermine dans quelle orientation le domino sera joué
        orientation = "normal"
        if domino.left != domino.right:
            if (side == "left" and domino.left == playable_values["left"]) or (
                    side == "right" and domino.right == playable_values["right"]):
                orientation = "inverse"
        else:
            orientation = "double"

        domino_value = dict(id=domino.id, orientation=orientation)

        # Joue le domino sur la table
        if len(table_de_jeu) > 0 and side == "left":  # si c'est joué a gauche avec des dominos déjà sur la table
            table_de_jeu.insert(0, domino_value)
        else:  # si c'est joué a droite | si c'est le premier domino
            table_de_jeu.append(domino_value)
        # Met à jour la ligne
        round.table = json.dumps(table_de_jeu)

        # Soustrait le domino joué de sa main
        player_dominoes.remove(domino.id)
        hand_player.dominoes = json.dumps(player_dominoes)
        hand_player.save()

        # Met à jour qui doit jouer mtn
        order = json.loads(session.order)
        index_next_player = 0 if order.index(round.player_turn.id) + 1 >= len(order) else order.index(
            round.player_turn.id) + 1

        next_player = Player.objects.filter(id=order[index_next_player]).first()

        round.player_turn = next_player
        round.save()  # SAUVEGARDE LES INFOS POUR LE ROUND

        # Son temps de reflexion
        reflexion_time_param = session.reflexion_time
        player_time_end = datetime.now(UTC) + timedelta(seconds=reflexion_time_param)

        # Transmet au joueur les informations à jour
        data_return["data"] = dict(dominoes=player_dominoes,
                                   table=table_de_jeu,
                                   player_turn=round.player_turn.pseudo,
                                   player_time_end=player_time_end)

        return Response(data_return, status=status.HTTP_200_OK)

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
