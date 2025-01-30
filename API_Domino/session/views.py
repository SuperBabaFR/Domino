import json

from django.shortcuts import render

# Create your views here.
import random
import string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from authentification.views import IsAuthenticatedWithJWT
from authentification.models import Session, Player, Game, Domino, Round, HandPlayer, Infosession, Statut




def verify_entry(data):
    # - Validation des entrées :
    player_id = data.get("player_id")
    if not player_id:
        return Response(dict(code=400, message="player_id manquant", data=None), status=status.HTTP_400_BAD_REQUEST)
    player = Player.objects.get(id=player_id)

    if not player:
        return Response(dict(code=404, message="joueur inexistant", data=None), status=status.HTTP_404_NOT_FOUND)



def generate_session_code(length=8):
    while True:
        session_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not Session.objects.filter(code=session_code).exists():
            return session_code


class CreateSessionView(APIView):
    permission_classes = []

    # permission_classes = [IsAuthenticatedWithJWT]
    def post(self, request):
            data_request = request.data
            verify_entry(data_request)

            player_id = data_request.get('player_id')
            max_players_count = data_request.get('max_players_count')
            reflexion_time = data_request.get('reflexion_time')
            definitive_leave = data_request.get('definitive_leave', False)
            if not reflexion_time:
                return Response(dict(code=400, message="reflexion_time manquant", data=None),
                                status=status.HTTP_400_BAD_REQUEST)

            if not max_players_count:
                return Response(dict(code=400, message="max_players_count manquant", data=None),
                                status=status.HTTP_400_BAD_REQUEST)

            if not definitive_leave:
                return Response(dict(code=400, message="definitive_leave manquant", data=None),
                                status=status.HTTP_400_BAD_REQUEST)
            if max_players_count < 2 or max_players_count > 4:
                return Response({"code": 400, "message": "Le nombre de joueurs doit être compris entre 2 et 4."}, status=status.HTTP_400_BAD_REQUEST)

            if reflexion_time < 20 or reflexion_time > 60:
                return Response({"code": 400, "message": "Le temps de réflexion doit être compris entre 20 et 60 secondes."}, status=status.HTTP_400_BAD_REQUEST)

            session_code = generate_session_code()
            player_hote = Player.objects.get(id=player_id)
            order = [player_hote.id]
            order_str = str(order)


            session = Session.objects.create(
                code=session_code,
                hote=player_hote,
                statut=Statut.objects.get(name="En cours"),
                order=order_str,
                max_players_count=max_players_count,
                reflexion_time=reflexion_time,
                definitive_leave=definitive_leave
            )


            infosess = Infosession.objects.create(
                session=session,
                player=player_hote
              #  statut=session.statut
            )


            return Response({
                "code": 201,
                "message": "Session créée",
                "data": {
                    "session_id": session.id,
                    "code": session.code,
                    "hote": player_hote.id,
                    "max_players_count": session.max_players_count,
                    "reflexion_time": session.reflexion_time,
                    "definitive_leave": session.definitive_leave
                }
            }, status=status.HTTP_201_CREATED)



class JoinSessionView(APIView):
    permission_classes = []

    # permission_classes = [IsAuthenticatedWithJWT]
    def post(self, request):
        data_request = request.data


        player_id = data_request.get('player_id')
        session_code = data_request.get('session_code')

        if not player_id:
            return Response({"code": 400, "message": "player_id manque"}, status=status.HTTP_400_BAD_REQUEST)

        if not session_code:
            return Response({"code": 400, "message": "code de session est requis"}, status=status.HTTP_400_BAD_REQUEST)


        session = Session.objects.filter(code=session_code).first()
        if not session:
            return Response({"code": 404, "message": "Session introuvable"}, status=status.HTTP_404_NOT_FOUND)

        player = Player.objects.get(id=player_id)

        order = json.loads(session.order)
        if len(order) >= session.max_players_count:
            return Response({"code": 400, "message": "La session est déjà pleine"}, status=status.HTTP_400_BAD_REQUEST)


        if player_id in order:
            return Response({"code": 400, "message": "Deja dans la session"}, status=status.HTTP_400_BAD_REQUEST)

        order.append(player_id)
        session.order = str(order)


        if not Infosession.objects.filter(session=session, player=player).exists():
            Infosession.objects.create(session=session, player=player)


        players_info = []
        for player_id in order:
            player_x = Player.objects.get(id=player_id)
            player_data = {
                "pseudo": player_x.pseudo,
                "image": player_x.image if player_x.image else "",
                "games_win": player_x.games,
                "ping_count": player_x.pigs
            }
            players_info.append(player_data)


        return Response({
            "code": 201,
            "message": "Session disponible",
            "data": {
                "session_id": session.id,
                "code": session.code,
                "hote": session.hote.id,
                "max_players_count": session.max_players_count,
                "reflexion_time": session.reflexion_time,
                "definitive_leave": session.definitive_leave,
                "players": players_info
            }
        }, status=status.HTTP_201_CREATED)

