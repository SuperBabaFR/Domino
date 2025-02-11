from datetime import datetime, UTC, timedelta
import random

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from authentification.models import Session, Player, Game, Domino, Round, HandPlayer, Statut, Infosession


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
    #
    # if not player_time_end:
    #     reflexion_time_param = session.reflexion_time
    #     player_time_end = datetime.now(UTC) + timedelta(seconds=reflexion_time_param)
    #     player_time_end = player_time_end.strftime('%Y-%m-%dT%H:%M:%SZ')

    table_de_jeu = json.loads(round.table)

    # Récupère les dominos jouables du prochain joueur
    hand_player_turn = HandPlayer.objects.filter(player=round.player_turn, session=session).first()
    hand_player_turn = json.loads(hand_player_turn.dominoes)
    playable_dominoes = []
    for domino_id in hand_player_turn:
        if not domino_list:
            domino_x = Domino.objects.get(id=domino_id)
        else:
            domino_x = domino_list[domino_id - 1]

        if not domino_playable(domino_x, table_de_jeu, "left", domino_list) and not domino_playable(domino_x, table_de_jeu,
                                                                                       "right", domino_list):
            continue
        playable_dominoes.append(dict(id=domino_id, left=domino_x.left, right=domino_x.right))
    # Notifie la personne qui doit jouer
    if len(playable_dominoes) == 0:
        data_next_player = dict(action="game.your_turn_no_match",
                                data=dict(player_time_end=player_time_end)
                                )
        notify_websocket("player", round.player_turn.id, data_next_player)
    else:
        data_next_player = dict(action="game.your_turn",
                                data=dict(
                                    playable_dominoes=playable_dominoes,
                                    player_time_end=player_time_end
                                )
                                )
        notify_websocket("player", round.player_turn.id, data_next_player)


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
            player_hote_hand = HandPlayer.objects.create(round=round, session=session, player=player_x, dominoes=json.dumps(dominoes))
        else:
            hands_list.append(HandPlayer.objects.create(round=round, session=session, player=player_x, dominoes=json.dumps(dominoes)))


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

            if info_player.statut.id != 7: # player.is_ready
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

        is_Last_domino = True if len(player_dominoes) == 1 else False

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

        if not is_Last_domino:
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

            # Notifie la session qu'un domino a été joué
            data_session = dict(action="game.someone_played",
                                data=dict(
                                    pseudo=player.pseudo,
                                    domino=dict(id=domino.id, left=domino.left, right=domino.right),
                                    side=side,
                                    player_turn=round.player_turn.pseudo,
                                    player_time_end=player_time_end
                                )
            )
            notify_websocket("session", session.id, data_session)

            notify_player_for_his_turn(round, session, domino_list, player_time_end)

            player_dominoes = get_full_domino_player(hand_player.dominoes, domino_list)

            # Transmet au joueur qui a joué les informations à jour
            data_return["data"] = dict(dominoes=player_dominoes,
                                       table=table_de_jeu,
                                       player_turn=round.player_turn.pseudo,
                                       player_time_end=player_time_end)
        else:
            # Récupère les infos de tout les joueurs
            info_player = Infosession.objects.get(player=player, session=session)
            info_players = list(Infosession.objects.filter(session=session).all())
            info_players.remove(info_player)
            # Ajoute la win au joueur
            info_player.round_win += 1
            # Véifie si c'est le round ou la partie qu'il vient de gagner
            type_finish = "round" if info_player.round_win < 3 else "game"
            # données si la partie est terminée
            data_end_game = None

            if type_finish == "game":
                info_player.games_win += 1
                player.wins += 1

                pigs = []

                for info in info_players:
                    if info.round_win > 0:
                        continue
                    # COCHON pour ceux qui ont pas de points
                    pigs.append(info.player.pseudo)
                    info.pig_count += 1
                    info.player.pigs += 1
                    info.save()
                    info.player.save()
                data_end_game = dict(action="session.end_game",
                                     data=dict(results=dict(winner=player.pseudo, pigs=pigs)))

                # Met a jour le dernier gagnant
                session.game_id.last_winner = player
                session.game_id.statut_id = 2  # Met a jour le statut de la partie

            # regarde si il a gagné déjà auparavent
            have_winstreak = True if session.game_id.last_winner == player else False

            # Notifie la session qu'un domino a été joué
            data_session = dict(action="game.someone_win",
                                data=dict(
                                    pseudo=player.pseudo,
                                    domino=dict(id=domino.id, left=domino.left, right=domino.right),
                                    side=side,
                                    type_finish=type_finish,
                                    winstreak=have_winstreak
                                )
            )
            notify_websocket("session", session.id, data_session)

            # envoie aux joueurs les résultats de la partie
            if data_end_game:
                notify_websocket("session", session.id, data_end_game)


            # Met a jour le statut du round
            round.statut_id = 12
            round.save()
            session.game_id.save()
            info_player.save()
            player.save()

            # données pour la requete http
            data_return["message"] = "Tu as gagne"
            data_return["data"] = dict(domino=dict(id=domino.id, left=domino.left, right=domino.right), side=side, type_finish=type_finish)

        return Response(data_return, status=status.HTTP_200_OK)
