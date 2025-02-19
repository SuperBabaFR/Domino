import json
import random
from datetime import datetime, timedelta, timezone

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from authentification.models import Player, HandPlayer, Infosession, Round, Session, Domino
from game.methods import get_all_playable_dominoes, domino_playable, update_player_turn, notify_websocket


def notify_player_for_his_turn(round, session, domino_list=None, player_time_end=None):
    table_de_jeu = json.loads(round.table)

    # Récupère les dominos jouables du prochain joueur
    hand_player_turn = HandPlayer.objects.filter(player=round.player_turn, round=round, session=session).first()

    hand_player_turn = json.loads(hand_player_turn.dominoes)
    playable_dominoes = get_all_playable_dominoes(domino_list, hand_player_turn, table_de_jeu)

    dt_utc = datetime.strptime(player_time_end, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)

    # Notifie la personne qui doit jouer
    if len(playable_dominoes) == 0:
        data_next_player = dict(action="game.your_turn_no_match",
                                data=dict(player_time_end=player_time_end)
                                )
        notify_websocket("player", round.player_turn.id, data_next_player)

        # Récupérer la file d'attente
        # Ajouter la tâche avec un ETA
        player_pass_task.apply_async((round.player_turn.id, round.id), eta=dt_utc)
    else:
        data_next_player = dict(action="game.your_turn",
                                data=dict(
                                    playable_dominoes=playable_dominoes,
                                    player_time_end=player_time_end
                                )
                                )
        notify_websocket("player", round.player_turn.id, data_next_player)
        # Ajouter la tâche avec un ETA
        auto_play_domino_task.apply_async((round.player_turn.id, session.id, round.id), eta=dt_utc)


@shared_task
def player_pass_task(player_id, round_id):
    player_turn = Round.objects.get(id=round_id).player_turn
    still_his_turn = player_turn.id == player_id
    if still_his_turn:
        group_name = f"player_{player_id}"
        channel_layer = get_channel_layer()  # Récupérer le Channel Layer de Django Channels
        async_to_sync(channel_layer.group_send)(
            group_name,  # Nom du groupe WebSocket
            {
                "type": "player_pass",
                "round_id": round_id
            }
        )
    else:
        print(f"c plus le tour de {player_id}, maintenant c'est {player_turn.id}")


@shared_task
def auto_play_domino_task(player_id, session_id, round_id, domino_id=None):
    player = Player.objects.get(id=player_id)
    session = Session.objects.get(id=session_id)
    round = Round.objects.get(id=round_id)
    domino = None
    if domino_id:
        domino = Domino.objects.get(id=domino_id)

    domino_list = list(Domino.objects.all())

    play_domino(player, session, round, domino_list, domino=domino)


def play_domino(player, session, round, domino_list, side=None, playable_values=None, domino=None):
    if not round.player_turn == player:
        return

    data_return = dict(code=200, message="Domino joué", data=None)

    # Dominos du joueurs
    hand_player = HandPlayer.objects.filter(player=player, round=round, session=session).first()
    player_dominoes: list = json.loads(hand_player.dominoes)

    # Dominos sur la table
    table_de_jeu: list = json.loads(round.table)

    if not domino:
        is_playable = False
        if len(table_de_jeu) == 0:
            domino = domino_list[max(player_dominoes) - 1]
        elif len(table_de_jeu) >= 1:
            sides = ["left", "right"]
            playable_dominoes = get_all_playable_dominoes(domino_list, player_dominoes, table_de_jeu, True)
            while not is_playable:
                domino = random.choice(playable_dominoes)
                side = random.choice(sides)
                is_playable = domino_playable(domino, table_de_jeu, side, domino_list)
        playable_values = is_playable

    is_last_domino = True if len(player_dominoes) == 1 else False

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

    if not is_last_domino:
        player_time_end, next_player = update_player_turn(round, session)

        # Notifie la session qu'un domino a été joué
        data_session = dict(action="game.someone_played",
                            data=dict(
                                pseudo=player.pseudo,
                                domino=domino.id,
                                side=side,
                                player_turn=round.player_turn.pseudo,
                                player_time_end=player_time_end
                            )
                            )
        notify_websocket("session", session.id, data_session)

        notify_player_for_his_turn(round, session, domino_list, player_time_end)

        # Transmet au joueur qui a joué les informations à jour
        data_return["data"] = dict(dominoes=hand_player.dominoes,
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
            info_player.statut_id = 6

            pigs = []

            for info in info_players:
                if info.round_win > 0:
                    continue
                # COCHON pour ceux qui ont pas de points
                pigs.append(info.player.pseudo)
                info.pig_count += 1
                info.player.pigs += 1
                info.statut_id = 6
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
                                domino=domino.id,
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
        data_return["data"] = dict(domino=domino.id,
                                   side=side,
                                   type_finish=type_finish)
    return data_return
