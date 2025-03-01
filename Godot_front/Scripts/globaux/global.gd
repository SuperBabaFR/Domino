extends Node
# Valeur des dominos
var dominos_ref_list = []
# Player
var player_data: Dictionary  # Stocke les infos utilisateur après connexion
var is_logged_in = false  # Statut de connexion
# Session
var session_infos: Dictionary
# Liste des infos des joueurs dans la session
var player_list_data = []

var game_data = {"table" : []}

func get_info(objet: String, key: String, default_value = null):
	if objet == "session":
		return session_infos.get(key, default_value)
	elif objet == "player":
		return player_data.get(key, default_value)

func set_player_data(data: Dictionary):
	data.erase("access_token")
	data.erase("refresh_token")
	player_data = data
	is_logged_in = true
	print("Joueur connecté :", player_data.pseudo)

func get_all_player_data():
	return player_data

func reset_player():
	player_data.clear()
	is_logged_in = false
	API.tokens = null
	print("Joueur déconnecté")

# Session
func set_session_data(data: Dictionary, created: bool):
	session_infos = data
	print(session_infos)
	if created:
		var data_creator = {
			"pseudo": player_data.pseudo,
			"image": player_data.image,
			"games_win": 0,
			"pig_count": 0,
			"statut": "player.is_not_ready"
		}
		add_player_info(data_creator)

func update_session_data(data: Dictionary):
	print("old data : ",session_infos)
	session_infos.merge(data, true)
	print("new data : ",session_infos)
	
func add_player_info(data: Dictionary):	
	if not data.has("statut"):
		data["statut"] = "player.not_ready"
	
	var info_player = {
		"pseudo": data.pseudo,
		"image": data.image,
		"rounds_win": 0,
		"domino_count": 7,
		"games_win": data.games_win,
		"pig_count": data.pig_count,
		"statut": data.statut
	}
	player_list_data.append(info_player)

func remove_player_info(pseudo: String):
	for player_info in player_list_data:
		if player_info.pseudo == pseudo:
			player_list_data.erase(player_info)
			return true
	return false

func get_player_info(pseudo: String):
	for player_info in player_list_data:
		if player_info.pseudo == pseudo:
			return player_info
	return false

func get_all_players_infos():
	return player_list_data

func clear_session_data():
	session_infos.clear()
	player_list_data.clear()

func set_game_data(data: Dictionary):
	game_data.merge(data)

func update_game_data(data: Dictionary):
	game_data.player_turn = data.player_turn
	game_data.player_time_end = data.player_time_end

func update_scores(data: Dictionary):
	var winner = data.results.winner
	var pigs = data.results.pigs
	
	for player in player_list_data:
		if player.pseudo == winner:
			player.games_win += 1
			continue
		if player.pseudo in pigs:
			player.pigs_count += 1
			
