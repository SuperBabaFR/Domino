from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import json

from authentification.models import Statut, Infosession, Session


class SessionConsumer(AsyncWebsocketConsumer):
    # Connexion au WEBSOCKET
    async def connect(self):
        # Vérifie la session avec l'id
        self.scope["session"] = await self.get_session(self.scope['url_route']['kwargs']['session_id'])


        if not self.scope["player"] or not self.scope["session"]:  # Vérifie si le joueur est authentifié ou si la session existe
            await self.close()  # Ferme la connexion si non authentifié
            return

        in_that_session = await self.is_player_in_that_session(self.scope["player"], self.scope["session"])

        if not in_that_session:
            await self.close()  # Ferme la connexion si il n'est pas dans la session
            return

        # Crée le nom du groupe
        self.group_name = f"session_{self.scope['session'].id}"

        # Group name individuel
        self.custom_channel_name = f"player_{self.scope["player"].id}"

        # Ajouter la connexion au groupe unique pour les messages directs
        await self.channel_layer.group_add(
            self.custom_channel_name,
            self.channel_name
        )
        # Ajouter la connexion au groupe de la session
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()  # Accepter seulement les connexions authentifiées
        print(f"Joueur connecté : {self.scope['player'].pseudo}")

    # DECONNEXION DU CLIENT
    async def disconnect(self, close_code):
        if not self.scope["player"] or not self.scope["session"]:  # Vérifie si le joueur est authentifié
            return # Ferme DIRECTEMENT la connexion si non authentifié

        if self.group_name and self.custom_channel_name:
            # Retirer la connexion du groupe de la session
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

            # Retirer la connexion au groupe unique pour les messages directs
            await self.channel_layer.group_discard(
                self.custom_channel_name,
                self.channel_name
            )

        print(f"Joueur déconnecté : {self.scope['player'].pseudo}")

    # TRAITEMENT DES MESSAGES RECUS
    async def receive(self, text_data):
        data = json.loads(text_data)

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
            type="session.player_statut",
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
            type="session.player_",
            data=dict(
                player=pseudo
            ))
        message["type"] += action
        if action == "join":
            message["data"] = dict(
                player=pseudo,
                image=image,
                wins=wins,
                pigs=pigs
            )

        await self.send(text_data=json.dumps(message))


    async def send_session_updates(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    # ------------ GAME METHODES ------------ #

    # Starting game


    # ------------ DATABASES METHODES ------------ #
    @database_sync_to_async
    def get_session(self, session_id):
        return Session.objects.filter(id=session_id).first()

    @database_sync_to_async
    def get_statut(self, statut_id):
        return Statut.objects.filter(id=statut_id).first()

    @database_sync_to_async
    def is_player_in_that_session(self, player, session):
        order = json.loads(session.order)
        return player.id in order # Retourne vrai si le joueur est dans la session

    @database_sync_to_async
    def update_player_statut(self, session, player, statut):
        info_player = Infosession.objects.filter(session=session, player=player).first()
        info_player.statut = statut
        info_player.save()



        # group_name = f"session_{self.session_id}"
        #
        # player = self.scope["player"]
        #
        # await self.channel_layer.group_send(
        #     group_name,
        #     {
        #         "type": "chat_message",
        #         "message": f"{player.pseudo} : {data["message"]}"
        #     }
        # )
        # {
        #     "type": "session.player_statut",
        #     "data": {
        #         "player": string,
        #         "statut": string
        #     }
        # }
