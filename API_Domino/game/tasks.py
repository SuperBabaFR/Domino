import json

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from authentification.models import Player, HandPlayer


@shared_task
def player_pass(player_id, round_id):
    data = dict(round_id=round_id)
    group_name = f"player_{player_id}"
    print(f"player_pass : {group_name}, {data}")
    channel_layer = get_channel_layer()  # Récupérer le Channel Layer de Django Channels
    async_to_sync(channel_layer.group_send)(
        group_name,  # Nom du groupe WebSocket
        {
            "type": "player_pass",
            "data": data
        }
    )

@shared_task
def auto_play_player(player: Player, round_id):
    # Dominos du joueurs
    hand_player = HandPlayer.objects.filter(player=player, round=round, session=session).first()

    player_dominoes: list = json.loads(hand_player.dominoes)

    # Dominos sur la table
    table_de_jeu: list = json.loads(round.table)

    # Si c'est le premier domino qui est joué il doit forcément jouer son plus gros domino

    # Sinon on le fait jouer un domino jouable au hasard

    # Met à jour la ligne

    # Soustrait le domino joué de sa main
