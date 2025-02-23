extends Node
# API
var API_URL = "https://api--domino--y6qkmxzm7hxr.code.run/"
const headers = ["Content-Type: application/json"]
# Valeur des dominos
var dominos_ref_list = []
# Player
var player_data  # Stocke les infos utilisateur après connexion
var is_logged_in = false  # Statut de connexion
# Tokens
var is_token_fresh = false
var tokens
# Session
var session_infos = {}
# Liste des infos des joueurs dans la session
var player_list_data = []


func get_info(objet: String, key: String, default_value = null):
	if objet == "session":
		return session_infos.get(key, default_value)
	elif objet == "player":
		return player_data.get(key, default_value)

func set_player_data(data: Dictionary):
	tokens = {"access_token": data.access_token, "refresh_token": data.refresh_token}
	is_token_fresh = true
	
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
	is_token_fresh = false
	print("Joueur déconnecté")

# Session
func set_session_data(data: Dictionary, created: bool):
	session_infos = data
	if created:
		add_player_info(data, true)
	
func add_player_info(data: Dictionary, is_hote: bool):
	var info_player = {
		"pseudo": data.pseudo,
		"image": data.image,
		"rounds_win": 0,
		"games_win": data.games_win,
		"ping_count": data.ping_count,
		"hote": is_hote
	}
	player_list_data.append(info_player)

func remove_player_info(pseudo: String):
	for player_info in player_list_data:
		if player_info.pseudo == pseudo:
			player_list_data.erase(player_info)
			return true
	return false

func clear_session_data():
	session_infos.clear()
	player_list_data.clear()


# Request METHOD
func makeRequest(action, method_signal, jsonBody=null, urlParams=null):
	print("--- Make request Début ---")
	print("Paramètres : action = " + str(action) + ", method_signal = " + str(method_signal) + ", urlParams = " + str(urlParams))
	var http_request = HTTPRequest.new()
	http_request.request_completed.connect(method_signal)
	http_request.request_completed.connect(http_request.queue_free.unbind(4))
	add_child(http_request)
	var error; var headers_auth = null
	if tokens != null:
		headers_auth = [
			"Content-Type: application/json",
			"Authorization: Bearer " + tokens.access_token
		]
	
	if action in ["login", "signup"]:
		error = http_request.request(API_URL + action, headers, HTTPClient.Method.METHOD_POST, jsonBody)
	
	if action in ["dominos", "sessions"]:
		error = http_request.request(API_URL + action, headers_auth, HTTPClient.Method.METHOD_GET)
	
	if action in ["create"]:
		error = http_request.request(API_URL + action, headers_auth, HTTPClient.Method.METHOD_POST, jsonBody)
	
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	print("--- Make request Fin ---")

# REFRESH TOKEN

func refreshToken():
	print("--- RefreshToken Début ---")
	is_token_fresh = false
	var action = "access"
	var json_body = JSON.stringify({"refresh_token": tokens.refresh_token})
	var http_request = HTTPRequest.new()
	http_request.request_completed.connect(self._when_token_refreshed)
	http_request.request_completed.connect(http_request.queue_free.unbind(4))
	add_child(http_request)
	var error = http_request.request(API_URL + action, headers, HTTPClient.Method.METHOD_POST, json_body)
	if error != OK:
		push_error("An error occurred in the HTTP request.")
	
	print("--- RefreshToken Fin ---")

func _when_token_refreshed(_result, response_code, _headers, body):
	print("--- _when_token_refreshed Début ---")
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	
	print("response code : ", response_code)
	print("message : ", response.message)
	
	if response_code == HTTPClient.RESPONSE_CREATED:
		tokens.access_token = response.data.access_token
		is_token_fresh = true
	elif response_code == HTTPClient.RESPONSE_UNAUTHORIZED:
		push_error(response.message)
		print("token refresh expiré -- Retour au menu principal")
		changeScene("principal")
	
	print("--- _when_token_refreshed Fin ---")

func changeScene(scene_name: String):
	print("change de scene vers : ",scene_name)
	get_tree().change_scene_to_file("res://Scenes/" + scene_name + ".tscn")

# DOMINOS
func pull_list_dominos():
	self.makeRequest("dominos", _on_list_dominos_pulled)
	pass


func _on_list_dominos_pulled(_result, response_code, _headers, body):
	var json = JSON.new()
	json.parse(body.get_string_from_utf8())
	var response = json.get_data()
	
	if response_code == HTTPClient.RESPONSE_OK:
		dominos_ref_list = response.data.domino_list
	elif response_code == HTTPClient.RESPONSE_UNAUTHORIZED:
		refreshToken()
		while not is_token_fresh:
			pass
		pull_list_dominos()
	else:
		push_error(response.message)
