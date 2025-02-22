import json
from datetime import datetime, timedelta, timezone
import random

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.response import Response
from authentification.models import Player, Domino, Round, HandPlayer, Infosession


# Create your views here.
@shared_task
def notify_websocket(cible, id, data, type="send_session_updates"):

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

#
# def get_full_domino_player(dominos, domino_list_ref):
#     player_dominoes_value = json.loads(dominos)
#
#     player_dominoes = []
#     for domino_id in player_dominoes_value:
#         domino = domino_list_ref[domino_id - 1]
#         player_dominoes.append(dict(id=domino.id, left=domino.left, right=domino.right))
#
#     return player_dominoes


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


def get_all_playable_dominoes(domino_list, hand_player_turn, table_de_jeu, objet=False):
    playable_dominoes = []
    for domino_id in hand_player_turn:
        if not domino_list:
            domino_x = Domino.objects.get(id=domino_id)
        else:
            domino_x = domino_list[domino_id - 1]

        if (not domino_playable(domino_x, table_de_jeu, "left", domino_list)
                and not domino_playable(domino_x, table_de_jeu,"right", domino_list)):
            continue
        if not objet:
            playable_dominoes.append(domino_id)
        else:
            playable_dominoes.append(domino_x)

    return playable_dominoes





def update_player_turn(round, session):
    # Met à jour qui doit jouer mtn
    order = json.loads(session.order)
    index_next_player = 0 if order.index(round.player_turn.id) + 1 >= len(order) else order.index(
        round.player_turn.id) + 1
    next_player = Player.objects.filter(id=order[index_next_player]).first()
    round.player_turn = next_player
    round.save()  # SAUVEGARDE LES INFOS POUR LE ROUND
    # Son temps de reflexion
    reflexion_time_param = session.reflexion_time + 5
    player_time_end = datetime.now(timezone.utc) + timedelta(seconds=reflexion_time_param)
    player_time_end = player_time_end.strftime('%Y-%m-%dT%H:%M:%SZ')
    return player_time_end, next_player
