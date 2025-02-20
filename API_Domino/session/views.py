import json
import random
import string

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from authentification.models import Session, Player, Game, Domino, Round, HandPlayer, Infosession, Statut
from authentification.views import IsAuthenticatedWithJWT


@shared_task
def notify_session(session_id, action, data=None):
    print(f"notify_session : session_{session_id}, {action}, {data}")
    channel_layer = get_channel_layer()  # Récupérer le Channel Layer de Django Channels
    async_to_sync(channel_layer.group_send)(
        f"session_{session_id}",  # Nom du groupe WebSocket
        {
            "type": "session_players_activity",
            "action": action,
            "data": data
        }
    )


def generate_session_code(length=8):
    while True:
        session_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not Session.objects.filter(code=session_code).exists():
            return session_code


def nuke_session(session):
    Infosession.objects.filter(session=session).delete()
    Game.objects.filter(session=session).delete()
    Round.objects.filter(session=session).delete()
    HandPlayer.objects.filter(session=session).delete()
    session.delete()

class CreateSessionView(APIView):
    permission_classes = [IsAuthenticatedWithJWT]
    def post(self, request):
        # Récupère les infos
        player_hote = request.player
        data_request = request.data

        # Récupère les infos
        max_players_count = data_request.get('max_players_count', False)
        reflexion_time = data_request.get('reflexion_time', False)
        definitive_leave = data_request.get('definitive_leave', False)

        # Vérifie reflexion_time
        if not reflexion_time:
            return Response(dict(code=400, message="reflexion_time manquant", data=None),
                            status=status.HTTP_400_BAD_REQUEST)
        elif reflexion_time < 20 or reflexion_time > 60:
            return Response(dict(code=400, message="Le temps de réflexion doit être compris entre 20 et 60 secondes."),
                status=status.HTTP_400_BAD_REQUEST)

        # Vérifie max_players_count
        if not max_players_count:
            return Response(dict(code=400, message="max_players_count manquant", data=None),
                            status=status.HTTP_400_BAD_REQUEST)
        elif max_players_count < 2 or max_players_count > 4:
            return Response(dict(code=400, message="Le nombre de joueurs doit être compris entre 2 et 4."),
                            status=status.HTTP_400_BAD_REQUEST)

        # Supprime la session existante s'il essaye de creer une nouvelle
        if Session.objects.filter(hote_id=player_hote).exists():
            old_session = Session.objects.filter(hote_id=player_hote).first()
            nuke_session(old_session)

        # Génère un code de session
        session_code = generate_session_code()
        # Stocke l'hôte dans la liste des joueurs
        order_str = json.dumps([player_hote.id])

        # Crée la session
        session = Session.objects.create(
            code=session_code,
            hote=player_hote,
            statut_id=3,
            order=order_str,
            max_players_count=max_players_count,
            reflexion_time=reflexion_time,
            definitive_leave=definitive_leave
        )
        # Renseigne les infos de session du joueurhôte
        infosess = Infosession.objects.create(
            session=session,
            player=player_hote,
            statut_id=6
        )

        return Response({
            "code": 201,
            "message": "Session créée",
            "data": {
                "session_id": session.id,
                "code": session.code,
                "hote": player_hote.pseudo,
                "max_players_count": session.max_players_count,
                "reflexion_time": session.reflexion_time,
                "definitive_leave": session.definitive_leave
            }
        }, status=status.HTTP_201_CREATED)


class JoinSessionView(APIView):

    permission_classes = [IsAuthenticatedWithJWT]
    def get(self, request):
        # Récupère les infos
        session_code = request.query_params.get('session_code', None)
        player = request.player

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
            # Met le statut de la session à full si elle est pleine
            if len(order) == session.max_players_count:
                session.statut_id = 4
            session.order = json.dumps(order)
            session.save()

        info_player = Infosession.objects.filter(session=session, player=player).first()

        # Récupère les infos du joueur
        if not info_player:
            # sinon on les crée
            info_player = Infosession.objects.create(session=session, player=player, statut_id=6)

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

        # Notifie les joueurs connectés à la session du nouveau joueur
        data_notify = dict(
            player=player.pseudo,
            image=player.image,
            wins=info_player.games_win,
            pigs=info_player.pig_count
        )

        notify_session.apply_async(args=(session.id, "join", data_notify))

        return Response({
            "code": 200,
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
        }, status=status.HTTP_200_OK)


class LeaveSessionView(APIView):

    permission_classes = [IsAuthenticatedWithJWT]
    def get(self, request):
        session_id = request.query_params.get('session_id', None)
        player = request.player

        if not session_id:
            return Response(dict(code=400, message="session_id manquant", data=None),
                            status=status.HTTP_400_BAD_REQUEST)
        session = Session.objects.filter(id=session_id).first()

        if not session:
            return Response(dict(code=404, message="session inexistante", data=None), status=status.HTTP_404_NOT_FOUND)

        if session.hote == player:
            # Notifie les joueurs connectés à la session qu'elle a été supprimée
            notify_session.apply_async(args=(session.id, "exit"))
            # notify_session(session.id, "exit")

            # Supprime la session
            nuke_session(session)

            return Response({
                "code": 200,
                "message": "Session supprimée",
                "data": None
            }, status=status.HTTP_200_OK)

        if not session.game_id:

            order = json.loads(session.order)

            # Vérifie si le joueur à déjà été dans la session
            if player.id not in order:
                return Response({"code": 400, "message": "Le joueur n'appartiens pas à la partie."},
                                status=status.HTTP_400_BAD_REQUEST)

            order.remove(player.id)

            # Met le statut de la session à open si elle libère une place
            if session.statut.name == "session.is_full":
                session.statut_id = 3

            session.order = json.dumps(order)
            session.save()
        else:
            Infosession.objects.filter(session=session, player=player).update(statut_id=10)


        # Notifie les joueurs connectés à la session du joueur qui a quitté
        data_notify = dict(
            player=player.pseudo
        )
        notify_session.apply_async(args=(session.id, "leave", data_notify))
        # notify_session(session.id, "leave", data_notify)

        return Response({
            "code": 200,
            "message": "Session quittée",
            "data": None
        }, status=status.HTTP_200_OK)


# class