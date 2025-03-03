import json
import random
from datetime import datetime, timedelta, timezone

from asgiref.sync import async_to_sync
from celery import shared_task
from celery.worker.control import revoke
from channels.layers import get_channel_layer

from authentification.models import Player, HandPlayer, Infosession, Round, Session, Domino, Statut
from game.methods import get_all_playable_dominoes, domino_playable, update_player_turn, notify_websocket, \
    notify_websocket_statut


def notify_player_for_his_turn(round, session, player_time_end, domino_list=None):
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
        notify_websocket.apply_async(args=("player", round.player_turn.id, data_next_player))

        # Récupérer la file d'attente
        # Ajouter la tâche avec un ETA
        result = player_pass_task.apply_async((round.player_turn.id, round.id), eta=dt_utc)
        round.auto_play_task_id = result.id
        round.save()
    else:
        data_next_player = dict(action="game.your_turn",
                                data=dict(
                                        playable_dominoes=(playable_dominoes if len(table_de_jeu) > 0 else [max(playable_dominoes)]),
                                        player_time_end=player_time_end
                                    )
                                )
        notify_websocket.apply_async(args=("player", round.player_turn.id, data_next_player))
        # Ajouter la tâche avec un ETA
        result = auto_play_domino_task.apply_async((round.player_turn.id, session.id, round.id), eta=dt_utc)

        round.auto_play_task_id = result.id
        round.save()

def revoke_auto_play_task(round):
    if round.auto_play_task_id:
        print("Revoking auto-play task {id} for player {p}".format(id=round.auto_play_task_id, p=round.player_turn_id))
        revoke(task_id=round.auto_play_task_id, state='REVOKED', terminate=True)
        # Supprimer l'ID pour éviter une révocation multiple
        round.auto_play_task_id = None
        round.save()

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

    play_domino(player=player, session=session, round=round, domino_list=domino_list, domino=domino)


def play_domino(player, session, round, domino_list, side=None, orientation=None, domino=None):
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
        # Détermine dans quelle orientation le domino sera joué
        orientation = is_playable

    # Si c son dernier domino
    is_last_domino = True if len(player_dominoes) == 1 else False

    domino_value = dict(id=domino.id, orientation=orientation)

    # Joue le domino sur la table
    if len(table_de_jeu) > 0 and side == "left":  # si c'est joué a gauche avec des dominos déjà sur la table
        table_de_jeu.insert(0, domino_value)
    else:  # si c'est joué a droite | si c'est le premier domino
        table_de_jeu.append(domino_value)
    # Met à jour la ligne
    round.table = json.dumps(table_de_jeu)

    # Soustrait le domino joué de sa main
    print(f'domino a jouer : {str(domino.id)}, liste des dominos : {str(player_dominoes)}')
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
                                orientation=orientation,
                                side=side if side != None else "left",
                                player_turn=round.player_turn.pseudo,
                                player_time_end=player_time_end
                            )
                            )
        notify_websocket.apply_async(args=("session", session.id, data_session))

        notify_player_for_his_turn(round, session, player_time_end, domino_list)

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

        # Statut non prêt
        not_ready_statut = Statut.objects.get(id=6)

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
                notify_websocket_statut.apply_async(
                    args=(info.player.id, dict(id=not_ready_statut.id, name=not_ready_statut.name)))
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
                                orientation=orientation,
                                type_finish=type_finish,
                                winstreak=have_winstreak
                            )
                            )
        notify_websocket.apply_async(args=("session", session.id, data_session))

        # envoie aux joueurs les résultats de la partie
        if data_end_game:
            notify_websocket.apply_async(args=("session", session.id, data_end_game))

        # Met a jour le statut du round
        round.statut_id = 12
        round.save()
        session.game_id.save()
        if type_finish == "game":
            session.game_id = None
            session.save()
        info_player.save()
        player.save()

        notify_websocket_statut.apply_async(args=(player.id, dict(id=not_ready_statut.id, name=not_ready_statut.name)))

        # données pour la requete http
        data_return["message"] = "Tu as gagne"
        data_return["data"] = dict(domino=domino.id,
                                   side=side,
                                   orientation=orientation,
                                   type_finish=type_finish)
    return data_return


def new_round(session, first=False):
    game = session.game_id
    game.round_count += 1
    game.save()

    # Crée un round
    round = Round.objects.create(game=game, session=session, table="[]", statut_id=11)

    # Distribue 7 dominos pour chaque joueurs de la session
    domino_list = list(Domino.objects.all())  # Liste des dominos
    domino_list_full = domino_list.copy()  # Liste des dominos complète
    player_id_list = json.loads(session.order)  # Liste des joueurs

    # Le joueur qui a le domino le plus fort
    heaviest_domino_owner = dict(player=None, domino_id=0)
    player_hote_hand = None
    hands_list = []

    # Statut actif
    actif_statut = Statut.objects.get(id=8)

    # Pour chacun des joueurs dans la partie
    for player_id in player_id_list:
        dominoes = []
        player_x = Player.objects.filter(id=player_id).first()

        notify_websocket_statut.apply_async(args=(player_x.id, dict(id=actif_statut.id, name=actif_statut.name)))

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

    # dernier gagnant
    last_winner = game.last_winner

    # Première personne à jouer
    player_turn = heaviest_domino_owner.get("player") if not last_winner else last_winner

    round.player_turn = player_turn
    round.save()  # Ecrit dans la base a qui le tour

    # Son temps de reflexion
    reflexion_time_param = session.reflexion_time
    player_time_end = datetime.now(timezone.utc) + timedelta(seconds=reflexion_time_param)
    player_time_end = player_time_end.strftime('%Y-%m-%dT%H:%M:%SZ')

    # notifie tout les joueurs sauf hote via le websocket de la session
    for hands in hands_list:
        data_notify = dict(
            action="session.start_" + ("game" if first else "round"),
            data=dict(
                round_id=round.id,
                dominoes=hands.dominoes,
                player_turn=player_turn.pseudo,
                player_time_end=player_time_end
            )
        )
        notify_websocket.apply_async(args=("player", hands.player.id, data_notify))  # Lui envoie


    data_hote = dict(round_id=round.id,
                     dominoes=player_hote_hand.dominoes,
                     player_turn=player_turn.pseudo,
                     player_time_end=player_time_end)

    if not first:
        msg_hote = dict(action="session.start_round", data=data_hote)
        notify_websocket.apply_async(args=("player", session.hote.id, msg_hote))

    notify_player_for_his_turn(round, session, player_time_end, domino_list_full)

    return data_hote