from datetime import datetime, timedelta, UTC

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from authentification.models import Statut, Infosession, Session, Round, Player, HandPlayer, Domino
from game.views import notify_player_for_his_turn, new_round, notify_websocket


class SessionConsumer(AsyncWebsocketConsumer):
    # Connexion au WEBSOCKET
    async def connect(self):
        # Crée le nom du groupe
        self.group_name = f"session_{self.scope['session'].id}"

        # Group name individuel
        self.individual_group_name = f"player_{self.scope["player"].id}"

        # Ajouter la connexion au groupe unique pour les messages directs
        await self.channel_layer.group_add(
            self.individual_group_name,
            self.channel_name
        )
        # Ajouter la connexion au groupe de la session
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()  # Accepter seulement les connexions authentifiées
        print(f"Joueur connecté : {self.scope['player'].pseudo}")
        print(f"Groupes : {self.group_name}, {self.individual_group_name}")

    # DECONNEXION DU CLIENT
    async def disconnect(self, close_code):
        if not self.scope["authorized"]:  # Vérifie si le joueur est authentifié
            return  # Ferme DIRECTEMENT la connexion si non authentifié

        if self.group_name and self.individual_group_name:
            # Retirer la connexion du groupe de la session
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

            # Retirer la connexion au groupe unique pour les messages directs
            await self.channel_layer.group_discard(
                self.individual_group_name,
                self.channel_name
            )

        print(f"Joueur déconnecté : {self.scope['player'].pseudo}")
        print(f"Groupes quittés : {self.group_name}, {self.individual_group_name}")

    # TRAITEMENT DES MESSAGES RECUS
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except ValueError:
            await self.send(text_data=json.dumps({"message": "Invalid JSON"}))
            return

        if not data["action"]:
            return

        if "mix_the_dominoes" in data["action"]:
            group_name = f"player_{self.scope["player"].id}"
            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "prepare_new_round"
                }
            )

        if "player_statut" in data["action"]:
            group_name = f"player_{self.scope["player"].id}"
            statut = await self.get_statut(data["data"]["statut"])
            if not statut:
                return

            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "statut_player",
                    "statut": dict(id=statut.id, name=statut.name)
                }
            )
        # Un joueur boudé passe son tour
        if "game.pass" in data["action"]:
            group_name = f"player_{self.scope["player"].id}"
            await self.channel_layer.group_send(
                group_name, {
                    "type": "player_pass",
                    "round_id": data["data"]["round_id"]
                }
            )
        print(f"Message reçu de {self.scope['player'].pseudo} : {data}")

    # ------------ SESSION METHODES ------------ #
    async def chat_message(self, event):
        await self.send(text_data=event["message"])

    # Statut des joueurs dans le lobby (READY | NOT READY) ou en partie (ACTIF | AFK | OFFLINE)
    async def statut_player(self, event):
        # Valeurs
        statut = event.get("statut")
        statut = Statut(id=statut["id"], name=statut["name"])
        player = self.scope.get("player")
        session = self.scope.get("session")
        # Change le statut du joueur
        await self.update_player_statut(session, player, statut)
        # Prépare le message
        message = dict(
            action="session.player_statut",
            data=dict(
                player=player.pseudo,
                statut=statut.name
            )
        )

        group_name = f"session_{self.scope['session'].id}"
        await self.channel_layer.group_send(
            group_name,
            {
                "type": "send_session_updates",
                "data": message
            }
        )

    # Mouvement des joueurs dans la session (JOIN | LEAVE | DELETE SESSION)
    async def session_players_activity(self, event):
        action = event.get("action")
        if action == "exit":
            await self.send(text_data=json.dumps(dict(type="session.hote_leave", data=None)))
            await self.close()
            return

        pseudo = event.get("data").get("player")
        image = event.get("data").get("image")
        wins = event.get("data").get("wins")
        pigs = event.get("data").get("pigs")

        message = dict(
            action="session.player_",
            data=dict(
                player=pseudo
            ))
        message["action"] += action
        if action == "join":
            message["data"] = dict(
                player=pseudo,
                image=image,
                wins=wins,
                pigs=pigs
            )
        await self.send(text_data=json.dumps(message))

    # Envoi de messages
    async def send_session_updates(self, event):
        print(event)
        await self.send(text_data=json.dumps(event["data"]))

    # ------------ GAME METHODES ------------ #

    # Un joueur boudé passe son tour
    async def player_pass(self, event):
        player = self.scope.get("player")
        round_id = event["round_id"]
        session = self.scope.get("session")

        data = await self.update_next_player(round_id, session)
        if not data:
            return
        next_player = data[0]
        round = data[1]

        reflexion_time_param = session.reflexion_time
        player_time_end = datetime.now(UTC) + timedelta(seconds=reflexion_time_param)
        player_time_end = player_time_end.strftime('%Y-%m-%dT%H:%M:%SZ')

        data_return = dict(action="game.someone_pass", data=dict(pseudo=player.pseudo, player_turn=next_player.pseudo,
                                                                 player_time_end=player_time_end))

        group_name = f"session_{self.scope['session'].id}"
        await self.channel_layer.group_send(
            group_name,
            {
                "type": "send_session_updates",
                "data": data_return
            }
        )

        await self.notify_player_for_his_turn_async(player_time_end, round, session)

    # Un joueur remue les dominos pour lancer un nouveau round
    async def prepare_new_round(self, event):
        player = self.scope.get("player")
        session = self.scope.get("session")
        # Envoie a tout le monde que quelqu'un remue
        group_name = f"session_{session.id}"
        data_session = dict(action="game.someone_mix_the_dominoes", data=dict(pseudo=player.pseudo))
        await self.channel_layer.group_send(
            group_name,
            {
                "type": "send_session_updates",
                "data": data_session
            }
        )
        await self.launch_new_round(session)

    # ------------ DATABASES METHODES ------------ #

    @database_sync_to_async
    def launch_new_round(self, session):
        new_round(session)

    @database_sync_to_async
    def notify_player_for_his_turn_async(self, player_time_end, round, session):
        notify_player_for_his_turn(round, session, player_time_end=player_time_end)

    @database_sync_to_async
    def get_session(self, session_id):
        return Session.objects.filter(id=session_id).first()

    @database_sync_to_async
    def update_next_player(self, round_id, session):

        round = Round.objects.filter(id=round_id).first()
        if round.game != session.game_id or round.statut.id != 11:
            self.send(text_data=json.dumps({"action": "error", "data": {"message": "Round incorrect"}}))
            return False


        hand_player = list(HandPlayer.objects.filter(session=session, round=round).all())
        partie_blocked = True

        # Vérifier si quelqu'un n'est pas boudé
        for hand in hand_player:
            if not hand.blocked:
                partie_blocked = False
                break

        # si tout le monde est boudé
        if partie_blocked:
            # Finir le round
            winner = dict(score=999, player=Player())
            player_id_list = json.loads(session.order)

            data_players = []

            for player_id in player_id_list:
                hand_player = HandPlayer.objects.filter(player_id=player_id, session=session, round=round).first()
                dominoes = json.loads(hand_player.dominoes)
                sum_of_dominoes = 0
                for domino_id in dominoes:
                    domino = Domino.objects.get(id=domino_id)
                    sum_of_dominoes += domino.left + domino.right

                if sum_of_dominoes < winner.get("score"):
                    winner = dict(score=sum_of_dominoes, player=hand_player.player)

                data_players.append(dict(pseudo=hand_player.player.pseudo, dominoes=hand_player.dominoes, points_remaining=sum_of_dominoes))

            info_player = Infosession.objects.filter(player=winner["player"], session=session).first()
            info_player.round_win += 1
            info_player.save()
            type_finish = "game" if info_player.round_win == 3 else "round"
            win_streak = True if session.game_id.last_winner == winner["player"] else False

            data_finish = dict(action="game.blocked",
                               data=dict(
                                   list_players=data_players,
                                   winner_pseudo=winner["player"].pseudo,
                                   points_remaining=winner["score"],
                                   type_finish=type_finish,
                                   win_streak=win_streak))
            notify_websocket("session", session.id, data_finish)
            return False
        else:
            hand_player.blocked = True
            hand_player.save()

        # Met à jour qui doit jouer mtn
        order = json.loads(session.order)
        index_next_player = 0 if order.index(round.player_turn.id) + 1 >= len(order) else order.index(
            round.player_turn.id) + 1

        next_player = Player.objects.filter(id=order[index_next_player]).first()

        round.player_turn = next_player
        round.save()  # SAUVEGARDE LES INFOS POUR LE ROUND
        return [next_player, round]

    @database_sync_to_async
    def get_statut(self, statut_id):
        return Statut.objects.filter(id=statut_id).first()

    @database_sync_to_async
    def update_player_statut(self, session, player, statut):
        info_player = Infosession.objects.filter(session=session, player=player).first()
        info_player.statut = statut
        info_player.save()
