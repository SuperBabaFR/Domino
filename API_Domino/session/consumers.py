import asyncio

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json


class SessionConsumer(AsyncWebsocketConsumer):
    # Connexion au WEBSOCKET
    async def connect(self):
        # Crée le nom du groupe
        session = self.scope['session']
        self.group_name = f"session_{session.id}"
        game = await self.get_game()
        # Met a jour le statut du joueur
        statut = None
        if not game:  # Si y'a aucune game en cours
            statut = await self.get_statut(6)
        else:
            statut = await self.get_statut(8)

        # Group name individuel
        self.individual_group_name = f"player_{self.scope['player'].id}"

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

        await self.channel_layer.group_send(
            self.individual_group_name,
            {
                "type": "statut_player",
                "statut": dict(id=statut.id, name=statut.name)
            }
        )

    # DECONNEXION DU CLIENT
    async def disconnect(self, close_code):
        if not self.scope["authorized"]:  # Vérifie si le joueur est authentifié
            return  # Ferme DIRECTEMENT la connexion si non authentifié

        if self.group_name and self.individual_group_name:
            # On le met hors ligne et on prévient tlm
            statut = await self.get_statut(10)
            await self.channel_layer.group_send(
                self.individual_group_name,
                {
                    "type": "statut_player",
                    "statut": dict(id=statut.id, name=statut.name)
                }
            )



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

        print(f"Message reçu de {self.scope['player'].pseudo} : {data}")

        if not data["action"]:
            return

        group_name = f"player_{self.scope['player'].id}"

        if "chat_message" in data["action"]:
            # par défaut le message est pour toute la session
            group_name = f"session_{self.scope['session'].id}"
            player_id = None
            # Si le message est privé on récupère l'id du joueur pour qui il est transmis
            if "global" not in data["data"]["channel"]:
                player_id = await self.get_id_player(data["data"]["channel"])
            # Seulement si on trouve le joueur mentionné on lui envoie sinon c'est pour tlm le message
            if player_id is not None:
                group_name = f"player_{player_id}"

            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "chat_message",
                    # On précise au client que c'était un message privé même si il recevra pas de message qui ne lui était pas conecerné
                    "data": json.dumps(dict(action="chat_message", data=dict(message=data["data"]["message"],
                                                                             sender=self.scope['player'].pseudo,
                                                                             is_private=(
                                                                                 True if player_id is not None else False))))
                }
            )
            return

        if "need_refresh" in data["action"]:
            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "need_refresh"
                }
            )
            return

        if "mix_the_dominoes" in data["action"]:
            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "prepare_new_round"
                }
            )
            return

        if "player_statut" in data["action"]:
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
            return
        # Un joueur boudé passe son tour
        if "game.pass" in data["action"]:
            await self.channel_layer.group_send(
                f"player_{self.scope['player'].id}", {
                    "type": "player_pass",
                    "round_id": data["data"]["round_id"]
                }
            )
            return

    # ------------ SESSION METHODES ------------ #
    async def chat_message(self, event):
        await self.send(text_data=event["data"])

    # Statut des joueurs dans le lobby (READY | NOT READY) ou en partie (ACTIF | AFK | OFFLINE)
    async def statut_player(self, event):
        from authentification.models import Statut

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
                pseudo=player.pseudo,
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

        pseudo = event.get("data").get("pseudo")
        image = event.get("data").get("image")
        wins = event.get("data").get("games_win")
        pigs = event.get("data").get("pig_count")

        message = dict(
            action="session.player_",
            data=dict(
                pseudo=pseudo
            ))
        message["action"] += action
        if action == "join":
            message["data"] = dict(
                pseudo=pseudo,
                image=image,
                games_win=wins,
                pig_count=pigs
            )
        await self.send(text_data=json.dumps(message))

    # Envoi de messages
    async def send_session_updates(self, event):
        print(event)
        await self.send(text_data=json.dumps(event["data"]))

    # ------------ GAME METHODES ------------ #

    async def need_refresh(self, event):
        game = await self.get_game()
        data = False
        if game:
            data = await self.get_game_info(game)

        if not data:
            await self.send(text_data=json.dumps({"action": "error", "data": {"message": "No active game in session"}}))
            return

        await self.send(text_data=json.dumps(data))

    # Un joueur boudé passe son tour
    async def player_pass(self, event):
        player = self.scope.get("player")
        round_id = event.get("round_id")
        session = self.scope.get("session")

        print(f"[DEBUG] Passage de tour détecté pour {player.pseudo}, Round ID : {round_id}")

        response = await self.update_next_player(round_id, session.id)
        if response == False:
            await self.send(text_data=json.dumps({"action": "error", "data": {"message": "Round incorrect"}}))
            return
        elif response == True:
            return

        next_player, round, player_time_end = response

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
        this_round = self.have_round_open()
        if type(this_round) is int:
            msg = "Round already open" if this_round == 0 else "Game already terminated"
            await self.send(text_data=json.dumps(dict(action="error", message=msg)))
            return
        else:
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
            await asyncio.sleep(3)
            await self.launch_new_round(session)

    # ------------ DATABASES METHODES ------------ #

    @database_sync_to_async
    def update_statut_player(self, statut_id):
        from authentification.models import Infosession

        player = self.scope.get("player")
        session = self.scope.get("session")
        info_player = Infosession.objects.get(player=player, session=session)
        info_player.statut_id = statut_id
        info_player.save()

    @database_sync_to_async
    def launch_new_round(self, session):

        from game.tasks import new_round
        new_round(session)

    @database_sync_to_async
    def notify_player_for_his_turn_async(self, player_time_end, round, session):
        from game.tasks import notify_player_for_his_turn
        notify_player_for_his_turn(round, session, player_time_end=player_time_end)

    @database_sync_to_async
    def get_session(self, session_id):
        from authentification.models import Session

        return Session.objects.filter(id=session_id).first()

    @database_sync_to_async
    def update_next_player(self, round_id, session_id):

        from game.methods import update_player_turn
        from authentification.models import  HandPlayer, Round,  Session
        from game.tasks import revoke_auto_play_task

        round = Round.objects.filter(id=round_id).first()
        session = Session.objects.filter(id=session_id).first()

        if not round or not session:
            print("[ERROR] Round ou session introuvable")
            return False

        # Forcer la synchronisation avant de modifier les données
        round.refresh_from_db()
        session.refresh_from_db()

        if round.game_id != session.game_id_id or round.statut_id != 11:
            print("[ERROR] Round terminé ou plus lié au jeu")
            return False

        # Révoque la tâche programmée au plus vite
        revoke_auto_play_task(round)

        hand_players = list(HandPlayer.objects.filter(session=session, round=round).all())
        partie_blocked = all(hand.blocked or hand.player == self.scope['player'] for hand in hand_players)

        # si tout le monde est boudé
        if partie_blocked:
            print("[INFO] Tous les joueurs sont boudés -> Fin du round")
            return self.finish_round(round, session)

        else:
            hand_player = next((hand for hand in hand_players if hand.player.id == self.scope['player'].id), None)
            if hand_player:
                hand_player.blocked = True
                hand_player.save()

        player_time_end, next_player = update_player_turn(round, session)

        # Vérifier si le tour a bien été mis à jour
        round.refresh_from_db()
        print(f"[DEBUG] Nouveau joueur à jouer : {next_player.pseudo}")

        return [next_player, round, player_time_end]

    def finish_round(self, round, session):
        from game.methods import notify_websocket
        from authentification.models import Infosession, Player, Domino, HandPlayer
        player = self.scope['player']
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

            data_players.append(dict(pseudo=hand_player.player.pseudo,
                                     dominoes=hand_player.dominoes,
                                     points_remaining=sum_of_dominoes))
        info_player = Infosession.objects.filter(player=winner["player"], session=session).first()
        info_player.round_win += 1
        type_finish = "game" if info_player.round_win == 3 else "round"
        win_streak = True if session.game_id.last_winner == winner["player"] else False
        data_finish = dict(action="game.blocked",
                           data=dict(
                               list_players=data_players,
                               winner_pseudo=winner["player"].pseudo,
                               points_remaining=winner["score"],
                               type_finish=type_finish,
                               win_streak=win_streak))
        notify_websocket.apply_async(args=("session", session.id, data_finish))
        # Met a jour le dernier gagnant
        session.game_id.last_winner = self.scope['player']
        if type_finish == "game":
            session.game_id.statut_id = 2  # Met a jour le statut de la partie

            info_players = list(Infosession.objects.filter(session=session).all())
            info_players.remove(info_player)

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
                                 data=dict(results=dict(winner=winner["player"].pseudo, pigs=pigs)))
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
        return True

    @database_sync_to_async
    def get_statut(self, statut_id):
        from authentification.models import Statut

        return Statut.objects.filter(id=statut_id).first()

    @database_sync_to_async
    def update_player_statut(self, session, player, statut):
        from authentification.models import Infosession

        info_player = Infosession.objects.filter(session=session, player=player).first()
        info_player.statut = statut
        info_player.save()

    @database_sync_to_async
    def get_game(self):
        from authentification.models import Game

        game = Game.objects.filter(session=self.scope.get("session"), statut_id=1).first()
        return game

    @database_sync_to_async
    def have_round_open(self):
        from authentification.models import Round

        session = self.scope.get("session")

        if session.game_id is None:
            return 1

        round = Round.objects.filter(game_id=session.game_id, statut_id=11).first()

        return round if round is not None else 0

    @database_sync_to_async
    def get_game_info(self, game):
        from authentification.models import Round, HandPlayer

        player = self.scope['player']
        session = self.scope["session"]
        this_round = Round.objects.filter(session=session, game=game, statut_id=11).first()
        if not this_round:
            return False

        dominoes = None
        table = json.loads(this_round.table)
        players = []

        all_hands = list(HandPlayer.objects.filter(round=this_round, session=session).all())

        for hand in all_hands:
            if hand.player == player:
                dominoes = hand.dominoes
            else:
                players.append(dict(pseudo=hand.player.pseudo, domino_count=len(json.loads(hand.dominoes))))

        data = dict(
            game_id=game.id,
            round_id=this_round.id,
            dominoes=dominoes,
            table=table,
            players=players,
            player_turn=this_round.player_turn.pseudo
        )
        return data

    @database_sync_to_async
    def get_id_player(self, pseudo):
        from authentification.models import Player

        player = Player.objects.filter(pseudo=pseudo).first()

        return player.id if player else None
