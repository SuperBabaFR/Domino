import cProfile
import pstats
import io

from django.db import connection
from rest_framework.utils import json
from rest_framework.views import APIView
from authentification.models import Session, Infosession, Game
from authentification.views import IsAuthenticatedWithJWT
from game.methods import *
from game.serializers import DominoSerializer
from game.tasks import play_domino, auto_play_domino_task


class CreateGame(APIView):
    permission_classes = [IsAuthenticatedWithJWT]

    def get(self, request):
        session_id = request.query_params.get('session_id', None)
        data_return = dict(code=201, message="Nouvelle partie lancée", data=None)

        if not session_id:
            return Response(dict(code=400, message=f'session_id manquant', data=None), status=status.HTTP_400_BAD_REQUEST)

        # Objets
        session = Session.objects.filter(id=session_id).first()
        player_hote = request.player

        # Vérifie l'existence de la session
        if not session:
            return Response(dict(code=400, message=f'Session inexistante', data=None), status=status.HTTP_400_BAD_REQUEST)

        # Joueur pas hote de session
        if session.hote != player_hote:
            return Response(dict(code=404, message="joueur non hote de la session", data=None),
                            status=status.HTTP_404_NOT_FOUND)

        player_id_list = json.loads(session.order)  # Liste des joueurs

        # Vérifie qu'il y a au moins deux joueurs
        if len(player_id_list) < 2:
            return Response(dict(code=400, message="Il n'y a pas assez de joueurs dans la session", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        # Vérifie si une partie n'est pas déjà en cours
        if session.game_id:
            if session.game_id.statut.id == 1:
                return Response(dict(code=400, message="Une partie est déjà en cours", data=None),
                                status=status.HTTP_400_BAD_REQUEST)

        # Si un joueur n'est pas prêt on crée pas de partie
        for player_id in player_id_list:
            info_player = Infosession.objects.get(session=session, player_id=player_id)

            if info_player.statut.id != 7:  # player.is_ready
                return Response(dict(code=400, message="Tout les joueurs ne sont pas prêts", data=None),
                                status=status.HTTP_400_BAD_REQUEST)

            info_player.round_wins = 0
            info_player.save()

        # Crée une partie
        game = Game.objects.create(session_id=session, statut_id=1)
        session.game_id = game
        session.statut_id = 5
        session.save()

        data_return["data"] = new_round(session, True)

        player_time_end = data_return["data"]["player_time_end"]
        round_id = data_return["data"]["round_id"]
        player_turn_id = Round.objects.get(id=round_id).player_turn.id
        dt_utc = datetime.strptime(player_time_end, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        auto_play_domino_task.apply_async(args=(player_turn_id, session.id, round_id), eta=dt_utc)

        # Transmet à l’hôte ses dominos
        return Response(data_return, status=status.HTTP_201_CREATED)


class PlaceDomino(APIView):
    permission_classes = [IsAuthenticatedWithJWT]

    def post(self, request):
        data_request = request.data
        player = request.player

        # Vérifie l'existance des keys dans le body
        keys = ["session_id", "round_id", "domino_id", "side"]

        response = verify_values(data_request, keys)
        if response:
            return response

        # Objets
        session = Session.objects.filter(id=data_request.get("session_id")).first()
        domino = Domino.objects.filter(id=data_request.get("domino_id")).first()
        round = Round.objects.filter(id=data_request.get("round_id")).first()
        # Liste
        domino_list = list(Domino.objects.all())  # Liste des dominos
        # Valeurs
        side = data_request.get("side")

        # Vérifie l'existence des objets
        objets_list = dict(session=session, domino=domino, round=round)
        response = verify_objets(objets_list)
        if response:
            return response

        # Side bien renseigné
        if not (side == "left" or side == "right"):
            return Response(dict(code=400, message="side mal renseigné (left or right)", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        #  Vérifier que c’est bien son tour
        if player != round.player_turn:
            return Response(dict(code=400, message="Ce n'est pas ton tour", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        #  Vérifier que c’est bien le round en cours
        if round.statut.name == "round.is_terminated":
            return Response(dict(code=400, message="Ce round est déjà fini", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        # Dominos du joueurs
        hand_player = HandPlayer.objects.filter(player=player, round=round, session=session).first()

        if not hand_player:
            return Response(dict(code=404, message="Le joueur n'a pas de données dans ce round", data=None),
                            status=status.HTTP_404_NOT_FOUND)

        player_dominoes: list = json.loads(hand_player.dominoes)
        #  Vérifie qu’il possède bien le domino
        if domino.id not in player_dominoes:
            return Response(dict(code=404, message="Le joueur ne possède pas le domino mentionné", data=None),
                            status=status.HTTP_404_NOT_FOUND)

        # Dominos sur la table
        table_de_jeu: list = json.loads(round.table)

        for domino_on_table in table_de_jeu:
            if domino_on_table['id'] == domino.id:
                return Response(dict(code=400, message="Le domino est déjà sur la table ...", data=None),
                                status=status.HTTP_400_BAD_REQUEST)

        # Vérifie si le joueur qui commence joue bien son plus gros domino
        if len(table_de_jeu) == 0 and round.game.last_winner is None and max(player_dominoes) != domino.id:
            return Response(dict(code=400, message="Le joueur doit jouer son plus gros domino", data=None),
                            status=status.HTTP_400_BAD_REQUEST)

        playable_values = domino_playable(domino, table_de_jeu, side, domino_list)
        # Si ce n'est pas le premier domino à poser, on vérifie qu'il est bien jouable
        if len(table_de_jeu) > 0 and playable_values == False:
            return Response(dict(code=400, message="Domino non jouable", data=None),
                            status=status.HTTP_400_BAD_REQUEST)  # Domino non jouable

        data_return = play_domino(player, session, round, domino_list, side, playable_values, domino)

        return Response(data_return, status=status.HTTP_200_OK)

class DominoList(APIView):
    permission_classes = [IsAuthenticatedWithJWT]
    def get(self, request):
        serializer = DominoSerializer(Domino.objects.all(), many=True)
        data = dict(code=200, message="Liste de tout les dominos", data=dict(domino_list=serializer.data))
        return Response(data, status=status.HTTP_200_OK)