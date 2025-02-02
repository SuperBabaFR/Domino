from django.db import models


class Player(models.Model):
    pseudo = models.TextField(max_length=20, unique=True)
    password = models.TextField(max_length=20)
    image = models.TextField(null=True, blank=True)
    wins = models.IntegerField(default=0)
    pigs = models.IntegerField(default=0)
    games = models.IntegerField(default=0)

    class Meta:
        db_table = 'Player'


class Domino(models.Model):
    left = models.IntegerField()
    right = models.IntegerField()

    class Meta:
        db_table = 'Domino'


class Statut(models.Model):
    name = models.TextField()

    class Meta:
        db_table = 'Statut'


class Session(models.Model):
    code = models.CharField(max_length=8, unique=True)
    hote = models.ForeignKey(Player, models.DO_NOTHING)
    game_id = models.ForeignKey('Game', models.SET_NULL, null=True, blank=True, db_column="game_id")
    statut = models.ForeignKey(Statut, models.SET_NULL, null=True)
    order = models.TextField()
    max_players_count = models.IntegerField(default=4)
    reflexion_time = models.IntegerField(default=20)
    definitive_leave = models.BooleanField(default=False)

    class Meta:
        db_table = 'Session'


class Game(models.Model):
    session_id = models.ForeignKey(Session, models.CASCADE, db_column="session_id")
    statut = models.ForeignKey(Statut, models.SET_NULL, null=True)
    round_count = models.IntegerField(default=1)
    last_winner = models.ForeignKey(Player, models.SET_NULL, null=True, blank=True, db_column="last_winner_id")

    class Meta:
        db_table = 'Game'


class Round(models.Model):
    game = models.ForeignKey(Game, models.CASCADE, db_column="game_id")
    session = models.ForeignKey(Session, models.CASCADE, db_column="session_id")
    statut = models.ForeignKey(Statut, models.SET_NULL, null=True)
    table = models.TextField(blank=True, null=True)
    last_player = models.ForeignKey(Player, models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'Round'


class Infosession(models.Model):
    session = models.ForeignKey(Session, models.CASCADE)
    player = models.ForeignKey(Player, models.CASCADE)
    statut = models.ForeignKey(Statut, models.SET_NULL, null=True)
    round_win = models.IntegerField(default=0)
    games_win = models.IntegerField(default=0)
    pig_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'InfoSession'
        unique_together = ('session', 'player')  # Définir l'unicité combinée


class HandPlayer(models.Model):
    round = models.OneToOneField(Round, models.CASCADE)
    session = models.ForeignKey(Session, models.CASCADE)
    player = models.ForeignKey(Player, models.CASCADE, db_column="player_id")
    dominoes = models.TextField()

    class Meta:
        db_table = 'HandPlayer'
