from http import HTTPStatus
import datetime

import jwt
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission
from rest_framework import status
from rest_framework.response import Response

from API_Domino.settings import SECRET_KEY, REFRESH_TOKEN_LIFETIME, ACCESS_TOKEN_LIFETIME


# Create your views here.
def generate_tokens(player_id):
    """Génère les tokens JWT."""
    now = datetime.datetime.utcnow()

    # Access Token
    access_payload = {
        "player_id": player_id,
        "exp": now + ACCESS_TOKEN_LIFETIME,
        "iat": now,
        "type": "access"
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm='HS256')

    # Refresh Token
    refresh_payload = {
        "player_id": player_id,
        "exp": now + REFRESH_TOKEN_LIFETIME,
        "iat": now,
        "type": "refresh"
    }
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256')

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


def verify_token(token, token_type="access"):
    """Vérifie et décode un token JWT."""

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != token_type:
            raise jwt.InvalidTokenError("Type de token invalide")
        return payload
    except jwt.ExpiredSignatureError:
        raise InvalidRefreshTokenException() # Token expiré
    except jwt.InvalidTokenError:
        raise InvalidAccessTokenException() # Token invalide


# AUTHENTIFICATION

class IsAuthenticatedWithJWT(BasePermission):
    """Permission personnalisée pour valider les tokens JWT."""

    def has_permission(self, request, view):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise NoTokenException()
        token = auth_header.split(" ")[1]
        try:
            payload = verify_token(token, token_type="access")
            request.player_id = payload["player_id"]
            return True
        except ValueError as e:
            raise InvalidAccessTokenException()


# ERRORS
class InvalidAccessTokenException(APIException):
    """Exception personnalisée pour les erreurs d'access token JWT."""
    status_code = HTTPStatus.UNAUTHORIZED
    default_detail = {"code": 401, "message": "Token invalide, veuillez en générer un nouveau"}
    default_code = "token_invalid"


class InvalidRefreshTokenException(APIException):
    """Exception personnalisée pour les erreurs de refresh token JWT."""
    status_code = HTTPStatus.UNAUTHORIZED
    default_detail = {"code": 401, "message": "Token expiré, reconnexion nécessaire"}
    default_code = "token_invalid"


class NoTokenException(APIException):
    """Exception personnalisée pour les erreurs de refresh token JWT."""
    status_code = HTTPStatus.UNAUTHORIZED
    default_detail = {"code": 401, "message": "Token nécessaire"}
    default_code = "token_invalid"
