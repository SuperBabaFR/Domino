from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from authentification.models import Player
from authentification.views import verify_token, InvalidAccessTokenException, InvalidRefreshTokenException


class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware pour authentifier les connexions WebSocket avec un token JWT.
    """
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]  # Récupérer le token JWT

        scope["player"] = None  # Par défaut, utilisateur inexistant

        if token:
            try:
                payload = verify_token(token)  # Vérifie et décode le token
                player = await self.get_player(payload["player_id"])  # Récupère le joueur en BDD
                scope["player"] = player # Associe le joueur à la connexion
            except jwt.DecodeError:
                raise InvalidAccessTokenException()  # Token invalide
            except jwt.ExpiredSignatureError:
                raise InvalidRefreshTokenException()  # Token expiré
            except jwt.InvalidTokenError:
                raise InvalidAccessTokenException()  # Token invalide
            except Player.DoesNotExist:
                print("Joueur introuvable")

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_player(self, player_id):
        return Player.objects.get(id=player_id)