import binascii
from datetime import datetime, timezone
from http import HTTPStatus
import base64
from PIL import Image, ImageOps
import jwt
import io

from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import APIException
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from API_Domino.settings import SECRET_KEY, REFRESH_TOKEN_LIFETIME, ACCESS_TOKEN_LIFETIME
from authentification.models import Player


# AUTHENTIFICATION

class PlayerNotFoundException(APIException):
    """Exception levée lorsque le joueur n'est pas trouvé dans la base de données."""
    status_code = HTTPStatus.UNAUTHORIZED
    default_detail = {"code": 401, "message": "Le joueur avec cet ID n'existe pas."}
    default_code = "token_invalid"


class IsAuthenticatedWithJWT(BasePermission):
    """Permission personnalisée pour valider les tokens JWT."""

    def has_permission(self, request, view):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise NoTokenException()
        token = auth_header.split(" ")[1]
        try:
            payload = verify_token(token, token_type="access")
            player_id = payload.get("player_id")

            if not player_id:
                raise InvalidAccessTokenException()

            try:
                player = Player.objects.get(id=player_id)
                request.player = player  # Attache l'objet Player à la requête pour un accès ultérieur
                return True
            except ObjectDoesNotExist:
                raise PlayerNotFoundException()

        except ValueError as e:
            raise InvalidAccessTokenException()

# Create your views here.
def generate_tokens(player_id):
    """Génère les tokens JWT."""
    now = datetime.now(timezone.utc)

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
        raise InvalidRefreshTokenException()  # Token expiré
    except jwt.InvalidTokenError:
        raise InvalidAccessTokenException()  # Token invalide


class tokenRefreshView(APIView):
    """Refresh un token."""
    permission_classes = []

    def post(self, request):

        # GARDER LE FORMAT

        # {
        #     "code": int,
        #     "message": string,
        #     "data": object | null
        # }

        refresh_token = request.data["refresh_token"]

        if not refresh_token:
            return Response(
                {
                    'code': 400,
                    'message': "Le token n'à pas été envoyé",
                    'data': None
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload = verify_token(refresh_token, token_type="refresh")
            id_player = payload.get("id_player")

            tokens = generate_tokens(id_player)
            return Response({
                'code': 200,
                'message': 'Le token à bien été actualisé',
                'data': tokens["access_token"]
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({
                'code': 401,
                'message': 'Erreur : '+str(e),
                'data': None
            }, status=status.HTTP_401_UNAUTHORIZED)


# LOGIN et INSCRIPTION
def is_base64_image(image_data):
    try:
        # Decode the Base64 string
        image_data = base64.b64decode(image_data)

        # Try to open the image using PIL
        image = Image.open(io.BytesIO(image_data))

        # If the image opens successfully, it's a valid image
        image.verify()
        return True
    except (base64.binascii.Error, IOError):
        # If decoding or opening the image fails, it's not a valid Base64 image
        return False


class SignupView(APIView):
    permission_classes = []

    def post(self, request):
        # Taille max de l'image reçue
        max_image_file_size = 5 * 1024 * 1024  # Kilobytes
        # Taille max de :'image en pixels
        maxSize = (300, 300)
        # Message retour de réussite
        data_return = dict(code=201, message="Joueur inscrit avec succès", data=None)
        # Données de requête
        data_request = request.data
        pseudo = data_request.get("pseudo")
        password = data_request.get("password")
        image_data = data_request.get("image")
        img_str = None

        # Vérifie si le pseudo est fourni
        if not pseudo:
            return Response(dict(code=400, message='Pseudo requis', data=None), status=status.HTTP_400_BAD_REQUEST)

        # Vérifie si le pseudo n'existe pas
        if Player.objects.filter(pseudo=pseudo).exists():
            return Response(dict(code=400, message='Pseudo déjà utilisé', data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        # Vérifie si le password est fourni
        if not password:
            return Response(dict(code=400, message='Password requis', data=None), status=status.HTTP_400_BAD_REQUEST)

        # Vérifie si le password est conforme
        if len(password) > 25 or len(password) < 8:
            return Response(dict(code=400, message='Le Password doit être compris entre 8 et 25', data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        if image_data is not None:
            # Vérifie la taille de l'image
            if (len(image_data) * 3) / 4 - image_data.count('=', -2) > max_image_file_size:
                return Response(dict(code=400, message='Image trop lourde', data=None),
                                status=status.HTTP_400_BAD_REQUEST)

            # Vérifie si les données de l'image correspondent à de la base 64
            try:
                # Décode le string en Base64
                image_data_base64 = base64.b64decode(image_data)

                # Si l'image s'ouvre c'est qu'elle est correcte
                image = Image.open(io.BytesIO(image_data_base64))
                image.verify()

            except (binascii.Error, IOError):
                return Response(dict(code=400, message='Image incorrecte', data=None),
                                status=status.HTTP_400_BAD_REQUEST)

            # Réduit la taille de l'image à 300x300
            image = Image.open(io.BytesIO(image_data_base64))

            if image.size > maxSize:
                image = ImageOps.contain(image, maxSize)

            # Converti l'image en JPEG pour réduire son poids
            buff = io.BytesIO()
            image.convert('RGB').save(buff, format="JPEG")
            img_str = base64.b64encode(buff.getvalue())

        # Crée le joueur
        player = Player.objects.create(pseudo=pseudo, password=make_password(password), image=img_str)
        # Génère les tokens
        tokens = generate_tokens(player.id)
        # Prépare les données
        data_return["data"] = dict(
            id=player.id,
            pseudo=player.pseudo,
            image=player.image,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"])

        return Response(data=data_return, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        # Message retour de réussite
        data_return = dict(code=200, message="Connexion réussie", data=None)

        data_request = request.data
        pseudo = data_request.get("pseudo")
        password = data_request.get("password")

        # Vérifie si le pseudo est fourni
        if not pseudo:
            return Response(dict(code=400, message='Pseudo requis', data=None), status=status.HTTP_400_BAD_REQUEST)

        # Vérifie si le password est fourni
        if not password:
            return Response(dict(code=400, message='Password requis', data=None), status=status.HTTP_400_BAD_REQUEST)

        player = Player.objects.filter(pseudo=pseudo).first()

        # Vérifie si le pseudo n'existe pas
        if not player:
            return Response(dict(code=404, message='Pseudo ou mdp incorrect', data=None),
                            status=status.HTTP_404_NOT_FOUND)

        if not check_password(password, player.password):
            return Response(dict(code=404, message='Pseudo ou mdp incorrect', data=None),
                            status=status.HTTP_404_NOT_FOUND)

        # Génère les tokens
        tokens = generate_tokens(player.id)

        # Prépare les données
        data_return["data"] = dict(
            id=player.id,
            pseudo=player.pseudo,
            image=player.image,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"])

        return Response(data=data_return, status=status.HTTP_200_OK)


class StatsView(APIView):
    permission_classes = [IsAuthenticatedWithJWT]
    def get(self, request):
        player = request.player
        data_return = dict(code=200, message="Stats du joueur", data=dict(wins=player.wins, pigs=player.pigs, games=player.games))

        return Response(data=data_return, status=status.HTTP_200_OK)

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
