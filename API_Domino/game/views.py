from datetime import datetime, UTC, timedelta
import random

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from authentification.models import Session, Player, Game, Domino, Round, HandPlayer, Infosession
from tasks import player_pass, play_domino


# Create your views here.
def notify_websocket(cible, id, data, type="send_session_updates"):
    print(f"notify_websocket : {cible}_{id}, {data}")
    channel_layer = get_channel_layer()  # Récupérer le Channel Layer de Django Channels
    async_to_sync(channel_layer.group_send)(
        f"{cible}_{id}",  # Nom du groupe WebSocket
        {
            "type": type,
            "data": data
        }
    )


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


def get_full_domino_player(dominos, domino_list_ref):
    player_dominoes_value = json.loads(dominos)

    player_dominoes = []
    for domino_id in player_dominoes_value:
        domino = domino_list_ref[domino_id - 1]
        player_dominoes.append(dict(id=domino.id, left=domino.left, right=domino.right))

    return player_dominoes


def domino_playable(domino, table_de_jeu, side, domino_list=None):
    # Si y'a aucun domino
    if len(table_de_jeu) == 0:
        return dict(left=domino.left, right=domino.right)

    # si y'a qu'un domino
    if len(table_de_jeu) == 1:
        if not domino_list:
            domino_one = Domino.objects.get(id=table_de_jeu[0]["id"])
        else:
            domino_one = domino_list[table_de_jeu[0]["id"] - 1]

        if (side == "left" and domino_one.left not in [domino.left, domino.right]) or (
                side == "right" and domino_one.right not in [domino.left, domino.right]):
            return False
        return dict(left=domino_one.left, right=domino_one.right)

    # Charge les dominos avant
    if not domino_list:
        domino_left = Domino.objects.get(id=table_de_jeu[0]["id"])
        domino_right = Domino.objects.get(id=table_de_jeu[len(table_de_jeu) - 1]["id"])
    else:
        domino_left = domino_list[table_de_jeu[0]["id"] - 1]
        domino_right = domino_list[table_de_jeu[len(table_de_jeu) - 1]["id"] - 1]

    # Domino tout à gauche
    domino_left = dict(left=domino_left.left, right=domino_left.right, orientation=table_de_jeu[0]["orientation"])
    # Valeur de gauche disponible
    value_left = domino_left["left"] if domino_left["orientation"] == "normal" else domino_left["right"]

    # Domino tout à droite
    domino_right = dict(left=domino_right.left, right=domino_right.right,
                        orientation=table_de_jeu[len(table_de_jeu) - 1]["orientation"])
    # Valeur de droite disponible
    value_right = domino_right["right"] if domino_right["orientation"] == "normal" else domino_right["left"]

    # Domino bien jouable là ou il est placé
    if (side == "left" and value_left not in [domino.left, domino.right]) or (
            side == "right" and value_right not in [domino.left, domino.right]):
        return False
    return dict(left=value_left, right=value_right)


def notify_player_for_his_turn(round, session, domino_list=None, player_time_end=None):
    table_de_jeu = json.loads(round.table)

    # Récupère les dominos jouables du prochain joueur
    hand_player_turn = HandPlayer.objects.filter(player=round.player_turn, session=session).first()
    hand_player_turn = json.loads(hand_player_turn.dominoes)
    playable_dominoes = get_all_playable_dominoes(domino_list, hand_player_turn, table_de_jeu)

    dt_utc = datetime.strptime(player_time_end, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=UTC)
    # Notifie la personne qui doit jouer
    if len(playable_dominoes) == 0:
        data_next_player = dict(action="game.your_turn_no_match",
                                data=dict(player_time_end=player_time_end)
                                )
        notify_websocket("player", round.player_turn.id, data_next_player)

        player_pass.apply_async((round.player_turn.id, round.id), eta=dt_utc)
    else:
        data_next_player = dict(action="game.your_turn",
                                data=dict(
                                    playable_dominoes=playable_dominoes,
                                    player_time_end=player_time_end
                                )
                                )
        notify_websocket("player", round.player_turn.id, data_next_player)
        play_domino.apply_async((round.player_turn, session, round, domino_list), eta=dt_utc)


def get_all_playable_dominoes(domino_list, hand_player_turn, table_de_jeu):
    playable_dominoes = []
    for domino_id in hand_player_turn:
        if not domino_list:
            domino_x = Domino.objects.get(id=domino_id)
        else:
            domino_x = domino_list[domino_id - 1]

        if not domino_playable(domino_x, table_de_jeu, "left", domino_list) and not domino_playable(domino_x,
                                                                                                    table_de_jeu,
                                                                                                    "right",
                                                                                                    domino_list):
            continue
        playable_dominoes.append(dict(id=domino_id, left=domino_x.left, right=domino_x.right))
    return playable_dominoes


def new_round(session, first=False):
    # Crée un round
    round = Round.objects.create(game=session.game_id, session=session, table="[]", statut_id=11)

    # Distribue 7 dominos pour chaque joueurs de la session
    domino_list = list(Domino.objects.all())  # Liste des dominos
    player_id_list = json.loads(session.order)  # Liste des joueurs
    domino_list_full = domino_list.copy()

    # Le joueur qui a le domino le plus fort
    heaviest_domino_owner = dict(player=None, domino_id=0)
    player_hote_hand = None
    hands_list = []

    # Pour chacun des joueurs dans la partie
    for player_id in player_id_list:
        dominoes = []
        player_x = Player.objects.filter(id=player_id).first()
        # Choisis 7 Dominos dans la liste
        for i in range(0, 7):
            new_domino = random.choice(domino_list)
            domino_list.remove(new_domino)
            dominoes.append(new_domino.id)
            if heaviest_domino_owner["domino_id"] <= new_domino.id:
                heaviest_domino_owner = dict(player=player_x, domino_id=new_domino.id)
        # Lie les dominos au joueur
        if player_id == session.hote.id:
            player_hote_hand = HandPlayer.objects.create(round=round, session=session, player=player_x,
                                                         dominoes=json.dumps(dominoes))
        else:
            hands_list.append(
                HandPlayer.objects.create(round=round, session=session, player=player_x, dominoes=json.dumps(dominoes)))

    # Dominos du joueur hôte
    player_hote_dominoes = get_full_domino_player(player_hote_hand.dominoes, domino_list_full)

    # dernier gagnant
    last_winner = session.game_id.last_winner

    # Première personne à jouer
    player_turn = heaviest_domino_owner.get("player") if not last_winner else last_winner

    round.player_turn = player_turn
    round.save()  # Ecrit dans la base a qui le tour

    # Son temps de reflexion
    reflexion_time_param = session.reflexion_time
    player_time_end = datetime.now(UTC) + timedelta(seconds=reflexion_time_param)
    player_time_end = player_time_end.strftime('%Y-%m-%dT%H:%M:%SZ')

    # notifie tout les joueurs sauf hote via le websocket de la session
    for hands in hands_list:
        player_x_dominoes = get_full_domino_player(hands.dominoes, domino_list_full)

        data_notify = dict(
            action="session.start_" + ("game" if first else "round"),
            data=dict(
                round_id=round.id,
                dominoes=player_x_dominoes,
                player_turn=player_turn.pseudo,
                player_time_end=player_time_end
            )
        )
        notify_websocket("player", hands.player.id, data_notify)  # Lui envoie

    data_hote = dict(round_id=round.id,
                     dominoes=player_hote_dominoes,
                     player_turn=player_turn.pseudo,
                     player_time_end=player_time_end)

    if not first:
        msg_hote = dict(action="session.start_round", data=data_hote)
        notify_websocket("player", session.hote.id, msg_hote)

    return data_hote


def update_player_turn(round, session):
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
    player_time_end = player_time_end.strftime('%Y-%m-%dT%H:%M:%SZ')
    return player_time_end, next_player


def r():
    pass


class CreateGame(APIView):
    permission_classes = []

    # permission_classes = [IsAuthenticatedWithJWT]


    def post(request):
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
            if session.game_id.statut.id == 1:
                return Response(dict(code=400, message="Une partie est déjà en cours", data=None),
                                status=status.HTTP_400_BAD_REQUEST)

        # Si un joueur n'est pas prêt on crée pas de partie
        for player_id in player_id_list:
            info_player = Infosession.objects.get(session=session, player_id=player_id)

            if info_player.statut.id != 7:  # player.is_ready
                return Response(dict(code=400, message="Tout les joueurs ne sont pas prêts", data=None),
                                status=status.HTTP_400_BAD_REQUEST)

            info_player.round_wins = 0
            info_player.save()

        # Crée une partie
        game = Game.objects.create(session_id=session, statut_id=1)
        session.game_id = game
        session.statut_id = 5
        session.save()

        data_return["data"] = new_round(session, True)

        # Transmet à l’hôte ses dominos
        return Response(data_return, status=status.HTTP_201_CREATED)


class PlaceDomino(APIView):
    permission_classes = []

    # permission_classes = [IsAuthenticatedWithJWT]

    def post(self, request):
        data_request = request.data

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
        # Liste
        domino_list = list(Domino.objects.all())  # Liste des dominos
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

        #  Vérifier que c’est bien le round en cours
        if round.statut.name == "round.is_terminated":
            return Response(dict(code=400, message="Ce round est déjà fini", data=None),
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

        playable_values = domino_playable(domino, table_de_jeu, side, domino_list)
        # Si ce n'est pas le premier domino à poser, on vérifie qu'il est bien jouable
        if len(table_de_jeu) > 0 and playable_values == False:
            return Response(dict(code=400, message="Domino non jouable", data=None),
                            status=status.HTTP_400_BAD_REQUEST)  # Domino non jouable

        data_return = play_domino(player, session, round, domino_list, side, playable_values, domino)

        return Response(data_return, status=status.HTTP_200_OK)
