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
    player = Player.objects.filter(id=player_id).first()

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

        # Vérifie les entrées communes
        response = verify_entry(data_request)
        if response:
            return response

        # Récupère les infos
        player_hote = Player.objects.filter(id=data_request.get('player_id')).first()
        max_players_count = data_request.get('max_players_count')
        reflexion_time = data_request.get('reflexion_time')
        definitive_leave = data_request.get('definitive_leave', False)

        # Vérifie reflexion_time
        if not reflexion_time:
            return Response(dict(code=400, message="reflexion_time manquant", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        if reflexion_time < 20 or reflexion_time > 60:
            return Response(
                {"code": 400, "message": "Le temps de réflexion doit être compris entre 20 et 60 secondes."},
                status=status.HTTP_400_BAD_REQUEST)

        # Vérifie max_players_count
        if not max_players_count:
            return Response(dict(code=400, message="max_players_count manquant", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        if max_players_count < 2 or max_players_count > 4:
            return Response({"code": 400, "message": "Le nombre de joueurs doit être compris entre 2 et 4."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Vérifie definitive_leave
        if definitive_leave is None:
            return Response(dict(code=400, message="definitive_leave manquant", data=None),
                            status=status.HTTP_400_BAD_REQUEST)


        # Supprime la session existante si il essaye de creer une nouvelle 
        if Session.objects.filter(hote_id=player_hote).exists():
            session_exist = Session.objects.filter(hote_id=player_hote)
            session_id = session_exist.first().id
            infosession =  Infosession.objects.filter(session_id=session_id)
            game = Game.objects.filter(session_id=session_id)
            round = Round.objects.filter(session_id=session_id)
            handplayer = HandPlayer.objects.filter(session_id=session_id)
            if handplayer:
                handplayer.delete()
            if infosession:
                infosession.delete()
            if game:
                game.delete()
            if round:
                round.delete()
            session_exist.delete()




        # Génère un code de session
        session_code = generate_session_code()
        # Stocke l'hôte dans la liste des joueurs
        order_str = str([player_hote.id])


        # Crée la session
        session = Session.objects.create(
            code=session_code,
            hote=player_hote,
            statut=Statut.objects.get(id=3),
            order=order_str,
            max_players_count=max_players_count,
            reflexion_time=reflexion_time,
            definitive_leave=definitive_leave
        )
        # Renseigne les infos de session du joueurhôte
        infosess = Infosession.objects.create(
            session=session,
            player=player_hote,
            statut=Statut.objects.get(id=6)
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

        # Vérifie les entrées communes
        response = verify_entry(data_request)
        if response:
            return response

        # Récupère les infos
        player = Player.objects.filter(id=data_request.get('player_id')).first()
        session_code = data_request.get('session_code')

        # Vérifie que le code est fourni
        if not session_code:
            return Response({"code": 400, "message": "code de session est requis"}, status=status.HTTP_400_BAD_REQUEST)

        # Vérifie si la session existe
        session = Session.objects.filter(code=session_code).first()
        if not session:
            return Response({"code": 404, "message": "Session introuvable"}, status=status.HTTP_404_NOT_FOUND)

        # Charge la liste des joueurs présents
        order = json.loads(session.order)

        # Vérifie si le joueur à déjà été dans la session
        if player.id not in order:
            # Si y'a de la place pour lui
            if len(order) >= session.max_players_count:
                return Response({"code": 400, "message": "La session est déjà pleine"},
                                status=status.HTTP_400_BAD_REQUEST)
            # On l'ajoute
            order.append(player.id)
            session.order = str(order)
            session.save()

        # Récupère les infos du joueur
        if not Infosession.objects.filter(session=session, player=player).exists():
            # sinon on les crée
            Infosession.objects.create(session=session, player=player, statut=Statut.objects.get(id=6))

        # Charge les infos des joueurs présenta dans la session
        players_info = []
        for player_id in order:
            player_x = Player.objects.get(id=player_id)
            info_player_x = Infosession.objects.get(session=session, player_id=player_id)
            player_data = {
                "pseudo": player_x.pseudo,
                "image": player_x.image,
                "statut": info_player_x.statut.name,
                "games_win": info_player_x.games_win,
                "ping_count": info_player_x.pig_count
            }
            players_info.append(player_data)

        return Response({
            "code": 201,
            "message": "Session disponible",
            "data": {
                "session_id": session.id,
                "session_code": session.code,
                "hote": session.hote.pseudo,
                "max_players_count": session.max_players_count,
                "reflexion_time": session.reflexion_time,
                "definitive_leave": session.definitive_leave,
                "players": players_info
            }
        }, status=status.HTTP_201_CREATED)


class LeaveSessionView(APIView):

    def get(self, request):
        data_request = request.data
        response = verify_entry(data_request)
        if response:
            return response


        session_id = data_request.get('session_id')
        player = Player.objects.filter(id=data_request.get('player_id')).first()

        if not session_id:
            return Response(dict(code=400, message="session_id manquant", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        session = Session.objects.filter(id=session_id).first()
        if not session:
            return Response({"code": 404, "message": "Session introuvable"}, status=status.HTTP_404_NOT_FOUND)

        order = json.loads(session.order)
        # if player.id in order:
        #     return

        # Vérifie si le joueur à déjà été dans la session
        if player.id not in order:
            return Response({"code": 400, "message": "Le joueur n'appartiens pas à la partie."},
                            status=status.HTTP_400_BAD_REQUEST)

        order.remove(player.id)
        session.order = str(order)
        session.save()

        # Récupère les infos du joueur
        infosession_player = Infosession.objects.filter(session=session, player=player).first()
        if infosession_player:
            Infosession.objects.filter(session=session, player=player).delete()

    #TODO PREVOIR LA CAS DE L'HOTE
