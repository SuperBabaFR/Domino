extends Node

var player_data = {}  # Stocke les infos utilisateur après connexion
var is_logged_in = false  # Statut de connexion

func set_player_data(data: Dictionary):
	player_data = data
	is_logged_in = true
	#print("Utilisateur connecté :", player_data)

func get_user_info(key: String, default_value = null):
	return player_data.get(key, default_value)

func get_all_player_data():
	return player_data

func reset_user():
	player_data.clear()
	is_logged_in = false
	print("Utilisateur déconnecté")


func makeRequest(route, jsonBody):
	pass
