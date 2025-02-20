extends Node

var user_data = {}  # Stocke les infos utilisateur après connexion
var is_logged_in = false  # Statut de connexion

func set_user_data(data: Dictionary):
	user_data = data
	is_logged_in = true
	#print("Utilisateur connecté :", user_data)

func get_user_info(key: String, default_value = null):
	return user_data.get(key, default_value)

func get_all_user_data():
	return user_data

func reset_user():
	user_data.clear()
	is_logged_in = false
	print("Utilisateur déconnecté")
