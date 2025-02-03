from channels.generic.websocket import AsyncWebsocketConsumer
import json


class SessionConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        if not self.scope["player"]:  # Vérifie si le joueur est authentifié
            await self.close()  # Ferme la connexion si non authentifié
            return

        # Récupère l'id de la session
        self.session_id = self.scope['url_route']['kwargs']['session_id']

        # Crée le nom du groupe
        self.group_name = f"session_{self.session_id}"

        # Force le channel_name
        self.custom_channel_name = f"session_{self.scope["player"].id}"

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

    async def disconnect(self, close_code):
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

    async def receive(self, text_data):
        data = json.loads(text_data)
        print(f"Message reçu de {self.scope['player'].pseudo} : {data}")

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["player"]:  # Vérifie si le joueur est authentifié
            await self.close()  # Ferme la connexion si non authentifié
            return

        self.session_name = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f"game_{self.session_name}"

        # Ajouter la connexion au groupe
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Retirer la connexion du groupe
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
