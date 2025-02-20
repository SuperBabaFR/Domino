from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework.utils import json

from API_Domino.settings import SECRET_KEY
from authentification.models import Player, Session
from authentification.views import verify_token, InvalidAccessTokenException, InvalidRefreshTokenException


class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware pour authentifier les connexions WebSocket avec un token JWT.
    """
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope['query_string'].decode())
        token = query_string.get("token", [None])[0]  # Récupérer le token JWT
        session_id = query_string.get("session_id", [None])[0]  # Récupérer le token JWT
        scope["authorized"] = False  # Par défaut, le joueur passe pas

        # Ferme si y'a pas de tokens
        if not token:
            await self.close_connection(send, "Token Requis", 400)
            return

        # Vérifie le token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])  # Vérifie et décode le token
            if payload.get("type") != "access":
                await self.close_connection(send, "Type de token invalide", 4400)
                return
        except jwt.DecodeError or jwt.InvalidTokenError:
            await self.close_connection(send, "Token invalide", 4400)
            return
        except jwt.ExpiredSignatureError:
            await self.close_connection(send, "Token access expire, refresh necessaire", 4400)
            return

        # Vérifie la session, le joueur et si il est dans la session
        session = await self.get_session(session_id) # Récupère la session en BDD
        player = await self.get_player(payload["player_id"])  # Récupère le joueur en BDD

        if not player:
            await self.close_connection(send, "Joueur inexistant", 4404)
            return

        if not session:
            await self.close_connection(send, "session inexistante", 4404)
            return

        if player.id not in json.loads(session.order):
            await self.close_connection(send, "Le joueur n'est pas dans la session", 4404)
            return

        scope['player'] = player  # Associe le joueur à la connexion
        scope['session'] = session  # Associe la session à la connexion
        scope['authorized'] = True
        return await super().__call__(scope, receive, send)

    async def close_connection(self, send, message, code=401):
        """Ferme proprement la connexion avec un message explicite"""
        await send({"type": "websocket.accept"})  # Accepter TEMPORAIREMENT
        await send({
            "type": "websocket.send",
            "text": json.dumps({"message": message, "code": code, "data": None})
        })
        await send({
            "type": "websocket.close",
            "code": code
        })

    @database_sync_to_async
    def get_player(self, player_id):
        return Player.objects.get(id=player_id)

    @database_sync_to_async
    def get_session(self, session_id):
        return Session.objects.filter(id=session_id).first()