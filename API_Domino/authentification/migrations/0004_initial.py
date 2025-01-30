# Generated by Django 5.1.5 on 2025-01-29 16:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentification', '0003_delete_domino_remove_session_game_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Domino',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('left', models.IntegerField()),
                ('right', models.IntegerField()),
            ],
            options={
                'db_table': 'Domino',
            },
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pseudo', models.TextField(max_length=20, unique=True)),
                ('password', models.TextField(max_length=20)),
                ('image', models.TextField(blank=True, null=True)),
                ('wins', models.IntegerField(default=0)),
                ('pigs', models.IntegerField(default=0)),
                ('games', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'Player',
            },
        ),
        migrations.CreateModel(
            name='Statut',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
            ],
            options={
                'db_table': 'Statut',
            },
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_count', models.IntegerField(default=0)),
                ('last_winner', models.ForeignKey(blank=True, db_column='last_winner_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to='authentification.player')),
            ],
            options={
                'db_table': 'Game',
            },
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=8, unique=True)),
                ('order', models.TextField()),
                ('max_players_count', models.IntegerField(default=4)),
                ('reflexion_time', models.IntegerField(default=20)),
                ('definitive_leave', models.BooleanField(default=False)),
                ('game_id', models.ForeignKey(blank=True, db_column='game_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to='authentification.game')),
                ('hote', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='authentification.player')),
                ('statut', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='authentification.statut')),
            ],
            options={
                'db_table': 'Session',
            },
        ),
        migrations.CreateModel(
            name='Round',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('table', models.TextField(blank=True, null=True)),
                ('game', models.ForeignKey(db_column='game_id', on_delete=django.db.models.deletion.CASCADE, to='authentification.game')),
                ('last_player', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='authentification.player')),
                ('session', models.ForeignKey(db_column='session_id', on_delete=django.db.models.deletion.CASCADE, to='authentification.session')),
            ],
            options={
                'db_table': 'Round',
            },
        ),
        migrations.AddField(
            model_name='game',
            name='session_id',
            field=models.ForeignKey(db_column='session_id', on_delete=django.db.models.deletion.CASCADE, to='authentification.session'),
        ),
        migrations.AddField(
            model_name='game',
            name='statut',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='authentification.statut'),
        ),
        migrations.CreateModel(
            name='HandPlayer',
            fields=[
                ('round', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='authentification.round')),
                ('dominoes', models.TextField()),
                ('player', models.ForeignKey(db_column='player_id', on_delete=django.db.models.deletion.CASCADE, to='authentification.player')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentification.session')),
            ],
            options={
                'db_table': 'HandPlayer',
            },
        ),
        migrations.CreateModel(
            name='Infosession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round_win', models.IntegerField(default=0)),
                ('games_win', models.IntegerField(default=0)),
                ('pig_count', models.IntegerField(default=0)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentification.player')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentification.session')),
                ('statut', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='authentification.statut')),
            ],
            options={
                'db_table': 'InfoSession',
                'unique_together': {('session', 'player')},
            },
        ),
    ]
